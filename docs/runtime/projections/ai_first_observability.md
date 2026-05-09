# AI-first Observability

Observability OS 只提供可见性，不成为新的质量或运行 authority。维护者需要看到 drift、trace、route-back、cache freshness、artifact stale 和 runtime recovery；用户只需要看到当前阶段、阻塞原因、下一步和是否需要人工判断。

## Surface Contract

`ai_first_observability_summary` 是只读摘要。它可以被 doctor report 渲染为默认 contract，也可以由 study runtime 传入真实 snapshot 生成当前摘要；两种形态都不得授权质量关闭、不得改写 runtime、不得替代 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json` 或 `controller_decisions/latest.json`。

`build_ai_first_operations_dashboard_summary()` 生成 `ai_first_operations_dashboard_summary`。它是 operations-facing read model，固定 `read_model=ai_first_operations_dashboard_read_model`，并声明 `product_entry_status`、`workspace_cockpit` 与 `study_progress` 消费同一只读摘要。该 surface 只投影已有 progress/runtime/quality/artifact snapshot，不 refresh cache、不 route-back、不 materialize artifact、不修改 runtime。

## Operator Signals

- AI-first drift audit status
- AI reviewer trace completeness
- publication eval freshness
- route-back count
- runtime action and retry budget
- stale artifact count
- current package canonical-source status
- gate cache freshness
- quality toil items

## User Projection

用户面不得暴露 raw terminal log、full prompt、secret、token stream 或底层执行噪声。用户面只呈现 on_track / attention_required，以及可执行下一步。

doctor report 没有 study-specific runtime snapshot 时，用户面显示 informational，并提示继续查看 `study_runtime_status` 或 `runtime_watch`。这只是默认摘要，表示 observability surface 存在且可审计；不代表当前 study 已 ready。

operations dashboard 用户面只显示 `current_stage`、`blockers`、`next_step` 与 `human_review_required`。维护者面可以显示 `ai_reviewer_trace`、`cache_freshness`、`route_back`、`artifact_stale` 与 `quality_toil`，并记录被排除的低层字段名用于审计。
