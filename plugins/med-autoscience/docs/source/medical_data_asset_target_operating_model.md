# Medical Data Asset Target Operating Model

Owner: `MedAutoScience`
Purpose: `medical_data_asset_target_operating_model_v3_runbook`
State: `active_runbook`
Machine boundary: 人读目标态。机器真相继续归 `data/datasets/**/dataset_manifest.yaml`、study contract / `study.yaml`、`memory/portfolio/data_assets/**` 的 controller projection、owner receipt、typed blocker 和真实 workspace artifact。

## 读法

本文定义医学数据资产的事实分层。DPCC 的 `restricted_raw -> deidentified_longitudinal -> standardized_longitudinal` 仅作为命名示例；真实 release 状态必须读取目标 workspace。

当前 canonical 在线路径是：

- 数据 body：`data/datasets/<family>/<version>/`
- 数据资产 registry / impact / mutation / startup readiness：`memory/portfolio/data_assets/**`
- study 绑定：`studies/<study-id>/study.yaml` 或 controller-authorized study contract
- study 派生 cohort、index event、sensitivity set 和 model-ready matrix：`studies/<study-id>/analysis/**`

v3 runbook 的操作者结论：

- DPCC 原始、清洗、标准化 release 都放在 `data/datasets/**` 的 body plane 下；study 只通过 manifest/study contract 消费 release ref。
- `manifest_refs` 是 controller 可重建 projection，不是手工 registry，也不是 dataset body。
- `data/datasets/**` 不进入 runtime residue cleanup、restore-proof compaction 或 runtime lifecycle SQLite payload retention。
- online workspace、dataset assets、cold store 和 remaining non-dataset large files 必须分账报告。
- OPL substrate 只消费 locator、ref、lineage/projection 和 restore/cold-store shell，不取得 MAS 医学数据 authority。

## 外部工程经验校准

- Databricks medallion architecture 把 lakehouse 数据按质量层推进，强调从 raw 到 cleaned/validated 再到 business-ready 的单一事实源分层：[Databricks docs](https://docs.databricks.com/aws/en/lakehouse/medallion)。
- OpenLineage 用 Dataset、Job、Run 和 facets 表达执行时 lineage 元数据，适合抽象为 MAS/OPL 的 refs-only lineage event 形状：[OpenLineage object model](https://openlineage.io/docs/spec/object-model/)。
- Great Expectations 把 expectation suites、validation results 和 Data Docs 连起来，让数据质量检查既机器可跑又人可审：[GX Data Docs](https://docs.greatexpectations.io/docs/0.18/reference/learn/terms/data_docs)。
- CDISC ADaM 强调分析数据、分析结果和 SDTM 源数据之间的 traceability，这是 MAS 临床论文数据面必须保留的最低医学审计链：[CDISC ADaM](https://www.cdisc.org/standards/foundational/adam)。
- OHDSI OMOP CDM 证明临床观测数据可以通过可重复 ETL、标准结构和标准词汇支持可复现分析；MAS 不必强制采用 OMOP，但应吸收 source preservation、standard vocabulary mapping 和 repeatable ETL 的纪律：[OHDSI ETL](https://ohdsi.github.io/TheBookOfOhdsi/ExtractTransformLoad.html)。
- FAIR 原则把机器可发现、可访问、可互操作、可复用作为研究数据治理目标；MAS 的 manifest、registry、lineage 和 quality result 应满足 agent 可操作，而不是只供人读：[GO FAIR](https://www.go-fair.org/fair-principles/)。

## 四个 Plane

MAS 数据资产 v3 按 body、contract、registry-lineage 和 study-binding 四个 plane 读取。四个 plane 可以由不同系统承载，但不能互相替代。

### 1. Body Plane

`data/datasets/<family>/<version>/` 只保存数据 release body 与随 release 固化的主输出。这个目录接近 immutable：已有 release 不静默改写；任何纠错、刷新、标准化或派生都生成新 version。

DPCC 分层示例：

```text
data/datasets/
  dpcc/
    restricted_raw/<raw-snapshot-or-release>/
      dataset_manifest.yaml
      raw_exports/
      source_inventory.*
      restricted_access_note.*
    deidentified_longitudinal/<release-version>/
      dataset_manifest.yaml
      longitudinal_episodes.*
      deidentification_report.*
      source_field_crosswalk.*
    standardized_longitudinal/<release-version>/
      dataset_manifest.yaml
      analysis_table.*
      medication_detail_long.*
      data_dictionary.*
      value_audit.*
      numeric_variable_contract.*
      medication_variable_contract.*
      standardization_report.*
      indexed_working_copy.sqlite
```

具体文件名由 release manifest 声明；上面的目录只固定 authority 分层。`restricted_raw`、`deidentified_longitudinal` 和 `standardized_longitudinal` 是 DPCC release family，不是 MAS 全局枚举。

推荐 family 语义按 release 责任命名，不按脚本名或论文名命名：

- `restricted_raw`：原始受限数据、直接标识符、真实机构/患者/记录标识，只能作为 provenance 和受限审计。
- `deidentified_*`：去标识后的源语义 release，保留字段来源、缺失审计和可回溯键。
- `standardized_*`：分析默认入口，包含单位、语义、词典、合理值、变量合同、质量报告和 indexed working copy。
- `public_*` 或 `external_*`：公开或外部验证数据，默认 remote metadata first，只有明确 study 用例、存储预算和 reuse/prune plan 才下载或物化。
- study-derived body 不写回 workspace 共享数据层；study 特定 cohort、index event、follow-up window、sensitivity set 和 model-ready matrix 放在 `studies/<study-id>/analysis/**`，并通过 refs 指向上游 release。

这些 family 名称不是全局硬编码枚举。硬约束是每个 release 必须有明确 access tier、direct study consumption policy、lineage、quality status、retention policy 和 owner。

### 2. Contract Plane

每个 release 必须有 `dataset_manifest.yaml`，其中 `release_contract` 是机器 contract 来源。最低字段应覆盖：

- identity：`dataset_id`、`family_id`、`version`、`raw_snapshot`
- ownership：owner、steward、生成脚本或受权 StageAttempt、生成时间
- access：privacy tier、direct identifiers、direct study consumption policy、restricted field exposure
- body inventory：main outputs、declared output presence、size/count/hash summary
- lineage：parent datasets、transform job、input refs、output refs、source snapshot、supersedes
- semantic readiness：data dictionary、codebook、derived variables、cohort accounting、standard vocabulary mapping
- quality gates：schema checks、range/plausibility checks、missingness report、row-count reconciliation、duplicate/key checks
- retention：online body policy、cold-store policy、restore command/ref、what must never be pruned
- allowed uses：descriptive analysis、prediction、external validation、causal analysis prohibited/allowed conditions

Manifest 可以继续用 YAML 维护，但 controller 应把它规范化为 JSON projection 供 OPL / App / runtime 读取。自然语言报告只能解释 contract，不能成为第二真相源。

### 3. Registry-Lineage Plane

`memory/portfolio/data_assets/**` 是 derived governance plane，不是手工 body store。

目标读法：

- `private/registry.json` 由 controller 从 `data/datasets/**/dataset_manifest.yaml` 重建。
- `public/registry.json` 记录外部数据候选、retain/reject、用途、license 和 target scope。
- `impact/latest_impact_report.json` 告诉每个 study 是否绑定旧 release、未闭合 contract 或有 advisory public support。
- `startup/latest_startup_data_readiness.json` 只描述 startup data readiness，不授权 study truth、publication verdict 或 artifact authority。
- `mutations/*.json` 是正式审计链，记录原始 payload、mutation result、refresh result 和失败边界。
- `lineage/**` 应采用 OpenLineage-like refs-only event shape：dataset input/output、job/run id、code ref、parameters fingerprint、schema fingerprint、quality result refs 和 artifact refs。
- `lineage/manifest_refs.json` 是 controller 生成的 refs-only 聚合文件，可以保存 manifest snapshot refs、projection refs；不得复制 release body。

`manifest_refs` 的 v3 读法：

- source of truth 是 `data/datasets/**/dataset_manifest.yaml` 与 owner-authorized mutation receipt。
- controller 可以随时从 manifest、mutation receipt、lineage event 和 study binding 重建 `manifest_refs`。
- `manifest_refs` 可以被 OPL / workbench / startup readiness 读取为 locator/projection。
- 缺失或过期的 `manifest_refs` 是 projection rebuild 任务；它不授权手写 registry，也不说明 dataset body 缺失。
- `manifest_refs` 不能声明 access tier、direct study consumption、publication traceability 或 source readiness verdict；这些 authority 继续归 MAS manifest / source readiness / owner receipt。

Registry 不持有医学结论，也不复制数据 body。它只回答“有哪些 release、从哪里来、质量/合同是否闭合、哪些 study 受影响、下一 owner 是谁”。

### 4. Study-Binding Plane

Study 只能通过 `study.yaml` 或 controller-authorized study contract 绑定数据：

- `dataset_inputs`：主分析 release，必须 direct consumption allowed。
- `source_provenance_inputs`：可回溯源层，默认不直接分析。
- `restricted_provenance_inputs`：受限原始层，只能受限审计。
- `data_management_policy`：canonical interchange table、indexed working copy、变量合同、用药/数值/术语 contract、study-local derived output boundary。

Study 不得静默修改共享 release。新增 cohort、index event、follow-up window、sensitivity set 和 model-ready matrix 必须写在 study analysis tree，并保留 parent release/version/manifest/lineage refs。

## OPL Substrate 与 MAS Authority

OPL 应上收通用数据资产 substrate，但不持有医学语义权威。

OPL 可拥有：

- generic dataset locator / State Index Kernel sidecar：dataset id、version、path、hash、manifest ref、lineage ref、quality result ref、current pointer、cold ref。
- immutable body / cold-store / restore / retention shell：对象去重、hash 校验、restore proof、online/cold 分账。
- generic lineage event store：Dataset / Job / Run / Facet 风格的 refs-only 事件。
- generic quality result index：validation suite ref、result ref、status、threshold、human-readable docs ref。
- App / workbench projection：按 workspace、study、release、quality gate、impact、next owner 分组展示，不复制 body。
- family-wide conformance：domain repo 是否暴露 data asset contract、是否禁止手工 registry、是否能重建 refs index。

MAS 必须继续拥有：

- medical dataset release contract 和 access tier 判定。
- direct study consumption / restricted raw / deidentification / source readiness 权威。
- clinical semantic mapping、变量解释、标准化合同、claim guardrails。
- study data binding、source readiness blocker、owner receipt、typed blocker。
- publication-facing traceability、analysis-ready verdict 和禁止过度 claim 的红线。

这个分工的目标是让 MAG、RCA、OMA 等 domain agent 复用同一 OPL data asset substrate，同时各自保留 domain-specific release contract。

## 保留与实际调用

数据 release body 与运行 payload 的保留职责见
[Data Asset Storage Retention](../runtime/data_asset_storage_retention.md)。
本页不持有真实 workspace 清理快照、私有 data action 清单或实现 backlog。
公开 Stage 能力和 handler 以 [Agent Interface](../runtime/contracts/agent_runtime_interface.md) 为准；
受权 StageAttempt 使用可发现工具维护数据，OPL 仅提供通用 transport 和 lifecycle。
