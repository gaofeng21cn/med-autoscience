# Medical Data Asset Target Operating Model

Owner: `MedAutoScience`
Purpose: `medical_data_asset_operating_and_retention_ssot`
State: `active_runbook`
Machine boundary: 机器真相归 `data/datasets/**/dataset_manifest.yaml`、study contract / `study.yaml`、`memory/portfolio/data_assets/**` 的 controller projection、runtime retention receipts、cold refs、SQLite integrity proof、owner receipts、typed blockers 和真实 workspace artifact。

本文统一定义 MAS 医学数据资产的 4-Plane 分层、准入与更新规则、四桶存储分账及保留边界。DPCC 的 `restricted_raw -> deidentified_longitudinal -> standardized_longitudinal` 仅作为命名示例；真实 release 状态必须读取目标 workspace。

## 四个 Plane

MAS 数据资产按 body、contract、registry-lineage 和 study-binding 四个 plane 读取，互不替代（借鉴 Medallion 分层、OpenLineage refs-only lineage、Great Expectations 可审计校验、CDISC ADaM 可追溯链、OHDSI 可重复 ETL 与 FAIR 原则）：

### 1. Body Plane（`data/datasets/<family>/<version>/`）

保存数据 release body 与随 release 固化的主输出，接近 immutable；任何纠错、随访刷新、标准化或派生都生成新 version，不静默覆盖正在被 study 使用的 source。

- `restricted_raw`：原始受限数据与直接标识符，仅用于受权审计和 provenance。
- `deidentified_*`：去标识源语义 release，保留字段来源、缺失审计与可回溯键。
- `standardized_*`：普通分析与写作默认入口，含单位、词典、变量合同、质量报告与 `indexed_working_copy.sqlite`。
- `public_*` / `external_*`：公开或外部验证数据，默认 remote metadata first，记录 accession、license、access tier、endpoint、target study 与纳入/拒绝理由；只有明确用例与预算才物化，可选公开数据机会不阻断当前研究。
- Study 派生 cohort、index event、sensitivity set 与 model-ready matrix 留在 `studies/<study-id>/analysis/**` 并引用 parent release，不写回共享数据层。

### 2. Contract Plane（`dataset_manifest.yaml`）

每个 release 必须通过 `dataset_manifest.yaml`（可规范化为 JSON projection 供 OPL/App 读取）声明 identity（`dataset_id`/`family_id`/`version`/`raw_snapshot`）、ownership、access tier 与 direct study consumption policy、body inventory、lineage、semantic readiness（字典/变量映射）、quality gates、retention/cold-store policy 与 allowed uses。空目录或 manifest 本身不证明数据可用。

### 3. Registry-Lineage Plane（`memory/portfolio/data_assets/**`）

Derived governance plane，不是手工 body store 或个人知识主源：

- `private/registry.json`、`public/registry.json`、`impact/latest_impact_report.json`、`startup/latest_startup_data_readiness.json`、`mutations/*.json` 与 OpenLineage-like `lineage/**` 由 controller 从 manifest 与 mutation receipt 重建。
- `lineage/manifest_refs.json` 是可重建 refs-only 聚合投影，供 OPL/workbench 读取；缺失或过期只触发 rebuild 任务，不得手写修复或把缺失解释为 release body 可删除。
- 新版本不自动使所有旧研究失效：需比较 cohort、变量、endpoint、转换与输入的实质变化，由 MAS 评估受影响 study、既有 Review 与 claim；缺失研究必需数据或违反 access/identity 边界时 fail closed，普通扩展机会保持 advisory。

### 4. Study-Binding Plane（`studies/<study-id>/study.yaml`）

Study 通过 `dataset_inputs`（主分析 release，必须允许直接消费）、`source_provenance_inputs`（默认不直接分析）、`restricted_provenance_inputs`（仅受限审计）与 `data_management_policy` 绑定上游数据，不静默改写共享 release。

## 四桶分账与存储保留边界

MAS storage 治理必须区分 dataset asset 与 runtime residue；“在线目录大”不是清理授权。每次审计按四桶列账：

| 桶 | 范围与判断方式 | 允许动作 |
| --- | --- | --- |
| `online_workspace` | 当前 truth、manifest、receipt、restore proof、latest pointer、runtime refs 与必要依赖 | 只按对应 owner surface 维护；不能按大小裸删 |
| `dataset_assets` | `data/datasets/**` 及 release-local manifest、字典、审计/质量输出、working copy | data asset impact、dataset-level retention proposal、source readiness / owner receipt |
| `cold_store` | `.cold_ref.json` 指向的 offline object、semantic capsule、legacy archive body（含 sha256/size/surface_kind/restore 策略） | reference audit、dedupe、semantic retention、dataset-level restore（不得把有效 cold-ref 对象当 orphan） |
| `remaining_non_dataset_large_files` | 非 dataset 的 `.ds` 历史残留、provider payload、诊断 JSONL、report snapshot、cache、venv、runtime SQLite | runtime retention、restore-proof compaction、SQLite integrity/compact（均须 dry-run、hash/proof 或 integrity proof） |

### SQLite 分账与禁止路径

| SQLite 类型 | 例子 | 处理方式 |
| --- | --- | --- |
| OPL-owned runtime lifecycle SQLite | `runtime_lifecycle.sqlite` | 按 OPL-authorized runtime lifecycle maintenance 与 integrity contract 处理 |
| 历史 MAS-local StateIndex SQLite | `domain_authority_refs.sqlite`、`mas_refs_only_state_index_pilot.sqlite` | 仅作 migration/archive/cleanup provenance；不得重建、compact 或恢复为 current MAS index |
| dataset release SQLite | DPCC `indexed_working_copy.sqlite` | 受 `dataset_manifest.yaml` 与 study impact 约束的 release output / rebuildable sidecar；不得纳入 runtime SQLite compact |

- 禁止用 `runtime maintain-storage`、historical retention 或 runtime SQLite compact 清理 `data/datasets/**` 或改写 study `dataset_inputs`。

## OPL Substrate 与 MAS Authority

| Owner | 持有范围 |
| --- | --- |
| OPL Substrate | generic dataset locator / StateIndex sidecar、immutable cold-store/restore/dedupe shell、refs-only lineage event transport、quality result index、App/workbench projection 与 family conformance |
| MAS Authority | medical release contract、access tier 与 direct consumption 判定、临床语义/变量标准化、claim guardrails、study data binding、source readiness、owner receipt、typed blocker 与 publication traceability |

ToolUniverse 等外部能力是否可调用由当前 descriptor/carrier 决定，不能替代 MAS source readiness 或 quality/artifact authority。公开 Stage 能力与 handler 边界见 [Runtime 边界](../runtime/runtime_boundary.md)。
