# DeepScientist Learning Intake 2026-05-05

Owner: `MedAutoScience`
Purpose: `program_history_record`
State: `history_provenance`
Machine boundary: 人读 program/process 历史记录。当前执行顺序、gap、runtime truth 和 owner boundary 继续归 active owner docs、核心五件套、contracts、source、runtime/controller surfaces 和 owner receipts。

这份记录对应维护者触发的“学习一下 DeepScientist 最新更新”之后的 MAS 侧吸收。MDS 已完成 fresh upstream audit，并在 `med-deepscientist` 记录 `docs/upstream_intake_round_2026_05_05.md`；本文件记录 MAS owner surface 如何承接其中值得长期保留的方法论。

## Fresh Upstream Range

- upstream_range: `1f042ef..bd0b92b`
- upstream_head: `bd0b92b` `Polish BenchStore tutorial flow`
- paired_mds_record: `med-deepscientist/docs/upstream_intake_round_2026_05_05.md`
- paired_mds_landing: `f1f3d0f` `Mirror refreshed summaries to quest root`

## MAS Absorption Lanes

| Lesson | MAS owner surface | Decision | Landing |
| --- | --- | --- | --- |
| `SUMMARY.md` freshness and cross-quest recall | `workspace_projection` + `portfolio_memory` | `adopt_contract` | `77b251a0` adds `study_recall_index.md` as a portfolio memory asset for canonical summaries, resume anchors and failed-path lessons, without becoming study truth or publication authority. |
| exploration-depth gate before all-negative closure | `controller_charter` + `eval_hygiene` | `adopt_contract` | `0c3d55e7` requires explicit exploration-depth review before closing weak/blocked all-negative routes through stop-loss. |
| prescriptive, future-facing limitations | `eval_hygiene` + `ai_reviewer` | `adopt_contract` | `b088affa` requires a future-facing limitations plan: limitation, claim impact, future analysis/data/design, and wording restraint. |

## Decision Matrix

| Upstream lesson | Owner surface | Decision | Rationale |
| --- | --- | --- | --- |
| explicit summary refresh mirrors canonical quest summary | `workspace_projection` / `portfolio_memory` | `adopt_contract` | MAS should read durable, canonical state and preserve reusable recall across studies; MDS implements the backend mirror, MAS owns disease-workspace memory and status semantics. |
| automatic summary refresh on every artifact record, upstream PR #82 | `runtime` | `watch_only` | Useful direction, but implicit per-record side effects need separate MAS authority review before promotion. |
| cross-quest recall / shared memory | `portfolio_memory` | `adopt_contract_without_mds_surface` | MAS absorbs the cross-study memory principle, not the upstream `sharedmemory::` document-id contract. |
| exploration-depth gate for all-negative rounds | `controller_charter` / `eval_hygiene` | `adopt_contract` | Weak or blocked evidence should not directly close a route until subgroup, alternative endpoint, data quality, statistical power and mechanism plausibility checks are explicit. |
| future-facing limitations guidance | `eval_hygiene` / `ai_reviewer` | `adopt_contract` | Limitations should guide what future analysis/data/design would resolve the weakness and how current manuscript language must be restrained. |
| Weixin connector timeout hardening | none | `watch_only` | Real upstream connector bugfix, but not a current MAS-facing runtime contract. |
| deterministic install and runtime Python env invalidation | none | `watch_only` | Useful operator lesson, but not part of current MAS study/runtime owner surface. |
| BenchStore/AISB catalog, tutorial, UI/TUI, Nature companion skills, badge-only PR | none | `reject_for_mas_mainline` | Product breadth, UI, benchmark catalog and marketing assets do not become MAS study truth, quality authority or controller decision surfaces. |

## Owner Boundaries

The absorbed lessons do not change MAS authority:

- `portfolio_memory` is cross-study recall and handoff support, not study truth, controller decision authority, publication quality authority or submission readiness.
- route stop-loss remains route-control guidance. It cannot authorize publication quality and cannot replace `publication_eval/latest.json`.
- future-facing limitations are AI reviewer critique requirements. They do not let mechanical projection approve manuscript quality.
- MDS remains a controlled backend / behavior oracle / upstream intake buffer, not a MAS product owner.

## Verification

Focused lane verification before absorb:

- `uv run pytest -q tests/test_portfolio_memory.py` -> `3 passed`
- `uv run pytest -q tests/test_route_control_stoploss.py` -> `8 passed`
- `uv run pytest -q tests/test_publication_critique_policy.py` -> `7 passed`
- `git diff --check` -> clean in each implementation worktree

The final closeout row in [Plan Completion Ledger](./plan_completion_ledger.md) records root verification, push and worktree cleanup.
