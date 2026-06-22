from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.dependencies import get_current_user
from models import User, Profile
from schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])

# 10 MB upper bound on resume uploads. Larger files are almost always
# scanned PDFs (which we can't parse anyway) or junk.
MAX_RESUME_BYTES = 10 * 1024 * 1024


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.put("/me", response_model=ProfileOut)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)

    if data.tech_stack is not None:
        profile.tech_stack = data.tech_stack
    if data.years_of_exp is not None:
        profile.years_of_exp = data.years_of_exp
    if data.current_level is not None:
        profile.current_level = data.current_level
    if data.target_companies is not None:
        profile.target_companies = data.target_companies
    if data.resume_text is not None:
        # Treat resume_text as the raw extracted text — store as-is in
        # resume_summary. We don't LLM-summarize on save; that happens
        # at upload time and the result is reviewed by the user.
        profile.resume_summary = data.resume_text
    if data.skill_map is not None:
        profile.skill_map = data.skill_map

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/resume")
async def upload_resume(
    file: UploadFile = File(..., description="PDF 简历，最大 10MB"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF resume. Returns extracted structured fields for review.

    Does NOT auto-save to Profile — the user reviews the LLM extraction
    and clicks save explicitly. This guards against LLM hallucinations
    silently polluting the profile.

    Response:
      {
        "extracted": {tech_stack, years_of_exp, current_level, skill_map, suggested_target_companies},
        "resume_text": "...",       # raw extracted text (first 8KB)
        "page_count": N,
        "is_scanned": bool,
        "file_name": "...",
        "file_size": N,
        "warning": "...or null"
      }
    """
    import logging
    from services.resume_parser import (
        extract_text_from_pdf,
        extract_profile_from_text,
        is_likely_scanned,
        save_pdf_to_disk,
    )

    # Validate content type. Browsers usually set this correctly for PDFs;
    # some don't, so we also check the file extension as a fallback.
    ct = (file.content_type or "").lower()
    fname = (file.filename or "").lower()
    if ct and "pdf" not in ct and not fname.endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"仅支持 PDF 文件，收到: {ct}")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="上传的文件为空")
    if len(pdf_bytes) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"文件超过 10MB 限制（{len(pdf_bytes) // (1024*1024)}MB）",
        )

    # Step 1: extract text
    text, page_count = extract_text_from_pdf(pdf_bytes)
    scanned = is_likely_scanned(text, page_count)

    # Scanned-PDF fallback: render pages and OCR them via DashScope.
    # If OCR works we proceed normally; if it fails too we surface a
    # clear message and let the user fill the form manually.
    if scanned or not text.strip():
        from services.resume_parser import extract_text_from_pdf_via_ocr

        save_pdf_to_disk(pdf_bytes, user.id, settings.upload_dir)
        try:
            ocr_text, ocr_pages = await extract_text_from_pdf_via_ocr(pdf_bytes)
        except Exception as e:
            import logging
            logging.getLogger("codemock.profile").warning(f"OCR fallback failed: {e}")
            ocr_text = ""

        if not ocr_text.strip():
            return {
                "extracted": None,
                "resume_text": "",
                "page_count": page_count,
                "is_scanned": True,
                "file_name": file.filename,
                "file_size": len(pdf_bytes),
                "warning": "扫描件 PDF 且 OCR 失败（请检查 DASHSCOPE_API_KEY 或手动填写）。",
            }

        # OCR succeeded — feed the OCR text through the same LLM pipeline.
        text = ocr_text
        # Note: page_count from pypdf is still authoritative even if OCR
        # processed a different number (e.g., blank pages).

    # Step 2: LLM extraction
    try:
        extracted = await extract_profile_from_text(text)
    except Exception as e:
        # Save the file but return what we have so the user can fill the
        # form manually. Don't fail the upload — we got something.
        save_pdf_to_disk(pdf_bytes, user.id, settings.upload_dir)
        logging.getLogger("codemock.profile").warning(f"resume LLM extraction failed: {e}")
        return {
            "extracted": None,
            "resume_text": text[:8000],
            "page_count": page_count,
            "is_scanned": False,
            "file_name": file.filename,
            "file_size": len(pdf_bytes),
            "warning": f"AI 抽取失败（{type(e).__name__}）。请手动填写。",
        }

    # Step 3: save PDF to disk (for future "view original" side-drawer)
    save_pdf_to_disk(pdf_bytes, user.id, settings.upload_dir)

    return {
        "extracted": extracted,
        "resume_text": text[:8000],
        "page_count": page_count,
        "is_scanned": False,
        "file_name": file.filename,
        "file_size": len(pdf_bytes),
        "warning": None,
    }


@router.delete("/resume")
async def delete_resume(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the saved resume PDF + clear extracted fields."""
    import os
    import glob
    user_dir = os.path.join(settings.upload_dir, user.id)
    removed = 0
    if os.path.isdir(user_dir):
        for path in glob.glob(os.path.join(user_dir, "resume_*.pdf")):
            try:
                os.remove(path)
                removed += 1
            except OSError:
                pass

    # Clear resume-related fields on the profile
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is not None:
        profile.resume_summary = None
        profile.skill_map = {}
        await db.commit()

    return {"deleted_files": removed, "ok": True}


@router.get("/resume/file")
async def get_resume_file(
    user: User = Depends(get_current_user),
):
    """Serve the user's most recent resume PDF.

    Returns the file bytes inline (not as attachment) so the side-drawer
    can render it in an <iframe>. Falls back to the most-recent
    resume_*.pdf when multiple exist (hash dedupes identical uploads,
    so usually there's only one).
    """
    import os
    import glob
    from fastapi.responses import FileResponse

    user_dir = os.path.join(settings.upload_dir, user.id)
    if not os.path.isdir(user_dir):
        raise HTTPException(status_code=404, detail="尚未上传简历")

    pdfs = sorted(
        glob.glob(os.path.join(user_dir, "resume_*.pdf")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not pdfs:
        raise HTTPException(status_code=404, detail="尚未上传简历")

    # Pick the most recently uploaded. Path stays inside user_dir because
    # we glob'd there, so no traversal risk.
    latest = pdfs[0]
    return FileResponse(
        latest,
        media_type="application/pdf",
        filename=os.path.basename(latest),
        # inline (not attachment) so the browser opens it in the iframe,
        # not as a download. Users can still right-click → save.
        headers={"Content-Disposition": "inline"},
    )