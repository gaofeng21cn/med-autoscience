# 架构概览

## 分层视图

当前架构按三层理解最清楚：

1. 产品层
   - 面向用户的对象是研究问题、工作区、进度反馈和文件交付。
   - `Med Auto Science` 在这一层以独立 medical research domain agent 身份组织同一条课题线，由单一 MAS app skill 先承接稳定 callable surface。

2. 操作与集成层
   - `CLI`、`MCP`、`controller`，以及 repo-tracked 的 workspace commands / scripts / contracts，是操作与自动化接口，也是对外稳定 capability surface。
   - 单一 MAS app skill 负责把这些稳定接口对外承接起来。
   - `OPL`、`product-entry manifest` 和其他机器可读桥接属于上层整合与自动化消费面；对外第一主语继续是 MAS domain agent。
   - `OPL` 在当前定位中是完整智能体运行框架：它提供 stage attempt、queue、wakeup、approval/retry/dead-letter、trace/projection 和 shared module/index 能力，可作为 MAS 外部依赖运行；医学研究 owner 留在 MAS。
   - 在 OPL Codex-first、stage-led family framework 中，MAS stage descriptor、handoff、receipt 和 projection 可以被 OPL 发现和托管；stage 内部的研究拆解、分析探索、写作、审核和路线判断由 MAS prompt/skill、AI reviewer、controller truth 和 `Codex CLI` 执行。
   - `OPL Runtime Manager` 是 OPL 侧的薄运行管理/投影层：它接收 MAS 暴露的 task registration、runtime_control projection、status/artifact locator 与 approval/wakeup 边界，再把这些信息挂到 OPL 的 profile、task、resume、doctor 与索引面。Provider-backed family topology 中，OPL Full online runtime 由已配置的 family runtime provider 提供 durable stage attempt、wakeup、signal/query、retry/dead-letter 与 transport；Temporal 是目标生产 provider，Hermes 是迁移期 legacy/optional provider 或 executor/proof lane。MAS 侧通过 `medautosci sidecar export|dispatch` 暴露受控桥接。高频文件/状态索引可由 OPL Rust native helper 加速，MAS 侧通过 `native_helper_consumption.proof_surface` 和 `contracts/opl-framework/native-helper-contract.json` 固定 index-only 边界；研究真相来源继续是 MAS truth surface。
   - 这一层负责把 MAS 控制面接到更高层入口；如果使用 integration handoff，它必须保持同一套研究语义与 owner 边界。

3. 运行时与持久真相层
   - `Med Auto Science` 持有课题与工作区权威语义、进度语义和发表判断，是唯一研究入口与 owner。
   - `MAS Runtime OS` 持有 Runtime Core；`MAS supervision scheduler contract` 持有外层监督调度语义；`Progress Portal` / `Live Console` / `study-progress` / cockpit 只做 Product Projection。
   - `Stage` 是一次大型研究步骤；`Codex CLI` 是 stage 内默认 concrete executor 和最小执行单元，继续继承本机 Codex 配置。OPL Full 的长期在线 substrate 由 OPL family runtime provider 承担。该 provider 负责唤醒、signal/query、delivery/approval transport、retry/dead-letter 与 family queue tick；MAS study truth、publication judgment、quality gate 和 artifact authority 继续由 MAS 持有。
   - `MedDeepScientist` 的当前角色是 frozen source archive、historical fixture、explicit archive import / backend-audit reference 与 provenance reference。

## 当前主链路

当前仓库的能力表达继续遵循 `policy -> controller -> overlay -> adapter` 这条主链路。
这条链路服务两个目标：

- 把研究治理、进度判断和交付语义固定在仓库跟踪真相上。
- 把研究执行、运行时底座和上层整合入口分层表达，避免混成一个黑盒运行时。

## 当前用户关心的对象

从用户角度，当前系统围绕四个对象组织：

- 研究问题
- 工作区语境
- 人话进度
- 文件交付

## 当前操作与自动化接口

当前操作路径继续由 `product-entry-status`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口组成。
其中 `study-progress` 是 restore point、autonomy soak、quality closure、artifact pickup、human gate 与 `study_macro_state -> user_visible_projection` 的源头投影；`workspace-cockpit` 负责把同一条 `research_runtime_control_projection` 和同一套用户可见状态放进 study item、attention queue 与 operator brief；`product-entry-status` 只消费这些 projection，不另建第二套运行解释。
`family_action_catalog` 是这些 callable action 的 MAS-owned metadata 单一声明面；CLI、MCP tool descriptor、single app skill command projection 与 product-entry manifest 中的 action metadata 都从它派生。`OPL` 读取该 catalog 做 OPL stage-runtime discovery/export/parity；MAS action execution、study truth、runtime controller truth、AI reviewer judgement、publication gate 和 artifact authority 留在 MAS。
`family_stage_control_plane` 是 OPL 标准可发现 stage descriptor；`family_stage_control_plane_descriptor` 是 Stage-Led Autonomy 的 MAS-owned 深度 descriptor projection。二者都从 `agent_entry_modes.yaml` 和 `stage_knowledge_plane_contract` 派生 route snapshot、stage packets、memory closeout/router/recall、evidence/review/controller/publication refs 与 `authority_boundary`。`OPL` 可以读取它们做 OPL stage-runtime indexing、display、freshness check 和 MAS-exported task discovery；route、study truth、evidence promotion 和 publication quality / submission readiness 继续由 MAS owner surfaces 授权。
`medautosci sidecar export|dispatch` 是 OPL family runtime provider 到 MAS owner surface 的受控桥接：export 投影 MAS-owned runtime/status/source refs 与 pending family tasks，dispatch 接收 allowlisted task 并回到 MAS controller/runtime owner chain 产出 receipt。`MCP`、action catalog、skill command projection、plugin manifest 与 product-entry manifest 都是 entry/projection surface；study truth、publication quality、quality gate、artifact authority、paper package、`study_runtime_status` 和 `runtime_watch` 由 MAS authority surfaces 持有。
MAS 在 stage-led OPL framework 下的可调用路线保持 direct skill 等价：直接通过 MAS app skill 调用，或通过 OPL stage/queue/handoff 调用，最终都回到同一套 MAS-owned stage entry、controller、ledger、review、route decision 与 artifact surface。OPL 持有 framework-level attempt/receipt/projection metadata；医学 research memory、evidence ledger、review ledger、publication verdict 和 current package authority 留在 MAS。
`MAS Progress Portal` 是这组投影面向用户的 landed 固定可视化入口：默认生成 `ops/mas/progress/index.html` 静态快照，也可由本地只读服务实时刷新。Portal 由 MAS 持有 domain-owned payload / HTML，消费 `study-progress`、`workspace-cockpit` 和 durable truth refs。它统一用户进度查看入口；functional monolith completion 的完成口径是 capability supersede / rewrite / retire。当前 Portal 的用户体验是部分等价：旧 MDS WebUI 以 project/quest 为主工作台，MAS Portal 仍偏 workspace overview + study rows；per-study/per-paper drilldown 是后续 UX parity 的 P0。
它们描述的是当前可执行的操作面。
`OPL` 调用、`product-entry manifest`、`handoff envelope` 和其他机器可读载荷继续属于集成接口和参考层。
当 OPL App 需要统一进度看板、长期托管、跨域唤醒或统一状态面时，`OPL Runtime Manager` 消费 MAS progress portal payload refs、HTML refs 和现有 MAS projection，并把结果索引为 OPL stage-runtime dashboard / runtime status；study truth、publication judgment 和 evidence ledger 继续由 MAS 持有。最佳集成形态见 [Progress Portal OPL App Integration](./references/integration/progress_portal_opl_app_integration.md)。

## 当前运行时责任分层

- `Med Auto Science`：唯一研究入口、课题与工作区权威语义、进度语义、发表判断 owner，同时对外暴露稳定 capability surface。
- `OPL stage-led framework`：完整智能体运行框架，负责 MAS stage descriptor discovery、attempt/queue/approval/retry/dead-letter/trace/projection 支撑，可作为外部依赖运行 MAS stage；医学结论、publication verdict 和 quality verdict 由 MAS 持有。
- `MAS supervision scheduler contract`：MAS standalone/local diagnostics 的外层 supervision cadence、job identity、tick receipt、SLO / drift projection 和 adapter migration owner；默认 adapter 是 MAS-owned `local` scheduler，macOS backend 已落地为 LaunchAgent。OPL Full online runtime 的 family-level wakeup 由 OPL family runtime provider 触发，再通过 `medautosci sidecar dispatch` 进入 MAS owner surface。
- `OPL Runtime Manager`：OPL 侧 product-managed adapter/projection layer，负责把 MAS registration/projection 接到高频索引、doctor/repair/resume 与 native helper catalog；MAS domain truth 留在 MAS。
- `OPL family runtime provider`：OPL Full online family runtime 的外部 durable substrate / hosted carrier / delivery transport；Temporal 是生产目标，Hermes 是迁移期 legacy/optional provider 或 executor/proof lane。MAS 默认 concrete executor、MAS domain truth、MAS quality 和 artifact owner 继续由 MAS 持有。
- `MedDeepScientist`：frozen source archive、historical fixture、explicit archive import / backend-audit reference 与 provenance reference。

## 当前自治与质量合同主线

- `study charter` 冻结方向锁定后的自治边界与论文质量合同。
- `evidence_ledger`、`review_ledger`、`publication_eval/latest.json` 负责把证据闭环、审阅闭环和投稿前判断投影成可审计真相。
- `publication_gate` 与 `medical_reporting_audit` 持有机械完整性、交付状态和 reporting blocker 判断；它们生成的 `publication_eval/latest.json` 是 `mechanical_projection`。科学质量、审稿 readiness 与 submission-facing 闭环判断由 AI reviewer workflow 持有。
- 主观医学论文文体质量由 AI reviewer workflow 持有：`medical_prose_review` 与 AI reviewer-backed `publication_eval/latest.json` 负责判断医学期刊声音、reader flow、论证节奏、claim restraint 和工作汇报残留；regex / pattern 只作为 `mechanical_safety_flags` 或 reviewer evidence snippets，不单独决定 `medical_journal_prose_style_not_met`。
- AI reviewer-backed `publication_eval/latest.json` 必须回指 manuscript、evidence ledger、review ledger 与 study charter，并使用 `medical_publication_critique_v1` policy；缺少该 provenance 时，下游只能输出 `review_required` / `projection_only`。
- 初稿质量属于 pre-draft runtime 关注点：写作前应能看到研究问题、数据资产支撑、reporting guideline、display-to-claim map 和 manuscript-native prose 约束；文档只说明这条可运行质量线，不新增 wording gate。
- 产物证明采用 canonical-source-first：manuscript、figures、tables 与 submission package 必须能从 canonical source 重建，artifact rebuild proof 才能支撑交付判断。
- `controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 负责把运行状态和控制动作沉成可回放记录。

## MAS AI-first Research OS 长线目标

长线目标固定为 `MAS AI-first Research OS`。它是 owner、authority、contract 与验收口径的目标架构，再按可运行能力逐步吸收和替换。

- `MAS Core` 是目标 owner 层：study truth、quality truth、publication truth、artifact truth 与用户可见 truth 都应归 MAS。
- `Quality OS` 的当前落点是 pre-draft quality runtime、evidence ledger、review ledger 与 AI reviewer-backed `publication_eval/latest.json` 的闭环；真实论文 soak 仍需继续积累。
- `Runtime OS` 的当前落点是 operations state、runtime health、retry budget、human gate、controller-owned resume action 与 MAS-owned Runtime Turn Lifecycle Kernel。Kernel 持有 `schedule_turn`、`complete_turn_and_normalize`、`inspect_turn_lifecycle`、user message queue、worker lease、runner monitor、delayed auto-continue timer 和 turn receipt；`runtime_watch`、supervisor scan、scheduler adapter / heartbeat 作为外层 reconcile / wakeup / stale recovery 调用方，runner completion 后的内生 auto-continue 主循环留在 Kernel。
- 因此 MAS/MDS 行为差异现在按两层判断：内层 `turn completion continuation` 已达到旧 MDS 自动科研连续跑的行为等价；外层 resident daemon 特征按 scheduler-bound MAS Runtime OS 处理，300 秒 tick 负责监督刷新、drift detection 和 stale recovery。Terminal/log observation 已由 `live-console-parity` 落为 MAS-owned read-only purpose parity；Progress Portal、Hermes cron 和 MAS Live Console 按 MAS 当前架构表达。WebSocket terminal attach / UI-issued runtime control 是后续 gated parity lane。
- `Artifact OS` 固定 canonical-source-first：manuscript、figures、tables、submission package 都从 canonical source 重建，并通过 artifact rebuild proof 支撑交付判断。
- `Evaluation OS` 的目标是把历史返工转为 AI reviewer calibration corpus、quality regression 与 AI-first drift audit；这些目标项按证据逐步关闭。
- `Observability OS` 面向维护者暴露 drift、trace、route-back、cache freshness、artifact stale 和 runtime recovery，但不成为 authority。
- `MDS Deconstruction` 已关闭到 functional monolith completion 口径；未来 MDS / DeepScientist learning 只能按 source provenance、capability classification、owner boundary 与 parity proof 进入 MAS-owned surface、historical fixture 或显式 diagnostic/provenance 引用。

这套目标架构的人工可读 contract 由 `docs/references/mainline/ai_first_research_os_architecture.md` 与 controller surface `ai_first_research_os_architecture_contract` 表达；外部工程依据固定为 ISO/IEC/IEEE 42010、NIST AI RMF、EQUATOR、FAIR、durable execution、OpenTelemetry、G-Eval 与 SRE toil elimination。它不授权新增文档 wording gate。

## MAS/MDS owner boundary fitness function

MAS/MDS 的模块数量已经足够大，单靠文档描述 owner 容易漂移。因此当前架构增加 `mas_mds_architecture_owner_boundary_report` 作为 architecture owner boundary fitness function。它确认并防护四类重复 authority 风险：entry projection 越权解释下一步、MDS oracle 被读成医学质量 owner、observability 输出直接驱动 control、runtime liveness 被多处局部重算。

该 surface 的规则是：

- `mas_core`、`quality_os`、`runtime_os` 才能持有 study truth、quality truth、runtime health 和 user-visible next action。
- `study_progress`、`workspace-cockpit`、`product-entry-status`、product-entry manifest 与 MCP 做 projection；authority 继续在 MAS owner surface。
- `Observability OS` 只提供 evidence、calibration、analytics 和 replay proof，不直接授权 finalize、submission 或 publication readiness。
- `MDS` 只保留 explicit backend audit、explicit archive import reference、upstream intake、parity oracle 四类角色；`paper_contract_health` 和 coverage 只能是 backend preflight / mechanical oracle。

当前修复计划见 [MAS/MDS Owner Boundary Refactor Plan](./policies/runtime-governance/mas_mds_owner_boundary_contract.md)。该计划采用 strangler-style 逐面吸收和 architecture fitness functions。

后续增强建议先通过 [Program Portfolio Consolidation](./program/program_portfolio_consolidation.md) 归并评估；旧 [MAS/MDS Unified Enhancement Program](./history/program/mas_mds_unified_enhancement_program.md) 作为历史 backlog 参考。真实 workspace soak、PI 动作投影、投稿结果 calibration、provider 运营、journal-family pack、legacy upgrade queue、delivery traffic-light、backfill blocker、audit compaction 和结构治理都服务对应 owner surface；系统状态解释继续回到 `StudyTruthKernel`、`RuntimeHealthKernel`、AI reviewer-backed `publication_eval/latest.json`、`controller_decisions/latest.json` 和 canonical artifact proof。

Runtime lifecycle 小文件治理和 quest Git 退役的执行入口固定为 [Runtime Lifecycle SQLite Migration Program](./program/runtime_lifecycle_sqlite_migration_program.md)。该 program 把 SQLite 定义为 runtime lifecycle authority 和 read-model layer，把 Git 固定为 repo source control，把 latest authority、restore metadata、paper/manuscript/package/dataset 交付物继续固定为文件或归档形态；它属于 Runtime OS / maintainability lane，study truth、publication truth 和 artifact authority 留在对应 MAS owner surface。

当前状态一致性合同已经收敛为一条执行链：`StudyTruthKernel/RuntimeHealthKernel -> study_macro_state -> owner_route -> consumer latest -> executor -> rescan`。`study_macro_state` 给出短枚举用户状态，细节进入 `details`；`owner_route` 持有当前可执行 owner、allowed action 和 idempotency key；consumer 和 executor 传播或执行这张票据。Artifact lifecycle 属 Artifact OS / maintainability，生成 retention plan、terminal lifecycle dry-run、checksum 与 restore-proof gate；study truth 和论文 authority 留在对应 owner surface。

2026-05-08 起，hub role hardening 把中心模块固定为四类角色：authority、read-model、adapter、materializer。authority hub 持有裁决；read-model hub 消费 canonical truth 并投影；adapter hub 做参数验证、owner surface 调用和结果渲染；materializer hub 在既有 owner 授权下做受控写入。`module_boundary_audit` 与 `architecture_owner_boundary` 将 read-model / adapter 写 authority surface、替代 `study_macro_state` / `owner_route` 做 owner 判断、或直接控制 runtime/publication 判为 blocking。fan-in/fan-out 规模本身只是维护风险，后续拆分按 owner 子域推进。

## Boundary Governance 与自然边界

全仓 `_parts` 目录已经成为当前结构治理的主要观察面。它们表达自然职责边界：controller 薄入口、read-model/projection、runtime lifecycle、publication gate、artifact lifecycle、display contract、CLI parser/command、test case family 等。`boundary_fitness` 因此把 hard blocking 与 advisory governance 分开：机械 `part/chunk/split` 编号仍是阻断；nested `_parts`、膨胀的 `shared_base.py`、接近 1000 行的单个 part、`exec(compile(...))` 拼接加载先作为 advisory 报告，服务后续自然边界拆分计划。

这组治理信号保持 public contract：现有 `CLI`、`MCP`、controller callable surface、product-entry payload、manifest/schema、import facade 与测试聚合入口都应保持兼容。后续 lane 若处理 advisory，在对应 owner 边界内把内部实现迁到更清晰的 importable module、case module 或 shared helper family；study truth、publication truth、runtime truth、artifact authority 和用户可见 next action 继续由对应 authority 持有。

live artifacts 不属于本治理面的写集。`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch`、`current_package`、submission package、runtime lifecycle SQLite、restore archives 与真实 workspace 产物都继续由 stable runtime / controller / canonical artifact flow 持有。Boundary governance 只报告 repo-tracked source/test/docs 的维护风险，不触碰或重生成 live study artifact。

2026-05-07 的全仓 `_parts` 收口已经把第一批 advisory 转为自然子域。`study_progress_parts` 拆成 projection inputs、status context、eval surface 和 payload assembly；`product_entry_parts/workspace_surfaces.py` 变成显式 import facade；publication/delivery 侧按 gate state/report、surface scan/reporting、package build/export、delivery staging/sync 与 quality materialization 切分；runtime/control 侧按 runtime tick、managed recovery、supervisor scan action family、gate-clearing context/repair plan 和 outer-loop action execution 切分；runtime model/transport 侧按 publication decision、runtime event relay、status read model、quest session/watchdog/execution 切分；display/MCP 侧按 domain registry、validation、contract family、layout helper、projection adapter 与 tool-result rendering 切分。这些边界是当前允许继续演进的 owner 子域，后续维护继续保持自然子域和 importable module 形态。

2026-05-07 模块化 architecture fitness wave 又完成了 runtime execution、runtime decision/events、product cockpit、progress/MCP render、publication/delivery 和 display validation 的二次收口。`study_runtime_execution.py`、`study_runtime_decision.py`、runtime events facade、product cockpit/workspace surfaces、`study_progress_parts/shared_base.py`、publication delivery sync、publication gate、medical publication surface reporting、display validation 的已确认结构债已按 owner 子域吸收；`boundary_fitness` 当前为 `0 blocking / 0 advisory`。Display validation 本轮经 focused tests 与 boundary fitness 复核后没有再引入新 contract，只作为验证收口记录。

同日 follow-up 又把 `product_entry_parts/shared_base.py` 中仍混在一起的 boundary contract 校验/markdown、CLI command helper、human status view label/narration 继续迁入 `boundary_surfaces.py`、`command_surfaces.py` 与 `human_status_view.py`。`shared_base.py` 保留 product-entry shared assembly 和兼容 re-export 所需的公共 helper；其他 helper 归入对应 owner 子域。

2026-05-08 hub role hardening 继续沿这条边界治理，但目标从“拆自然文件边界”转为“固定 hub 的角色”。Runtime Supervisor 只读取 canonical inputs、消费 RuntimeHealth / owner-route facts、生成 action/lifecycle projection；Product Cockpit 只消费 progress/runtime/publication/artifact/readiness projection 并分离 command assembly、attention、health card 和 markdown brief；MCP server 收口为 declarative tool registry、handler adapter 与 renderer；Display Validation 以 schema-id / display-family registry dispatch validator，只返回 verdict。外部 tool names、payload shape、controller callable surface 与 display registry id 保持不变。

## 2026-05-07 模块化评估

当前 MAS 的模块化状态应判断为“分层方向干净，owner 边界基本成型，但 hub 风险仍需持续治理”。fresh Sentrux 扫描显示 DSM `above_diagonal=0`，boundary fitness `0 blocking / 0 advisory`；这说明当前依赖没有逆流，且 repo 已经可以用结构 gate 防止明显退化。短板也很明确：Sentrux `modularity`、`equality` 仍是相对弱项，`product_entry`、`study_progress`、runtime/control、MCP/display 仍是高 fan-in/fan-out 热点。

因此后续架构治理采用 owner 子域内的 fitness-budget 式维护：新功能消费 `study_macro_state -> user_visible_projection` 和 `owner_route -> consumer latest -> executor dispatch`；触碰 high-churn hub 或 near-limit part 时按自然子域补 focused tests 和 importable module；触碰中心 hub 时保持 hub role guard green。详细评估见 [MAS Modularity Assessment 2026-05-07](./references/mainline/mas_modularity_assessment_2026_05_07.md)。

## 当前架构明确保留的边界

- `Med Auto Science` 负责研究工作线，并保持唯一入口与 owner 身份。
- `OPL` 负责 OPL stage-runtime session/runtime/projection 与 shared modules/contracts/indexes 的上层整合。
- `OPL` 的 stage-led framework 语义取代旧 gateway / federation 定位；对外第一身份是 `Med Auto Science` domain agent。
- `MedDeepScientist` 只保留 frozen source archive / historical fixture / explicit archive import reference / provenance reference 角色。
- 运行时底座、后端执行和产品入口继续分层表达。
- 迁移、解构、切换和历史推进记录继续留在 `docs/program/`、`docs/runtime/`、`docs/references/` 和 `docs/history/`。
