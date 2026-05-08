# MAS/MDS Owner Boundary Refactor Plan

Status: `active contract`  
Date: `2026-05-04`

## 结论

结构性重复 authority 风险已经确认。当前 MAS/MDS 不是简单的“模块多”，而是多类模块会在不同层面读取、解释或投影同一组事实：runtime liveness、study next action、publication gate、artifact delivery、manuscript quality、operator progress。只要没有硬 owner matrix，entry projection、observability、MDS oracle、runtime adapter 都可能越权变成第二判断者，形成表面上更完整、实际更混乱的系统。

本计划的修复方向是：用 owner matrix 固定 authority，用 strangler refactor 逐面吸收 MDS 能力，用 architecture_fitness_functions 把边界变成测试和结构门禁。允许重构，但不做 big-bang rewrite；每个 surface 先证明 owner、parity proof、rollback surface 与 quality-not-relaxed，再 promotion 或 absorb。

## 当前重叠风险

| risk_id | 风险 | 必须保持的 owner |
| --- | --- | --- |
| `entry_projection_as_authority` | `study_progress`、`workspace-cockpit`、`product-entry-status`、MCP、product-entry manifest 自己解释下一步 | `StudyTruthKernel`、`RuntimeHealthKernel`、`publication_eval/latest.json`、`controller_decisions/latest.json` |
| `mds_oracle_as_quality_owner` | MDS `paper_contract_health`、coverage、prompt stage wording 或 artifact state 被读成医学质量 ready | MAS AI reviewer-backed `publication_eval/latest.json` 与 Quality OS |
| `observability_as_control` | rubric score、trajectory replay、feedback analytics、OAR projection 直接驱动 finalize/submission | MAS controller decision 与 publication authority |
| `runtime_status_double_parse` | 多个 controller 局部解析 live worker、active run、recovery action | RuntimeHealthKernel 与 control-plane fact resolver |

## Owner Matrix

| layer | owner | role | authority |
| --- | --- | --- | --- |
| `mas_core` | MAS | authority | study truth、artifact authority、user-visible next action |
| `quality_os` | MAS | authority | scientific quality、medical writing quality、publication readiness、submission authority |
| `runtime_os` | MAS | authority | runtime health、canonical runtime action |
| `entry_projection` | MAS | projection | no authority；只投影 MAS durable truth |
| `observability_os` | MAS | observability | no authority；只提供 evidence、calibration、analytics |
| `mds_backend` | MDS | controlled backend / oracle | no MAS authority；只提供 daemon、quest layout、native runtime events 与 mechanical oracle |

## 文档 / Reference 一致性 Guard

README、status、policy、runtime reference 与 program reference 都是人读面，但它们不能各自长出新的 owner truth。对应的机器合同是 `mas_mds_doc_reference_semantic_guard`，它把文档语义固定为以下几类：

- 受约束的文档族：`README`、`docs/README`、`docs/status`、`docs/policies`、`docs/program`、`docs/runtime`、`docs/references`
- 允许的 MDS 角色：`frozen_source_archive`、`historical_fixture`、`explicit_legacy_diagnostic`、`provenance_reference`、`parity_oracle`、`upstream_intake_source`
- 禁止的 MDS 语义：默认运行依赖、默认诊断依赖、默认 WebUI/progress owner、默认 runner、product owner、study / quality / publication / runtime authority、contributor history import
- MAS-owned packaging surface：`artifacts/runtime/progress_portal/latest.json`、`ops/mas/progress/index.html`、`ops/mas/bin/start-web`、`medautosci workspace progress-portal --serve`
- hub 角色约束：`product_entry`、`study_progress`、`MCP`、`Progress Portal`、`display/quality entrances` 只能是 thin read-model / adapter / materializer，不得升级成 authority

这条 guard 的目标是让文档更新继续跟随真实 MAS/MDS contract，而不是反过来让 README/status/policy 自己生成第二套 truth。

## 外部工程依据

- `strangler_fig`：成熟 legacy 替换通常采用逐步包裹、迁移和切换，适合 MDS deconstruction；在本项目中体现为 capability-by-capability promotion，而不是一次性 monorepo absorb。
- `architecture_fitness_functions`：架构约束应进入自动化检查；在本项目中体现为 `tests/test_architecture_owner_boundary.py`、MDS strangler registry、line budget、Sentrux structure lane。
- `team_topologies_cognitive_load`：复杂系统需要按职责和认知负载划边界；在本项目中体现为 MAS 只承接医学 research/product authority，MDS 只承接 runtime/backend/oracle。
- `private_owned_data`：owner state 只能通过稳定接口消费；在本项目中体现为 durable truth surfaces 的 owner-private 规则，projection 不能写回或替代 authority。

## 修复程序

1. `freeze_authority_matrix`
   - 已落地：`med_autoscience.controllers.architecture_owner_boundary`。
   - 验证：`tests/test_architecture_owner_boundary.py`。

2. `guard_projection_surfaces`
   - `study_progress`、`workspace-cockpit`、`product-entry-status`、product-entry、MCP 只能消费 truth，不做第二判断。
   - 后续新增 projection 必须声明 consumed authority surface。

3. `strangle_mds_authority_residue`
   - MDS surface 的机器分类只允许 `mas_owned`、`rewrite_in_mas`、`fixture_only`、`retire`、`external_source_archive_only` 五档。
   - 任何带 publication/submission/user-progress/medical-evidence authority 的 MDS surface 必须 fail-closed。

4. `block_big_bang_absorb`
   - physical absorb 只在 parity proof、owner cutover、rollback surface 与 quality-not-relaxed gate 成立后进行。
   - 当前目标是减少混乱和 owner drift，不是把所有代码搬进一个目录。

## 验收

- `make test-meta` 必须覆盖 owner-boundary report 与文档入口。
- `scripts/verify.sh structure` 继续覆盖 line budget 与结构质量。
- MDS `scripts/verify.sh docs` 必须覆盖 runtime protocol / transition contract / strangler registry。
- 任何新增 MAS/MDS bridge、projection、oracle、runtime adapter，都必须能说明：当前 owner、目标 owner、authority surface、promotion gate、parity proof、rollback surface。
