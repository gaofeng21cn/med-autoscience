# 架构概览

## 分层视图

当前架构按三层理解最清楚：

1. 产品层
   - 面向用户的对象是研究问题、工作区、进度反馈和文件交付。
   - `Med Auto Science` 在这一层以独立 medical research domain agent 身份组织同一条课题线，由单一 MAS app skill 先承接稳定 callable surface。

2. 操作与集成层
   - `CLI`、`MCP`、`controller`，以及 repo-tracked 的 workspace commands / scripts / contracts，是操作与自动化接口，也是对外稳定 capability surface。
   - 单一 MAS app skill 负责把这些稳定接口对外承接起来。
   - `OPL`、`product-entry manifest` 和其他机器可读桥接属于上层整合与自动化消费面，不是第一主语。
   - `OPL Runtime Manager` 是 OPL 侧的薄运行管理/投影层：它接收 MAS 暴露的 task registration、runtime_control projection、status/artifact locator 与 approval/wakeup 边界，再把这些信息挂到外部 `Hermes-Agent` substrate 的 profile、task、resume、doctor 与索引面；高频文件/状态索引可由 OPL Rust native helper 加速，MAS 侧通过 `native_helper_consumption.proof_surface` 和 `contracts/opl-gateway/native-helper-contract.json` 明确其 index-only 边界，但不能写成 MAS 研究真相来源。
   - 这一层负责把 MAS 控制面接到更高层入口；如果使用 integration handoff，它必须保持同一套研究语义与 owner 边界。

3. 运行时与持久真相层
   - `Med Auto Science` 持有课题与工作区权威语义、进度语义和发表判断，是唯一研究入口与 owner。
   - 默认执行继续继承本机 `Codex` 配置；`Hermes-Agent` 只作为可选 hosted runtime target / reference-layer 运行载体。
   - `MedDeepScientist` 只保留为当前受控研究后端、behavior oracle 与 upstream intake buffer，承接仍留在后端的研究执行能力；它不是用户入口，也不是第二 owner。

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

当前操作路径继续由 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口组成。
其中 `study-progress` 是 restore point、autonomy soak、quality closure、artifact pickup 与 human gate 的源头投影；`workspace-cockpit` 负责把同一条 `research_runtime_control_projection` 放进 study item、attention queue 与 operator brief；`product-frontdesk` 只消费 cockpit preview，不另建第二套运行解释。
它们描述的是当前可执行的操作面。
`OPL` 调用、`product-entry manifest`、`handoff envelope` 和其他机器可读载荷继续属于集成接口和参考层。
当 OPL 需要长期托管、跨域唤醒或统一状态面时，`OPL Runtime Manager` 只能消费这些现有 MAS projection，并把结果索引为 family-level runtime status；它不能在 OPL 侧生成新的 study truth、publication judgment 或 evidence ledger。

## 当前运行时责任分层

- `Med Auto Science`：唯一研究入口、课题与工作区权威语义、进度语义、发表判断 owner，同时对外暴露稳定 capability surface。
- `OPL Runtime Manager`：OPL 侧 product-managed adapter/projection layer，负责把 MAS registration/projection 接到外部 runtime substrate、高频索引、doctor/repair/resume 与 native helper catalog；不持有 MAS domain truth。
- `Hermes-Agent`：外部 runtime substrate / hosted carrier，只在可选 hosted runtime target / reference-layer 语境出现，不改写默认 capability contract。
- `MedDeepScientist`：当前受控研究后端、behavior oracle、upstream intake buffer；不承担用户入口或第二 owner 身份。

## 当前自治与质量合同主线

- `study charter` 冻结方向锁定后的自治边界与论文质量合同。
- `evidence_ledger`、`review_ledger`、`publication_eval/latest.json` 负责把证据闭环、审阅闭环和投稿前判断投影成可审计真相。
- `controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 负责把运行状态和控制动作沉成可回放记录。

## 当前架构明确保留的边界

- `Med Auto Science` 负责研究工作线，并保持唯一入口与 owner 身份。
- `OPL` 负责 family-level session/runtime/projection 与 shared modules/contracts/indexes 的上层整合。
- `gateway / harness` 继续保留为内部架构边界语言，不作为对外第一身份。
- `MedDeepScientist` 只保留受控后端 / behavior oracle / upstream intake buffer 角色。
- 运行时底座、后端执行和产品入口继续分层表达。
- 迁移、解构、切换和历史推进记录继续留在 `docs/program/`、`docs/runtime/`、`docs/references/` 和 `docs/history/`。
