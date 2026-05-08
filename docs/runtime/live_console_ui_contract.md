# MAS Live Console UI Contract

Status: `landed read-only display contract`
Owner: `MedAutoScience Runtime OS + Product Projection`
Related contract: `live-console-parity`

## Purpose

MAS Live Console is the MAS-authored replacement for the useful observation class of the old MDS WebUI. It gives operators one local place to inspect workspace, study, run, terminal tail, log tail, runtime health, supervision freshness, event refs, and artifact refs.

The current landed scope is read-only observation. Resident WebSocket terminal attach, terminal input/resize/detach, and UI-issued runtime control are not implemented in this scope; they remain future parity candidates that require explicit safety, owner, idempotency, and audit gates before becoming default MAS behavior. The old MDS WebUI module, bundle, product identity, Git history, and contributor metadata are not imported.

User-view parity gaps for per-paper navigation, executor conversation, and interactive terminal/control are tracked in [MDS WebUI User Parity Gap Review](../references/mds_webui_user_parity_gap_review.md).

## Stable Entry

- Static shell: `ops/mas/live-console/index.html`
- Session read model: `artifacts/runtime/live_console/session_read_model/latest.json`
- CLI snapshot: `medautosci runtime live-console --profile <profile> --snapshot`
- CLI local stream: `medautosci runtime live-console --profile <profile> --serve --bind 127.0.0.1`

The shell is single-file HTML with inline CSS/JS. It must not require a remote CDN, a frontend build chain, the external MDS repo, or old MDS bundle assets.

## Display Contract

The UI displays:

- workspace identity and generated time;
- all discovered studies in the selected profile;
- selected study only when the caller explicitly passes `--study-id` or `--study-root`;
- active run id and worker state when available;
- runtime health and supervision freshness;
- terminal tail and log tail source refs;
- artifact refs and event refs;
- controller action intent links.

When no study is selected, the profile-level read model keeps `selected_study_id=null`; it must not default to `001`.

## Authority Boundary

The UI is read-only. It can show action intent for pause / resume / relaunch / reconcile, but UI 不直接执行 apply.

The real-workspace soak surface is also read-only. `portal-console-soak` may refresh the Progress Portal and Live Console snapshot, then materialize display evidence under `artifacts/runtime/portal_console_soak/latest.json`. It must not turn a page refresh into runtime reconcile, package rebuild, publication gate update, controller decision, or runtime SQLite write.

Forbidden writes:

- `paper/current_package`
- `manuscript/current_package`
- `paper/submission_minimal`
- `manuscript/submission_minimal`
- `publication_eval/latest.json`
- `controller_decisions/latest.json`
- `study_truth`
- `runtime_lifecycle.sqlite`

Any runtime mutation still goes through MAS controller/runtime owner surfaces. Any paper/package/publication readiness change still goes through canonical MAS owner surfaces.

## Real Workspace Soak Contract

`medautosci workspace portal-console-soak --profile <profile>` checks the Live Console purpose-equivalence surface against a real workspace profile. Required observations:

- multiple studies/runs stay distinguishable by `study_id` / `run_id`;
- terminal tail and log tail refs resolve to readable local refs when available;
- source refs do not promote `med-deepscientist`, `.ds/worktrees`, or old MDS launcher paths to current truth;
- generated pages retain MAS product identity;
- forbidden authority writes remain untouched.

Allowed writes are limited to Portal / Console / soak read-model artifacts and static HTML display files. A blocked soak is acceptable evidence; it must report concrete blockers rather than claiming MDS WebUI parity or paper autonomy stability.

## Clean-Room Rule

The implementation may preserve behavior semantics and information architecture, but must not copy old MDS React/WebUI source, CSS, assets, lockfiles, WebSocket server code, commits, contributor metadata, or product identity.
