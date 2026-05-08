# DeepScientist Learning Intake 2026-05-08

这份记录对应维护者触发的“按当前 protocol 学习 upstream DeepScientist 最新更新”的 MAS 侧试跑。
本轮直接面向 upstream `DeepScientist` 做 fresh audit；没有修改外部 `med-deepscientist` fork，也没有刷新 legacy source archive、parity fixture 或 backend diagnostic。

## Fresh Upstream Range

- upstream_source_mirror: `/Users/gaofeng/workspace/med-deepscientist`
- upstream_remote: `upstream` -> `git@github.com:ResearAI/DeepScientist.git`
- audit_command: `git fetch upstream --prune`
- prior_recorded_upstream_head: `bd0b92b` `Polish BenchStore tutorial flow`
- upstream_range: `bd0b92b..a3ba701`
- upstream_head: `a3ba701` `fix(aisb): point catalog downloads to release assets`
- delta_commits:
  - `860401d` `fix(claude): keep prompts out of variadic tools args`
  - `3090f8a` `docs(readme): update WeChat group image`
  - `a3ba701` `fix(aisb): point catalog downloads to release assets`

The local source mirror remains a provenance input only. It is not a MAS runtime owner, diagnostic dependency, WebUI dependency, or default learning landing repo.

## MAS Absorption Lanes

No MAS code, contract, runtime, or template lane was adopted in this round.

| Lesson | MAS owner surface | Decision | Landing |
| --- | --- | --- | --- |
| Claude Code startup probe keeps natural-language prompt outside variadic tool arguments | `runtime` / `agent_entry` watch surface | `watch_only` | No MAS callsite currently uses the same Claude variadic tools probe pattern; keep this as an adapter correctness lesson for future provider-probe work. |
| README WeChat image refresh | none | `reject_for_mas_mainline` | Community image / product-shell asset, no MAS study/runtime/quality/publication owner value. |
| AISB catalog release asset URL publication | none | `reject_for_mas_mainline` | Upstream benchmark catalog packaging and release-asset bookkeeping, not MAS medical research owner truth. |

## Decision Matrix

| Upstream change | Owner surface | Decision | Rationale |
| --- | --- | --- | --- |
| `860401d` moves the Claude hello probe prompt to subprocess input and appends `--tools ""` after model options | `runtime` / `agent_entry` | `watch_only` | This is a real adapter correctness fix, but current MAS has no matching `claude -p ... --tools ""` invocation. MAS also keeps Claude Code under the generalized agent runtime interface instead of maintaining a DeepScientist-style provider setup flow. |
| `3090f8a` updates the README WeChat group image | none | `reject_for_mas_mainline` | Provider/community/marketing surface. It does not affect MAS durable truth, runtime recovery, publication gate, progress projection, or artifact delivery. |
| `a3ba701` changes AISB catalog entries from local placeholder downloads to published release assets | none | `reject_for_mas_mainline` | BenchStore/AISB catalog distribution belongs to upstream benchmark packaging. MAS should not promote external catalog release metadata into study truth or quality authority. |

## Owner Boundaries

This intake does not change MAS authority:

- `controller_charter`, `runtime`, `eval_hygiene`, `workspace_projection`, `Progress Portal`, `MCP`, and `product-entry` retain their existing owner roles.
- No `publication_eval/latest.json`, `controller_decisions/latest.json`, `study_runtime_status`, `runtime_watch`, `study_macro_state/latest.json`, paper package, manuscript package, or runtime SQLite surface was written.
- External `med-deepscientist` remains frozen source archive / historical fixture / explicit legacy diagnostic / provenance reference only.
- Upstream provider, community, benchmark catalog, and release-asset packaging changes remain outside MAS mainline authority.

## Verification

- Fresh upstream audit: `git fetch upstream --prune` in `/Users/gaofeng/workspace/med-deepscientist`.
- Delta review: `git log --reverse --oneline bd0b92b..upstream/main` identified three upstream commits.
- MAS callsite check: `rg "variadic tools args|--tools \"\"|Reply with exactly HELLO|claude -p" src docs scripts tests` found no matching MAS probe callsite.
- Because this round only records docs/history status and rejects/watchlists the upstream delta, verification is documentation review plus `git diff --check`; no pytest is needed for Markdown wording.
