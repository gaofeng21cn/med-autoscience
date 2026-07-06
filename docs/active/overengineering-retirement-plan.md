# MAS 过度设计退役与收薄计划

Owner: `MedAutoScience`
Purpose: `active_cleanup_plan`
State: `active_plan`
Machine boundary: 本文是人读规划与执行地图。机器真相继续归 `agent/`、`contracts/`、source、CLI/MCP/API 行为、runtime/controller durable surfaces、真实 workspace artifact、owner receipt 和 repo-native verification。

## 目标读法

MAS 长期形态收敛为 `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。MAS 保留医学研究 truth、stage semantics、AI reviewer / auditor quality gate、publication route、source readiness、artifact authority、owner receipt、typed blocker 和 safe action refs；generic runtime、queue、attempt、lifecycle、workspace shell、package/install、observability 与 generated UI/API 默认上收到 OPL。

完成口径分两层：

- 功能/结构完成：active caller 已迁移、legacy facade / wrapper / root artifact / vendored build helper 已删除或退为 provenance，focused tests 与 repo-native verify 通过。
- 后置证据：真实 paper-line owner receipt、publication-ready、domain-ready、provider long-soak、artifact mutation authority 另账验收。docs、focused tests、projection clean、contract pass 或 package build 不等于论文进展或 publication-ready。

## 模块定位

| 模块 | 保留职责 | 收薄方向 | 禁止承担 |
| --- | --- | --- | --- |
| PaperMission / StageOutcome | 默认 next-action authority、stage terminal decision、owner answer consumption、publication route。 | 保留 minimal authority function；删除 legacy diagnostic/current-work-unit/provider-admission producer tail 的 active facade。 | 不恢复旧 MAS-local scheduler、queue、attempt loop 或 provider carrier。 |
| Display / delivery | 医学图件 quality verdict、publication-facing renderer family、submission package authority refs。 | Display pack 作为版本化 pack / descriptor / gallery refs；build 时不靠 `setup.py` 私有复制投影制造隐藏库存。 | 不拥有 OPL generic Pack OS；display descriptor / lock 不授权 publication-ready。 |
| Runtime / control-plane tail | MAS-owned owner receipt、typed blocker、human gate、safe action refs。 | `runtime_protocol/runtime_surface_retirement_parts` 等私有 runtime tail 只保 authority adapter / tombstone / refs-only projection；generic lifecycle 上收 OPL。 | 不维护第二套 runtime maintenance、health、storage lifecycle、attempt queue 或 workbench shell。 |
| Facade / product entry | 对外 entry 只暴露当前 domain-handler target 和 minimal product route。 | active caller 直连真实 owner module；wildcard-import facade 与历史 alias 删除或收薄。 | 不用 facade 保留旧 public projection 或兼容旧 mainline。 |
| Root artifacts / fixtures | repo 根只保源码、合同、文档和明确 fixture。 | 未引用 demo artifact 移入 history/assets 或删除；超大测试按 semantic case 拆分。 | 不把 demo PNG/PDF 当 active package、gallery truth 或 visual evidence。 |

## 落地清单

| 优先级 | 项 | 动作 | 验证 |
| --- | --- | --- | --- |
| P0 | MAS 私有 runtime/control-plane tail | 对 `runtime_protocol/runtime_surface_retirement_parts`、legacy diagnostic/current-work-unit/provider-admission tail 做 active caller proof；可删则删，不可删则 tombstone 为 authority adapter / refs-only projection。 | focused tests；`scripts/verify.sh` 或 relevant regression lane；no forbidden MAS runtime writes。 |
| P0 | Wildcard-import facade | 迁移 active callers 到真实模块，删除/收薄 `controllers/submission_minimal.py`、`study_progress.py`、`study_runtime_decision.py`、`product_entry.py`、`medical_publication_surface.py` 等 facade tail。 | `rg` 无 active import 依赖退役 facade；focused CLI/domain-handler tests。 |
| P1 | Display pack vendoring / `setup.py` projection | 明确 display-pack 版本化来源；删除自定义复制路径，或把它降为显式 dev/provenance helper。 | package/build smoke；display focused tests；no hidden generated resource inventory。 |
| P1 | Root demo artifacts | 删除或移入 history/assets 未被 active tests/source 引用的 `Rplots.pdf`、`visual_qa_demo.png`。 | `rg` 引用证明；git diff sanity；visual/paper tests 不依赖 root artifact。 |
| P2 | 超大测试 / fixture | 将 narrative/compat/alias assertions 收敛成 semantic case modules；删除重复实现细节。 | line budget；focused tests；`scripts/verify.sh` appropriate lane。 |

## P0 runtime/control-plane tail 执行注记

- 2026-07-06 active caller proof：`runtime_surface_retirement_parts` 当前保留面按文件/函数归类，避免把 P0 runtime tail 写成泛化 blocker：
  - `private_runtime_residue_validators.py` / `private_runtime_residue_maintenance_validators.py` / `runtime_health_kernel_validators.py`：被 `runtime_surface_retirement.py` 调用的 no-authority / minimal authority validator；只能验证 MAS 侧 forbidden authority、OPL takeover tail 和 physical-delete gate，不能写 study truth、owner receipt、typed blocker、human gate、runtime queue 或 provider attempt。
  - `live_runtime_evidence_rollup.py::live_runtime_evidence_rollup_readback` 与 `public_root_commands.py live-runtime-evidence-rollup`：refs-only rollup readback；只能汇总 live-tail / live-gap evidence records 和 typed-blocker-required 状态，不能替代 live-runtime readiness、paper progress 或 production-ready evidence。
  - `live_tail_work_orders.py` / `live_runtime_gap_work_orders.py`：typed-blocker evidence guard；保留 duplicate / unknown / malformed / forbidden-source validator，防止 docs、focused tests、queue empty 或 repo-source retirement 被误读为 live runtime evidence。
  - `completion_evidence_layers.py` / `authority_flags.py` / `surface_helpers.py`：shared physical-delete gate helper；只服务 retirement audit 的 evidence-layer 分账和 forbidden-authority flag scan。
- 本轮可安全删除的是旧 aggregate test fixture `test_private_runtime_residue_active_callers.py`；合同与测试引用已改为具体 case module：`private_runtime_residue_active_callers.py`、`runtime_surface_no_authority_audit.py`、`domain_authority_refs_index.py`。这只删除重复 collection/旧路径别名，不改变 runtime authority 语义。
- 仍未删除的 runtime/control-plane helpers 均有 active caller 或 contract guard 作用；后续只能在对应 active caller 迁移、contract ref 改到 concrete module、focused tests 证明 no-forbidden-write 后继续物理收薄。

## 停止条件

- 若某 facade 仍是唯一 public import 或 domain-handler target，先迁移 caller，再删除。
- 若某 runtime tail 仍签 MAS owner receipt、typed blocker、human gate 或 artifact authority，保留为 minimal authority function，不上收到 OPL。
- 若 display pack 改造缺 packaging proof，只能先文档化边界与删除无引用 artifact，不能声明 display-pack release-ready。

## 2026-07-06 P1 root artifact / facade cleanup evidence

- `Rplots.pdf`、`visual_qa_demo.png`：`rg --hidden --glob '!.git/**' --glob '!*.pdf' --glob '!*.png' 'Rplots\.pdf|visual_qa_demo\.png' .` 仅命中本文 P1 清单；两者是未被 active source/tests 引用的 root demo artifact，已删除而非移入 history。
- `submission_minimal.py`：已把 `study_delivery_sync_parts/submission_delivery_descriptions.py` 的 `describe_submission_minimal_authority` 迁到 `submission_minimal_parts.authority`；facade 仍被 `study_manual_finish.py` 作为 dynamic controller import 使用，且测试仍有 exact facade import，typed blocker 为 `facade_active_public_import_surface`。
- `study_runtime_decision.py`：已把 `domain_status_projection.py` 的 `_status_payload` / `_status_state` / `_record_quest_runtime_audits` 迁到真实 parts；facade 仍被 publication runtime / gate dynamic import 和 parts `__name__` guard 使用，typed blocker 为 `facade_active_runtime_controller_identity`.
- `study_progress.py`、`product_entry.py`、`medical_publication_surface.py`：production surface 仍存在 controller identity / `sys.modules` 依赖，测试 exact facade imports 分别为 71 / 38 / 11 个文件；本轮不做批量 public surface 删除，typed blocker 为 `facade_active_public_import_surface`.

## 2026-07-06 P2 test surface cleanup evidence

- `tests/test_cli_cases/paper_mission_command_cases/materialized_readback.py` 已把 stage-closure-ledger 相关 case 拆到 `tests/test_cli_cases/paper_mission_command_cases/materialized_readback_cases/test_stage_closure_ledger_readback.py`；原入口从约 1705 行降到约 1471 行，回到 preferred boundary advisory 范围。
- `tests/test_cli_cases/paper_mission_command_cases/receipt_owner_consumption.py` 已把 route checkpoint / stage closure 相关 case 拆到 `tests/test_cli_cases/paper_mission_command_cases/receipt_owner_consumption_cases/route_checkpoint_stage_closure.py`；原入口从约 1610 行降到约 1320 行，退出 clear `>1500` 超线范围。
- `tests/test_cli_cases/paper_mission_commands_cases/stage_closure_terminalizer.py` 已把 source-selection / route-back precedence case 拆到 `tests/test_cli_cases/paper_mission_commands_cases/stage_closure_terminalizer_cases/test_source_selection.py`；原入口从约 2493 行降到约 1154 行，新 case 文件约 1350 行，退出 clear `>1500` 超线范围。
- 该拆分只改变测试组织，不改 PaperMission / StageOutcome 语义，不写真实 study artifact、publication eval、controller decision、owner receipt、typed blocker、human gate、runtime queue 或 provider attempt。
- 当前 P2 完成口径是 first safe slice landed；剩余超大测试 / fixture 继续按 source-governance lane 逐个语义拆分，不能把 line-budget advisory 当成 runtime / publication / domain-ready blocker。

## 2026-07-06 MAS wildcard-import facade final slice

- `submission_minimal.py`、`study_runtime_decision.py` 已删除 facade 内 `import *`，保留 public module identity 但改为按固定 parts 列表 re-export；与 main 对比，两个 facade 的可见 symbol 集合保持一致。
- Active caller 收薄：CLI `export-submission-minimal` 与 `submission_targets.export_submission_targets()` 改为调用 `submission_minimal_parts.package_builder`；`study_manual_finish` 改为调用 `submission_minimal_parts.authority`；publication gate / study progress / stage outcome publication-eval materialization 改为函数内直连 `study_runtime_decision_parts.publication_and_submission`，避免恢复 facade import 依赖。
- 剩余 blocker：`gate_clearing_batch` 仍把 submission package builder、profile config、fingerprint helper 和 authority helper 作为同一 controller 传入；publication gate parts 仍共享 submission profile/QC helpers；测试与 public module identity 仍直接 import 两个 facade。当前状态降为 `facade_public_identity_and_multi-part_controller_surface`，不再是 facade 内 wildcard import blocker。
