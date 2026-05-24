# MAS 标准 OPL Agent 私有实现台账

Status: `active_migration_inventory`
Owner: `MedAutoScience`
Purpose: `standard_opl_agent_private_surface_inventory`
State: `active_support`
Machine boundary: 本文是 machine-adjacent human-readable 台账，不是机器真相。机器真相继续归 `contracts/functional_privatization_audit.json`、`contracts/private_functional_surface_policy.json`、`contracts/generated_surface_handoff.json`、`contracts/pack_compiler_input.json`、CLI/MCP/API 行为、sidecar receipt、runtime/controller durable surfaces、owner receipt 和真实 workspace artifact。

## 当前目标态

MAS 的 OPL 标准智能体目标态是：

`Declarative Medical Research Pack + OPL hosted/generated surfaces + minimal authority functions + refs-only domain projections`

这表示：

- `agent/` 和相关 contracts 声明医学研究 stage、prompt、skill、knowledge、quality gate、action catalog、receipt refs 和 forbidden authority boundary。
- OPL hosted/generated surfaces 承接通用 CLI、MCP、Skill、product-entry、sidecar、status、workbench、projection shell、attempt、queue、retry/dead-letter、watch shell、generic state-machine runner、locator/index/lifecycle 和 operator workbench。
- MAS repo 内长期保留的程序面只允许是医学 authority function、domain handler target、AI-first record validator、owner receipt signer、typed blocker materializer、body-free domain authority refs surface、diagnostic/provenance reader 或 historical fixture。
- OPL 可以托管、调度、索引、展示和 dispatch allowlisted task；不能写 MAS study truth、publication verdict、AI reviewer verdict、source readiness verdict、publication-route memory body、artifact authority、`current_package`、paper package 或 runtime/controller durable truth。

本台账只记录当前源码形态和迁移门槛。它不表示 OPL provider long soak、真实 paper closure、publication-ready、medical-ready、artifact mutation authorization 或真实 workspace scaleout 已完成。

## 当前分类词表

| class | 含义 | 允许输出 | 退役口径 |
| --- | --- | --- | --- |
| `declarative_pack_generated_surface` | 可由 MAS pack 输入或 OPL generated/hosted surface 承接的通用外壳。 | descriptor、target refs、dispatch receipt、status/projection refs。 | OPL default caller parity、MAS receipt parity、focused tests 和 no-forbidden-write proof 成立后，MAS 侧只留 domain handler target 或删除。 |
| `domain_authority_refs` | MAS 只保留 body-free authority / provenance refs 的 surface。 | owner receipt ref、typed blocker ref、surface ref、artifact/source/workspace locator ref、guarded apply ref。 | 只要开始承担 generic runtime lifecycle、scheduler、queue、attempt、worker residency 或 workbench owner 语义，即按标准 Agent 纯净度 regression 修复。 |
| `minimal_authority_function` | MAS 必须保留的医学研究 authority 或 authority validator。 | AI-first reviewer/auditor record refs、publication/source/memory/artifact verdict refs、owner receipt、typed blocker、guarded apply ref。 | 不迁到 OPL；只可继续收窄接口和验证 provenance。 |

## 当前机器面

| surface | 当前角色 | 当前证据入口 | 允许保留在 MAS 的内容 | 不允许回流的内容 |
| --- | --- | --- | --- | --- |
| `agent/` | Declarative Medical Research Pack canonical source。 | `contracts/pack_compiler_input.json`、`contracts/stage_control_plane.json`、`contracts/action_catalog.json`。 | medical stage、prompt、quality gate、knowledge、action intent、receipt refs。 | CLI/MCP/status/workbench runtime owner、queue/attempt/retry owner。 |
| `src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/consumer_migration_inventory.py` | 当前 functional module inventory source；只记录 15 个标准 Agent surface。 | `build_functional_consumer_boundary()`、`contracts/functional_privatization_audit.json`、`contracts/test-lane-manifest.json`。 | 三类标准 Agent 分类、domain authority refs、minimal authority functions、generated surface handoff。 | deleted helper、cleanup registry、generic runtime owner、scheduler owner、worker lease owner。 |
| `functional_consumer_boundary.standard_agent_purity` | 当前默认 product-entry / sidecar / read-model 纯净度信号。 | product-entry manifest、sidecar export、OPL unique handoff、focused tests。 | active private generic residue count、active default caller absence、refs-only projection policy。 | 当前默认面中的历史细节、兼容 alias、wrapper、generic owner claim。 |
| `generated_surface_handoff` | OPL generated/hosted shell handoff。 | `contracts/generated_surface_handoff.json`、product-entry / CLI / MCP focused tests。 | domain handler target refs、direct path parity refs、no-forbidden-write proof。 | MAS hand-written shell 成为 default generic CLI/MCP/status/workbench owner。 |
| `domain_authority_refs_index` | Domain authority refs index，不是 generic persistence engine。 | `src/med_autoscience/runtime_protocol/domain_authority_refs_index.py`、sidecar export、artifact/source/storage tests。 | owner receipt refs、typed blocker refs、artifact/source locator refs、restore/retention proof refs。 | runtime lifecycle DB、generic restore engine、queue/outbox/retry owner。 |
| `owner_route_handoff*` | Owner-route body-free handoff / dispatch receipt source。 | sidecar export/dispatch tests、owner-route protocol tests、domain dispatch evidence payload。 | MAS owner-route refs、typed blocker、safe-action receipt、no-forbidden-write proof。 | queue hydration、attempt retry、dead-letter、provider resume、runtime liveness arbitration。 |
| product-entry / status / workbench projection helpers | Direct MAS projection source and OPL handoff input。 | product-entry manifest/status tests、Progress Portal tests、OPL App/workbench drilldown refs。 | domain progress refs、route refs、owner receipt refs、typed blocker refs、artifact/source refs。 | generic App/workbench owner、terminal/log transport、worker residency、lifecycle owner。 |
| CLI / MCP / Skill direct path | Domain handler target and diagnostic direct entry。 | CLI/MCP/product-entry parity tests、generated surface handoff。 | authority callable、refs reader、AI-first validator command、owner receipt signer。 | default generated shell owner、scheduler/status/remove cleanup surface、compatibility alias。 |
| production acceptance contract | Structural conformance and production-like receipt-chain evidence。 | `contracts/production_acceptance/mas-production-acceptance.json`、production acceptance tests。 | standard Agent shape, receipt chain refs, typed blocker refs, no-forbidden-write refs。 | domain-ready、publication-ready、artifact mutation authorization、`current_package` update。 |

## 当前关闭门

| gate | 关闭条件 | 验证入口 |
| --- | --- | --- |
| `generated_surface_default_owner_cutover` | OPL generated/default shell consumes MAS pack and refs; MAS hand-written shell 只保留 domain handler target。 | generated surface handoff tests、product-entry / CLI / MCP focused tests、OPL descriptor validation。 |
| `domain_authority_refs_thinning` | Storage、artifact、memory、source、owner-route 和 status helper 只输出 refs、receipts、blockers 或 locators。 | sidecar export tests、storage/artifact/source focused tests、domain authority refs index tests。 |
| `standard_agent_purity_guard` | Current product-entry、sidecar、status/read-model 默认只暴露标准 Agent 口径、domain refs、owner receipts 和 typed blockers。 | `tests/standard_agent_purity_helpers.py`、`tests/test_opl_unique_control_plane_boundary.py`、`tests/test_test_lane_governance.py`。 |
| `opl_app_workbench_drilldown` | MAS 只提供 route/source/quality/artifact/memory/blocker/action refs；OPL owns App/workbench shell。 | product-entry manifest/status tests、App/workbench drilldown refs。 |
| `lifecycle_locator_retention_restore_ledger_reconciliation` | OPL lifecycle/index/restore/retention consumes MAS refs without writing MAS truth、memory body or artifacts。 | artifact lifecycle / storage audit tests、OPL current-control-state refs、focused meta lane。 |

## 当前保留与删除规则

- 当前源码、tests、contracts 和 active docs 只承认 `declarative_pack_generated_surface`、`domain_authority_refs`、`minimal_authority_function` 与 `standard_agent_purity_guard`。
- 旧 runtime/control/workbench/scheduler 名称只可出现在 `docs/history/**`、explicit tombstone contract 或 absence guard 中；它们不得成为 product-entry、sidecar、status、read-model、CLI、MCP 或 test-lane 默认字段。
- 满足 OPL generated/provider parity、MAS receipt parity、focused tests、no-forbidden-write proof 和 history/provenance refs 后，旧 wrapper、facade、alias 和只保护旧调用路径的测试直接删除、archive 或 tombstone。
- 仍缺真实 paper-line provider apply、publication-route memory receipt、artifact lifecycle receipt、human gate/resume 和 provider SLO long-soak 的证据时，只记录为测试/证据差距；不得回写成 MAS 结构未清理或 private generic owner retained。

## 当前验证入口

| 验证 | 覆盖内容 |
| --- | --- |
| `tests/test_opl_unique_control_plane_boundary.py` | functional consumer boundary、standard Agent purity guard、handoff key shape。 |
| `tests/test_test_lane_governance.py` | test-lane manifest 与 runtime boundary 同步。 |
| `tests/test_product_entry.py`、`tests/test_mcp_server.py` | product-entry / MCP 默认面不输出旧 active/default surface。 |
| `tests/test_opl_family_contract_adoption.py` | OPL family contract adoption proof refs。 |
| `make test-meta` | machine-readable contract / docs governance focused meta lane。 |
| `scripts/verify.sh` | repo-native smoke and hygiene floor。 |
