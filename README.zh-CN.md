<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="Med Auto Science Logo" width="132" />
</p>

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh-CN.md"><strong>中文</strong></a>
</p>

<h1 align="center">Med Auto Science 医学自动科研平台</h1>

<p align="center"><strong>Research Foundry 的首个成熟医学实现</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>面向谁</strong><br/>
      从专病数据出发、希望把研究稳定推进到论文交付的医学团队与研究者
    </td>
    <td width="33%" valign="top">
      <strong>对外角色</strong><br/>
      共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` gateway 与 `Domain Harness OS`
    </td>
    <td width="33%" valign="top">
      <strong>在联邦中的位置</strong><br/>
      <code>One Person Lab -> Research Foundry -> Med Auto Science</code>
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="Med Auto Science 主示意图" width="100%" />
</p>

> 对外，`Med Auto Science` 是 `Research Foundry` 主线中的医学 `Research Ops` gateway；对内，它是共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` `Domain Harness OS`。

## 对外一句话理解

如果你的目标是把专病数据持续推进成可投稿的正式研究，`Med Auto Science` 提供的是一条可治理、可审计、可持续推进的医学研究主线。

## 它处在什么位置

`Med Auto Science` 位于 `Research Foundry` 主线内部，承担 active medical `Research Ops` surface，而顶层 `OPL` 继续负责 gateway 与 federation 层。

它当前承担的是：

- `Research Foundry` 主线上的首个成熟医学实现
- `Research Ops` 在医学场景下的 active carrier
- 负责医学 `Research Ops` 的领域合同与交付要求
- 负责组织医学课题、证据包与投稿交付的 domain gateway
- 共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` `Domain Harness OS`
- 位于 repo-side 外层 runtime seam 与受控 `MedDeepScientist` research backend 之上的 harness 化运行面

公开链路可以概括为：

`User / Agent -> OPL Gateway（可选顶层）-> Unified Harness Engineering Substrate -> Research Foundry -> Med Auto Science -> repo-side 外层 runtime seam -> 受控 MedDeepScientist research backend`

## 它能帮你做什么

- 把专病级 workspace、数据资产、study 组合和交付物组织在同一个可审计表面上。
- 把课题从数据清洗、资产登记推进到分析、验证、证据组织和稿件交付。
- 让研究逻辑贴近临床读者与期刊写作要求，并保持清晰的医学叙事结构。
- 对论文图表、表格和 submission surface 施加更严格的结构化约束。

## 它为什么存在

很多自动科研系统更擅长“把流程跑完”，但不擅长控制论文质量。

`Med Auto Science` 的优先级不同：

- 先识别值得继续投入的方向，再分配执行预算
- 先围绕临床意义、报告逻辑和证据链组织研究
- 先把关键状态落到可审计表面，形成可追踪的研究记录
- 让 Agent 负责执行，把关键继续/停止判断保留给人类

## 当前默认运行形态

旧 `Codex-default host-agent runtime` 现在只保留为迁移期对照面与 regression oracle，不再是长期产品方向。
formal-entry matrix 继续固定为：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`。
这套矩阵描述的是 Agent 如何进入 runtime，而公开产品继续保持 agent-operated、domain-governed 的医学研究主线。
当前 repo-tracked 产品主线仍按 `Auto-only` 理解；未来如果要做 `Human-in-the-loop` 产品，应作为兼容 sibling 或 upper-layer product 复用同一 substrate。
当前长线目标的 runtime topology 是：

- `Med Auto Science` 继续是唯一研究入口、research gateway 与 study/workspace authority owner
- 上游 `Hermes-Agent` 成为外层 runtime substrate owner
- `MedDeepScientist` 作为 controlled research backend 保留

当前 repo-side seam 已经冻结到单一 `runtime backend interface` contract 后面。需要明确的是：本仓**还没有**真正完成上游 `Hermes-Agent` 集成。现在落下来的，是 future outer-runtime boundary、outer-loop contract、watch / supervision / durable surface 的 repo-side 收口；真实长时执行仍然通过受控 `MedDeepScientist` backend 完成。

## 入口分层与产品边界

当前稳定、可验证的入口仍然是 `operator entry` 和 `agent entry`，也就是说：

- `operator entry`：给人类操作同事使用的 workspace 准备、调试、检查和人工治理入口
- `agent entry`：由 `Codex` 或其他 host-agent 调用的 `CLI + MCP`
- `product entry`：真正成熟的 direct user-facing 入口还没有落地

现在仓内已经补上一层 repo-tracked 的轻量 `product-entry shell`，但它仍然是克制收口的：

- `workspace-cockpit`：先看 workspace readiness、最新任务摘要、supervisor service 在线态、stale progress 告警和 study supervision
- `submit-study-task`：把任务意图写成 durable study task intake，并同步进 startup brief surface
- `launch-study`：启动/续跑 study，并立刻返回监控入口、当前任务摘要和进度信号

这个仓的目标 domain 级入口形态应是：

`User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`

而在更大的 `OPL` 家族入口里，应兼容：

`User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`

这条 handoff 至少共享下面这组最小 envelope：

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `runtime_session_contract`
- `return_surface_contract`

在这层共享 envelope 之上，`Med Auto Science` 再补充研究域 payload，例如 `study_id`、`journal_target`、`evidence_boundary`。

这里冻结的仍然只是目标架构，不是说产品入口已经完成落地。
因为 external runtime gate 还没有清除，所以当前对用户最诚实的路径仍然是 agent-operated，而不是成熟的独立产品前台。
新补上的这层 shell 解决的是“怎么启动、怎么下任务、怎么持续看进度”的实用缺口，但不把它写成已经完成的独立产品前台。

### 当前 `Hermes` 到底指什么

- 在当前仓内，`Hermes` 首先指 repo-side outer runtime seam 与当前主线的集成边界，不等于上游 `Hermes-Agent` runtime 已经落地。
- 现在本仓可以诚实地写出 `runtime_backend_id = hermes`，因为 `med_autoscience.runtime_transport.hermes` 已不再只是 alias：它已经成为 repo-side real adapter，会先把每个 managed runtime root 绑定到显式的 external `Hermes-Agent` runtime 证据，先对 `inspect_hermes_runtime_contract(...)` fail-closed，再通过 backend contract 把 quest control 委托给受控 `MedDeepScientist` transport。
- 这并不是空名字：外环已经可以用 `runtime_watch` 发现掉线，用 `ensure_study_runtime` 请求恢复，把连续失败写进 `runtime_supervision/latest.json`，再由 `study_progress` 输出医生/PI 能读的人话进度。
- `2026-04-12` 已在真实 study `002-dm-china-us-mortality-attribution` 上拿到一条完整 proof：`ensure-study-runtime` 把等待中的 quest 拉回 live managed runtime，`watch --apply --ensure-study-runtimes` 与短周期 `watch --loop` 连续刷新了 `runtime_watch/latest.json` 和 `runtime_supervision/latest.json`，`study-progress` 也已恢复为带监控入口的人话进度。
- 但这仍不等于“已经完成上游 Hermes 完整接管”：研究执行目前仍由受控 `MedDeepScientist` backend 承担，独立上游 `Hermes-Agent` host 对 backend engine 的完整替代、完整 upstream ownership，以及其他宿主机/其他 study 的 external gate 仍需继续诚实验证。

## 当前仓库侧状态

当前优先级已经冻结，并且前两条 tranche 已完成：

这意味着：

- `P0 runtime native truth` 已在 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a` 完成
- `P1 workspace canonical literature / knowledge truth` 已在 `Med Auto Science` 完成
- `P2 controlled cutover -> physical monorepo migration` 仍是当前 active tranche，但当前落地的是 repo-side real adapter 与 contract cleanup，不是上游 `Hermes-Agent` 已完成接管证明

现在仓库里已经同时承载 native-runtime transport contract、workspace canonical literature / reference-context contract、repo-side outer-runtime seam，以及 `MedDeepScientist` 解构地图。external runtime gate 仍然存在，它也继续阻止我们把当前状态写成“上游 `Hermes-Agent` 已经落地”。

## 运行句柄与持久表面

- `study_id`：医学 study 的持久聚合根身份。
- `quest_id`：绑定到该 study 的受控 research backend quest 正式运行句柄。
- `active_run_id`：当前 quest 内 live daemon run 的细粒度执行句柄；它不能取代 `study_id` 或 `quest_id`。
- `program_id`：当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针。
- 当前 canonical durable status / audit / decision surface：`study_runtime_status`、`runtime_watch`、`artifacts/publication_eval/latest.json`、`artifacts/reports/escalation/runtime_escalation_record.json`、`artifacts/controller_decisions/latest.json`、`artifacts/runtime/last_launch_report.json`。
- `runtime_binding.yaml` 现在会同时记录 outer-substrate metadata（`runtime_backend_id`、`runtime_engine_id`）和 controlled research backend metadata（`research_backend_id`、`research_engine_id`）。
- repo-tracked runtime truth 与本地 operator handoff surface 必须分开：前者负责产品/runtime 合同，后者只负责机器本地恢复与 continuation 状态。

## 未来托管形态下的不变项

即使未来迁移到同一底座上的 managed web runtime，下列核心口径保持不变：

- 人类可审计的状态与决策链
- 医学领域合同（数据、课题推进、证据组织、投稿交付）
- 领域层与执行引擎之间的受控边界

## 医学论文展示面是长期稳定的发表交付层

论文展示面现在应被理解为长期稳定的 publication-facing layer，而不是某个短期阶段标签。

这套系统的目标是保住论文图表与表格的下限，但不限制针对具体课题做上限优化。平台约束的不只是配色或外观，而是版式边界、字段组织、导出结构和质量检查。像文字重叠、注释越界、子图难读、复合 panel 失衡这类低级问题，会被当作 contract / QC 问题处理，而不是留到人工临时补救。

现在这条展示主线有三层分工：

- 顶层目标：用 `A-H` 八大类 paper family 定义长期路线
- 工程审计：用 audited audit families 管理 schema、renderer、QC 与 materialization
- 具体库存：用 template catalog 记录当前已经正式注册的模板、壳层与表格

这意味着：

- roadmap 负责回答“平台最终要覆盖哪些常见医学论文证据家族”
- audit guide 负责回答“当前哪些模板已经严格 audited”
- template catalog 负责回答“代码里现在到底注册了哪些模板与 contract”

如果你想继续从维护中的文档入口往下读，优先查看：

- [公开文档索引](docs/README.zh-CN.md)

展示路线图、审计指南和模板目录这类细节文档当前仍按仓库跟踪的操作文档维护；除非被显式提升到双语公开面，否则默认不扩成双语正文。

## 典型交付结果

如果一个课题值得继续推进，平台的目标是帮助你得到：

- 值得继续投入的研究方向，而不是一次性运行记录
- 可追踪、可扩展的数据资产
- 在病种 workspace 内按 study 管理的结果包
- 面向稿件与投稿的证据组织
- 论文、补充材料和 submission package

## 更适合的课题形态

`Med Auto Science` 特别适合下面这些场景：

- 你已经有一个专病队列，或一批稳定的临床数据
- 你希望多个课题复用同一个 workspace 和数据底座
- 论文需要外部验证、亚组分析、校准、临床效用或机制 sidecar
- 最终目标不只是分析结果，而是完整稿件与投稿交付

## 最快开始方式：通过你的 Agent

对大多数医学用户来说，最快的方式是先把目标、数据和约束交给 Agent，再让它调用 `Med Auto Science`。

但针对真实课题继续推进，需要先明确一个边界：`P0` 与 `P1` 已经进入仓库主线，剩余是否能继续 end-to-end 推进，取决于 `P2` 的受控 cutover 验证、parity gate，以及 `docs/program/` 下剩余 external runtime / workspace gates。

通常只需要三步：

1. 选择或创建一个病种级 workspace，把原始数据、变量字典、终点定义、纳排标准和参考文章放进去。
2. 让 Agent 先把这些数据整理成机读、可审计的研究资产。
3. 再让 Agent 用 `Med Auto Science` 作为医学 `Research Ops` gateway 推进课题，并把目标期刊、重点终点、亚组要求和其他发表约束一起带入运行链路。

你可以直接把下面这段话发给 Agent：

> 请先读取我放在这个研究目录中的数据和说明文档。第一步，把数据清洗并登记为机读、可审计的研究资产，明确变量定义、终点定义和可用范围。第二步，使用 Med Auto Science（`https://github.com/gaofeng21cn/med-autoscience`）作为共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` `Domain Harness OS`，通过受控 MedDeepScientist surface 推进课题，形成发表级证据链、图表表格、稿件表面和投稿材料。请把我提供的目标期刊、终点优先级、亚组要求和其他约束一并带入运行 contract。优先判断课题是否值得继续投入；若方向偏弱，请止损、改题或补充合适 sidecar。

### 当前用户怎么启动、怎么看进度

如果你现在就在 agent-operated 路径上继续一个真实 study，最核心的用户循环已经收成一层轻量 product-entry shell：

- 如果你先想知道这个 repo 的理想形态、当前阶段、五阶段完善梯子和剩余缺口，先看：`uv run python -m med_autoscience.cli mainline-status`
- 先看 workspace 全局 cockpit：`uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>`
- cockpit 现在会更像当前 repo-tracked 的用户 inbox：它会直接投影 repo 主线快照、每篇 study 最近一次 durable task intake、MAS watch-runtime service 是否 visibly online、哪些 study 已经 stale / 缺少明确进度信号，以及“启动 / 下任务 / 持续看进度”这一整条命令回路。
- 写入或刷新当前 study 的任务意图：`uv run python -m med_autoscience.cli submit-study-task --profile <profile> --study-id <study_id> --task-intent "<intent>"`
- 正式启动或续跑，并直接拿到监督入口：`uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>`
- 随时看医生/PI 能直接读的人话进度：`uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>`
- `study-progress` 现在还会带上最新 durable task intake 摘要与 progress freshness signal，尽量把“没进度 / 卡住 / 空转”早点暴露出来，而不是变成黑盒。
- 刷新 MAS 外环监管心跳：`uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> --profile <profile> --ensure-study-runtimes --apply`
- 把 MAS supervisor loop 作为用户级服务常驻在线：`ops/medautoscience/bin/install-watch-runtime-service`

更底层的兼容入口仍然保留：

- `ensure-study-runtime`：直接做 controller-driven 的 runtime continuation
- `study-runtime-status`：看完整结构化真相面
- `watch`：做 supervisor tick 与 outer-loop reconciliation

如果 workspace 是旧骨架初始化出来的，先重新跑一次 `init-workspace` 再安装 service。当前 controller 已能在不加 `--force` 的前提下，就地升级 service-critical managed entry scripts。

如果 `study-runtime-status` 返回 `autonomous_runtime_notice.required = true` 或 `execution_owner_guard.supervisor_only = true`，就表示 study 已处于 live managed runtime。此时用户真正会看到的是：

- `browser_url` / `quest_session_api_url` / `active_run_id` 这组监督入口
- `study-progress` 输出的当前阶段、人话摘要、当前任务摘要、progress freshness、当前阻塞、下一步，以及 runtime_watch 已发现的 figure-loop / 质量守卫告警
- `install-watch-runtime-service` 背后持续在线的 supervisor heartbeat，以及前台 agent 自动切到 supervisor-only，而不是继续直接写 runtime-owned surface

## 文档入口

- [文档索引](docs/README.zh-CN.md)
- [轻量产品入口与 OPL Handoff](docs/references/lightweight_product_entry_and_opl_handoff.md)

更细的操作文档继续保留在仓库中，但默认属于内部中文文档；只有被提升到双语公开面时，才会同步补齐英文与中文镜像。

## 技术验证

开发与验证建议使用仓库内 `uv` 环境：

```bash
uv sync --frozen --group dev
make test-full
uv run python -m build --sdist --wheel
```

本地测试分层入口：

- `make test-fast`：默认开发切片，排除 meta-only 与 display-heavy 套件
- `make test-meta`：repo-tracked 文档、workflow、打包与 contract surface 检查
- `make test-display`：display materialization 与 golden regression 套件
- `make test-full`：clean-clone 基线使用的完整验证入口

如果你主要通过 Codex 接入，优先查看：

- [Codex plugin 接入](docs/references/codex_plugin.md)
- [Codex plugin 发布说明](docs/references/codex_plugin_release.md)
