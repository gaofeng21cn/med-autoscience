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
      面向 Agent 的医学 Research Ops gateway 与 domain harness OS
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

> 对外，`Med Auto Science` 是 `Research Foundry` 主线中的医学 `Research Ops` gateway；对内，它由一套 `Agent-first, human-auditable` 的医学自动科研 harness OS 驱动。

## 对外一句话理解

如果你的目标是把专病数据持续推进成可投稿的正式研究，`Med Auto Science` 提供的不是零散脚本，而是一条可治理、可审计、可持续推进的医学研究主线。

## 它处在什么位置

`Med Auto Science` 不是 `Research Foundry` 的全部本体，也不是顶层的 `OPL` gateway。

它当前承担的是：

- `Research Foundry` 主线上的首个成熟医学实现
- `Research Ops` 在医学场景下的 active carrier
- 负责组织医学课题、证据包与投稿交付的 domain gateway
- 位于 `MedDeepScientist` 之上的 harness 化运行面

公开链路可以概括为：

`User / Agent -> OPL Gateway（可选顶层）-> Research Foundry -> Med Auto Science -> Medical Research Harness OS -> MedDeepScientist`

## 它能帮你做什么

- 把专病级 workspace、数据资产、study 组合和交付物组织在同一个可审计表面上。
- 把课题从数据清洗、资产登记推进到分析、验证、证据组织和稿件交付。
- 让研究逻辑更贴近临床读者与期刊写作要求，而不是默认退化成通用 ML 论文结构。
- 对论文图表、表格和 submission surface 施加更严格的结构化约束。

## 它为什么存在

很多自动科研系统更擅长“把流程跑完”，但不擅长控制论文质量。

`Med Auto Science` 的优先级不同：

- 先判断一个方向是否值得继续投入，而不是默认把预算花完
- 先围绕临床意义、报告逻辑和证据链组织研究
- 先把关键状态落到可审计表面，而不是藏在瞬时会话里
- 让 Agent 负责执行，把关键继续/停止判断保留给人类

## 医学论文展示面已经进入正式模板化阶段

论文展示面现在已经进入正式模板化阶段。

这套系统的目标是保住论文图表与表格的下限，但不限制针对具体课题做上限优化。平台约束的不只是配色或外观，而是版式边界、字段组织、导出结构和质量检查。像文字重叠、注释越界、子图难读、复合 panel 失衡这类低级问题，会被当作 contract / QC 问题处理，而不是留到人工临时补救。

当前范围包括：

- 面向医学 AI 论文高频展示的 8 大类模板
- 朝 40 种图表与表格类型持续扩展
- 已经正式纳入 renderer 链路的 20 个 audited evidence template
- 临床入组流程图、基线特征表、主要结果表、补充结果表等正式壳层

代表性大类包括：

- 预测性能
- 临床效用
- 生存与时间结局
- 降维与分布展示
- 热图与矩阵模式
- 效应量与亚组比较
- 模型解释
- 泛化与外部验证

如果你想继续看模板目录和审计规则，可以直接查看：

- [医学展示面审计指南](docs/medical_display_audit_guide.md)
- [医学展示面模板目录](docs/medical_display_template_catalog.md)
- [公开文档索引](docs/README.zh-CN.md)

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

对大多数医学用户来说，最快的使用方式不是先学习底层命令，而是先把研究目标、数据和约束交给自己的 Agent，再让它调用 `Med Auto Science`。

通常只需要三步：

1. 选择或创建一个病种级 workspace，把原始数据、变量字典、终点定义、纳排标准和参考文章放进去。
2. 让 Agent 先把这些数据整理成机读、可审计的研究资产。
3. 再让 Agent 用 `Med Auto Science` 作为医学 `Research Ops` gateway 推进课题，并把目标期刊、重点终点、亚组要求和其他发表约束一起带入运行链路。

你可以直接把下面这段话发给 Agent：

> 请先读取我放在这个研究目录中的数据和数据说明文档。第一步，把这些数据清洗、整理成适合机读、可审计、可继续研究推进的形式，并明确变量定义、终点定义和可用范围。第二步，使用 Med Auto Science（`https://github.com/gaofeng21cn/med-autoscience`）作为 `Research Foundry` 主线中的医学 `Research Ops` gateway / harness 实现，目标是围绕这些数据形成发表级研究路线、证据链、图表与表格、稿件表面和投稿交付材料。如果我提供了参考文章、目标期刊、纳排标准、重点终点、亚组要求或其他约束，请一并带入运行 contract。请优先判断课题是否值得继续投入；如果方向偏弱，请及时止损、改题或补充合适的 sidecar，而不是机械地把弱路线做到底。

## 文档入口

- [文档索引](docs/README.zh-CN.md)
- [病种 workspace 快速起步](docs/disease_workspace_quickstart.md)
- [Agent Runtime Interface](docs/agent_runtime_interface.md)
- [Agent Entry Modes](docs/agent_entry_modes.md)
- [Runtime Boundary](docs/runtime_boundary.md)
- [Workspace Architecture](docs/workspace_architecture.md)
- [Open Harness OS 架构边界](docs/open_harness_os_architecture.md)
- [Research Foundry 定位](docs/research_foundry_positioning.md)
- [Research Foundry 与 Med Auto Science 的 repo 拆分边界](docs/repo_split_between_research_foundry_and_med_autoscience.md)

## 技术验证

开发与验证建议使用仓库内 `uv` 环境：

```bash
uv sync --frozen --group dev
uv run pytest
uv run python -m build --sdist --wheel
```

如果你主要通过 Codex 接入，优先查看：

- [Codex plugin 接入](docs/codex_plugin.md)
- [Codex plugin 发布说明](docs/codex_plugin_release.md)
