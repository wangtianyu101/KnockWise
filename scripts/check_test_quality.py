#!/usr/bin/env python3
"""Reject empty, placeholder, or undocumented skipped Python tests.

The checker deliberately does not require a literal ``assert`` in every test:
``pytest.raises``, mock assertions, and assertion helpers are all valid styles.
Instead, it blocks the structural patterns that create false-green pytest runs.
"""
from __future__ import annotations

import argparse
import ast
import io
import re
import tokenize
from dataclasses import dataclass
import datetime
from pathlib import Path
from typing import Iterable, Sequence


PLACEHOLDER_PATTERN = re.compile(
    r"(?:\b(?:todo|fixme|xxx|placeholder)\b|待实现|待补|未实现)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    test_name: str
    message: str


def _call_name(node: ast.AST) -> str:
    """Return a dotted name for simple calls such as pytest.mark.skip."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _is_nonempty_reason(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and bool(node.value.strip())
    # Dynamic reasons (for example f-strings containing a path) are documented.
    return isinstance(node, (ast.FormattedValue, ast.JoinedStr, ast.Name, ast.Attribute))


def _reason_from_call(call: ast.Call, *, skipif: bool) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == "reason":
            return keyword.value
    position = 1 if skipif else 0
    if len(call.args) > position:
        return call.args[position]
    return None


def _is_skip_decorator(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    name = _call_name(target)
    return name.endswith((".skip", ".skipif")) or name in {"skip", "unittest.skip"}


def _is_xfail_decorator(decorator: ast.expr) -> bool:
    """P1-4: 识别 @pytest.mark.xfail / @pytest.xfail"""
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    name = _call_name(target)
    return name.endswith((".xfail",)) or name == "xfail"


# P1-4: xfail metadata 4 字段
_XFAIL_REQUIRED_FIELDS = ("owner", "issue", "expiry", "reason")
_XFAIL_FIELD_RE = re.compile(r"\b(owner|issue|expiry|reason)\s*=\s*([^;,\n]+)")


def _extract_xfail_metadata(reason_str: str) -> dict:
    """从 reason 字符串提取 4 字段 metadata"""
    return {m.group(1): m.group(2).strip() for m in _XFAIL_FIELD_RE.finditer(reason_str)}


def _is_static_string(node: ast.AST) -> bool:
    """reason 必须是静态字符串 (允许常量拼接)"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return _is_static_string(node.left) and _is_static_string(node.right)
    if isinstance(node, ast.JoinedStr):
        return all(_is_static_string(v) for v in node.values if isinstance(v, ast.FormattedValue))
    return False


def _get_xfail_strict(decorator: ast.expr) -> bool:
    """从 @pytest.mark.xfail(strict=...) 取 strict 值；默认 True"""
    if not isinstance(decorator, ast.Call):
        return True  # 没参数 → strict 默认真
    for kw in decorator.keywords:
        if kw.arg == "strict":
            if isinstance(kw.value, ast.Constant):
                return bool(kw.value.value)
            return True
    return True


def _xfail_decorator_violations(decorators: Iterable[ast.expr]) -> list[Violation]:
    """P1-4 决策: 4 个 violation code:
    - test-debt-metadata: 缺字段
    - xfail-not-strict: strict=False
    - test-debt-expired: expiry < today
    - test-debt-budget-exceeded: 总数超预算 (预算统计由 main() 传)
    """
    violations = []
    today = datetime.date.today()
    for dec in decorators:
        if not _is_xfail_decorator(dec):
            continue
        # reason must be static string
        reason_node = _reason_from_call(dec if isinstance(dec, ast.Call) else ast.Call(func=dec, args=[], keywords=[]), skipif=False)
        if reason_node is None or not _is_static_string(reason_node):
            violations.append(Violation(
                path=Path("<xfail>"), lineno=0,
                code="test-debt-metadata",
                message="xfail reason must be a static string (no f-strings, no variables)",
            ))
            continue
        if not isinstance(reason_node, ast.Constant):
            continue
        reason_str = reason_node.value
        # extract 4 fields
        fields = _extract_xfail_metadata(reason_str)
        missing = [f for f in _XFAIL_REQUIRED_FIELDS if f not in fields]
        if missing:
            violations.append(Violation(
                path=Path("<xfail>"), lineno=0,
                code="test-debt-metadata",
                message=f"xfail reason missing fields: {missing} (need: owner=...; issue=...; expiry=YYYY-MM-DD; reason=...)",
            ))
            continue
        # expiry 格式 + 是否过期
        try:
            exp_date = datetime.date.fromisoformat(fields["expiry"])
            if exp_date < today:
                violations.append(Violation(
                    path=Path("<xfail>"), lineno=0,
                    code="test-debt-expired",
                    message=f"xfail expired on {fields['expiry']} (today: {today.isoformat()})",
                ))
        except ValueError:
            violations.append(Violation(
                path=Path("<xfail>"), lineno=0,
                code="test-debt-metadata",
                message=f"xfail expiry must be ISO YYYY-MM-DD (got: {fields['expiry']!r})",
            ))
        # strict
        if not _get_xfail_strict(dec):
            violations.append(Violation(
                path=Path("<xfail>"), lineno=0,
                code="xfail-not-strict",
                message="@pytest.mark.xfail must be strict=True (per P1-4 decision)",
            ))
    return violations


def _has_skip_decorator(decorators: Iterable[ast.expr]) -> bool:
    return any(_is_skip_decorator(decorator) for decorator in decorators)


def _skip_decorator_without_reason(decorators: Iterable[ast.expr]) -> ast.AST | None:
    for decorator in decorators:
        if isinstance(decorator, ast.Call):
            name = _call_name(decorator.func)
            if name.endswith(".skipif"):
                if not _is_nonempty_reason(_reason_from_call(decorator, skipif=True)):
                    return decorator
            elif name.endswith(".skip") or name in {"skip", "unittest.skip"}:
                if not _is_nonempty_reason(_reason_from_call(decorator, skipif=False)):
                    return decorator
        else:
            name = _call_name(decorator)
            if name.endswith(".skip") or name in {"skip", "unittest.skip"}:
                return decorator
    return None


def _runtime_skip_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and _call_name(node.func) in {"pytest.skip", "skip"}
    ]


def _skip_without_reason(function: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST | None:
    """Return the first undocumented skip decorator/call, if present."""
    decorator = _skip_decorator_without_reason(function.decorator_list)
    if decorator is not None:
        return decorator

    for node in _runtime_skip_calls(function):
        if not _is_nonempty_reason(_reason_from_call(node, skipif=False)):
            return node
    return None


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _is_noop_statement(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.Pass):
        return True
    if isinstance(statement, ast.Expr):
        return isinstance(statement.value, ast.Constant) and statement.value.value is Ellipsis
    if isinstance(statement, ast.Return):
        return statement.value is None or (
            isinstance(statement.value, ast.Constant) and statement.value.value is None
        )
    return False


def _is_empty_test(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(function.body)
    if body and _is_docstring(body[0]):
        body = body[1:]
    return not body or all(_is_noop_statement(statement) for statement in body)


def _comment_markers(source: str) -> dict[int, str]:
    markers: dict[int, str] = {}
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            match = PLACEHOLDER_PATTERN.search(token.string)
            if match:
                markers[token.start[0]] = match.group(0)
    except tokenize.TokenError:
        # ast.parse reports the actionable syntax error separately.
        pass
    return markers


def _placeholder_marker(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    comment_markers: dict[int, str],
) -> tuple[int, str] | None:
    docstring = ast.get_docstring(function, clean=False)
    if docstring:
        match = PLACEHOLDER_PATTERN.search(docstring)
        if match:
            first_statement = function.body[0]
            return first_statement.lineno, match.group(0)

    for line, marker in sorted(comment_markers.items()):
        if function.lineno <= line <= (function.end_lineno or function.lineno):
            return line, marker
    return None


def scan_file(path: Path) -> tuple[list[Violation], int]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [
            Violation(
                path=path,
                line=error.lineno or 1,
                code="syntax-error",
                test_name="<module>",
                message=error.msg,
            )
        ], 0

    comments = _comment_markers(source)
    violations: list[Violation] = []
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    # P1-4: xfail violations (function-level)
    for function in ast.walk(tree):
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_xfail_decorator_violations(function.decorator_list))

    tests = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    tests.sort(key=lambda node: (node.lineno, node.name))

    for function in tests:
        skip_present = _has_skip_decorator(function.decorator_list) or bool(
            _runtime_skip_calls(function)
        )
        undocumented_skip = _skip_without_reason(function)
        ancestor = parents.get(function)
        while ancestor is not None:
            if isinstance(ancestor, ast.ClassDef):
                skip_present = skip_present or _has_skip_decorator(ancestor.decorator_list)
                if undocumented_skip is None:
                    undocumented_skip = _skip_decorator_without_reason(ancestor.decorator_list)
            ancestor = parents.get(ancestor)
        documented_skip = skip_present and undocumented_skip is None

        marker = _placeholder_marker(function, comments)
        if marker is not None and not documented_skip:
            line, text = marker
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    code="placeholder-marker",
                    test_name=function.name,
                    message=f"placeholder marker {text!r} must be removed or replaced by an explained skip",
                )
            )
        elif _is_empty_test(function) and not documented_skip:
            violations.append(
                Violation(
                    path=path,
                    line=function.lineno,
                    code="empty-test",
                    test_name=function.name,
                    message="test body contains only pass, ellipsis, docstring, or an empty return",
                )
            )

        if undocumented_skip is not None:
            violations.append(
                Violation(
                    path=path,
                    line=getattr(undocumented_skip, "lineno", function.lineno),
                    code="skip-without-reason",
                    test_name=function.name,
                    message="skip/skipif must include a non-empty reason",
                )
            )

    return violations, len(tests)


def collect_test_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(candidate for candidate in path.rglob("test_*.py") if candidate.is_file())
        elif path.is_file() and path.suffix == ".py":
            files.add(path)
    return sorted(files)


def scan_paths(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in collect_test_files(paths):
        file_violations, _ = scan_file(path)
        violations.extend(file_violations)
    return violations


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject false-green Python tests before they reach CI.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("backend/tests")],
        help="Python test files or directories (default: backend/tests)",
    )
    args = parser.parse_args(argv)

    missing = [path for path in args.paths if not path.exists()]
    if missing:
        parser.error("path does not exist: " + ", ".join(str(path) for path in missing))

    files = collect_test_files(args.paths)
    violations: list[Violation] = []
    test_count = 0
    for path in files:
        file_violations, file_test_count = scan_file(path)
        violations.extend(file_violations)
        test_count += file_test_count

    for violation in violations:
        print(
            f"{_display_path(violation.path)}:{violation.line}: "
            f"{violation.code} {violation.test_name} - {violation.message}"
        )
    print(
        f"Test quality: {len(files)} file(s), {test_count} test(s), "
        f"{len(violations)} violation(s)"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
