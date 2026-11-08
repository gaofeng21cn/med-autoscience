# Stage Route Contract Reference

本文只解释 Stage 合同的来源与字段作用，不复制 YAML 正文或创建第二张 route table。

- `agent/stages/manifest.json` 定义六个 canonical Stage 与其 prompt/knowledge/policy。
- `contracts/action_catalog.json` 将公开 action 绑定到 Stage manifest。
- `agent/stages/stage_route_contract.yaml` 持有研究 route 的语义、evidence obligations 与普通 progress policy。
- `contracts/stage_run_kernel_profile.json` 与 `contracts/stage_quality_cycle_policy.json` 定义 OPL StageRun 的消费方式和独立质量循环。
- `contracts/mas-paper-study-stage-pack.json` 持有论文物理 artifact 阶段；它不是另一套运行路由 authority。

Route 的 goal、key question、scope、evidence、human gate 与输出义务给 Stage 提供研究上下文。旧短 route id 不作为新 public action alias；调用者使用 action catalog 的 canonical id。

Decisive Attempt 产生语义 route decision，OPL controller 校验角色、identity、declared target 并物化 transition。具体角色与 handoff 规则见 [Stage / Route / Handoff](../stage_route_handoff_standard.md)。

普通质量债与缺 receipt 关闭更高质量或 ready claim，不自动阻止有可消费 artifact 的下一步。权限、身份、来源、安全、不可逆动作与 human gate 仍须守住。不存在要求先调用旧 MAS controller、bootstrap 或私有 CLI 的前置规则。

更改 route/action contract 后运行受影响 Stage 与 boundary tests；纯文案检查不固定 YAML 的自然语言措辞或 Markdown 章节。
