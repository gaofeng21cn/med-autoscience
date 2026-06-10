# Medical Data Asset Target Operating Model

Owner: `MedAutoScience`
Purpose: `medical_data_asset_target_operating_model`
State: `active_design`
Machine boundary: Human-readable target design. Current machine truth remains in `data/datasets/**/dataset_manifest.yaml`, `study.yaml`, `memory/portfolio/data_assets/**`, controller outputs, owner receipts and typed blockers.

## 读法

本文定义 MAS 医学研究数据资产的目标态，不以当前 DPCC 实现为上限。当前 DPCC 的 `restricted_raw -> deidentified_longitudinal -> standardized_longitudinal` 是合理实例，但长期一致性应来自通用 release contract、lineage、quality gate 和 OPL substrate，而不是每个 Codex 会话各自发明目录。

当前 canonical 在线路径是：

- 数据 body：`data/datasets/<family>/<version>/`
- 数据资产 registry / impact / mutation / startup readiness：`memory/portfolio/data_assets/**`
- study 绑定：`studies/<study-id>/study.yaml`
- study 派生队列、事件 cohort 和敏感性集合：`studies/<study-id>/analysis/**`

旧根层 `datasets/` 和 `portfolio/data_assets/` 只作为 legacy/provenance 或兼容扫描输入，不再作为新 workspace、文档、study YAML 或 runbook 的默认生成路径。

## 外部工程经验校准

- Databricks medallion architecture 把 lakehouse 数据按质量层推进，强调从 raw 到 cleaned/validated 再到 business-ready 的单一事实源分层：[Databricks docs](https://docs.databricks.com/aws/en/lakehouse/medallion)。
- OpenLineage 用 Dataset、Job、Run 和 facets 表达执行时 lineage 元数据，适合抽象为 MAS/OPL 的 refs-only lineage event 形状：[OpenLineage object model](https://openlineage.io/docs/spec/object-model/)。
- Great Expectations 把 expectation suites、validation results 和 Data Docs 连起来，让数据质量检查既机器可跑又人可审：[GX Data Docs](https://docs.greatexpectations.io/docs/0.18/reference/learn/terms/data_docs)。
- CDISC ADaM 强调分析数据、分析结果和 SDTM 源数据之间的 traceability，这是 MAS 临床论文数据面必须保留的最低医学审计链：[CDISC ADaM](https://www.cdisc.org/standards/foundational/adam)。
- OHDSI OMOP CDM 证明临床观测数据可以通过可重复 ETL、标准结构和标准词汇支持可复现分析；MAS 不必强制采用 OMOP，但应吸收 source preservation、standard vocabulary mapping 和 repeatable ETL 的纪律：[OHDSI ETL](https://ohdsi.github.io/TheBookOfOhdsi/ExtractTransformLoad.html)。
- FAIR 原则把机器可发现、可访问、可互操作、可复用作为研究数据治理目标；MAS 的 manifest、registry、lineage 和 quality result 应满足 agent 可操作，而不是只供人读：[GO FAIR](https://www.go-fair.org/fair-principles/)。

## 目标态分层

MAS 数据资产应按四个 plane 读取。

### 1. Body Plane

`data/datasets/<family>/<version>/` 只保存数据 release body 与随 release 固化的主输出。这个目录应接近 immutable：已有 release 不静默改写；任何纠错、刷新、标准化或派生都生成新 version。

推荐 family 语义按 release 责任命名，不按脚本名或论文名命名：

- `restricted_raw`：原始受限数据、直接标识符、真实机构/患者/记录标识，只能作为 provenance 和受限审计。
- `deidentified_*`：去标识后的源语义 release，保留字段来源、缺失审计和可回溯键。
- `standardized_*`：分析默认入口，包含单位、语义、词典、合理值、变量合同、质量报告和 indexed working copy。
- `public_*` 或 `external_*`：公开或外部验证数据，默认 remote metadata first，只有明确 study 用例、存储预算和 reuse/prune plan 才下载或物化。
- `study-derived` 不应写回 workspace 共享数据层；study 特定 cohort、index event、sensitivity set 放在 `studies/<study-id>/analysis/**`，并通过 refs 指向上游 release。

这些 family 名称不是硬编码枚举。硬约束是每个 release 必须有明确 access tier、direct study consumption policy、lineage、quality status 和 owner。

### 2. Contract Plane

每个 release 必须有 `dataset_manifest.yaml`，其中 `release_contract` 是机器 contract 来源。最低字段应覆盖：

- identity：`dataset_id`、`family_id`、`version`、`raw_snapshot`
- ownership：owner、steward、生成脚本或 controller、生成时间
- access：privacy tier、direct identifiers、direct study consumption policy、restricted field exposure
- body inventory：main outputs、declared output presence、size/count/hash summary
- lineage：parent datasets、transform job、input refs、output refs、source snapshot、supersedes
- semantic readiness：data dictionary、codebook、derived variables、cohort accounting、standard vocabulary mapping
- quality gates：schema checks、range/plausibility checks、missingness report、row-count reconciliation、duplicate/key checks
- retention：online body policy、cold-store policy、restore command/ref、what must never be pruned
- allowed uses：descriptive analysis、prediction、external validation、causal analysis prohibited/allowed conditions

Manifest 可以继续用 YAML 维护，但 controller 应把它规范化为 JSON projection 供 OPL / App / runtime 读取。自然语言报告只能解释 contract，不能成为第二真相源。

### 3. Registry And Lineage Plane

`memory/portfolio/data_assets/**` 是 derived governance plane，不是手工 body store。

目标读法：

- `private/registry.json` 由 controller 从 `data/datasets/**/dataset_manifest.yaml` 重建。
- `public/registry.json` 记录外部数据候选、retain/reject、用途、license 和 target scope。
- `impact/latest_impact_report.json` 告诉每个 study 是否绑定旧 release、未闭合 contract 或有 advisory public support。
- `mutations/*.json` 是正式审计链，记录原始 payload、mutation result、refresh result 和失败边界。
- lineage 应新增 OpenLineage-like refs-only event shape：dataset input/output、job/run id、code ref、parameters fingerprint、schema fingerprint、quality result refs 和 artifact refs。

Registry 不应复制数据 body，也不应持有医学结论。它只回答“有哪些 release、从哪里来、质量/合同是否闭合、哪些 study 受影响、下一 owner 是谁”。

### 4. Study Binding Plane

Study 只能通过 `study.yaml` 或 controller-authorized study contract 绑定数据：

- `dataset_inputs`：主分析 release，必须 direct consumption allowed。
- `source_provenance_inputs`：可回溯源层，默认不直接分析。
- `restricted_provenance_inputs`：受限原始层，只能受限审计。
- `data_management_policy`：canonical interchange table、indexed working copy、变量合同、用药/数值/术语 contract、study-local derived output boundary。

Study 不得静默修改共享 release。新增 cohort、index event、follow-up window、sensitivity set 和 model-ready matrix 必须写在 study analysis tree，并保留 parent release/version/manifest/lineage refs。

## OPL 基座优化

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

## 理想命令面

长期命令面应收敛为两层。

MAS domain commands：

```text
medautosci data assets-status --workspace-root <workspace>
medautosci data startup-readiness --workspace-root <workspace> --study-id <study>
medautosci data apply-asset-update --workspace-root <workspace> --payload-file <payload.json>
medautosci data asset-impact --workspace-root <workspace>
medautosci data release-explain --workspace-root <workspace> --dataset-id <id> --version <version>
```

OPL generic commands：

```text
opl data-asset index rebuild|doctor|integrity-check --workspace <workspace>
opl data-asset lineage explain --dataset <id>@<version>
opl data-asset restore --cold-ref <ref>
opl data-asset conformance --domain mas|mag|rca|oma
```

MAS commands decide medical authority. OPL commands rebuild generic indexes, restore body, and display refs.

## 近期落地顺序

1. Path currentness：所有 active policy、quickstart、workspace architecture 和 live workspace pointers 统一到 `data/datasets` 与 `memory/portfolio/data_assets`。
2. Manifest schema hardening：为 `release_contract` 增加 repo-level schema / focused tests，至少覆盖 access tier、direct consumption、main outputs、lineage、quality gate refs、retention policy。
3. Lineage event shape：新增 refs-only lineage event projection，先兼容 existing `generated_by` / `source_release`，再扩到 input/output/job/run/facet。
4. Quality result projection：不直接引入 Great Expectations 依赖，先定义 MAS-native expectation/result/doc refs contract；需要时再接 GX-like renderer。
5. Study-derived boundary：让 `study.yaml` 和 data asset impact report 明确区分 shared release 与 study-local cohort/event artifacts。
6. OPL substrate adoption：在 OPL State Index Kernel 上新增 data asset family conformance，MAS 只投影 refs 和 authority result。
7. UI/workbench：先 body-free 展示 data asset currentness、quality status、study impact、lineage graph 和 next owner，不提供手工编辑 registry。

## 禁止路径

- 不把 `runtime/`、attempt ledger 或 OPL queue 当作数据主存储。
- 不把 SQLite refs index 当作 dataset body authority；SQLite 可以是 indexed working copy 或 rebuildable sidecar。
- 不让 Codex 手写 `memory/portfolio/data_assets/private/registry.json` 代替 manifest/controller mutation。
- 不把受限原始数据直接作为 study `dataset_inputs`。
- 不在共享 release 目录内写 study-specific cohort。
- 不把 public dataset 的存在写成 hard blocker；只有 study contract 明确要求时才升级。
- 不为 DPCC 的 family 名称写全局硬编码；DPCC 是实例，不是 MAS 数据资产模型本身。
