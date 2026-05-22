Owner: `Med Auto Science`
Purpose: 记录 MAS 仓内仍可见的私有平台化 surface、当前分类、保留 authority 与 OPL 上收/默认化门槛。
State: `active_inventory`
Machine boundary: 本文是人读迁移台账；机器真相以源码、contracts、runtime receipts 与 repo-native tests 为准。

# MAS 私有平台化实现迁移台账

## 当前 Clean Truth

- MAS 必须保留医学研究 truth、publication quality verdict、artifact/package authority、source readiness verdict、AI reviewer/auditor judgment、owner receipt signing、typed blocker materialization 与 domain-specific policy/rubric/quality gate。
- OPL / shared family layer 承担 generic runtime/provider、queue/attempt ledger、scheduler/watch、generated CLI/MCP/Skill/product-entry/status/workbench shell、workspace/source/artifact/memory locator、lifecycle/projection/read-model display shell。
- repo-local product-entry、sidecar、CLI/MCP、status、workbench、runtime/watch 名称面只能作为 migration input、refs-only adapter、domain handler target、diagnostic 或 retained authority function 读取；不能因 active caller 存在而写成长期 MAS-owned platform。

## Inventory

| Surface | 行数 | 当前 active caller | 当前实际职责 | 分类 | MAS 必须保留的 authority | 可迁往 OPL 的 generic 子域 | 迁移/退役门槛 | 推荐验证入口 |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| `src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py` | 557 | `controllers/product_entry.py` re-export、domain entry、CLI/MCP product-entry/status、`tests/product_entry_cases/*` | 现在保留 product-entry manifest/status 薄入口、runtime/provider/adoption refs 组装与最终 manifest assembly；product-entry shell/orchestration/quickstart/overview 已拆入 `manifest_shell_surfaces.py`。 | `needs_split_before_migration` -> `already_thin_adapter` | MAS-owned study refs、publication/artifact authority refs、quality verdict refs、owner receipt/typed blocker refs、domain transition refs | generated product-entry/status/workbench manifest shell、App operator projection shell、family product-entry shell assembly | OPL generated/default caller 消费同一 action/stage/pack refs，direct/hosted parity、owner receipt/typed blocker roundtrip、no-forbidden-write proof 和 no-active compatibility alias scan 稳定后，继续删除或 tombstone repo-local handwritten shell。 | `scripts/run-pytest-clean.sh tests/product_entry_cases/action_catalog_parity_cases/action_catalog_cases.py tests/product_entry_cases/functional_consumer_boundary.py tests/test_domain_entry.py -q` |
| `src/med_autoscience/controllers/product_entry_parts/manifest_shell_surfaces.py` | 348 | `build_product_entry_manifest` | 只做 product-entry shell catalog、operator loop actions、family orchestration、quickstart、overview、readiness 与 linked shell surfaces 的自然责任 assembly。 | `opl_framework_migration_candidate` | human inspection package authority boundary、study/progress refs by reference only | OPL generated product/status/workbench shell primitive | 同上；该文件不应继续扩写 runtime/provider/quality/artifact logic。 | 同上 |
| `src/med_autoscience/controllers/product_entry_parts/generated_status_projection.py` | 275 | `manifest_surfaces.py` | runtime inventory、task lifecycle、session continuity、progress projection、artifact inventory refs-only builders。 | `opl_framework_migration_candidate` | MAS progress/status/artifact refs 的来源边界 | runtime/status/workbench projection shell、artifact lifecycle/index projection | OPL projection/default caller parity 与 domain authority refs preserved 后继续收薄；不能把 projection pass 写成 publication ready。 | `scripts/run-pytest-clean.sh tests/product_entry_cases/*status* tests/product_entry_cases/functional_consumer_boundary.py -q` |
| `src/med_autoscience/runtime_transport/__init__.py` | 3 | package import only；无 callable facade | package marker；不再导出 generic runtime callables。 | `already_thin_adapter` | 无；真实 MAS runtime adapter 留在显式 module/backend registry | OPL provider-backed stage runtime registry/default backend | 已收薄；保持 no `create_quest` / `resume_quest` / `schedule_turn` package-level facade。 | `scripts/run-pytest-clean.sh tests/test_runtime_transport_opl_provider_defaults.py tests/test_runtime_backend.py tests/test_study_runtime_transport.py -q` |
| `src/med_autoscience/controllers/runtime_live_console_ui.py` | 721 | live-console controller、CLI live-console commands、live-console tests | read-only operator UI payload + HTML render。 | `opl_framework_migration_candidate` | 无 quality/verdict/artifact mutation authority；只读 MAS runtime observation refs | App/workbench display shell、runtime observation display shell | OPL App/workbench display shell default caller 稳定后，MAS 保留 refs-only payload provider；HTML/render shell 可迁出或 tombstone。 | `scripts/run-pytest-clean.sh tests/test_runtime_live_console_ui.py tests/test_runtime_live_console_read_model.py tests/test_runtime_live_console_stream.py -q` |
| `src/med_autoscience/controllers/domain_owner_action_dispatch.py` | 999 | MAS owner action dispatch / hard-methodology callable path | domain owner action execution、safe action authorization、typed blocker、dispatch receipt。 | `domain_authority_retained` | domain owner action policy、safe action refs、typed blocker、owner receipt | 只可上收 generic receipt/index helper，不迁 action execution | 不能迁移 authority；若拆分，只拆 JSON read/write/history envelope。 | `scripts/run-pytest-clean.sh tests/test_domain_owner_action_dispatch*.py -q` |

## 本轮已修复

- `manifest_surfaces.py` 不再继续承载 product-entry shell/orchestration/quickstart/overview 大段组装；新增 `manifest_shell_surfaces.py` 做自然责任拆分，主 manifest builder 行数从 829 降到 557。
- 该拆分没有把 MAS domain truth、quality verdict、artifact/publication authority、source readiness、owner receipt 或 typed blocker 迁出 MAS，也没有声明 OPL generated/default caller 已完全接管。

## 仍需 OPL 默认化的手段

- generated product-entry/status/workbench shell 成为 active/default caller。
- App/operator projection shell 消费 MAS refs，并证明 direct/hosted parity、owner receipt/typed blocker roundtrip、continuous no-forbidden-write。
- lifecycle/session/artifact/runtime projection shell 提供默认 caller 后，继续删除或 tombstone repo-local handwritten shell residue。
