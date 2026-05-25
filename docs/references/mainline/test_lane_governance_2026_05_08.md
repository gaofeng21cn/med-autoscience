# MAS Test Lane Governance 2026-05-08

Owner: `MedAutoScience`
Purpose: `Preserve MAS mainline architecture and quality reference analysis.`
State: `support_reference`
Machine boundary: Human-readable reference only; current architecture and quality truth remains in source, contracts, tests, diagnostics, active gap plan, and verification receipts.

本记录说明 2026-05-08 测试治理的 repo-level 结果。它是维护参考，不是 runtime truth、publication readiness、controller authority 或 active execution gate。

## Fresh Baseline

本轮在治理 worktree 中重新 collect：

- `smoke`: 4 collected tests after narrowing to the manifest-backed minimal entry surface.
- `meta`: 215 collected tests after removing family-owned preflight files from meta and dropping the explicit architecture-owner rerun.
- `family`: 55 collected tests, still owned by the family shared boundary lane.
- `regression`: 2611 collected tests after excluding `materialization_heavy`.
- `submission_heavy or materialization_heavy`: 248 collected tests.

这些数字是 2026-05-08 本地 worktree 快照，不是永久预算。后续判断应重新运行 collect-only。

## Governance Decisions

- `smoke` is a minimal entry contract. It covers the smoke entrypoint itself and line-budget sanity, not broad command-surface or subprocess-heavy tests.
- `meta` owns repo-tracked contracts, workflows, package surfaces, and entry consistency. It no longer owns `test_dev_preflight.py` or `test_dev_preflight_contract.py`; those stay in `family`.
- `control-plane` is a focused owner-surface gate. It intentionally overlaps with regression and is used for high-risk control-plane changes, not as a mutually exclusive full-lane partition.
- `submission` owns both `submission_heavy` and `materialization_heavy`, so artifact/package materialization tests stay out of default regression.
- `contracts/test-lane-manifest.json` is the durable read model for lane intent and allowed overlap policy.

## Cleanup Rule

Historical single-case regressions can be deleted or archived only when the removal cites the replacing surface:

- a lower-level contract test,
- a golden fixture,
- an owner-surface manifest guard,
- or a durable generated schema/catalog check.

Absent that evidence, keep the regression and move it to the correct lane instead of deleting it.
