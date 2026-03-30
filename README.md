<p align="center">
  <img src="assets/branding/medautoscience-logo.svg" alt="MedAutoScience Logo" width="132" />
</p>

<h1 align="center">MedAutoScience 医学自动科研平台</h1>

<p align="center"><strong>面向专病数据、研究推进与投稿交付的医学 AI 平台</strong></p>
<p align="center">Clinical Research Progression · Evidence Packaging · Submission Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>面向谁</strong><br/>
      从专病数据起步的医学研究
    </td>
    <td width="33%" valign="top">
      <strong>控制什么</strong><br/>
      研究质量、证据链和最终收口
    </td>
    <td width="33%" valign="top">
      <strong>最终产出</strong><br/>
      研究路线、证据组织与投稿交付材料
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="MedAutoScience 主示意图" width="100%" />
</p>

> 对外，它是医学研究平台；对内，它是一个 `Agent-first, human-auditable` 的自动科研运行层。

## 这个平台面向什么研究

- 围绕某个专病问题起步，希望把相关数据组织成可投稿研究的课题
- 不想只得到零散分析脚本，而是希望把选题、数据、分析、扩展验证和稿件组织成一条可持续推进的研究链
- 希望技术同事和 Agent 参与执行，但最终仍由人类审阅结果并做关键判断

## 它控制的不是流程，而是研究质量

很多自动科研系统更像工程执行器，能把任务链跑通，但未必适合医学论文生产。

`MedAutoScience` 聚焦的是另一件事：

- 先判断某个方向是否值得继续投入，而不是默认把整条线做完
- 先按医学期刊和临床读者的逻辑组织研究，而不是按通用 AI/ML 论文习惯成文
- 先形成完整证据链，包括临床意义、工作量、可解释性、亚组分析、临床效用、外部验证与公开数据扩展
- 先止损与换题，不在明显偏弱、难发表的方向上空转

## 当前已经稳定支持的能力

| 平台控制面 | 当前已经稳定支持 |
| --- | --- |
| 研究推进 | 研究入口、策略门控、运行监控，以及把课题持续推进到交付收口 |
| 数据资产 | 私有数据版本登记、公开数据扩展登记、数据影响评估与可审计更新 |
| 证据组织 | 把分析结果、扩展验证、功能解释和医学写作前验要求收束到同一研究链 |
| 投稿交付 | 最小投稿包导出、正式交付同步，以及面向稿件的最终收口流程 |
| 审计与协作 | Agent 通过稳定接口推进任务，人类可对关键状态和结果进行复核 |

## 典型交付结果

如果一个课题值得继续推进，平台更希望帮你得到这些结果：

- 值得继续投入的研究方向，而不是只是“跑过一遍”的流程记录
- 可追踪的数据资产和公开数据扩展线索
- 相对完整的分析结果、验证结果和证据组织
- 面向投稿的稿件、补充材料和交付收口结果

## 适用数据与课题

<table>
  <tr>
    <td width="50%" valign="top">
      <strong>数据基础</strong><br/>
      以专病数据为起点，支持临床结构化数据、影像、病理及其他多模态数据、组学或功能分析相关数据，以及围绕同一研究问题组织起来的连续证据链
    </td>
    <td width="50%" valign="top">
      <strong>更适合的课题形态</strong><br/>
      已有明确临床问题、需要形成连续证据链、需要外部验证或亚组比较、或需要把分析结果与稿件交付放在同一条运行链上的课题
    </td>
  </tr>
</table>

专病数据可以来自自有队列、公开数据，或两者结合；关键不是来源本身，而是能否围绕同一研究问题组织出可继续推进的证据链。

## 平台如何工作

这个平台的工作逻辑，不是“人来操作一堆工具”，而是“人类定义研究目标，Agent 调用运行层接口推进，平台保留可审计状态”。

通常按下面的顺序推进：

1. 先判断课题是否值得继续投入，以及是否符合医学论文的组织逻辑
2. 再组织私有数据与可用公开数据，明确数据版本、扩展机会和影响范围
3. 再推进分析、扩展验证、功能解释和证据组织
4. 最后收敛为面向投稿的稿件、补充材料和交付结果

在这条链路里：

- 人类负责定义问题、补充研究上下文、审阅结果并做关键继续/停止判断
- Agent 负责调用平台接口推进运行过程，而不是让医学用户手工执行底层命令
- 平台负责把关键状态、数据资产变化和交付结果落盘，确保过程可审计

如果只看高层角色，可以把内部组成理解为：

- 医学研究主控与门控：`MedAutoScience`
- 主运行层与长期研究执行：`DeepScientist`
- 算法创新侧翼执行层：`ARIS`
- 协调推进智能体：`Codex`
- 外部知识、工具与专项分析扩展层：`ToolUniverse`

## 最快速度使用本项目（以对话方式引导你的 Agent）

如果你是医生或医学专家，最快的使用方式不是先学习底层命令，而是先把研究目标、数据和约束条件清楚地交给你自己的 Agent，让它带着 `MedAutoScience` 推进。

通常只需要三步：

1. 先准备一个单独的研究目录，把原始数据、数据说明文档、变量定义、终点定义、纳排标准、分组规则，以及你已有的参考文章或研究设想放进去。
2. 再对你的 Agent（例如 Codex、Claude Code、OpenClaw 等）明确说明两件事：先把这些数据清洗、整理成适合机读和可审计的研究资产；再使用 [MedAutoScience](https://github.com/gaofeng21cn/med-autoscience) 作为自动科研运行框架，围绕你的目标展开自动科研。
3. 最后把你的具体要求直接说清楚，例如目标是发表二区以上的 SCI、希望仿照哪篇文章、已有怎样的科研思路、哪些终点或亚组必须重点分析，这些都可以直接告诉 Agent，由它继续传达给 `MedAutoScience` 的运行过程。

你可以直接把下面这段话发给 Agent：

> 请先读取我放在这个研究目录中的数据和数据说明文档。第一步，把这些数据清洗、整理成适合机读、可审计、可继续研究推进的形式，并明确每份数据的含义、变量定义、终点定义和可用范围。第二步，使用 MedAutoScience（`https://github.com/gaofeng21cn/med-autoscience`）作为自动科研运行框架，目标是围绕这些数据展开自动科研，尽可能形成一篇二区以上 SCI 论文所需的研究路线、分析结果、验证结果、证据组织和投稿交付材料。如果我提供了参考文章、明确的科研思路、目标期刊偏好、纳排标准、重点终点、亚组要求或其他约束，请一并纳入，并把这些要求传递给 MedAutoScience 的运行过程。请优先判断课题是否值得继续投入；如果方向偏弱，请及时止损、改题或补充 sidecar，而不是机械地把一条弱路线做到底。

通过这三步，你自己的 Agent 就可以带着 `MedAutoScience` 进入自主研究推进；你主要负责补充医学判断、审核关键结果，并决定继续还是停止。

## 当前优先支持的研究方向

| 方向 | 当前优先原因 |
| --- | --- |
| 临床风险分层与分类 | 终点相对明确，容易组织临床效用、亚组分析和可解释性证据 |
| 数据驱动亚型重构 | 适合异质性问题，便于形成分层比较、预后差异和治疗反应讨论 |
| 外部验证与模型更新 | 能直接回答泛化性、迁移性、再校准和模型更新问题 |
| 灰区分诊与追加检查分流 | 临床路径价值清楚，更容易形成确诊 / 排除 / 灰区的研究设计 |

机制扩展与公开组学支持、临床窄任务智能体评测仍然支持，但更常作为特定课题的侧翼路线或补充模块进入。更细的内部策略命名和规则，放在技术文档里。

<details>
<summary><strong>给技术同事 / AI 执行者</strong></summary>

如果你需要接入 workspace、查看运行接口、阅读 controller 行为或理解平台规则，请从这里进入：

如果你主要通过 Codex 驱动 `MedAutoScience`，现在已经可以直接使用仓库内置的 Codex plugin。
它提供了 plugin、skill、MCP 和一键安装脚本，但不会替代现有的 `medautosci`、controller、profile 或 overlay 接口。

- Agent 接入与运行接口：[guides/agent_runtime_interface.md](guides/agent_runtime_interface.md)
- 第三方 Agent 入口模式契约：[guides/agent_entry_modes.md](guides/agent_entry_modes.md)
- Codex plugin 接入：[guides/codex_plugin.md](guides/codex_plugin.md)
- Codex plugin 发布说明：[guides/codex_plugin_release.md](guides/codex_plugin_release.md)
- Workspace 架构与迁移：[guides/workspace_architecture.md](guides/workspace_architecture.md)
- 工作区接入与部署：[bootstrap/README.md](bootstrap/README.md)
- 控制器与内部能力：[controllers/README.md](controllers/README.md)
- 数据资产策略：[policies/data_asset_management.md](policies/data_asset_management.md)
- 默认研究场景：[policies/study_archetypes.md](policies/study_archetypes.md)
- 研究路线偏置：[policies/research_route_bias_policy.md](policies/research_route_bias_policy.md)

如果你要给 `Codex`、`Claude Code`、`OpenClaw` 这类外部 Agent 提供可直接消费的入口资产，可直接使用：

- 公开契约镜像：[`templates/agent_entry_modes.yaml`](templates/agent_entry_modes.yaml)
- `Codex` 入口模板：[`templates/codex/medautoscience-entry.SKILL.md`](templates/codex/medautoscience-entry.SKILL.md)
- `OpenClaw` 入口模板：[`templates/openclaw/medautoscience-entry.prompt.md`](templates/openclaw/medautoscience-entry.prompt.md)

首页优先保留面向公开读者的能力概览与接入导览；更完整的运行接口、部署方式和技术细节，请以以上文档为准。
其中，`guides/` 主要承载随仓库发布的稳定技术指南；`docs/` 主要用于内部设计与过程性记录，不作为公开主入口。

### macOS 预发布 CLI 入口

当前的 macOS 首发版本以纯命令行的 `medautosci` Python CLI 形式提供，是预发布状态的运行工具【不是桌面 App】。请通过终端安装并运行它；我们仍在收集反馈并对运行流程做进一步稳定。

1. 安装

   ```bash
   curl -fsSL https://github.com/gaofeng21cn/med-autoscience/releases/download/v0.1.0a4/install-macos.sh | bash
   ```

   - 安装脚本会自动下载或复用 `uv`，再用受管的 Python 3.12 安装当前 Release 对应的 `medautosci`。
   - 默认会把 `medautosci` 和 `uv` 放到 `~/.local/bin`。如果安装后执行 `medautosci --help` 提示 `command not found`，请执行：

   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile
   source ~/.zprofile
   ```

2. 运行前提

   - macOS，架构仅支持 Apple Silicon `arm64` 或 Intel `x86_64`
   - 系统里可用 `bash`、`curl`、`tar`
   - 有稳定的网络，用于下载 `uv`、Python 3.12 runtime 和当前 Release 资产
   - 当前 Release 只解决 CLI 安装，不会替你安装 `DeepScientist`、`Codex`、`pandoc` 或创建研究 workspace

3. 升级与卸载

   ```bash
   curl -fsSL https://github.com/gaofeng21cn/med-autoscience/releases/download/v0.1.0a4/install-macos.sh | bash
   ~/.local/bin/uv tool uninstall med-autoscience
   ```

   - 当前首发版没有独立升级命令；升级到后续版本时，直接执行目标版本 release notes 里的安装命令即可。
   - 如果 `uv` 已经在 `PATH` 中，也可以直接运行 `uv tool uninstall med-autoscience`。

4. 重点提示

   - 当前 CLI 仍在换代，所有命令仅在 Terminal 里执行，暂不提供图形窗口。
   - 该包仅包含运行层代理与 controller 命令，不会自动创建研究 workspace；仍需按照 `profiles` 模板指定已有的临床研究目录。
   - 当前预发布版本号为 `0.1.0a4`，对应 GitHub tag `v0.1.0a4`。
</details>

## 当前边界

当前版本已经能支撑一批医学课题进入可审计、可持续推进的运行流程，但还不是一个把所有研究环节都完全产品化的成熟系统。

目前更适合那些研究问题相对明确、数据基础较清楚、需要稳定推进到论文交付的课题。

对于高度复杂的多中心数据持续更新、更加深入的机制扩展、以及更个性化的投稿适配策略，当前仍需要更多人工判断和技术支持。
