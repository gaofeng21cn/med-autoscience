# Display Pack docs SSOT closeout 2026-06-12

Owner: `MedAutoScience`
Purpose: `docs_lifecycle_governance_closeout`
State: `history_provenance`
Machine boundary: 本文是人读 docs lifecycle closeout 记录。当前 Display Pack 机器真相继续归 `contracts/display-pack-contract.v2.json`、`contracts/medical_figure_spec_contract.json`、`contracts/publication_figure_quality_contract.json`、source validators、CLI behavior、tests、display pack descriptors、paper artifact refs、lock、submission manifest 和 owner receipts。

## Scope

本轮只治理 Display Pack active-path 文档措辞。写入范围为 `docs/decisions.md`、`docs/delivery/medical-display/examples/display_pack_v2_e2e_skeleton.md` 和本 history closeout；未修改源码、contracts、tests、workflow、CLI/API 或 runtime surfaces。

## Semantic Theme

Display Pack E2E 文档曾把 `python_plugin` 和 `paper/figure_spec.json` 写成当前 active path 的 compatibility / 兼容面叙述。当前 SSOT 是：

- `python_plugin` 仍是 source/contract 支持的 renderer adapter，用于 MAS host-native renderer、轻量 fixture 和内部 materializer。
- R/ggplot2-first subprocess renderer 是医学论文 evidence figure 的推荐默认路线。
- `paper/figure_spec.json` 是单图 grammar 面；`paper/figure_specs.json` 是批量 grammar 面。
- baseline / legacy comparison provenance 只能说明 P1 renderer promotion 的历史对照，不授权 publication readiness、artifact authority、owner receipt、quality verdict 或 submission readiness。

## Foldback

- `docs/decisions.md`：把标题和决策项从 compatibility / 兼容面口径收薄为 adapter / grammar 口径。
- `docs/delivery/medical-display/examples/display_pack_v2_e2e_skeleton.md`：示例继续展示同一 descriptor contract，但不把 host-native adapter 或单图 grammar 写成兼容承诺。
- `docs/history/program/README.md`：将本 closeout 并入主题级 docs lifecycle provenance。

## Verification Scope

Docs-only verification is sufficient because no machine-readable contract, source, tests, CLI/API behavior or runtime semantics changed:

- `rtk git diff --check`
- conflict-marker scan over tracked `README*`, `docs/**/*.md` and `contracts/**/*.md`
- `opl-doc-doctor doctor . --format json`

## Remaining Scope

本轮不授权删除 `python_plugin`、`paper/figure_spec.json`、任何 Display Pack source/test/contract/workflow/CLI/API surface 或 renderer template。后续物理退役仍需要 replacement owner、no-active-caller、fixture/provenance 读法、focused tests 和 tombstone/provenance 指针。
