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

- Agent 接入与运行接口：[guides/agent_runtime_interface.md](guides/agent_runtime_interface.md)
- 工作区接入与部署：[bootstrap/README.md](bootstrap/README.md)
- 控制器与内部能力：[controllers/README.md](controllers/README.md)
- 数据资产策略：[policies/data_asset_management.md](policies/data_asset_management.md)
- 默认研究场景：[policies/study_archetypes.md](policies/study_archetypes.md)
- 研究路线偏置：[policies/research_route_bias_policy.md](policies/research_route_bias_policy.md)

首页不再直接展示 CLI 命令、JSON payload 和部署细节；这些内容统一下沉到上述文档，供 Agent 调用和人类审计。
其中，`guides/` 用于放随仓库发布的稳定技术指南；`docs/` 更偏内部设计稿与 agent 工作过程记录，不作为公开主入口。
</details>

## 当前边界

当前版本已经能支撑一批医学课题进入可审计、可持续推进的运行流程，但还不是一个把所有研究环节都完全产品化的成熟系统。

目前更适合那些研究问题相对明确、数据基础较清楚、需要稳定推进到论文交付的课题。

对于高度复杂的多中心数据持续更新、更加深入的机制扩展、以及更个性化的投稿适配策略，当前仍需要更多人工判断和技术支持。
