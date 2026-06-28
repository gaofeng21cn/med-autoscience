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
| `paper_mission_owner_surface_parts/owner_route.py` legacy re-export | `physically_deleted_2026_06_27` | Fresh exact-caller proof found no non-test active import of `med_autoscience.controllers.paper_mission_owner_surface_parts.owner_route`; the only repo reference was a compatibility test for the legacy import path. Current consumers import `med_autoscience.runtime_control.owner_route` directly. | Completed in `codex/mas-ponytail-physical-cleanup-20260627`: deleted the re-export file and removed the compatibility test; kept `test_owner_route_scan_consumer_and_executor_share_contract_import` as replacement parity proof. |
| `stage_outcome/opl-handoff` carrier | `owner_gated_keep` | 旧名字仍作为 OPL StageRun ABI、provider-hosted owner callable carrier、fixture 和 fail-closed legacy dispatch boundary 出现在 source/tests/docs 中；不能按字符串命中删除。 | Prove default paper path stays on `paper_mission/start_or_resume`; prove every active caller either consumes canonical owner-callable / transition request readback or is diagnostic only; keep manual legacy dispatch fail-closed; run focused domain-handler / owner-route tests. |
| domain diagnostic / owner-route / PaperRecovery old path wording | `owner_gated_keep_or_tombstone_only` | 当前只允许 diagnostic / migration / provenance role，但部分 source/tests still protect currentness, readback, and fail-closed behavior. | Prove no active caller for the specific wrapper or alias; prove replacement parity and no-forbidden-write; keep tombstone/provenance ref; run focused paper-mission / study-progress / owner-route tests. |
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

## 2026-06-27 Follow-up Evidence

- User owner authorization was granted in the OPL Ponytail cleanup thread for safe physical cleanup across user-owned repos, bounded by no functional regression.
- Physical delete landed only for `src/med_autoscience/controllers/paper_mission_owner_surface_parts/owner_route.py`, an exact legacy re-export with no source active caller. `rg` found the old import path only in the removed compatibility test.
- Replacement parity remains `med_autoscience.runtime_control.owner_route`; `tests/paper_mission_owner_surface_cases/test_owner_route_contract.py::test_owner_route_scan_consumer_and_executor_share_contract_import` passed.
- Focused owner-route suite passed with the known baseline failure excluded: `scripts/run-pytest-clean.sh tests/paper_mission_owner_surface_cases/test_owner_route_contract.py -q -k 'not materialize_domain_action_requests_preserves_owner_route_in_dispatch'` produced 12 passed / 1 deselected.
- The deselected test was rerun on root `main` before absorption and failed with the same `KeyError: 'owner_route'`, so it is a pre-existing domain-action materializer baseline failure, not caused by the legacy re-export delete.
- `stage_outcome/opl-handoff`, PaperMission carrier, domain diagnostic/PaperRecovery diagnostics, capability refs, MDS provenance, runtime health/workbench/storage tails, owner receipts, typed blockers, human gates, publication eval, controller decisions, current package, runtime DB, and provider attempts were not touched.
