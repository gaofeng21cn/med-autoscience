# OPL Managed Runtime Three-Layer Contract

这份文档冻结当前 `OPL` 系列仓在托管运行时上的理想统一分层。

目标不是立刻把三个仓抽成一个共享代码包，而是先把跨仓不该再漂移的 contract 写死。

## 一句话形状

统一按三层理解：

- `OPL Runtime Manager` / scheduler adapter
  - 长期运行、托管与调度能力 owner；默认消费 domain-owned scheduler projection，Hermes-Agent 只是显式 optional hosted provider
- domain supervision
  - 领域治理、质量门控、进度真相、恢复判断 owner
- quest executor
  - 具体干活、产出 artifact、落研究或交付副作用

对应到当前医学线：

- `MAS supervision scheduler contract`
  - local default scheduler owner；Hermes-Agent 仅在显式 hosted/runtime target 时作为 optional adapter
- `MedAutoScience`
  - medical supervision / publication governance / progress truth owner
- `MedDeepScientist`
  - concrete research executor

## 为什么必须这样切

如果长期运行 owner 和领域治理 owner 不分开，就会反复出现两类错误：

- 上层 supervision 不知道底层 live run 有没有掉线
- 上层又会在 runtime 还没做完时，自己跳过去抢后半段活

三层切开后的好处是：

- runtime manager / scheduler adapter 只负责“长期在线、能拉起、能调度、能恢复 session/run”
- domain supervision 只负责“现在该不该继续、该不该放行、卡在哪、该怎么恢复”
- executor 只负责“按当前路线把活干出来”

## 三层硬边界

### 1. Runtime manager / scheduler adapter 层

允许：

- 持有 gateway / scheduler / cron / hosted run substrate
- 管 session / run / watch / recovery substrate
- 提供长期在线托管能力
- 在显式选择时使用 Hermes-Agent hosted/runtime provider

不允许：

- 直接持有 domain quality gate
- 直接决定论文/grant/deliverable 是否可以放行
- 自己发明 domain completion truth

### 2. Domain Supervision 层

允许：

- 读取 runtime/status/progress/durable artifacts
- 维护 publication/review/progress/gate/recovery truth
- 决定 next step、人工判断门、恢复建议、是否继续自动推进

不允许：

- 自己变成第二个长期在线 host service
- 绕开 runtime manager / scheduler contract 直接抢 runtime-owned downstream execution
- 直接覆盖 executor runtime-owned surface

### 3. Quest Executor 层

允许：

- 按被放行的路线执行具体任务
- 写 quest-local artifact / paper / grant / deliverable worktree
- 输出 progress evidence、runtime events 与产物

不允许：

- 自己宣布 domain 全局 gate 已放行
- 自己决定长期 supervision owner
- 越过 domain supervision 直接把 partial/local truth 冒充全局真相

## 当前 OPL 仓的统一落点

### MedAutoScience

- `MAS supervision scheduler contract`
  - default local scheduler / optional Hermes hosted adapter
- `MedAutoScience`
  - medical supervision / publication governance / workspace cockpit / progress truth
- `MedDeepScientist`
  - research executor

### RedCube AI

- `OPL Runtime Manager`
  - 长期运行与托管能力目标 owner；Hermes-Agent 是显式 optional hosted provider
- `RedCube AI`
  - visual deliverable governance / audit / publication projection / review truth
- concrete executor
  - 当前 routed visual execution chain

### Med Auto Grant

- `OPL Runtime Manager`
  - runtime substrate / orchestration owner；Hermes-Agent 是显式 optional hosted provider
- `Med Auto Grant`
  - author-side grant truth / progress / review / package gate owner
- concrete executor
  - route-selected grant authoring executor

## 共享 contract 优先抽什么

当前最适合先共享的是 contract，不是代码包。

第一批应共享的内容：

- 三层角色命名与 owner truth
- supervision status shape
- default scheduler projection 与 optional hosted runtime owner invariants
- domain supervision 不得越过 runtime 的 fail-closed 规则
- 单一 MAS app skill 下的 product/entry_status/cockpit 内部 command contract 术语

第二批再考虑抽离的内容：

- adapter-aware supervision job manifest shape
- runtime owner / domain owner / executor owner 的 machine-readable envelope
- 通用 attention queue / recovery contract 结构

最后才考虑代码级共享：

- 如果三个仓的 job install/status/remove controller 已经高度同构
- 再抽 `opl-runtime-contracts` 一类共享模块

## 当前不做的事

- 不在这一轮直接做跨仓 monorepo
- 不因为要统一而把三个仓的 domain logic 硬揉成一个 controller
- 不把 domain supervision 再降级成 prompt 约定

## 验收标准

当三个仓都满足下面条件时，才算统一成立：

- 长期在线 owner 由 OPL/runtime-manager 或 domain scheduler contract 声明；Hermes-Agent 只作为显式 optional hosted provider 进入
- domain repo 自己不再默认安装第二个 host-level 常驻 supervision service
- domain repo 的 product/entry_status/cockpit 文案能明确说清三层分工
- runtime blocked / paused / stale / completion request 等问题会先回到 domain supervision，而不是直接让 executor 或用户硬猜
