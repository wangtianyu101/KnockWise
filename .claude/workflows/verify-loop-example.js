// .claude/workflows/verify-loop-example.js
//
// 通用 verify-loop 模板：writer → verifier → fix 闭环（来源：CLAUDE.md § 6.7.1）
//
// 用法：
//   1) 复制本文件改名（如 verify-loop-pr6-sidebar.js）
//   2) 替换下方 planStep 占位符为目标 plan 条目号（如 "3.2 接口定义"）
//   3) 跑：Workflow({scriptPath: '.claude/workflows/<your>.js'}) 或对话中调用
//
// 参数：
//   planStep    - 要验证的需求条目号（如 "3.2"），对照 plan.md §<step>
//   maxRetries  - 最大重试次数（默认 3）· 超过则升级用户
//
// 适用：≥ 3 verify cycle 或 ≥ 5 phase 任务 · 关键 commit / 安全 / 性能

export const meta = {
  name: 'verify-loop-example',
  description: '通用 verify-loop 模板（writer → verifier → fix until PASS）',
  phases: [{title: 'Write'}, {title: 'Verify'}, {title: 'Fix'}],
}

const WRITER_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    filesChanged: {type: 'array', items: {type: 'string'}},
    testsAdded:   {type: 'array', items: {type: 'string'}},
  },
}

const VERIFIER_SCHEMA = {
  type: 'object',
  properties: {
    passed:   {type: 'boolean'},
    failures: {type: 'array', items: {type: 'string'}},
  },
}

// === 可调参数 ===
const planStep   = process.env.PLAN_STEP || 'X.Y'   // TODO: 替换为真实条目
const maxRetries = Number(process.env.MAX_RETRIES) || 3

// === 主循环 ===
let retries = 0, failures = []
while (retries < maxRetries) {
  phase(retries === 0 ? 'Write' : 'Fix')
  await agent(
    retries === 0
      ? `writer: 实施 plan.md §${planStep}，含单测（happy path + 边界 + Pydantic 校验）`
      : `writer: 修复以下偏差 — ${failures.join('; ')}`,
    {schema: WRITER_RESULT_SCHEMA}
  )
  phase('Verify')
  const v = await agent(
    `verifier: 对照 plan.md §${planStep}：(1) 对照需求 · (2) 跑相关 pytest/vitest · (3) 实测行为 (curl/dev server/浏览器) · 输出 PASS/FAIL + 具体偏差清单（file:line + 期望 vs 实际）`,
    {schema: VERIFIER_SCHEMA}
  )
  if (v.passed) { log(`✅ PASSED after ${retries} fix(es)`); break }
  failures = v.failures
  retries++
}

if (retries >= maxRetries) {
  log(`⚠️ MAX RETRIES (${maxRetries}) reached — 报用户列剩余偏差，等决策，不绕过`)
}

// === 可选：对抗式 verify（critical fix 推荐）===
// 替换上面 phase('Verify') 那一段，改用 parallel() 屏障同时跑 correctness / 回归 / spec 三视角 verifier：
//
//   const [c, r, s] = await parallel([
//     () => agent('correctness 检查：业务逻辑 + 边界',               {schema: VERIFIER_SCHEMA}),
//     () => agent('回归测试检查：现有测试是否仍绿',                {schema: VERIFIER_SCHEMA}),
//     () => agent(`spec §${planStep} 业务规则 + Pydantic 校验`,     {schema: VERIFIER_SCHEMA}),
//   ])
//   const passed = [c, r, s].filter(v => v.passed).length >= 2  // 2/3 共识
//   if (passed) { log('✅ PASSED (adversarial, 2/3 consensus)'); break }
