# Display Pack Agent OS 目标架构

Owner: `MedAutoScience`
Purpose: `agent_native_scientific_display_system_target_architecture`
State: `stage_affordance_target_with_internal_residue`
Machine boundary: 本文是 MAS/OPL display owner-boundary 支撑。机器真相归 V2 action catalog/Stage manifest、`contracts/display-pack-contract.v2.json`、figure/quality contracts、ScholarSkills provider manifest、OPL package/runtime receipts、paper artifact refs、visual-audit receipt 与 MAS owner receipts。

## 结论

Display Agent OS 不是 MAS 私有 orchestrator、Pack OS、renderer runtime 或 public action family。目标链路是：

```text
MAS figure intent / claim-data refs
  -> OPL-hosted manuscript_authoring Stage
  -> Stage Tool Affordance Boundary
  -> ScholarSkills display descriptor + OPL package/environment/Runway
  -> candidate render/QC refs
  -> independent review_and_quality_gate
  -> MAS artifact/publication authority
  -> finalize_and_publication_handoff
```

模板提供质量下限；Codex executor 负责开放式构图、比较、修订与工具选择；contracts/QC 只托底输入、输出、权限、provenance 与 authority。不能为了保留旧 handler 而降低能力或改回手工流程。

## Owner split

| Surface | Owner | Boundary |
| --- | --- | --- |
| Template/renderer/professional Skill/gallery source | ScholarSkills display package | 不写 MAS claim/data/statistics truth或 owner receipt |
| Package lifecycle、descriptor discovery、environment、renderer transport、StageRun、receipt/refs、workbench | OPL Pack/Atlas/Stagecraft/Runway/Ledger/Console | 不签 MAS quality/artifact/publication authority |
| Figure intent/spec、medical semantics、claim-display relation、visual/medical quality、artifact/package decision | MAS | 不复制 generic runtime/package control plane |
| Independent visual/medical review | separate reviewer invocation | executor self-review不能关闭 quality gate |

## Stage behavior

`manuscript_authoring` Stage：

- 从当前研究目标、claim/data/analysis-summary refs 形成 figure intent/spec；
- 通过 affordance 发现 template family、renderer、style/QC profile 与 environment requirement；
- 允许 Agent 调整 family、variant、layout、panel、palette、legend、scale、backend 和 composition；
- 保持 input/output refs、estimand、source、template/version/lock、environment、hash 与 layout sidecar provenance；
- 只返回 candidate artifact/receipt refs，不授权进入 current package。

`review_and_quality_gate` Stage：

- 消费 deterministic QC、layout sidecar、rendered image/PDF 与 claim-display map；
- 使用独立 reviewer/auditor invocation；
- 输出 visual findings、repair route、quality debt、owner-gate refs 或 typed blocker candidate；
- 不让 renderer success、golden match 或 self-review关闭 gate。

`finalize_and_publication_handoff` Stage：

- 绑定 final display refs、visual-audit receipt、publication manifest 与 submission package refs；
- 检查 same-identity/currentness；
- 只有 MAS owner authority 可以接受 artifact mutation、publication-ready 或 submission-ready。

## Analysis boundary

Renderer 可以对明确声明 `computed_in_template` 的局部转换执行受限计算；ROC、PR、calibration、DCA、KM、time-dependent ROC、forest、SHAP、omics/model audit 等 summary-only 模板必须消费上游已验证 analysis summary。收到 raw analysis input 时：

- render affordance fail closed；
- 返回 `analysis_summary_required_before_display_render` candidate 与 required refs；
- 由 MAS Stage/owner route决定补分析、换图型、降级 claim 或 human gate；
- renderer 不拟合模型、不重算统计量、不静默填值。

## Legacy residue

旧 `display_pack_agent.orchestrate`、`display_pack_capability_discover`、`display_pack_figure_plan`、`display_pack_orchestrate`、`display_pack_preflight` 和 `display_pack_render` 已退出 V2 public/default catalog。现有 source/handler/tests 若仍有 active caller，只能作为迁移 residue：

- 不生成 CLI/MCP/Skill/product action；
- 不新增 alias、command template、registry 或 wrapper；
- 只在 Stage-internal tool/authority replacement尚未闭合时保留；
- replacement parity、no-active-caller、no-forbidden-write 和 source-closure成立后物理删除。

## Completion boundary

Public/default cutover可以由 V2 catalog、Stage manifest、generated interfaces 与 default-caller readback证明。它不能单独证明：

- legacy display implementation 已物理删除；
- OPL package/environment/provider 在目标机器 live；
- 真实 paper figure/table 已通过 independent review；
- artifact/current package/publication/submission authority 已关闭。

完整退役需要 caller inventory清零、Stage affordance replacement parity、fresh source-closure/residue decisions、focused display tests和 no-resurrection tombstone。真实质量仍需要 exact paper artifact、visual/medical reviewer receipt 与 MAS owner verdict。

## 相关入口

- [Display Pack v2 status](./display_pack_v2_landing_status.md)
- [Visual audit protocol](./medical_display_visual_audit_protocol.md)
- [Template-pack architecture](../plans/medical_display_template_pack_architecture.md)
- [E2E skeleton](../examples/display_pack_v2_e2e_skeleton.md)
- [Runtime environment consumer design](../../../runtime/designs/opl_dependency_environment_substrate_target.md)
