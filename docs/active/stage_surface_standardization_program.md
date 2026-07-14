# MAS Stage Surface Standardization

Owner: `MedAutoScience`
Purpose: `declarative_stage_surface_boundary`
State: `active_support`
Machine boundary: 本文解释 Stage pack 形态。机器真相归 `agent/stages/`、`agent/prompts/`、action/schema、quality-cycle contracts 与 OPL generated StageRun surfaces。

## 标准形态

每个 MAS Stage 只声明：

- goal、good result 与 scope；
- required knowledge / ScholarSkills / tool affordances；
- artifact roles、source/evidence obligations 与 forbidden writes；
- quality rubric、formal Review policy 与 repair budget；
- declared route targets、handoff refs 与 authority boundary。

Stage declaration不实现 runner、queue、session、lifecycle、artifact index、memory store、
workbench、provider transport 或 transition controller。

## 六个 canonical Stage

| Stage | 领域职责 |
| --- | --- |
| `direction_and_route_selection` | 研究方向、问题边界与路线选择 |
| `baseline_and_evidence_setup` | protocol/source/evidence 基线 |
| `bounded_analysis_campaign` | 可审计分析与结果产出 |
| `manuscript_authoring` | canonical manuscript bytes |
| `review_and_quality_gate` | 独立 cross-Stage Meta Review 与 defect-owner route-back |
| `finalize_and_publication_handoff` | exact reviewed bytes 的机械 handoff packaging |

## Attempt 与 Review

- producer、reviewer、repairer、re_reviewer 都是 OPL StageRun 下的独立 Attempt role。
- formal reviewer/re_reviewer 必须使用与 producer 不同的 session，并审阅 exact artifact/source/rubric refs。
- reviewer outcome 只写入 `route_impact.stage_quality_cycle.outcome`，五值为 `pass`、`repair_required`、`quality_debt`、`blocked`、`human_gate`。
- Attempt 不签发 review receipt；OPL controller 校验 identity/lineage/hash 后物化 receipt。
- optional observation不重开 repair loop，也不强制整体降级。
- repair budget 尚存且缺陷可在当前 Stage 修复时，`repair_required` 只给 recommendation并继续 repair；若最窄 canonical owner 是另一个 declared Stage，reviewer/re_reviewer 可提前以 `repair_required + route_back` 终结当前 StageRun，这是预算耗尽前唯一允许的终局 `repair_required` 路由；预算耗尽且 artifact 可消费时，终局 reviewer/re_reviewer 给 route decision，controller 投影 `completed_with_quality_debt`。
- 零可消费 artifact、真实 hard gate 或 human gate 不给 route decision。

## Route owner

- `semantic_route_decision_owner=decisive_codex_attempt`
- `stage_transition_materialization_owner=opl_stage_run_controller`

Primary-only Stage 的 producer可以是 decisive Attempt；formal Review Stage 的终局
reviewer/re_reviewer可以是 decisive Attempt。repairer和非终局 reviewer永不拥有
route decision authority。

## 专业能力

医学研究方法、写作、审阅、统计、表格、figure/display、submission 与数据治理能力
由 canonical primary skill、`agent/` declarations 与 `mas-scholar-skills` 提供。
OPL 提供工具执行、connector、environment、resource materialization 与 receipt；
MAS 的独立 Review/authority result决定医学质量，不维护私有 renderer transport或
quality validator runtime。

## 维护门

- Stage/prompt/quality 变更必须同步 machine contracts 与 focused tests。
- 不用 Markdown生成器或 MAS-local projection builder制造第二 Stage surface。
- 不把 provider completion、queue status、tests green或 workbench visibility写成领域完成。
- Live paper-line、owner receipt、artifact delta 与 provider long-soak单列后置 evidence。
