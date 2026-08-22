# MAS/MDS Owner Boundary Policy

Status: `active policy`
Date: `2026-05-04`
Owner: `MedAutoScience`
Purpose: `Define stable MAS runtime governance, dependency, owner-boundary, and stabilization policy.`
State: `active_policy`
Machine boundary: Human-readable runtime-governance policy only; runtime truth remains in contracts, source, CLI/read-model output, runtime ledgers, controller artifacts, and owner receipts.

## 结论

MAS 持有 study truth、医学质量与 publication、canonical artifact mutation 以及 owner receipt；OPL 持有通用 runtime、lifecycle、transport、generated interface 和 read model。MDS/DeepScientist 只作为 historical source、fixture、显式 archive import 或 parity reference，不是默认依赖或 authority。

本文只记录当前 owner 边界。机器事实以 contracts、source、runtime readback、artifact 和 owner receipt 为准。

## 当前重叠风险

| risk_id | 风险 | 必须保持的 owner |
| --- | --- | --- |
| `entry_projection_as_authority` | read model、status projection 或 transport surface 自己解释下一步 | Codex-selected declared stage；`StageOutcome`、legacy route context、`publication_eval/latest.json` 与 `controller_decisions/latest.json` 只作输入或 domain evidence |
| `mds_oracle_as_quality_owner` | MDS `paper_contract_health`、coverage、prompt stage wording 或 artifact state 被读成医学质量 ready | MAS AI reviewer-backed `publication_eval/latest.json` 与 Quality OS |
| `observability_as_control` | rubric score、trajectory replay、feedback analytics、OAR projection 直接驱动 finalize/submission | MAS controller decision 与 publication authority |
| `runtime_status_double_parse` | MAS controller 局部解析 live worker、active run 或 recovery action | OPL current-control / StageRun / Observability readback |

## Owner Matrix

| layer | owner | role | authority |
| --- | --- | --- | --- |
| `mas_core` | MAS | authority | study truth、artifact authority、user-visible next action |
| `quality_os` | MAS | authority | scientific quality、medical writing quality、publication readiness、submission authority |
| `domain_authority_refs` | MAS | authority refs | owner receipt、typed blocker、runtime-domain refs、canonical domain action refs |
| `entry_projection` | MAS | projection | no authority；只投影 MAS durable truth |
| `observability_os` | MAS | observability | no authority；只提供 evidence、calibration、analytics |
| `mds_backend` | MDS | historical backend / parity fixture | no MAS authority；只提供显式 archive、fixture 或 parity 语义 |

## 文档 / Reference 一致性 Guard

README、status、policy、runtime reference 与 program reference 都是人读面，不能各自长出新的 owner truth。MDS 的机器分类以 `docs/references/med-deepscientist/source_provenance.json` 为准：

- 受约束的文档族：`README`、`docs/README`、`docs/status`、`docs/active`、`docs/policies`、`docs/runtime`、`docs/references`
- 允许的 MDS 角色：`frozen_source_archive`、`historical_fixture_ref`、`explicit_archive_import_ref`、`source_provenance`、`parity_oracle`、`upstream_intake_source`
- 禁止的 MDS 语义：默认运行依赖、默认诊断依赖、默认 WebUI/progress owner、默认 runner、product owner、study / quality / publication / runtime authority、contributor history import
- MAS-owned packaging surface：`study-progress` / `paper-mission` / current-control handoff refs、owner receipt / typed blocker refs 和 body-free projection JSON；repo-local Progress Portal/static HTML 已退役为 provenance。
- hub 角色约束：`product_entry`、`study_progress`、`MCP`、OPL hosted workbench/display consumer 和 `display/quality entrances` 只能是 thin read-model / adapter / materializer，不得升级成 authority。

这条 guard 的目标是让文档更新继续跟随真实 MAS/MDS contract，而不是反过来让 README/status/policy 自己生成第二套 truth。

## 当前控制

1. Owner matrix 由 `contracts/private_functional_surface_policy.json` 和
   `contracts/functional_privatization_audit.json` 持有，并由
   `tests/test_standard_agent_boundary.py` 覆盖。

2. OPL generated CLI/MCP/product/status/workbench 只能消费 StageRun/current-control
   和 MAS owner truth，不做第二判断；legacy `study_progress` 只作 internal
   diagnostic projection。

3. MDS surface 只能使用 `source_provenance.json` 声明的分类；带有
   publication、submission、user-progress、medical-evidence 或 runtime authority
   的外部 surface 不得成为 MAS 默认 owner。

4. 新增 bridge、projection、oracle 或 runtime adapter 时，必须先写明当前
   owner、authority surface 和可验证的切换证据；否则保持为 reference 或 fixture。

## 验证

- `tests/test_standard_agent_boundary.py` 检查 active source boundary 和 retired
  callable 的残留引用。
- `scripts/verify.sh` 运行 tracked-path hygiene 与 pytest；`full` 另外运行 OPL
  source-hygiene。
- Runtime、paper progress、publication 和 production claim 仍需 fresh live
  readback、artifact 或 owner receipt；文档和测试本身不构成这些结论。
