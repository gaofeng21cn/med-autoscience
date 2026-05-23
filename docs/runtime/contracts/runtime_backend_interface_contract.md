# Runtime Backend Interface Contract

## 1. 目标

冻结 `MedAutoScience -> OPL generic runtime + MAS domain authority refs` 的单一 contract，使 `MedAutoScience` 只依赖 OPL runtime contract 与 MAS owner receipt / typed blocker / diagnostic refs，而不再把 `med-deepscientist` 或 MAS 私有 runtime core 当作通用运行框架真相。

当前默认 generic runtime owner 是：

- `runtime_owner = one-person-lab`
- `runtime_substrate = opl_provider_backed_stage_runtime`
- `runtime_backend_id = opl_provider_backed_stage_runtime`
- `runtime_engine_id = opl-provider-backed-stage-runtime`
- `runtime_backend_role = opl_provider_default_runtime_with_mas_domain_authority_refs`
- `runtime_backend_is_generic_owner = false`
- `default_runtime_backend_is_opl_provider_owned = true`

MAS 不再声明 delegated runtime adapter identity。历史 payload 里的 `delegated_domain_adapter_id = mas_runtime_core`、`domain_runtime_adapter_id = mas_runtime_core`、`research_backend_id = mas_runtime_core` 只能按 retired provenance / migration input 读取，不能作为当前 runtime owner、diagnostic fallback 或 compatibility alias。

旧 `Codex-default host-agent runtime` 继续作为 executor 配置来源；direct `med_deepscientist` backend lane 只保留为 frozen source archive / historical fixture / explicit archive import reference，不作为 runnable dependency。

默认 MAS operation 的外部 MDS 依赖必须由 machine-readable contract 明确表达：

- `external_mds_required_for_default_operation = false`
- external MDS 只服务 source provenance、historical fixture 和 explicit archive import reference
- profile JSON 顶层不得重新暴露 `med_deepscientist_*` 字段；历史引用面只能位于 `source_provenance`、`historical_fixture_ref` 与 `explicit_archive_import_ref`

## 2. Backend 选择规则

`MedAutoScience` 解析 study execution 时，按下面顺序选择 backend：

1. `execution.runtime_backend_id`
2. `execution.runtime_backend`
3. 对 `auto_entry == on_managed_research_intent` 的历史 managed execution：
   - 若 legacy `execution.engine` 指向 `med_deepscientist` 或为空
   - controller 先把 execution 归一化到 profile 默认 backend；当前默认是 `opl_provider_backed_stage_runtime`
   - controlled research metadata 只解析到 MAS domain authority refs、owner receipt 或 typed blocker；历史 `mas_runtime_core` 字段按 retired provenance 处理
4. 其余场景再使用 `execution.engine` 映射到已注册 backend

fail-closed 规则：

- 如果 `execution.runtime_backend_id` / `execution.runtime_backend` 被显式设置，但仓内没有注册对应 backend，`progress_projection` 必须返回阻断，而不是静默降级成 lightweight
- 如果 execution 里没有显式 backend，且 `execution.engine` 也映射不到任何已注册 backend，才可判定为非 managed runtime execution

## 3. Backend Contract Surface

managed runtime backend 必须显式暴露：

- `BACKEND_ID`
- `ENGINE_ID`

并实现下列 controller-facing 操作：

- `resolve_daemon_url(...)`
- `create_quest(...)`
- `resume_quest(...)`
- `relaunch_stopped_quest(...)`
- `pause_quest(...)`
- `stop_quest(...)`
- `get_quest_session(...)`
- `inspect_quest_live_runtime(...)`
- `inspect_quest_live_execution(...)`
- `update_quest_startup_context(...)`
- `artifact_complete_quest(...)`
- `artifact_interact(...)`

可选但当前主线已使用的扩展 metadata：

- `CONTROLLED_RESEARCH_BACKEND_ID`
- `CONTROLLED_RESEARCH_ENGINE_ID`
- `DOMAIN_AUTHORITY_REFS_CONTRACT_REF`
- `REQUIRED_CLOSEOUT_PACKET_REF`

`MedAutoScience` controller 只能通过这层 contract 调 backend，不得再直接依赖 backend-specific module name 作为控制逻辑判断条件。

## 3.1 MAS implements only domain authority refs / receipt / blocker role

`mas_runtime_core` 已从当前 runtime owner 口径退役。MAS 当前只作为 domain authority refs、owner receipt、typed blocker、artifact/source/quality refs 和 standalone diagnostic explanation provider；generic scheduler、queue、attempt ledger、retry/dead-letter、worker residency、transition runner、persistence/lifecycle engine 和 workbench owner 归 OPL provider-backed stage runtime。

- OPL provider-backed stage runtime 负责 start/query/resume/pause/stop/retry/dead-letter、attempt state、worker liveness 和 typed closeout。
- MAS owner callable 只消费 typed closeout refs，返回 owner receipt、typed blocker、route-back、artifact/source/quality refs 或 no-forbidden-write proof。
- MAS 不写 `.ds/runtime_state.json`、worker lease、runtime session read model 或 runtime recovery intent 作为当前控制面。
- `chat_quest`、`artifact_complete_quest`、`artifact_interact` 这类历史 runtime event / queue / artifact handoff 语义只能通过 OPL stage runtime + MAS authority refs 重建，不保留 MAS runtime fallback。

因此，旧 MDS daemon 的长期价值被拆成两部分：runtime transport/control 归 OPL，MAS 只签收 domain receipt、typed blocker 与 diagnostic refs；MDS 只保留 frozen source archive、historical fixture、explicit archive import / provenance reference 和 read-only backend audit，不再保留 runnable MAS transport。

## 3.2 Registry validation

backend registry 当前必须 fail-closed 校验：

1. `BACKEND_ID` 非空
2. `ENGINE_ID` 非空
3. 上述 controller-facing callable 全部存在
4. callable 参数表与 contract surface 对齐，不允许缺字段、意外新增必填字段，或把 required 参数改成别的名字

这条规则的意义是：

- 不让 backend abstraction 停留在“只有两个 ID 字段”的假抽象
- 在 `Hermes` outer substrate owner 已切入后，继续把 controller callsite 所依赖的最小可执行 contract 冻结出来

## 4. Managed Runtime 判定

managed runtime execution 的正式条件是：

- backend 已通过 contract 成功解析
- `execution.auto_entry == on_managed_research_intent`

因此，下面这些语义不再允许直接绑死到 `engine == med-deepscientist`：

- supervisor tick required
- runtime event required
- autonomous runtime notice required
- execution owner guard required
- pending interaction / session probing required
- outer-loop managed runtime input contract required

## 5. Runtime Binding Durable Surface

`runtime_binding.yaml` 现在必须同时写出：

- `runtime_backend_id`
- `runtime_backend`
- `runtime_engine_id`
- `research_backend_id`
- `research_backend`
- `research_engine_id`
- `runtime_home`
- `runtime_quests_root`

当前保留的兼容字段：

- `engine`
- `runtime_root`
- `historical_fixture_ref.runtime_root`

这意味着 controller / outer-loop 不应再依赖 `med_deepscientist_runtime_root` 这一实现名义字段来推导 authority truth。

## 6. 当前仓库边界

这份 contract 完成的是：

- controller 与 OPL generic runtime / MAS domain authority refs 之间的 backend abstraction freeze
- OPL provider-backed stage runtime 作为默认 generic runtime owner/substrate 的 repo-side contract，MAS 只作为 domain authority refs / owner receipt / typed blocker surface
- `MedDeepScientist` 作为 frozen archive / historical fixture / explicit archive import reference 的显式边界
- default MAS operation 不依赖 external `med-deepscientist` repo / runtime root
- external MDS 只作为显式 backend audit、historical fixture / explicit archive import reference、historical fixture 和 source provenance target
- optional hosted runtime / workspace truth packaging 已由 MAS Progress Portal 承接：`artifacts/runtime/progress_portal/hosted_package.json` 只打包 MAS-owned read-model payload、HTML 入口、source refs、conditions 和 OPL handoff refs，不消费 MDS WebUI 或 external MDS runtime root

这份 contract 还没有完成的是：

- future upstream source intake review；external MDS repo 只能作为 source archive / historical fixture 保留在 default operation 之外
- GitHub default-branch contributor surface 的 post-push 检查；本地 no-history guard 已阻止上游 history / co-author footprint 进入 MAS commits
