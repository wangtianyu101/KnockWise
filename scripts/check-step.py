#!/usr/bin/env python3
"""
check-step.py — 7 步 DOD 校验工具

用法：
  python3 scripts/check-step.py research <file.md>
  python3 scripts/check-step.py spec <file.md>
  python3 scripts/check-step.py plan <file.md>
  python3 scripts/check-step.py tasks <file.md>
  python3 scripts/check-step.py verify <file.md>
  python3 scripts/check-step.py ship <file.md>
  python3 scripts/check-step.py retro <file.md>

返回：
  退出码 0 = 校验通过
  退出码 1 = 校验失败（打印所有不通过项）

校验规则参考 docs/DOD.md（7 步 × 38 条 DOD）
"""
import sys
import os
import re


# ─── 0 步 调研 ───────────────────────────────────────────────
def check_research(content):
    errors = []

    # 1. §0 任务规模自检 6 字段非空
    #    "无" 是合法的（明确表示"没有"，如"无关联议題"）
    #    "待定"/"略"/"待写"/"TBD"/"todo" 才是未填
    fields = ['主词', '修饰词', '主任务类型', '副任务', '涉及文件数', '紧急度', '关联议題', '触发词命中']
    for field in fields:
        pattern = rf'\*\*{field}\*\*:\s*(待定|略|待写|TBD|todo)\s*$'
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            errors.append(f'§0 字段 "{field}" 未填（出现 "待定/略/待写"）')

    # 2. 路径模式行存在且匹配
    if not re.search(r'路径模式:\s*(full-7|fix-mini|refactor-6|timebox)', content):
        errors.append('路径模式行缺失或格式错误（应匹配 full-7 / fix-mini / refactor-6 / timebox）')

    # 3. 必填段（new-feature 5 段：任务理解/现状扫描/依赖发现/风险评估/输出建议）
    required_sections = ['任务理解', '现状扫描', '依赖发现', '风险评估', '输出建议']
    for section in required_sections:
        if not re.search(rf'##\s+\d+\.\s*{section}', content):
            errors.append(f'必填段缺失: ## N. {section}')

    # 4. "≥ N" 数量满足（简化：只要出现 ≥ 即可）
    ge_match = re.findall(r'≥\s*(\d+)', content)
    if not ge_match:
        errors.append('未找到任何 "≥ N" 量化要求')

    # 5. 自检清单全勾
    unchecked = re.findall(r'-\s*\[\s*\]\s*[^\n]*', content)
    # 排除证据清单里的 - [ ] 项（证据清单每段 ≥ 1 条，所以前面是 - [ ] 状态）
    # 简化：只检查"自检清单"段内的
    checklist_match = re.search(r'## 自检清单.*?(?=^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
    if checklist_match:
        checklist_unchecked = re.findall(r'-\s*\[\s*\]', checklist_match.group(0))
        if checklist_unchecked:
            errors.append(f'自检清单还有 {len(checklist_unchecked)} 项未勾选')

    # 6. 证据清单段存在
    if '## 📎 证据清单' not in content and '## 证据清单' not in content:
        errors.append('证据清单段缺失（应有 "## 📎 证据清单"）')

    return errors


# ─── 1 步 规格 ───────────────────────────────────────────────
def check_spec(content):
    errors = []

    # 1. 5 段齐全
    sections = ['用户故事', '验收标准', '边界条件', '数据契约', '测试用例']
    for section in sections:
        if not re.search(rf'##\s+\d+\.?\s*{section}', content):
            errors.append(f'5 段缺失: ## N. {section}')

    # 2. GWT ≥ 3 条（Given-When-Then）
    gwt_pattern = re.findall(r'Given\s+', content)
    if len(gwt_pattern) < 3:
        errors.append(f'GWT 不足 3 条（找到 {len(gwt_pattern)} 个 Given）')

    # 3. 数据契约 ≥ 1 schema
    schema_patterns = ['Pydantic', 'BaseModel', 'Zod', 'interface ', 'type ', 'Schema']
    if not any(re.search(p, content) for p in schema_patterns):
        errors.append('数据契约缺少 schema 关键字（Pydantic/BaseModel/Zod/interface/type/Schema）')

    # 4. 测试场景 ≥ 3 条（在 ## 5 测试用例 段内）
    test_section = re.search(r'##\s+5\.?\s*测试用例.*?(?=^##\s|\Z)', content, re.MULTILINE | re.DOTALL)
    if test_section:
        test_items = re.findall(r'-\s+\[?\s*\]?\s*\*?\*?TC[-_]?\d+', test_section.group(0))
        if len(test_items) < 3:
            # 退而求其次：数 - 开头的项
            test_items = re.findall(r'-\s+', test_section.group(0))
            if len(test_items) < 3:
                errors.append(f'测试场景不足 3 条（找到 {len(test_items)} 个项）')
    else:
        errors.append('找不到 "## 5. 测试用例" 段')

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

    # 5. 引用完整
    refs = ['spec.md', 'research.md']
    has_product_doc_ref = 'product-doc.md' in content
    missing = [r for r in refs if r not in content]
    if missing:
        errors.append(f'缺少引用: {", ".join(missing)}（应包含 spec.md + research.md + product-doc.md）')
    if not has_product_doc_ref:
        errors.append('缺少 product-doc.md 引用')

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

    # 5 层 gate
    layers = {
        'L1.*类型': r'L1.*类型|\*\*L1\*\*',
        'L2.*单元': r'L2.*单元|\*\*L2\*\*',
        'L3.*集成': r'L3.*集成|\*\*L3\*\*',
        'L4.*代码审查|reviewer': r'L4.*(代码审查|reviewer|\*\*L4\*\*)',
        'L5.*运行时|staging': r'L5.*(运行时|staging|\*\*L5\*\*)',
    }

    for name, pattern in layers.items():
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f'5 层 gate 缺失: {name}')

    # L2 覆盖率 ≥ 80%（用 DOTALL 让 . 匹配换行）
    if re.search(r'L2', content) and not re.search(r'L2.*?[8-9]\d\s*%|L2.*?coverage.*?[8-9]\d\s*%', content, re.IGNORECASE | re.DOTALL):
        errors.append('L2 单元测试覆盖率应 ≥ 80%')

    # 每层必须有 PASSED / 通过 / ✅
    for layer_id in ['L1', 'L2', 'L3', 'L4', 'L5']:
        layer_section = re.search(rf'{layer_id}.*?(?=L\d|$)', content, re.IGNORECASE | re.DOTALL)
        if layer_section:
            if not re.search(r'PASSED|通过|✅|✓', layer_section.group(0)):
                errors.append(f'{layer_id} 段未标记通过')

    return errors


# ─── 6 步 发布 ──────────────────────────────────────────────
def check_ship(content):
    errors = []

    # 1. 灰度策略（10%/50%/100%）
    if not re.search(r'10%|50%|100%', content):
        errors.append('缺少灰度策略（应有 10%/50%/100%）')

    # 2. 监控 + 告警
    if not re.search(r'告警|alert|monitoring|监控', content, re.IGNORECASE):
        errors.append('缺少监控/告警配置')

    # 3. 回滚预案
    if not re.search(r'回滚|rollback', content, re.IGNORECASE):
        errors.append('缺少回滚预案')

    # 4. 通报模板
    if not re.search(r'通报|通知|notification', content, re.IGNORECASE):
        errors.append('缺少通报模板')

    # 5. ship.md 3 段（部署 + 监控 + 回滚）
    sections = ['部署', '监控', '回滚']
    for section in sections:
        if not re.search(rf'##\s*\d*\.?\s*{section}', content):
            errors.append(f'ship.md 3 段缺失: ## {section}')

    return errors


# ─── 7 步 复盘 ──────────────────────────────────────────────
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
    if not re.search(r'CLAUDE\.md|spec|skill|DOD\.md|模板|流程', content):
        errors.append('未提及知识库更新（CLAUDE.md / spec / skill / DOD.md 之一）')

    return errors


# ─── 主入口 ─────────────────────────────────────────────────
CHECKS = {
    'research': check_research,
    'spec': check_spec,
    'plan': check_plan,
    'tasks': check_tasks,
    'implement': check_implement,
    'verify': check_verify,
    'ship': check_ship,
    'retro': check_retro,
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