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
      <strong>对外角色</strong><br/>
      面向 Agent 与医学团队的 Research Ops Gateway
    </td>
    <td width="33%" valign="top">
      <strong>在 OPL 中的位置</strong><br/>
      `Research Ops` 的 domain gateway；负责把研究从数据推进到论文与投稿交付
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-hero.png" alt="MedAutoScience 主示意图" width="100%" />
</p>

> 对外，它是面向 Agent 与医学团队的 `Research Ops Gateway`；对内，它由一个 `Agent-first, human-auditable` 的医学自动科研 `Harness OS` 驱动。

## 对外一句话理解

如果你希望把专病数据持续推进成正式研究与投稿交付，`MedAutoScience` 提供的不是零散工具，而是一条可治理、可审计、可持续推进的研究主线。

## 在 OPL 联邦中的位置

如果放在 `One Person Lab (OPL)` 顶层语义里，更准确的定位是：

- `MedAutoScience` 是 `Research Ops` 的正式 domain gateway
- 它下面承载的是 research harness，而不是一堆零散脚本
- 它可以通过 `OPL Gateway` 被路由到，也必须保留独立可用的 domain gateway 角色

理想链路是：

`User / Agent -> OPL Gateway（可选顶层）-> MedAutoScience Gateway -> Research Harness OS -> MedDeepScientist`

## Agent 合同分层

<!-- AGENT-CONTRACT-BASELINE:START -->
- 根目录 `AGENTS.md` 仅用于本仓库开发环境中的 Codex/OMX 协作，不单独承载项目真相合同
- 项目真相合同位于 `contracts/project-truth/AGENTS.md`
- OMX project-scope 编排层位于 `.codex/AGENTS.md`，只供 OMX / CODEX_HOME 会话加载
- 可选本机私有覆盖层约定为 `.omx/local/AGENTS.local.md`，保持未跟踪
- 本地工具运行态目录 `.omx/` 与 `.codex/` 必须保持未跟踪，不进入版本库
<!-- AGENT-CONTRACT-BASELINE:END -->

## 这个平台面向什么研究

- 手里已经有，或后续会持续更新某个专病的一批数据，希望把它们组织成长期可用的研究资产
- 不想只得到零散分析脚本，而是希望把选题、数据、分析、扩展验证和稿件组织成一条可持续推进的研究链
- 希望在同一个病种 workspace 内，围绕共享数据底座并行推进多个课题，持续产出多篇论文
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
| 病种级组织 | 以一个 workspace 管理同一病种的私有/公开数据、多个 studies 与持续累积的研究组合 |
| 研究推进 | 研究入口、策略门控、运行监控，以及把课题持续推进到交付收口 |
| 数据资产 | 私有数据版本登记、公开数据扩展登记、数据影响评估与可审计更新 |
| 证据组织 | 把分析结果、扩展验证、功能解释、论文图表模板与医学写作前验要求收束到同一研究链 |
| 投稿交付 | 最小投稿包导出、正式交付同步，以及面向稿件的最终收口流程 |
| 审计与协作 | Agent 通过稳定接口推进任务，人类可对关键状态和结果进行复核 |

## 医学论文展示面已经进入正式模板化阶段

`MedAutoScience` 正在把医学论文中高频、强约束、直接影响投稿质量的图表与表格，沉淀为正式模板能力。平台约束的不只是出图风格，更包括临床论文常用的展示结构、字段组织、版式边界与质量检查，以减少文字遮挡、元素重叠、布局失衡和展示逻辑不一致等常见问题。

目前已经建立面向临床医学 AI 论文的 8 大类模板体系，覆盖：

- 预测性能
- 临床效用
- 生存与时间结局
- 数据结构与降维分布
- 矩阵模式与热图
- 效应量与亚组比较
- 模型解释
- 泛化与外部验证

这一体系面向医学论文中高频使用的 40 种图表类型持续扩展，目标是直接支持发表级高质量论文配图与表格输出。当前已经纳入正式模板体系的，包括 20 个证据图模板，以及临床入组流程图、基线特征表、主要结果表、补充结果表等高频展示壳层。

在实际投稿中，展示质量主要取决于模板约束、字段组织、导出边界与质量检查是否一致，而不是临时增加多少绘图脚本。基于这一原则，`MedAutoScience` 对常见展示内容采用统一模板体系，并沿同一套可审计机制持续扩展。

如果你想了解当前已经支持的具体模板、适用场景和扩展方向，可以继续查看：

- [医学展示面审计指南](docs/medical_display_audit_guide.md)
- [医学展示面模板目录](docs/medical_display_template_catalog.md)

## 典型交付结果

如果一个课题值得继续推进，平台更希望帮你得到这些结果：

- 值得继续投入的研究方向，而不是只是“跑过一遍”的流程记录
- 可追踪的数据资产和公开数据扩展线索
- 在同一病种 workspace 内按 `study` 拆分的多条研究线
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

## 最快速度使用本项目（以对话方式引导你的 Agent）

如果你是医生或医学专家，最快的使用方式不是先学习底层命令，而是先把研究目标、数据和约束条件清楚地交给你自己的 Agent，再让它带着 `MedAutoScience` 推进。

通常只需要三步：

1. 如果你还没有病种级 workspace，先让 Agent 用 `MedAutoScience` 创建一个；如果已经有了，就把原始数据、数据说明文档、变量定义、终点定义、纳排标准、分组规则，以及你已有的参考文章或研究设想放进去。
2. 再对你的 Agent（例如 Codex、Claude Code、OpenClaw 等）明确说明两件事：先把这些数据清洗、整理成适合机读和可审计的研究资产；再使用 [MedAutoScience](https://github.com/gaofeng21cn/med-autoscience) 作为 `Research Ops Gateway / harness` 框架，围绕你的目标展开自动科研。
3. 最后把你的具体要求直接说清楚，例如目标是发表二区以上的 SCI、希望仿照哪篇文章、已有怎样的科研思路、哪些终点或亚组必须重点分析，这些都可以直接告诉 Agent，由它继续传达给 `MedAutoScience` 的运行过程。

你可以直接把下面这段话发给 Agent：

> 请先读取我放在这个研究目录中的数据和数据说明文档。第一步，把这些数据清洗、整理成适合机读、可审计、可继续研究推进的形式，并明确每份数据的含义、变量定义、终点定义和可用范围。第二步，使用 MedAutoScience（`https://github.com/gaofeng21cn/med-autoscience`）作为 `Research Ops Gateway / harness` 框架，目标是围绕这些数据展开自动科研，尽可能形成一篇二区以上 SCI 论文所需的研究路线、分析结果、验证结果、证据组织和投稿交付材料。如果我提供了参考文章、明确的科研思路、目标期刊偏好、纳排标准、重点终点、亚组要求或其他约束，请一并纳入，并把这些要求传递给 MedAutoScience 的运行过程。请优先判断课题是否值得继续投入；如果方向偏弱，请及时止损、改题或补充 sidecar，而不是机械地把一条弱路线做到底。

通过这三步，你自己的 Agent 就可以带着 `MedAutoScience` 进入自主研究推进；你主要负责补充医学判断、审核关键结果，并决定继续还是停止。

## 当前优先支持的研究方向

| 方向 | 当前优先原因 |
| --- | --- |
| 临床风险分层与分类 | 终点相对明确，容易组织临床效用、亚组分析和可解释性证据 |
| 数据驱动亚型重构 | 适合异质性问题，便于形成分层比较、预后差异和治疗反应讨论 |
| 外部验证与模型更新 | 能直接回答泛化性、迁移性、再校准和模型更新问题 |
| 灰区分诊与追加检查分流 | 临床路径价值清楚，更容易形成确诊 / 排除 / 灰区的研究设计 |

机制扩展与公开组学支持、临床窄任务智能体评测仍然支持，但更常作为特定课题的侧翼路线或补充模块进入。更细的内部策略命名和规则，放在技术文档里。

## 平台如何工作

如果你已经确认这类平台适合你的课题，再往下看它的运行方式即可。这个平台的工作逻辑，不是“人来操作一堆工具”，而是“人类定义研究目标，Agent 调用 `Research Ops Gateway` 推进，平台保留可审计状态”。

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

- 医学研究主控与顶层 gateway：`MedAutoScience`
- 底层 research harness 与长期研究执行：`MedDeepScientist`（仓库：`med-deepscientist`，上游来源：`DeepScientist`）
- 算法创新侧翼执行层：`ARIS`
- 协调推进智能体：`Codex`
- 外部知识、工具与专项分析扩展层：`ToolUniverse`

## 默认组织方式：病种级 workspace

如果你需要继续理解平台内部默认怎样组织研究资产和课题，可以把 `MedAutoScience` 看成“病种级 workspace”，而不是“单篇论文目录”。

一个标准 workspace 通常对应一个病种，或一个稳定的专病研究主题，并同时承担三件事：

- 维护共享数据底座：私有数据、公开数据、数据版本与语义合同
- 维护研究组合：围绕同一批数据并行推进多个 `study`
- 维护投稿交付：把每条研究线收敛成稿件、补充材料与正式投稿包

默认层级可以这样理解：

- `workspace`：病种级长期资产层
- `datasets/` 与 `portfolio/data_assets/`：workspace 级数据资产层
- `studies/<study-id>/`：单条研究线，通常对应一篇主稿或一组强关联投稿产物
- `quest`：`MedDeepScientist` 在该 study 下的运行状态
- `paper bundle / submission package`：面向投稿的 study-local 交付物

<details>
<summary><strong>给技术同事 / AI 执行者</strong></summary>

如果你需要接入 workspace、查看运行接口、阅读 controller 行为或理解平台规则，请从这里进入：

如果你要从零新建一个病种 workspace，现在优先使用：

1. Agent 已接入 `medautosci-mcp` 时，优先调用 MCP tool `init_workspace`
2. 如果当前环境还没有接 MCP，再用 CLI `init-workspace`

例如本地开发环境可以直接运行：

```bash
uv run python -m med_autoscience.cli init-workspace \
  --workspace-root /ABS/PATH/TO/NEW-WORKSPACE \
  --workspace-name my-disease
```

如果你是在这个仓库里做开发、测试或发包，统一使用仓库自己的 `uv` 项目环境，不要直接调用系统 Python、Homebrew 默认 `python3` 或裸 `pytest`：

```bash
uv sync --frozen --group dev
uv run pytest
uv run python -m build --sdist --wheel
```

如果你主要通过 Codex 驱动 `MedAutoScience`，现在已经可以直接使用仓库内置的 Codex plugin。
它提供了 plugin、skill、MCP 和一键安装脚本，但不会替代现有的 `medautosci`、controller、profile 或 overlay 接口。

研究真正运行前，仍需单独准备受控 runtime `MedDeepScientist`（仓库名 `med-deepscientist`），并把 profile 里的 `med_deepscientist_repo_root` 指向该 checkout。

- Agent 接入与运行接口：[docs/agent_runtime_interface.md](docs/agent_runtime_interface.md)
- 第三方 Agent 入口模式契约：[docs/agent_entry_modes.md](docs/agent_entry_modes.md)
- Codex plugin 接入：[docs/codex_plugin.md](docs/codex_plugin.md)
- Codex plugin 发布说明：[docs/codex_plugin_release.md](docs/codex_plugin_release.md)
- 新病种 workspace 快速起步：[docs/disease_workspace_quickstart.md](docs/disease_workspace_quickstart.md)
- Workspace 架构与迁移：[docs/workspace_architecture.md](docs/workspace_architecture.md)
- 工作区接入与部署：[bootstrap/README.md](bootstrap/README.md)
- 控制器与内部能力：[controllers/README.md](controllers/README.md)
- 数据资产策略：[docs/policies/data_asset_management.md](docs/policies/data_asset_management.md)
- 默认研究场景：[docs/policies/study_archetypes.md](docs/policies/study_archetypes.md)
- 研究路线偏置：[docs/policies/research_route_bias_policy.md](docs/policies/research_route_bias_policy.md)

如果你要给 `Codex`、`Claude Code`、`OpenClaw` 这类外部 Agent 提供可直接消费的入口资产，可直接使用：

- 公开契约镜像：[`templates/agent_entry_modes.yaml`](templates/agent_entry_modes.yaml)
- `Codex` 入口模板：[`templates/codex/medautoscience-entry.SKILL.md`](templates/codex/medautoscience-entry.SKILL.md)
- `OpenClaw` 入口模板：[`templates/openclaw/medautoscience-entry.prompt.md`](templates/openclaw/medautoscience-entry.prompt.md)

首页优先保留面向公开读者的能力概览与接入导览；更完整的运行接口、部署方式和技术细节，请以以上文档为准。
其中，`docs/` 承载随仓库发布的公开文档，`docs/policies/` 承载稳定规则；`docs/superpowers/` 只保留本地 AI / Superpowers 过程文档，不进入公开仓库。

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
   - 当前 Release 只解决 CLI 安装，不会替你安装 `MedDeepScientist`（仓库名 `med-deepscientist`）、`Codex`、`pandoc` 或创建研究 workspace

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
