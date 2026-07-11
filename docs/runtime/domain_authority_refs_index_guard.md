# Domain Authority Refs Index Guard

Status: `retired_local_index_body_free_source_adapter_guard`
Date: `2026-07-11`
Owner: `MedAutoScience domain authority refs boundary`
Purpose: `domain_authority_refs_no_runtime_lifecycle_resurrection_guard`
State: `active_support`
Machine boundary: 本文是人读 owner / provenance guard。机器真相继续归 OPL current control state / provider attempt ledger、MAS body-free StateIndex source adapter、owner receipts、typed blockers、artifact/source/quality refs、migration ledgers、restore indexes、archive manifests、runtime/controller surfaces 和 live workspace evidence。

完整历史记录：[2026-05-08 runtime lifecycle SQLite migration full record](../history/program/runtime_lifecycle_sqlite_migration_program_2026_05_08_full_record.md)。

## 当前结论

MAS-local StateIndex 已退役。当前实现只保留 `med_autoscience.opl_domain_pack.state_index_source_refs`，向 OPL StateIndex owner 发出 body-free ref metadata。

- `refs_only_state_index_pilot.py`、`domain_authority_refs_index.py`、本地 SQLite persistence / inspection / replay API、旧 locator 和无效果的 `db_path` 参数已物理删除。
- active callers 不创建、打开、检查或重建 `domain_authority_refs.sqlite` / `mas_refs_only_state_index_pilot.sqlite`。
- `source_adapter_contract()` / `source_adapter_manifest()` 固定 `local_persistence=absent`、`body_included=false` 和 `state_index_owner=one-person-lab`。
- paper、study、publication、artifact、owner receipt 与 typed blocker truth 继续归 MAS authority surfaces；queue、attempt、lifecycle、generic state index、observability 和 workbench shell 归 OPL。
- 旧 SQLite、pilot 报告和 dated canary 只可作为 history、migration、archive 或 cleanup provenance，不是 current adoption、runtime readiness、paper progress 或 owner readback。

## 当前机器入口

| 面 | 当前入口 | 边界 |
| --- | --- | --- |
| MAS source refs | `src/med_autoscience/opl_domain_pack/state_index_source_refs.py` | 只发 body-free source refs，不持久化，不写 OPL runtime state |
| OPL adoption manifest | `runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json` semantic ref | 由 `source_adapter_manifest()` 投影；不是 MAS-local database |
| StateIndex adoption contract | `contracts/state_index_kernel_adoption.json`、`contracts/stage_artifact_kernel_adoption.json` | MAS role 仅为 source adapter；generic index owner 为 OPL |
| Retirement inventory | `contracts/runtime/mas-runtime-surface-retirement-inventory.json` | 固定 12 个 physically retired surface 和 6 个 retained tail |
| Historical migration record | `docs/history/program/runtime_lifecycle_sqlite_migration_program_2026_05_08_full_record.md` | provenance only，不恢复 current helper、pilot 或 CLI |

`runtime_surface_retirement.REQUIRED_RETIRED_SURFACES` 固定每个 retired surface 的 `surface_id`、`replacement_ref`、`tombstone_ref` 和 `retained_mas_role=none`。validator 必须拒绝删除、重命名、错误 replacement、错误 tombstone 或重新赋予 MAS role。

## Authority Boundary

body-free source adapter 可以引用：

- owner receipt、typed blocker、domain intent、owner route、artifact/source/status locator；
- archive、checksum、migration/export provenance；
- stage artifact delta ref metadata。

`paper_progress_transition_refs` 不属于 StateIndex adapter family；它直接保留 body-free policy-request receipt JSONL，由 OPL `DomainProgressTransitionRuntime` 消费。

它不得持有或授权：

- OPL queue、attempt ledger、provider state、retry/dead-letter、worker liveness、current control state；
- generic persistence、lifecycle、StateIndex 或 read-model ownership；
- medical quality、publication/submission readiness、study truth、controller decision、AI reviewer verdict、dataset manifest、canonical manuscript/package 或 current-package mutation。

历史 `domain_authority_refs.sqlite`、`mas_refs_only_state_index_pilot.sqlite` 或相关报告即使仍存在于 workspace/archive，也不得被 active code inspect、replay、compact 或重建为 current MAS index。需要保留时只按 migration/archive/cleanup policy 处理；需要 current index/readback 时回到 OPL owner surface。

## Drift 处理

发现旧 SQLite、pilot flag、helper import、CLI alias 或 locator 时：

1. 先确认是否存在 active caller。只有 active import、调用、参数或 current projection 才是 resurrection regression。
2. 仅存在于 history、tombstone、migration receipt、archive manifest 或 cleanup provenance 时，保持历史语境，不恢复实现。
3. active regression 统一迁回 `opl_domain_pack.state_index_source_refs` 或 OPL StateIndex owner surface，并更新 retirement inventory/test。
4. 涉及真实 workspace 删除或归档时，先绑定 owner、scope、hash/restore proof 和 fresh runtime readback；不要把 repo retirement 直接解释成 live workspace cleanup authorization。
5. runtime/paper/currentness 结论分别从 OPL live readback 与 MAS owner surfaces读取，不能从旧 DB 文件是否存在推断。

## 验证入口

- `make test-paths -- -q tests/test_adapter_retirement_boundary.py`
- `make test-paths -- -q tests/test_opl_family_persistence_adapter.py`
- `make test-paths -- -q tests/test_stage_artifact_kernel_adoption_contract.py`
- `scripts/verify.sh`
- `make test-meta`

focused tests、contracts 和 clean source scans 只证明 repo-source retirement guard；它们不证明 OPL live StateIndex readback、provider running、paper progress、publication readiness 或 production readiness。

## 历史内容归位

旧 schema rationale、pilot 命令、SQLite canary、dated workspace closeout、quest/root Git cutover、restore-proof 数字和 DM002/DM003 当日状态已归入完整历史记录或对应 workspace receipt。当前读者只使用本文理解今天的 body-free adapter 与禁止复活边界；需要追溯时再读历史材料。
