# MAS Single-Project MDS Absorb Program

Status: `long-line execution program`
Date: `2026-05-05`
Owner: `MedAutoScience`

## 结论

MAS 长线应成为唯一项目、唯一研究入口和唯一运行治理 owner；MDS 不应继续作为独立日常项目存在。目标不是把 `med-deepscientist` 原样搬进来，而是把 MDS 解构为 MAS 内部可验证能力：能被 MAS 直接拥有的能力进入 MAS owner 模块；仍需对照的能力降级为 oracle fixture；没有长期价值的入口、目录和命名退休。

这个 program 一步到位定义最终可用状态：repo、运行入口、真实论文 workspace layout、兼容导出、GitHub contributor footprint、验证与清理规则都必须一起收敛。执行可以并行开 worktree，但每条 lane 必须有明确 write set、验证和吸收顺序；没有 parity proof 和 rollback surface 的能力不得物理吸收。

## 最终目标形态

目标 repo 拓扑：

```text
med-autoscience/
  src/med_autoscience/
    mas_core/
    quality_os/
    runtime_os/
    artifact_os/
    observability_os/
    runtime_compat/
      legacy_deepscientist/
    backend_oracles/
      deepscientist_legacy/
    migration/
      mds_absorb/
```

目标 workspace 拓扑：

```text
workspace/
  studies/<study_id>/
  artifacts/
  runtime/
    quests/
    lifecycle.sqlite
    archives/
    restore_index/
  ops/mas/
  delivery/
```

旧布局只作为迁移输入和只读兼容层存在：

```text
ops/med-deepscientist/runtime/.ds/
ops/med-deepscientist/runtime/quests/
<quest>/.ds/worktrees/
```

新建 workspace 不得再默认生成 `ops/med-deepscientist`、`.ds` 或以 MDS/DS 为第一身份的路径。旧 workspace 可以保留原路径直到迁移完成，但所有新写入必须进入 MAS-owned runtime layout，旧路径只能通过 compatibility reader、restore index 或 explicit import surface 被读取。

## Contributor Footprint Rule

repo 吸收必须采用 `no-history import`。

禁止：

- `git merge --allow-unrelated-histories` 吸收 `med-deepscientist`
- `git subtree add` 保留上游历史
- `git filter-repo --to-subdirectory-filter` 后把上游历史接进 MAS `main`
- 把上游 DeepScientist / med-deepscientist commit authorship 带入 `med-autoscience` default branch

允许：

- 用 MAS-authored commit 导入经过审计的代码 snapshot
- 用文档记录 upstream ref、source archive hash、license notice、decision matrix 和 retained/rejected capability
- 把完整上游历史保留在外部 archive、tag、private/reference mirror 或 artifact bundle 中，不接入 `main`

吸收前后必须执行 contributor audit：

1. import 前记录 `git shortlog -sne`、候选 source authors、license/provenance refs。
2. import commit 必须使用 MAS maintainer author/committer identity。
3. import 后检查 `git log --format='%an <%ae>' origin/main..HEAD`，不得出现不想进入 MAS contributor graph 的上游作者。
4. push 后用 GitHub contributors / default-branch history 做可见面验证。
5. 若出现不应出现的 contributor footprint，立即停止后续吸收，修正历史后再推进。

## Authority Rules

- MAS Core 持有 study truth、controller truth、user-visible next action。
- Quality OS 持有 scientific quality、medical writing quality、publication readiness、submission authority。
- Runtime OS 持有 runtime health、durable execution、recovery action。
- Artifact OS 持有 canonical rebuild、package locator、delivery authority。
- Observability OS 只持有 evidence、calibration、provider/runtime drift projection。
- `legacy_deepscientist` 只能是 compat/oracle，不得写 study truth、quality truth、publication truth、delivery truth 或 user-visible next action。

任何保留 `deepscientist` 字样的模块必须带 `legacy`、`compat` 或 `oracle` 语义，不得成为产品入口、默认 runtime owner 或独立 governance surface。

## Capability Absorb Matrix

| capability | final MAS owner | MDS final status | absorb gate |
| --- | --- | --- | --- |
| runtime execution | Runtime OS | oracle fixture until cutover | execution replay parity、recovery regression、rollback surface |
| quest layout | Runtime OS | compatibility reader | new MAS runtime layout writer、old layout reader、restore proof |
| `.ds` runtime payload | Runtime OS / runtime lifecycle | archived import source | SQLite lifecycle index、cold archive、restore index |
| artifact inventory | Artifact OS | fixture only | MAS package locator parity、old current_package reader compatibility |
| paper contract health | Quality OS | mechanical oracle only | AI reviewer / publication eval authority unchanged |
| manuscript coverage | Quality OS | mechanical oracle only | coverage can request review, cannot authorize ready |
| prompt stage discipline | Quality OS / Runtime OS | example and violation fixture | MAS stage contract owns transitions |
| memory / lesson store | Evaluation OS | intake fixture | incident learning import, observability-only output |
| product entry / CLI / MCP | MAS app skill / MAS CLI / MAS MCP | retired | all active commands route through MAS |
| skills / overlay templates | MAS-owned app skill | legacy template source | no global MDS skill injection |

## Long-Line Lanes

这些 lane 可以并行执行，但必须在吸收回 `main` 前完成对应验证。

| lane | branch suggestion | write set | target |
| --- | --- | --- | --- |
| `L0_target_contract` | `codex/mas-mds-absorb-target-contract` | docs/program、architecture/status references、contract tests | 固定单项目拓扑、no-history import、workspace去 MDS/DS 化规则。 |
| `L1_workspace_layout_contract` | `codex/mas-workspace-layout-v3` | workspace layout helpers、runtime protocol layout tests、docs/runtime | 新 workspace 默认写 MAS layout；旧 `.ds` / `ops/med-deepscientist` 只读兼容。 |
| `L2_mds_inventory_and_classification` | `codex/mas-mds-capability-inventory` | migration inventory tooling、capability matrix、source snapshot manifest | 盘点 MDS 能力，逐项标记 `absorb` / `oracle` / `retire`。 |
| `L3_runtime_absorb` | `codex/mas-runtime-os-absorb` | Runtime OS、runtime_protocol、recovery tests | 吸收 execution/recovery/quest lifecycle，保留 MDS trace replay oracle。 |
| `L4_artifact_and_storage_absorb` | `codex/mas-artifact-storage-absorb` | Artifact OS、runtime lifecycle SQLite、storage migration tests | 吸收 artifact inventory、storage audit、cold archive / restore proof。 |
| `L5_quality_oracle_absorb` | `codex/mas-quality-oracle-absorb` | Quality OS、publication eval、AI reviewer fixtures | paper health / coverage 变成 mechanical oracle，不授权 ready。 |
| `L6_entrypoint_retirement` | `codex/mas-mds-entry-retirement` | CLI/MCP/product-entry/skill docs/tests | 退休 MDS product entry、global skill、重复 status/progress surface。 |
| `L7_contributor_and_license_guard` | `codex/mas-no-history-import-guard` | scripts/tests/docs/legal or provenance records | no-history import guard、author audit、license/provenance snapshot。 |
| `L8_real_workspace_cutover` | `codex/mas-real-workspace-layout-cutover` | real workspace migration ledgers only | NF-PitNET、DM-CVD、DPCC 等 workspace dry-run、apply、compat export、restore proof。 |

## Execution Order

1. `L0` 先吸收，作为所有后续 lane 的 contract baseline。
2. `L1`、`L2`、`L7` 可并行；它们分别冻结 layout、inventory 和 contributor guard。
3. `L3`、`L4`、`L5` 依赖 `L1/L2`，可以按 disjoint write set 并行。
4. `L6` 只能在 MAS 入口 parity 通过后执行。
5. `L8` 只能在 repo capability 通过后对真实 workspace 做 controller-authorized migration。

## Workspace Layout Migration Rule

新 workspace：

- 默认生成 `runtime/quests/`、`runtime/lifecycle.sqlite`、`runtime/archives/`、`runtime/restore_index/`、`ops/mas/`。
- 不生成 `.ds`、`ops/med-deepscientist` 或 MDS-first path。
- `study-progress`、`runtime_watch`、`product-frontdesk`、MCP 都只暴露 MAS layout。

旧 workspace：

- 第一次 maintenance 生成 `artifacts/runtime/layout_migration/latest.json`。
- live quest 只允许 audit/index，不移动或删除。
- stopped/cold quest 允许 dry-run、archive、restore proof、compat export、apply。
- 旧 `.ds` 内容迁入 `runtime/archives/` 或 `runtime/quests/` 后，必须写 restore index、source checksum、compatibility reader proof。
- old reader 必须能解释旧路径，但新 writer 不得继续写旧路径。

## Repo Import Rule

所有从 MDS 进入 MAS 的代码必须走 snapshot import：

1. 从受控 MDS ref 生成 source snapshot。
2. 删除不吸收的 provider/UI/global skill/old product entry。
3. 写 `source_provenance.json`，包括 upstream repo/ref、snapshot sha256、license refs、capability classification。
4. 以 MAS maintainer 身份创建 import commit。
5. import commit message 只记录 upstream ref 和 provenance file，不带上游 co-author trailers。
6. import 后运行 author audit 和 capability parity tests。

如果需要保留完整历史，只能放在不进入 default branch contributor graph 的外部 reference surface。

## Verification Gates

Repo gates：

- `make test-meta`
- `scripts/verify.sh`
- owner-boundary tests
- runtime layout tests
- MDS capability parity tests
- contributor author audit
- `git diff --check`

Workspace gates：

- layout inventory ledger
- old path reader compatibility
- new path writer proof
- restore index and checksum proof
- live audit-only proof
- stopped/cold apply proof
- user-facing progress still reads the same study truth

Contributor gates：

- no unwanted upstream author in new MAS commits
- no upstream co-author trailers in MAS import commits
- GitHub default-branch contributor surface checked after push
- provenance retained outside contributor graph

## Definition Of Done

这个 program 完成时必须同时满足：

- `med-autoscience` 是唯一日常 repo 和唯一用户入口。
- 新 workspace 完全使用 MAS layout。
- 旧 workspace 有 migration ledger、compat export 和 restore proof。
- MDS 独立 repo 不再是运行必需 owner。
- 所有保留的 DeepScientist 资产都位于 `legacy` / `compat` / `oracle` 语义下。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 等 MAS truth surface 不被 MDS 写回。
- GitHub contributor graph 不因 no-history import 出现上游 DeepScientist contributor。
- 真实论文线至少完成一个 stopped/cold workspace apply 和一个 live workspace audit-only 验证。

## Non-Goals

- 不把 MDS 原始历史接入 MAS `main`。
- 不把 `.ds` 作为新 layout 的隐藏默认目录。
- 不用 MDS mechanical oracle 授权医学论文 ready。
- 不在 live quest 上做破坏性 layout migration。
- 不把文档计划写成 repo capability 或真实 workspace cutover 已完成。
