# 架构概览

## 分层视图

当前架构按三层理解最清楚：

1. 产品层
   - 面向用户的对象是研究问题、工作区、进度反馈和文件交付。
   - `Med Auto Science` 在这一层负责把研究推进组织成同一条课题线。

2. 操作与集成层
   - `CLI`、`MCP`、`controller` 是操作与自动化接口。
   - `OPL`、`product-entry manifest` 和其他机器可读桥接属于上层整合与自动化消费面。
   - 这一层负责把 MAS 接到更高层入口。

3. 运行时与持久真相层
   - `Med Auto Science` 持有课题与工作区权威语义、进度语义和发表判断。
   - 上游 `Hermes-Agent` 指外部运行时目标与监管责任方。
   - `MedDeepScientist` 继续作为当前受控研究后端，承接仍留在后端的研究执行能力。

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
它们描述的是当前可执行的操作面。
`OPL` 调用、`product-entry manifest`、`handoff envelope` 和其他机器可读载荷继续属于集成接口。

## 当前运行时责任分层

- `Med Auto Science`：研究入口、课题与工作区权威语义、进度语义、发表判断。
- 上游 `Hermes-Agent`：外部运行时底座与监管责任方。
- `MedDeepScientist`：当前受控研究后端。

## 当前自治与质量合同主线

- `study charter` 冻结方向锁定后的自治边界与论文质量合同。
- `evidence_ledger`、`review_ledger`、`publication_eval/latest.json` 负责把证据闭环、审阅闭环和投稿前判断投影成可审计真相。
- `controller_decisions/latest.json`、`study_runtime_status`、`runtime_watch` 负责把运行状态和控制动作沉成可回放记录。

## 当前架构明确保留的边界

- `Med Auto Science` 负责研究工作线。
- `OPL` 负责上层整合。
- 运行时底座、后端执行和产品入口继续分层表达。
- 迁移、解构、切换和历史推进记录继续留在 `docs/program/`、`docs/runtime/`、`docs/references/` 和 `docs/history/`。
