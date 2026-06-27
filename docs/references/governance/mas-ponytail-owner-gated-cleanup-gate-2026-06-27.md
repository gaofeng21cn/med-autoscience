# MAS Ponytail Owner-Gated Cleanup Gate 2026-06-27

Owner: `MedAutoScience`
Purpose: `Support owner-gated Ponytail cleanup intake for legacy aliases, route wrappers, capability catalog refs, and stale cleanup docs.`
State: `support_reference`
Machine boundary: Human-readable cleanup gate only. Machine truth remains in contracts, source, tests, CLI/read-model output, runtime artifacts, owner receipts, typed blockers, human gates, publication eval, controller decisions, and study workspaces. This note does not authorize physical deletion by itself.

## 读法

本页记录 2026-06-27 MAS Ponytail cleanup intake 的 owner-gated 结论。它只帮助后续维护者区分“可删候选”和“旧名字但仍有 authority / ABI / provenance 角色的当前面”。

任何后续物理删除、alias 退役、wrapper 收薄或 capability refs 清理，都必须重新读取 fresh git state、核心五件套、相关 contracts/source/tests 和 repo-native 验证输出。旧矩阵、本文或 focused grep 命中都不是删除授权。

## 当前结论

| Surface | Cleanup stance | Why it is gated | Minimum gate before physical delete |
| --- | --- | --- | --- |
| `domain_owner/default-executor-dispatch` carrier | `owner_gated_keep` | 旧名字仍作为 OPL StageRun ABI、provider-hosted owner callable carrier、fixture 和 fail-closed legacy dispatch boundary 出现在 source/tests/docs 中；不能按字符串命中删除。 | Prove default paper path stays on `paper_mission/start_or_resume`; prove every active caller either consumes canonical owner-callable / transition request readback or is diagnostic only; keep manual legacy dispatch fail-closed; run focused domain-handler / owner-route tests. |
| DHD / owner-route / PaperRecovery old path wording | `owner_gated_keep_or_tombstone_only` | 当前只允许 diagnostic / migration / provenance role，但部分 source/tests still protect currentness, readback, and fail-closed behavior. | Prove no active caller for the specific wrapper or alias; prove replacement parity and no-forbidden-write; keep tombstone/provenance ref; run focused paper-mission / study-progress / owner-route tests. |
| MAS capability registry / ScholarSkills refs | `owner_gated_refs_only` | ScholarSkills source of truth lives outside MAS; MAS must not copy a second catalog or delete refs that prove refs-only consumption and owner-gate boundaries. | Prove the target is local duplicate wording only, not source truth or consumer ABI; fresh-read external ScholarSkills contract/skill when changing semantics; run `tests/test_scientific_capability_registry.py` when source/tests are touched. |
| MDS / MedDeepScientist references | `history_provenance_keep` | MDS remains historical fixture, parity oracle, backend audit, upstream intake, and explicit archive-import reference. Broad deletion would erase provenance and parity context. | Delete only a scoped stale active-path claim after proving replacement, provenance location, and no active default dependency; do not delete parity/reference material as cleanup. |
| Cleanup docs and dated closeouts | `shrink_not_authority` | Active docs should not accumulate long proof ledgers, but dated closeouts and tombstones may be the only provenance for why an old surface must not revive. | Move stale execution detail to history or reference; do not turn support notes into active backlog or runtime truth. |

## Required Evidence

Before a future MAS cleanup lane deletes source, tests, contracts, or active docs, require all applicable evidence:

- fresh `git status --short --branch` and worktree ownership check;
- active caller or no-active-caller proof for the exact symbol/path, not a broad legacy-term scan;
- replacement parity or current owner route that covers the behavior;
- no-forbidden-write proof for paper authority, owner receipts, typed blockers, human gates, publication eval, controller decisions, current package, runtime DB and provider attempts;
- tombstone or provenance ref when history still matters;
- focused repo-native tests for the touched owner surface, plus `make test-meta` when machine-readable contracts or test entry semantics change;
- `git diff --check`.

## Non-Claims

This gate does not claim paper progress, runtime readiness, provider running, publication readiness, submission readiness, domain readiness, production readiness, owner receipt creation, typed blocker authority, human gate handling, `publication_eval/latest.json` freshness, `controller_decisions/latest.json` freshness, `current_package` freshness, or physical retirement of any source surface.
