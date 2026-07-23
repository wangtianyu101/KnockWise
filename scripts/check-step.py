#!/usr/bin/env python3
"""
check-step.py — 6 步 v2 DOD 校验工具

用法：
  python3 scripts/check-step.py research <file.md>
  python3 scripts/check-step.py spec <file.md>
  python3 scripts/check-step.py plan <file.md>
  python3 scripts/check-step.py tasks <file.md>
  python3 scripts/check-step.py verify <file.md>
  python3 scripts/check-step.py retro <file.md>

返回：
  退出码 0 = 校验通过
  退出码 1 = 校验失败（打印所有不通过项）

校验规则参考 docs/DOD.md（0 调研前置 + 1-6 正式步骤）
"""
import sys
import os
import re


# ─── 豁免清单（白名单）───────────────────────────────────────
# 这些文件不参与 DOD 校验（通常是已归档的旧格式文档或重构专用格式）
# 维护规则：
#   - 仅当文件无法/不值得迁移到当前标准格式时加入
#   - 优先考虑 git mv 到 docs/archive/ 而不是加豁免
#   - 每次加入要在 commit message 里写明理由
EXEMPT_SPECS = [
    # 旧 一/二/三...十 格式（v3.5 之前，已归档）
    'docs/archive/spec-old-format/2026-06-22-new-feature-ai-push/spec.md',
    'docs/archive/spec-old-format/2026-06-22-new-feature-question-bank/spec.md',
    # 重构专用格式（结构与新功能 spec 不同，已归档）
    'docs/archive/spec-old-format/2026-07-11-refactor-v3-mockup-align/spec.md',
]


def is_exempt(step, filepath):
    """检查路径是否在豁免清单中"""
    if step != 'spec':
        return False
    # 用 substring 匹配（兼容绝对路径和相对路径）
    for exempt in EXEMPT_SPECS:
        if exempt in filepath:
            return True
    return False


# ─── 0 步 调研 ───────────────────────────────────────────────
def check_research(content):
    errors = []

    mode_match = re.search(
        r'路径模式[：:]\s*`?(full-6|fix-mini|refactor-6|timebox)`?', content
    )
    if not mode_match:
        errors.append('路径模式缺失或错误（应为 full-6 / fix-mini / refactor-6 / timebox）')
        return errors

    mode = mode_match.group(1)
    required_by_mode = {
        'full-6': ['任务理解', '现状扫描', '依赖发现', '风险评估', '输出建议'],
        'fix-mini': ['任务理解', '复现路径', '影响范围', '根因假设', '最近相关改动', '输出建议'],
        'refactor-6': ['任务理解', '现状分析', '重构方案', '风险评估', '输出建议'],
        'timebox': ['影响', '临时止血', '根本原因', '后续时间盒', '沟通'],
    }
    required_sections = required_by_mode[mode]
    for section in required_sections:
        if not re.search(rf'##\s+\d+\.\s*{section}', content):
            errors.append(f'必填段缺失: ## N. {section}')

    if mode != 'timebox':
        for evidence in ['docs/issues.md', 'git log', 'git status']:
            if evidence not in content:
                errors.append(f'调研证据缺失: {evidence}')

    checklist_match = re.search(r'## 自检清单.*?(?=^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
    if checklist_match:
        checklist_unchecked = re.findall(r'-\s*\[\s*\]', checklist_match.group(0))
        if checklist_unchecked:
            errors.append(f'自检清单还有 {len(checklist_unchecked)} 项未勾选')

    return errors


# ─── 1 步 规格 ───────────────────────────────────────────────
def check_spec(content):
    errors = []

    # 1. 5 段齐全（测试场景/用例 都接受）
    sections = ['用户故事', '验收标准', '边界条件', '数据契约', '测试(?:用例|场景)']
    for section in sections:
        if not re.search(rf'##\s+\d+\.?\s*{section}', content):
            errors.append(f'5 段缺失: ## N. {section}')

    # 2. Requirement + Scenario（升级：GWT → Requirement+Scenario 双层，2026-07-17）
    # 2.1 Requirement ≥ 1（### Requirement: ...）
    requirement_matches = re.findall(r'^###\s+Requirement\s*:', content, re.MULTILINE)
    if len(requirement_matches) < 1:
        errors.append(f'Requirement 不足 1 条（找到 {len(requirement_matches)} 个 "### Requirement:"）')

    # 2.2 SHALL ≥ 1（每个 Requirement 必须用 SHALL 强承诺）
    shall_matches = re.findall(r'\bSHALL\b', content)
    if len(shall_matches) < 1:
        errors.append(f'SHALL 不足 1 条（找到 {len(shall_matches)} 个 "SHALL"）—— Requirement 必须用 SHALL 强约束')

    # 2.3 Scenario ≥ 3（#### Scenario: ...）—— 取代旧 Given ≥ 3
    scenario_matches = re.findall(r'^####\s+Scenario\s*:', content, re.MULTILINE)
    if len(scenario_matches) < 3:
        # 向后兼容：旧 GWT 写法也接受（Given ≥ 3）
        gwt_pattern = re.findall(r'Given\s+', content)
        if len(gwt_pattern) < 3:
            errors.append(f'Scenario 不足 3 条（找到 {len(scenario_matches)} 个 "#### Scenario:"；旧 Given 也仅 {len(gwt_pattern)} 个）—— 至少 happy + invalid + edge/failure 各 1')

    # 3. 数据契约 ≥ 1 schema
    schema_patterns = ['Pydantic', 'BaseModel', 'Zod', 'interface ', 'type ', 'Schema']
    if not any(re.search(p, content) for p in schema_patterns):
        errors.append('数据契约缺少 schema 关键字（Pydantic/BaseModel/Zod/interface/type/Schema）')

    # 4. 测试场景 ≥ 3 条（在 ## 5 测试用例 / 测试场景 段内）
    test_section = re.search(r'##\s+5\.?\s*测试(?:用例|场景).*?(?=^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
    if test_section:
        test_items = re.findall(r'-\s+\[?\s*\]?\s*\*?\*?TC[-_]?\d+', test_section.group(0))
        if len(test_items) < 3:
            # 退而求其次：数 - 开头的项
            test_items = re.findall(r'-\s+', test_section.group(0))
            if len(test_items) < 3:
                errors.append(f'测试场景不足 3 条（找到 {len(test_items)} 个项）')
    else:
        errors.append('找不到 "## 5. 测试用例 / 测试场景" 段')

    # 5. §0 调研结论摘要引用
    if not re.search(r'调研.*引用|research\.md|调研报告', content):
        errors.append('缺少调研结论摘要引用（应引用 research.md）')

    # 6. 用户故事已验收
    if not re.search(r'已验收|已确认|已签字|approved|✓\s*验收', content, re.IGNORECASE):
        errors.append('用户故事缺少"已验收"标记')

    return errors


# ─── 2 步 计划 ───────────────────────────────────────────────
def check_plan(content):
    errors = []

    # 1. 方案 ≥ 2 个（"方案 A" / "方案 B" / "Plan A" / "Plan B"）
    plan_count = len(re.findall(r'方案\s*[A-Z]|Plan\s*[A-Z]', content))
    if plan_count < 2:
        errors.append(f'方案不足 2 个（找到 {plan_count} 个 "方案 A/B" 或 "Plan A/B"）')

    # 2. 推荐方案明确
    if not re.search(r'\*\*推荐\*\*|推荐方案:|推荐:\s*方案', content):
        errors.append('推荐方案未明确（应有 "**推荐**: 方案 X"）')

    # 3. 风险点带等级（🔴/🟡/🟢）
    risk_levels = re.findall(r'[🔴🟡🟢]', content)
    if len(risk_levels) < 3:
        errors.append(f'风险点等级不足 3 个（找到 {len(risk_levels)} 个 🔴/🟡/🟢）')

    # 4. 决策点 ≥ 1
    decision_count = len(re.findall(r'决策\s*\d+|\*\*决策\s*\d+\*\*', content))
    if decision_count < 1:
        errors.append(f'决策点不足 1 个（找到 {decision_count} 个）')

    # 5. 引用完整；product/design 文档按任务适用性处理。
    refs = ['spec.md', 'research.md']
    missing = [r for r in refs if r not in content]
    if missing:
        errors.append(f'缺少引用: {", ".join(missing)}（应包含 spec.md + research.md）')
    for optional_doc in ['product-doc.md', 'design-spec.md']:
        if optional_doc not in content:
            errors.append(f'缺少 {optional_doc} 适用性说明（应引用或标注不适用）')

    return errors


# ─── 3 步 任务拆分 ──────────────────────────────────────────
def check_tasks(content):
    errors = []

    # 1. 每个任务 ≤ 1h（找 "估时" 字段）
    tasks = re.findall(r'-\s*\[\s*\]\s*T\d+', content)
    if len(tasks) < 1:
        errors.append('找不到任务项（应有 "- [ ] T1: ..." 格式）')

    # 检查每个任务都有估时 ≤ 1h（只检查任务行内的估时，排除"总估时"）
    # 提取每个 T1/T2/... 任务块，再找块内的"估时"字段
    # 兼容 markdown bold：**估时**: / **估时**:** / 估时:（retro §3 改进项 #1）
    task_blocks = re.findall(r'-\s*\[\s*\]\s*T\d+.*?(?=-\s*\[\s*\]\s*T\d+|^##|\Z)', content, re.MULTILINE | re.DOTALL)
    over_hour_count = 0
    for block in task_blocks:
        # 找任务内的"估时"字段（容忍可选 ** bold 标记）
        estimate_match = re.search(r'\*{0,2}估时\*{0,2}:\s*(\d+)\s*h', block)
        if estimate_match:
            hours = int(estimate_match.group(1))
            if hours > 1:
                over_hour_count += 1
    if over_hour_count > 0:
        errors.append(f'有 {over_hour_count} 个任务估时 > 1h，违反粒度约束')

    # 2. 1 commit = 1 task（commit 字段）
    commit_count = len(re.findall(r'commit|对应\s*commit', content, re.IGNORECASE))
    if commit_count < len(tasks) and len(tasks) > 0:
        errors.append(f'任务数 {len(tasks)} 但只 {commit_count} 个提到 commit，可能未对齐')

    # 3. 任务对应测试（容忍 bold）
    test_refs = len(re.findall(r'对应测试|\*{0,2}测试\*{0,2}:|test[-_]case', content, re.IGNORECASE))
    if test_refs < len(tasks) and len(tasks) > 0:
        errors.append(f'任务 {len(tasks)} 个但只 {test_refs} 个标注测试用例')

    # 4. 依赖关系明确（容忍 bold）
    if not re.search(r'\*{0,2}依赖\*{0,2}[:：]|depends on|前置', content, re.IGNORECASE):
        errors.append('任务依赖关系未明确（应有"依赖: T3"格式）')

    # 5. 总估时字段
    if not re.search(r'总估时|总耗时|总工时', content):
        errors.append('缺少"总估时"字段（事后验证偏差用）')

    return errors


# ─── 4 步 实现 ──────────────────────────────────────────────
def check_implement(content):
    """
    4 步产出物是 git commit + test-cases.md。
    content 参数是 test-cases.md 的内容。
    """
    errors = []

    # 1. 测试策略段
    if not re.search(r'##\s*0\.?\s*测试策略|##\s*测试策略', content):
        errors.append('缺少"## 0. 测试策略"段')

    # 2. 验收测试 ≥ 3 条
    verify_count = len(re.findall(r'TC[-_]?\d+|TC\s*\d+', content, re.IGNORECASE))
    if verify_count < 3:
        errors.append(f'验收测试不足 3 条（找到 {verify_count} 个 TC）')

    # 3. 自动化覆盖率 ≥ 80%（测试策略里）
    if not re.search(r'自动化.*覆盖率.*[8-9]\d%|自动化.*coverage.*[8-9]\d%', content, re.IGNORECASE):
        if not re.search(r'覆盖率.*目标.*[8-9]\d%', content):
            errors.append('缺少"自动化覆盖率 ≥ 80%"目标')

    # 4. 自动化测试段（test_xxx.py 引用）
    if not re.search(r'##\s*2\.?\s*自动化测试|test_\w+\.py', content):
        errors.append('缺少"## 2. 自动化测试"段或 test_xxx.py 引用')

    # 5. 回归测试段
    if not re.search(r'##\s*4\.?\s*回归测试|回归', content):
        errors.append('缺少"## 4. 回归测试"段')

    return errors


# ─── 5 步 验证 ──────────────────────────────────────────────
def check_verify(content):
    errors = []

    for distributed in ['L1', 'L2', 'L4']:
        if distributed not in content:
            errors.append(f'缺少步骤 4 分布式证据引用: {distributed}')

    for layer_id, label in [('L3', '整合测试'), ('L5', 'staging 运行时验证')]:
        pattern = rf'(?:^|\n)##\s[^\n]*{layer_id}[^\n]*\n(.*?)(?=\n##\s|\Z)'
        layer_sections = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        if not layer_sections:
            errors.append(f'缺少 {layer_id} {label}段')
            continue
        section_text = layer_sections[-1]
        has_pass = re.search(r'PASSED|通过|✅|✓', section_text, re.IGNORECASE)
        if not has_pass:
            errors.append(f'{layer_id} 段未标记通过')
        if re.search(r'结果\s*[：:]\s*(?:FAILED|❌|未通过)', section_text, re.IGNORECASE):
            errors.append(f'{layer_id} 最终结果为失败')

    return errors


# ─── 6 步 复盘 ──────────────────────────────────────────────
def check_retro(content):
    errors = []

    # 1. retro.md 5 段（用 substring 检查，更稳健）
    sections = ['数据', '做对', '做错', '改进', '沉淀']
    found_sections = set()
    for section in sections:
        # 段标题里包含关键词就算有（如"## 一、数据"、"## 二、做对的事"）
        if re.search(rf'##[^#]*{section}', content):
            found_sections.add(section)

    if len(found_sections) < 4:
        missing = set(sections) - found_sections
        errors.append(f'retro.md 5 段缺失: {", ".join(missing)}')

    # 2. 工作量数据
    if not re.search(r'小时|commit\s*数|任务数|耗时', content, re.IGNORECASE):
        errors.append('缺少工作量数据（小时 / commit 数）')

    # 3. 返工次数（可选，但如果有返工必须分析）
    rework = re.search(r'返工\s*\d+\s*次|返工次数[:：]\s*\d+', content)
    if rework:
        # 有返工次数必须分析
        if not re.search(r'返工.*原因|原因.*返工', content):
            errors.append('返工次数 ≥ 1 但未分析原因')

    # 4. 改进项已分配（@name 或 "负责人: ..."）
    if not re.search(r'@[\w一-龥]+|负责人[:：]|owner[:：]', content):
        errors.append('改进项未分配（应有 @xxx 或"负责人: xxx"）')

    # 5. 已更新知识库
    if not re.search(r'CLAUDE\.md|AGENTS\.md|spec|skill|DOD\.md|模板|流程', content):
        errors.append('未提及知识库更新（CLAUDE.md / AGENTS.md / spec / skill / DOD.md 之一）')

    return errors


# ─── Traceability Matrix (per P1-2) ────────────────────────
TRACEABILITY_RE = re.compile(r'\|?\s*\|?\s*REQ-?(\d+)\s*\|', re.IGNORECASE)
SCN_RE = re.compile(r'\bSCN-?(\d+)\b', re.IGNORECASE)
TC_RE = re.compile(r'\bTC-?(\d+)\b', re.IGNORECASE)
E2E_PATH_RE = re.compile(r'\bE2E-?(\d+)\b', re.IGNORECASE)
EV_RE = re.compile(r'\bEV-?(\d+)\b', re.IGNORECASE)
METRIC_RE = re.compile(r'\bMETRIC-?(\d+)\b', re.IGNORECASE)


def check_traceability(content):
    """Per spec § 1 REQ-4 + REQ-5: 10 不变量"""
    errors = []
    # 找 traceability 段
    trace_section = re.search(
        r'(?:^|\n)(?:#{1,3}\s*)?(?:##\s*)?(?:Traceability|## 0\.\d+|## Traceability)\b(.*?)(?=\n##\s|\Z)',
        content, re.IGNORECASE | re.DOTALL
    )
    if not trace_section:
        # 软警告，不阻断
        return errors  # 没 trace 段不强求
    body = trace_section.group(1)

    # 1. 所有 ID 唯一
    all_ids = []
    for pat in (TRACEABILITY_RE, SCN_RE, TC_RE, E2E_PATH_RE, EV_RE, METRIC_RE):
        all_ids += pat.findall(body)
    dup = {x for x in all_ids if all_ids.count(x) > 1}
    if dup:
        errors.append(f'ID 重复: {sorted(dup)}')

    # 2. SCN 引用存在的 REQ
    reqs = set(TRACEABILITY_RE.findall(body))
    for m in re.finditer(r'\bSCN-?(\d+)\b', body):
        scn_id = m.group(1)
        # 邻近行是否含 REQ
        if not re.search(rf'REQ-?\d+', body[max(0, m.start()-200):m.end()+200]):
            errors.append(f'SCN-{scn_id} 未引用 REQ')

    # 3. TC 引用存在的 SCN
    scns = set(SCN_RE.findall(body))
    for m in re.finditer(r'\bTC-?(\d+)\b', body):
        tc_id = m.group(1)
        if not re.search(rf'SCN-?\d+', body[max(0, m.start()-200):m.end()+200]):
            errors.append(f'TC-{tc_id} 未引用 SCN')

    # 4. Task 至少引用一个 TC + Test Node
    for m in re.finditer(r'\bT\d+\b', body):
        chunk = body[max(0, m.start()-300):m.end()+300]
        if not TC_RE.search(chunk):
            errors.append(f'{m.group()} 未引用 TC')
        if '::' not in chunk:  # Test Node 形如 foo.py::test_xxx
            errors.append(f'{m.group()} 缺少 Test Node')

    # 5. PASS TC 至少有一个 L2/L3/L5 evidence（软提示）
    # 简化: 任何 status PASS 的行附近含 L2/L3/L5
    for m in re.finditer(r'(TC-\d+).*?PASS', body, re.DOTALL | re.IGNORECASE):
        chunk = body[m.start():min(len(body), m.end()+300)]
        if not re.search(r'\bL[235]\b', chunk):
            errors.append(f'{m.group(1)} PASS 缺少 L2/L3/L5 evidence')

    # 6. E2E 行有 E2E-* + Mock 边界合规
    for m in re.finditer(r'\bE2E-?(\d+)\b', body):
        chunk = body[max(0, m.start()-200):m.end()+200]
        if not re.search(r'\bL[34]\b', chunk):
            errors.append(f'E2E-{m.group(1)} 缺 L3/L4 标记')

    # 7. EV-* 退出码 0；BLOCKED 可无 artifact 但需原因 (软)
    # 跳过详细检查 - BLOCKED 文档本身已说明

    # 8. Metric 绑定事件 + REQ (软)
    for m in re.finditer(r'\bMETRIC-?(\d+)\b', body):
        chunk = body[max(0, m.start()-200):m.end()+200]
        if not re.search(r'REQ-\d+', chunk):
            errors.append(f'METRIC-{m.group(1)} 缺 REQ 引用')

    # 9. Requirement 全部必需 TC PASS 才 PASS
    for m in re.finditer(r'REQ-?(\d+).*?PASS', body, re.DOTALL | re.IGNORECASE):
        chunk = body[max(0, m.start()-1000):m.end()]
        if re.search(r'REQ-?\d+.*?FAIL|RE-?\d+.*?BLOCKED', chunk, re.IGNORECASE):
            errors.append(f'REQ-{m.group(1)} 标 PASS 但有失败/阻塞项')

    # 10. 禁止仅凭任务 checkbox 或全 pytest 绿判 PASS (软)
    if re.search(r'(?<!-- )(✓|✅).*?(pytest|test_).*?(PASS|绿)', body, re.IGNORECASE):
        errors.append('仅凭任务 checkbox 或 pytest 绿判 PASS 不充分')

    return errors


# ─── 主入口 ─────────────────────────────────────────────────
CHECKS = {
    'research': check_research,
    'spec': check_spec,
    'plan': check_plan,
    'tasks': check_tasks,
    'implement': check_implement,
    'verify': check_verify,
    'retro': check_retro,
    'traceability': check_traceability,
}


def main():
    if len(sys.argv) != 3:
        print('用法: check-step.py <step> <file.md>')
        print()
        print('step 取值:')
        for s in CHECKS.keys():
            print(f'  {s}')
        sys.exit(1)

    step = sys.argv[1]
    filepath = sys.argv[2]

    if step not in CHECKS:
        print(f'❌ 未知 step: {step}')
        print(f'   取值: {", ".join(CHECKS.keys())}')
        sys.exit(1)

    # 豁免检查（白名单）
    if is_exempt(step, filepath):
        print(f'⏭️  豁免（白名单）: {filepath}')
        sys.exit(0)

    if not os.path.exists(filepath):
        print(f'❌ 文件不存在: {filepath}')
        sys.exit(1)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f'❌ 读取文件失败: {e}')
        sys.exit(1)

    errors = CHECKS[step](content)

    if errors:
        print(f'❌ {step} DOD 校验失败 ({filepath}):')
        print(f'   共 {len(errors)} 项不通过:')
        for e in errors:
            print(f'   - {e}')
        print()
        print(f'💡 完整 DOD 定义见 docs/DOD.md')
        sys.exit(1)
    else:
        print(f'✅ {step} DOD 校验通过 ({filepath})')
        sys.exit(0)


if __name__ == '__main__':
    main()
