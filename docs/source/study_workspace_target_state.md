# Study Workspace Target State

Owner: `MedAutoScience`
Purpose: `study_workspace_target_state`
State: `active_support`
Machine boundary: 本文是人读 target-state reference。机器真相继续归 workspace profile、study manifests、stage manifests、runtime/controller surfaces、owner receipts、typed blockers、schemas、CLI/MCP 行为和真实 study workspace artifacts。本文不授权直接手改 study truth、paper body、publication eval、controller decision、runtime state 或 current package。

## 结论

MAS/OPL 的理想论文 workspace 必须同时表达两层结构：

1. `studies/<study_id>/` 是单篇论文的唯一 canonical 用户入口。
2. `artifacts/stage_outputs/<stage_id>/` 是 Stage Native 的唯一 stage-owned artifact 目录。

`paper/`、`analysis/`、`evidence/`、`publication/` 是论文产品视图，方便用户检查当前稿件、分析、证据和投稿包。它们不是 Stage Native 运行目录。Stage 是否完成、卡住或能否进入下一阶段，只能由对应 stage folder 内的 `stage_manifest.json`、role artifacts、`receipts/owner_receipt.json` 或 `receipts/typed_blocker.json` 证明。

如果只整理出 `paper/analysis/evidence/publication`，但没有 stage folder、stage index 和 receipt/blocker，目录看起来会干净，系统仍会继续依赖散落 read-model 和 runtime residue 推断进度。这不是目标态。

## Disease Workspace

病种级 workspace 管共享资源，不承载单篇论文当前真相：

```text
<disease-workspace>/
  README.md
  WORKSPACE_STATUS.md
  workspace.yaml
  workspace_index.json

  data/
    catalog.yaml
    raw_restricted/
    derived/
    external/
    locks/

  literature/
    corpus/
    searches/
    screening/
    summaries/

  memory/
    disease_level/
    methods/
    journal_targets/
    prior_decisions/

  studies/
    <study_id>/

  runtime/
    quests/
      <study_id>/

  reports/
    workspace_dashboard.md
    studies_index.json
    latest_status.json

  archive/
    legacy_mds/
    old_runtime/
    old_paper_surfaces/
```

病种级 `workspace_index.json` 至少应能回答：

- 当前有哪些 study。
- 每个 study 的 canonical root 在哪里。
- 每个 study 当前 stage 是什么。
- runtime/provenance root 在哪里。
- 用户检查入口在哪里。
- 哪些 archive 只作 provenance，不能作为 current truth。

## Study Workspace

单篇论文的目标结构：

```text
studies/<study_id>/
  STUDY_STATUS.md
  study.yaml
  paper.yaml

  control/
    current_stage.json
    next_action.json
    stage_index.json
    blockers.json
    owner_route.json

  artifacts/
    stage_outputs/
      01-intake_and_scope/
      02-source_and_literature_readiness/
      03-analysis_contract/
      04-analysis_execution/
      05-figures_and_tables/
      06-manuscript_writing/
      07-independent_review_and_revision/
      08-publication_gate_and_package/
    immutable_refs/
    package_refs/

  paper/
    draft.md
    medical_manuscript_blueprint.json
    claim_evidence_map.json
    review/
      review_ledger.json
    figures/
      figure_catalog.json
    tables/
      table_catalog.json

  analysis/
    analysis_plan.md
    scripts/
    results/
    validation/

  evidence/
    source_refs.json
    evidence_ledger.json
    reviewer_refs.json
    gate_refs.json

  publication/
    current_package/
    inspection_package/
    submission_package/
    journal_requirements/
    ro-crate-metadata.json

  _archive/
    legacy_surfaces/
    migration_manifest/
```

这组目录的分工是固定的：

| 路径 | 职责 | Truth 级别 |
| --- | --- | --- |
| `study.yaml` | study identity、scope、profile binding | study identity truth |
| `paper.yaml` | paper-facing metadata、journal route、current package refs | paper metadata truth |
| `control/` | 当前 stage、下一动作、owner、blocker、用户检查入口 | control/read-model projection |
| `artifacts/stage_outputs/` | Stage Native stage-owned artifacts、receipts、blockers、lineage | stage evidence / transition authority |
| `paper/` | 当前可读论文正文、表图目录、review ledger | canonical product surface |
| `analysis/` | 分析计划、脚本、结果、验证 | analysis product surface |
| `evidence/` | source/evidence/reviewer/gate refs | evidence product surface |
| `publication/` | 当前检查包、投稿包、RO-Crate metadata | delivery product surface |
| `_archive/` | 旧面、迁移记录、provenance | non-current provenance |

## Stage Native Folder

每个 Stage 必须有单独目录，且目录内必须能独立回答“这个 stage 消费了什么、产出了什么、谁关闭了它、为什么能进下一步或为什么卡住”。

```text
artifacts/stage_outputs/06-manuscript_writing/
  stage_manifest.json

  inputs/
    consumed_artifact_refs.json
    source_fingerprint.json

  outputs/
    draft_delta.md
    writing_plan.json
    claim_evidence_delta.json

  role_artifacts/
    executor_closeout.json
    reviewer_input.json
    auditor_input.json

  receipts/
    owner_receipt.json
    typed_blocker.json

  lineage/
    prov.json
    openlineage_event.json

  projection/
    current_owner_delta.json
```

规则：

- `outputs/` 说明 stage 做出了哪些 evidence。
- `role_artifacts/` 说明 executor、reviewer、auditor 或 human gate 分别留下了什么。
- `receipts/owner_receipt.json` 是推进到下一 stage 的成功凭证。
- `receipts/typed_blocker.json` 是不能推进时的稳定阻断凭证。
- `projection/current_owner_delta.json` 只给 CLI/App/用户读，不拥有 truth。
- 没有 receipt 或 blocker，stage folder 再完整也不能被判定为关闭。

## Product Views vs Stage Outputs

Stage folder 和产品视图不能混成一套目录。

Stage folder 是过程证据和 transition authority：

```text
artifacts/stage_outputs/06-manuscript_writing/outputs/draft_delta.md
artifacts/stage_outputs/06-manuscript_writing/receipts/owner_receipt.json
```

产品视图是用户检查当前成果：

```text
paper/draft.md
paper/claim_evidence_map.json
publication/current_package/
```

二者通过 manifest/ref 绑定，而不是靠用户猜测路径关系。典型绑定写在：

```text
control/stage_index.json
artifacts/stage_outputs/<stage_id>/stage_manifest.json
paper.yaml
```

如果某个 stage 修改了 `paper/draft.md`，stage folder 应记录 produced ref、hash、lineage 和 receipt；`paper/draft.md` 仍是当前正文入口。这样用户看 `paper/` 能检查正文，看 `artifacts/stage_outputs/<stage_id>/` 能检查推进证据。

## Current Stage Index

`control/stage_index.json` 是用户和机器共同定位 stage 的入口。最低字段：

```json
{
  "schema_version": "mas.study_stage_index.v1",
  "study_id": "002-dm-china-us-mortality-attribution",
  "canonical_study_root": "studies/002-dm-china-us-mortality-attribution",
  "current_stage_id": "06-manuscript_writing",
  "stage_outputs_root": "artifacts/stage_outputs",
  "stages": [
    {
      "stage_id": "06-manuscript_writing",
      "stage_root": "artifacts/stage_outputs/06-manuscript_writing",
      "manifest": "artifacts/stage_outputs/06-manuscript_writing/stage_manifest.json",
      "status": "typed_blocked",
      "receipt_ref": null,
      "typed_blocker_ref": "artifacts/stage_outputs/06-manuscript_writing/receipts/typed_blocker.json",
      "product_refs": [
        "paper/draft.md",
        "paper/claim_evidence_map.json"
      ]
    }
  ]
}
```

这个 index 不能替代 stage receipt/blocker。它只是定位和投影。

## Runtime Boundary

`runtime/quests/<study_id>/` 不是论文主目录。它只保留：

- OPL/MAS execution state。
- attempt、lease、worker、queue、retry、event log。
- provider closeout。
- runtime receipt。
- historical provenance。
- restore/archive refs。

用户检查论文进度时，默认入口永远是：

```text
studies/<study_id>/STUDY_STATUS.md
studies/<study_id>/control/next_action.json
studies/<study_id>/control/stage_index.json
studies/<study_id>/publication/current_package/
```

如果某条运行态 evidence 对论文仍重要，必须以 opaque ref 或 provenance ref 进入 stage manifest / lineage / receipt，不能让用户直接去 runtime 目录里找 current truth。

## Clean-Room Migration

旧 workspace 太脏时，合理做法是从 current artifacts 重建干净 study root，而不是在旧 runtime residue 上继续解释。

clean-room migration 必须先生成 manifest：

```text
_archive/migration_manifest/
  current_truth_map.json
  legacy_provenance_map.json
  target_path_map.json
  materialization_plan.json
  validation_result.json
```

manifest 至少证明：

- `paper/draft.md`、claim/evidence map、review ledger、figure/table catalog、blueprint、package artifacts 的 current 去向。
- legacy MDS、runtime residue、旧 submission mirror、supervision artifacts 的 archive/provenance 去向。
- 哪些路径被复制，哪些路径只记录 ref，哪些路径降级为 archive。
- `studies/<study_id>/` 是唯一 canonical study root。
- `runtime/quests/<study_id>/` 未被当成 current paper root。
- 每个 current stage 至少有 stage folder、manifest 和 receipt/blocker 状态。

## External Practice Mapping

MAS/OPL 不直接复制外部项目结构，只吸收稳定工程原则：

| 外部经验 | 可吸收原则 | MAS/OPL 映射 |
| --- | --- | --- |
| [BIDS folder/files](https://bids.neuroimaging.io/getting_started/folders_and_files/folders.html) | 标准目录、稳定命名、metadata sidecar 让研究数据可复用、可自动处理。 | `workspace.yaml`、`study.yaml`、controlled `study_id`、固定 stage/product directories。 |
| [Kedro Data Catalog](https://docs.kedro.org/en/stable/data/data_catalog.html) | 数据源由 catalog 声明，不靠代码或人工猜路径。 | `data/catalog.yaml`、`workspace_index.json`、`source_refs.json`。 |
| [DVC pipelines](https://dvc.org/doc/user-guide/pipelines) | stage、依赖、输出和复现关系显式化。 | `stage_manifest.json`、`inputs/consumed_artifact_refs.json`、`lineage/prov.json`。 |
| [RO-Crate](https://www.researchobject.org/ro-crate/specification/1.1/introduction.html) | 研究对象和交付包用 metadata 描述文件、实体、作者、工具和 provenance。 | `publication/ro-crate-metadata.json`、`publication/current_package/`、package refs。 |

## Acceptance Criteria

一个 clean-room study workspace 只有同时满足以下条件，才算目录治理完成：

1. 用户从 `studies/<study_id>/STUDY_STATUS.md` 能看懂当前论文状态。
2. `control/next_action.json` 指向一个具体 owner、stage、blocked surface 或 safe action。
3. `control/stage_index.json` 能定位 current stage folder。
4. current stage folder 有 `stage_manifest.json`，并有 `owner_receipt.json` 或 `typed_blocker.json`。
5. `paper/`、`analysis/`、`evidence/`、`publication/` 只承载当前产品视图，不混入 runtime residue。
6. `_archive/` 或 workspace-level `archive/` 只承载 non-current provenance，并有 migration manifest。
7. `runtime/quests/<study_id>/` 从用户视角降级为 runtime/provenance。
8. MAS validator/CLI 能 fail closed 检测错误 canonical root、缺 stage manifest、runtime root 被误用为 paper root、archive 被误用为 current truth。
