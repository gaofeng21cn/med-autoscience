# Sidecar Provider And Figure Sidecar Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

## Goal

把当前 `ARIS` 的特例化 sidecar 接入升级为统一的 provider 框架，并在同一骨架下引入 `AutoFigure-Edit` 作为受约束的 `figure` sidecar。

## Non-goals

- 不修改 `DeepScientist core`
- 不让任何 sidecar 直接写 `paper/`、`studies/` 或其他正式交付表面
- 不把 `AutoFigure-Edit` 扩展成可生成结果型证据图的自由工具

## Design

### 1. 通用 sidecar provider 骨架

新增统一 provider registry，公共层只抽这几个稳定能力：

- `provider_id`
- `domain_id`
- `instance_key`
- recommendation gate
- frozen input contract
- handoff root
- imported artifact root
- manifest/hash 校验
- imported audit surface resolution

其中业务语义仍留在 provider 自己的 contract 与导入校验里，不做“所有 sidecar 一个 schema”的过度抽象。

### 2. 路径规则

- 单例 provider，例如 `aris`：
  - `runtime/quests/<quest-id>/sidecars/aris/`
  - `runtime/quests/<quest-id>/artifacts/algorithm_research/aris/`
- 多实例 provider，例如 `autofigure_edit`：
  - `runtime/quests/<quest-id>/sidecars/autofigure_edit/<figure-id>/`
  - `runtime/quests/<quest-id>/artifacts/figures/autofigure_edit/<figure-id>/`

### 3. ARIS provider

保留现有契约和导入要求，只把实现迁移到通用框架中。原有 `aris_sidecar` controller / adapter / CLI 入口保留，作为向后兼容包装层。

### 4. AutoFigure-Edit provider

`autofigure_edit` 固定为 `figure` domain provider，只允许处理：

- `method_overview`
- `study_workflow`
- `graphical_abstract`
- `cohort_schema`

不允许处理：

- ROC、KM、校准曲线、DCA、forest plot、SHAP、subgroup 统计图等结果型证据图
- 任意 metrics / claim 文本的自由篡改

### 5. Figure handoff contract

正式 handoff 至少要求：

- `sidecar_manifest.json`
- `final_figure.svg`
- `final_figure.pdf`
- `preview.png`
- `caption.md`
- `source_trace.json`
- `figure_catalog_entry.json`

导入时要严格验证：

- manifest 的 `provider/status/input_contract_hash`
- `source_trace.json` 引用的 quest-relative source artifacts 真实存在
- `figure_catalog_entry.json` 的 `figure_id` 与 provider instance 一致
- `figure_catalog_entry.json` 只能声明允许的 `paper_role`

导入后把 `figure_catalog_entry.json` 重写成可直接被主线消费的 audit-surface 版本，其 `export_paths` 指向 `artifacts/figures/autofigure_edit/<figure-id>/...`

### 6. CLI

新增通用命令：

- `recommend-sidecar --provider ...`
- `provision-sidecar --provider ...`
- `import-sidecar --provider ...`

原有：

- `recommend-aris-sidecar`
- `provision-aris-sidecar`
- `import-aris-sidecar`

继续保留，内部转发到通用 controller。

## Testing

- 通用 provider registry 与路径布局测试
- `ARIS` 旧测试继续通过
- 新增 `autofigure_edit` recommendation / provision / import / resolve 测试
- CLI 新增通用 sidecar 命令分发测试
