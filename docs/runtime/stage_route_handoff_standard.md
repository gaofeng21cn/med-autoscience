# MAS Stage / Route / Handoff 标准

Owner: `MedAutoScience`
Purpose: `stage_route_handoff_standard`
State: `active_support`
Machine boundary: 机器真相归 `agent/stages/manifest.json`、`agent/stages/stage_route_contract.yaml`、V2 action catalog、Stage quality-cycle policy 与 OPL StageRun/Attempt contracts。

## 六个 canonical Stage

1. `direction_and_route_selection`
2. `baseline_and_evidence_setup`
3. `bounded_analysis_campaign`
4. `manuscript_authoring`
5. `review_and_quality_gate`
6. `finalize_and_publication_handoff`

旧 physical route、domain-transition、NextAction、PaperRecovery、owner-route wrapper 与 queue hydration 不形成第二 Stage graph，也不再是 active caller。

## Authority split

- `semantic_route_decision_owner=decisive_codex_attempt`
- `stage_transition_materialization_owner=opl_stage_run_controller`

Primary-only StageRun 的 producer 是 decisive Attempt。Formal Review StageRun 只有终局 reviewer / re-reviewer 是 decisive Attempt；在这种 StageRun 内 producer、repairer 始终只能给 recommendation。仍有 repair budget 且缺陷可在当前 Stage 修复时，`repair_required` reviewer也只给 recommendation；若最窄 canonical owner 是另一个 declared Stage，则 reviewer / re-reviewer 可提前以 `repair_required + route_back` 终结当前 StageRun，这是预算耗尽前唯一允许的终局 `repair_required` 路由。预算耗尽且 artifact 可消费时，终局 reviewer / re-reviewer 给 route decision，controller 以 `completed_with_quality_debt` 物化。

Attempt 只返回：

- `route_impact.stage_route_recommendation` 或 `route_impact.stage_route_decision`；
- reviewer / re-reviewer 的 `route_impact.stage_quality_cycle.outcome`；
- exact artifact/source/rubric/lineage refs、findings 与 required closeout refs。

OPL controller 只验证角色资格、declared target、identity、lineage 与 exact hashes，然后记录 transition。它不解释或改写医学语义。MAS authority function只处理 host 注入的医学 owner boundary，不启动 runtime、不写 session、不物化 transition。

## Handoff

Handoff 是 body-free refs 与 evidence 的交接，不是 MAS 私有 queue 或 runner。OPL 可以据此启动目标 StageRun、记录 Attempt、传输 receipt/blocker/human gate并投影 status；不能写 MAS study truth、publication verdict、artifact body、memory body或 current package。

## Hard stop 与 progress

普通质量缺口在预算耗尽且 artifact 可消费时进入 `completed_with_quality_debt`。只有真实 authority/safety/identity/currentness/credential/irreversible/human gate，或在 diagnostic 尝试后仍无任何可消费 artifact，才是 hard stop。成功物化的 no-output/failure diagnostic 本身可以作为可消费进展 artifact。

## 验证

运行 `scripts/verify.sh full`，并在冻结 Framework 读取单仓 interfaces/conformance/default-callers/residue/source-closure。结构绿不替代真实 StageRun、Review receipt、owner result 或 paper artifact evidence。
