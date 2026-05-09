# MAS Live Console UI Contract

Status: `landed MAS-native display + terminal attach MVP contract`
Owner: `MedAutoScience Runtime OS + Product Projection`
Related contract: `live-console-parity`
Related focused lane: `terminal-attach-gate`

## Purpose

MAS Live Console is the MAS-authored replacement for the useful observation class of the old MDS WebUI. It gives operators one local place to inspect workspace, study, run, terminal tail, log tail, runtime health, supervision freshness, event refs, and artifact refs.

The current landed scope is MAS-native observation plus a gated terminal attach MVP. Observation remains read-only by default. Terminal attach/input/resize/detach is visible only when a MAS terminal attach owner publishes an available owner contract with token, lease, idempotency, audit, and endpoint capability fields. Without that owner, the surface fails closed. The old MDS WebUI module, bundle, product identity, Git history, WebSocket owner, and contributor metadata are not imported.

User-view parity gaps for per-paper navigation, executor conversation, and interactive terminal/control are tracked in [MDS WebUI User Parity Gap Review](../../references/mds-parity/mds_webui_user_parity_gap_review.md).

2026-05-09 fresh assessment: Live Console is the MAS-native observation replacement for the old WebUI observation class. Study-scoped filtering, action receipts, authorized Progress Portal pause/resume/stop apply, and terminal attach owner gating are now repo-tracked contracts. The terminal attach MVP does not recreate the old resident WebSocket owner; it exposes attach/input/resize/detach controls only when a MAS-owned owner contract is present.

2026-05-09 paper progress degradation closeout: Live Console may display the production blocker impact projection for the selected study, including next owner, why not running, same fingerprint or handoff state, will-start-LLM, safe reconcile command, route refs, and source refs. This is an observation surface only. It must not execute reconcile, dispatch a worker, update publication gates, change controller decisions, write runtime SQLite, or mark quality/publication/submission readiness.

## Stable Entry

- Static shell: `ops/mas/live-console/index.html`
- Session read model: `artifacts/runtime/live_console/session_read_model/latest.json`
- CLI snapshot: `medautosci runtime live-console --profile <profile> --snapshot`
- CLI local stream: `medautosci runtime live-console --profile <profile> --serve --bind 127.0.0.1`
- CLI terminal attach gate: `medautosci runtime live-console --profile <profile> --enable-terminal-attach`

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
- controller action intent links;
- terminal attach/input/resize/detach controls when the MAS terminal attach owner is available.

When no study is selected, the profile-level read model keeps `selected_study_id=null`; it must not default to `001`.

主 UI 标签默认中文，英文技术值只保留在 source ref、status code、command 或 payload field value 中。页面顶部必须显示本机时间和 UTC 时间；运行表、时间线、终端输出、日志输出、产物来源、事件来源、控制器动作意图都使用中文标题。

When no live run exists, the read model and UI must render an explicit no-live-run state instead of an empty console. The UI should say 当前没有 live run, show whether each study has `active_run_id=null` / `worker_running=false`, list available blocker/action fields such as `blocking_reasons`, `canonical_runtime_action`, `allowed_controller_actions`, `next_action_summary`, and keep terminal/log `missing` source refs visible as evidence. Empty state copy must not be only `none`, `unknown`, `No stream tail supplied`, or other generic placeholders.

The UI must localize timeline topics and common status values in visible labels. `study.status`, `runtime.health`, `terminal.tail`, `log.tail`, `none`, `unknown`, and raw `source` labels are payload/internal values; the rendered shell should show 论文线状态、运行健康、终端尾部、日志尾部、无 live run、未提供、终端摘要或 worker 日志. Raw codes can remain in JSON payloads, command examples, and source refs for auditability.

When terminal/log files are missing, the console should explain that absence as runtime evidence. A missing terminal tail for a no-live-run study is not a page failure; it is one more proof that the worker/run is not observable from the MAS live-console read model.

## Authority Boundary

The Live Console UI is read-only. It can show action intent for pause / resume / relaunch / reconcile, but Live Console does not execute apply.

Progress Portal has a separate local-loopback action endpoint. It remains disabled by default; when explicitly served with `--enable-actions`, it may call MAS runtime owner surfaces for `pause`, `resume`, and `stop`, write audit receipts, dedupe repeated user clicks by idempotency key, and fail closed on disallowed actions or missing `quest_id/study_id`. It must not reuse the old MDS daemon as an owner. Terminal attach/input/resize/detach is owned by the MAS terminal attach owner contract, not by the generic Portal action endpoint.

The real-workspace soak surface is also read-only. `portal-console-soak` may refresh the Progress Portal and Live Console snapshot, then materialize display evidence under `artifacts/runtime/portal_console_soak/latest.json`. It must not turn a page refresh into runtime reconcile, package rebuild, publication gate update, controller decision, or runtime SQLite write.

Paper progress degradation evidence is also read-only. It may explain whether a blocker affects automatic paper production, whether a same-fingerprint loop or owner handoff exists, and what safe reconcile command would be appropriate. It cannot authorize quality ready, publication ready, submission ready, package rebuild, controller apply, or terminal input.

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

## Terminal Attach Gate

Interactive terminal attach is part of the formal parity gate. The current status is fail-closed by default with a MAS-native MVP path: until a MAS terminal attach owner publishes a complete owner contract, any explicit attach request returns the `mas_terminal_attach_gate` payload with `status=blocked_by_missing_terminal_input_owner` and must not start an attach session. When the owner contract is available, the same surface returns `status=available` and exposes attach/input/resize/detach capability endpoints without using the legacy MDS daemon/WebSocket owner.

The machine-readable contract lives in `contracts/test-lane-manifest.json` at `focused_lanes.terminal-attach-gate`. It fixes the current implementation status as `landed_mas_native_mvp`, the forbidden owner as `legacy_mds_daemon_websocket`, and `read_only_default=true` for the no-owner/default path.

Required gate payload fields:

- `surface_kind=mas_terminal_attach_gate`
- `status=blocked_by_missing_terminal_input_owner` without owner, or `status=available` when the MAS owner contract is present
- `owner_surface_kind=mas_terminal_attach_owner` when available
- `threat_model`
- `required_owner_contract` with `token`, `lease`, `idempotency`, `audit`, `input`, `resize`, and `detach`
- `capabilities=[attach,input,resize,detach]` and `endpoints` when available
- `forbidden_owner=legacy_mds_daemon_websocket`
- `read_only_default=true`

The CLI `--enable-terminal-attach` flag is an explicit parity/API probe. It fails before starting Live Console materialization or any legacy MDS daemon/WebSocket route when the MAS owner contract is missing. With an available MAS owner contract, it returns the attach/input/resize/detach endpoint contract and does not materialize the Live Console read model as a side effect.

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
