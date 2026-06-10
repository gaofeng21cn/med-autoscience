# Data Asset Storage Retention Runbook

Owner: `MedAutoScience`
Purpose: `data_asset_storage_retention_runbook`
State: `active_runbook`
Machine boundary: 人读 runbook。机器真相继续归 `data/datasets/**/dataset_manifest.yaml`、controller projections、runtime retention receipts、cold refs、SQLite integrity proof、owner receipts、typed blockers 和真实 workspace artifact。

## 结论

MAS storage 治理必须先区分 dataset asset 与 runtime residue。`data/datasets/**` 是医学数据 release body，不属于 `.ds`、attempt ledger、runtime lifecycle payload、restore-index detail 或 refs-index cleanup 的默认目标。任何移动、冷归档、删除或重建数据 release body，都必须回到 dataset manifest、source readiness、study impact 和 MAS owner-authorized data asset mutation。

## 四桶分账

每次报告 workspace 体积或清理计划时，按四桶列账：

| 桶 | 判断方式 | 允许动作 |
| --- | --- | --- |
| `online_workspace` | workspace 内当前 truth、manifest、receipt、restore proof、latest pointer、runtime refs 和必要运行依赖 | 只按对应 owner surface 维护；不能按大小裸删 |
| `dataset_assets` | `data/datasets/**` 及 release-local manifest、quality/audit/index 输出 | data asset impact、dataset-level retention proposal、source readiness / owner receipt |
| `cold_store` | `.cold_ref.json` 指向的 offline object、semantic capsule、legacy archive body | reference audit、dedupe、semantic retention、dataset-level restore |
| `remaining_non_dataset_large_files` | 非 dataset 的 runtime payload、legacy archive、report/detail array、cache、venv、SQLite payload | runtime retention、restore-proof compaction、SQLite integrity/compact、bootstrap/cache lifecycle |

“在线目录大”不是清理授权。若大头是 `dataset_assets`，先做数据资产 runbook；若大头是 `remaining_non_dataset_large_files`，再进入 runtime retention。

## Dataset Body 保护规则

以下路径不得作为 runtime residue cleanup 目标：

- `data/datasets/**`
- release-local `dataset_manifest.yaml`
- release-local dictionary、quality report、audit report、contract、indexed working copy 或 declared output
- study contract 中仍绑定的 release body
- data asset mutation receipt 明确要求保留的 parent release

Runtime retention 命令不得把这些对象当作 oversized payload、historical body、restore-index detail、runtime lifecycle SQLite payload 或 refs-only state index 内容处理。

## Runtime Retention 可处理对象

以下对象属于 runtime/storage lifecycle，可按既有 runtime guard 执行：

- legacy `.ds` intake residue；
- `.ds/runs`、`.ds/codex_homes`、`.ds/python_pycache` 等 stopped-cold runtime buckets；
- provider attempt payload、large diagnostic JSONL、runtime report snapshot；
- restore proof 中可外置的 detail arrays；
- runtime lifecycle SQLite 的 externalized payload refs；
- body-free domain authority refs index、cursor/index/outbox/receipt refs；
- 已验证 cold refs 中仍承诺 exact raw restore 的 legacy archive/body 对象。

这些动作仍必须有 dry-run、receipt、hash/proof、cold ref 或 SQLite integrity proof。它们不授权 dataset body mutation、study truth、paper truth、publication verdict、current package 或 artifact authority。

## Cold Store 与 Dataset Release

Cold store 是存储层，不是 authority owner。

Dataset release body 可以进入 cold store，但需要 dataset-level cold ref：

- source `dataset_manifest.yaml` 记录 retention / restore policy；
- cold object 有 sha256、size、surface kind、restore command 或 semantic restore policy；
- study impact report 说明哪些 study 绑定该 release；
- owner receipt 或 typed blocker 说明 mutation 是否完成或为何不能完成。

Generic cold-store reference audit 只能判断 object 是否被 ref 引用。它不能判断 DPCC raw、deidentified 或 standardized release 是否可删。即使 cold store 很大，只要 object 被有效 cold ref 引用，就先读 surface kind 和 manifest policy，再决定是否进入 semantic retention。

## SQLite Compact 分账

SQLite 有两类完全不同的角色：

| SQLite 类型 | 例子 | 处理方式 |
| --- | --- | --- |
| runtime refs / lifecycle SQLite | `artifacts/runtime/domain_authority_refs.sqlite`、`runtime_lifecycle.sqlite`、`mas_refs_only_state_index_pilot.sqlite` | 可按 runtime lifecycle payload retention、refs-only rebuild、`VACUUM INTO`、`PRAGMA integrity_check` 处理 |
| dataset release SQLite | DPCC `standardized_longitudinal/**/indexed_working_copy.sqlite` | 作为 release output 或 rebuildable sidecar，由 `dataset_manifest.yaml` 和 study impact 决定保留/重建/冷归档 |

不得因为文件扩展名是 `.sqlite` 就把 dataset release working copy 纳入 runtime lifecycle compact。runtime SQLite compact 不得改写 manifest、release body、study `dataset_inputs` 或 data asset projection authority。

## manifest_refs 重建

`memory/portfolio/data_assets/**/manifest_refs.json` 是 controller rebuildable projection。

操作规则：

1. 先读 `data/datasets/**/dataset_manifest.yaml` 和 data asset mutation receipts。
2. 由 controller 重建 registry、lineage、impact、startup readiness 和 manifest refs。
3. 若 projection 缺失或 stale，记录 projection rebuild 任务。
4. 不手写 `manifest_refs` 来修复 authority。
5. 不把 `manifest_refs` 缺失解释为 release body 可删除。

OPL 可以消费 `manifest_refs` 做 locator/workbench projection；MAS 保留 release contract、access tier、source readiness、direct study consumption 和 study binding authority。

## DPCC 操作口径

DPCC release 当前按三层读取：

- `restricted_raw`：原始受限 release，只作 provenance 和受限审计。
- `deidentified_longitudinal`：去标识 episode/source-semantics release，保留 episode collapse 和字段来源链。
- `standardized_longitudinal`：普通 analysis / manuscript work 默认入口，含 analysis table、dictionary、audit、contracts、standardization report 和 indexed working copy。

DPCC 在线体积审计时，先把这三层列入 `dataset_assets`。只有 manifest、study impact 和 owner-authorized data asset mutation 说明可外置、替换或退役某个 release 时，才生成 dataset-level retention receipt。否则它们不是 runtime cleanup 候选。

## OPL / MAS 分工

OPL 可以持有：

- generic locator / ref index；
- cold-store object shell、restore proof、dedupe / reference audit；
- lineage event transport；
- quality result index；
- App / workbench projection；
- family-wide conformance check。

OPL 不能持有：

- DPCC access tier；
- restricted raw / direct study consumption 判定；
- clinical semantic mapping；
- source readiness verdict；
- study data binding authority；
- owner receipt、typed blocker 或 publication traceability verdict。

MAS 只把 locator/ref/projection 交给 OPL substrate；医学数据 authority 留在 MAS manifest、source readiness、study contract、owner receipt 和 typed blocker。

## 禁止路径

- 不用 `runtime maintain-storage`、historical retention、restore-proof compaction 或 runtime lifecycle SQLite compact 清理 `data/datasets/**`。
- 不把 `manifest_refs` 当成手写 registry 或 dataset body。
- 不把 cold-store referenced object 当成 orphan。
- 不把 dataset release SQLite 当成 runtime lifecycle SQLite。
- 不因 workspace 总大小大就移动 DPCC release body。
- 不让 OPL workbench projection、locator 或 quality-result index 升级为 MAS source readiness 或 study binding authority。
