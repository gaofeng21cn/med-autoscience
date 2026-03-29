# MedAutoScience

`MedAutoScience` 的目标，是把“基于手头专病数据，稳定、可控地产出可发表医学论文”这件事，做成一个真正面向医学用户的自动科研平台。

它面向的输入，不局限于单一临床表格数据，也包括：

- 临床结构化数据
- 影像或其他多模态数据
- 组学/功能分析相关数据
- 可公开获取的外部数据集

它围绕医学论文生产链，支持如下工作：

- 自动调研与文献梳理
- 研究选题筛选和发表门槛控制
- 统计分析、建模、有监督学习、无监督学习、亚组分析、可解释性分析、临床 utility 分析
- 调用外部工具做功能分析、知识检索和公开数据扩展
- 组织成更接近真实投稿流程的医学论文工作流

## 这个项目要解决什么问题

很多自动科研框架能“把流程跑完”，但不一定适合医学论文生产。

`MedAutoScience` 想解决的是另一类问题：

- 不是为了把工程跑完，而是为了尽快判断一个方向能不能发论文
- 不是默认按 AI/ML 论文套路写，而是按医学期刊和临床读者的逻辑组织工作
- 不是在弱结果上反复消耗 token，而是尽快止损、分支或换题
- 不是只做一个模型，而是围绕“临床意义 + 工作量 + 可发表性”组织整套分析包

## 当前已经实现了什么

当前版本还是第一期骨架，但已经完成了几件关键事情：

- 建立了独立仓库，不再绑在某一个具体疾病项目目录里
- 明确了产品分层：
  - `MedAutoScience` 是医学用户主入口
  - `DeepScientist` 是自动科研执行引擎
  - `Codex` 是总协调与外层治理
- 建立了 workspace profile 机制，可以把这个平台挂接到现有专病研究目录
- 提供了最小 CLI：
  - `medautosci doctor`
  - `medautosci show-profile`
  - `medautosci bootstrap`
  - `medautosci watch`
  - `medautosci export-submission-minimal`
  - `medautosci overlay-status`
  - `medautosci install-medical-overlay`
  - `medautosci reapply-medical-overlay`
- 提供了通用 workspace profile 模板
- 已经迁入第一批真实治理能力：
  - publishability gate
  - medical publication surface
  - submission minimal exporter
  - runtime watch controller
- 已经具备医学写作 overlay 机制：
  - 前移到 `deepscientist-scout`
  - 前移到 `deepscientist-idea`
  - 前移到 `deepscientist-decision`
  - 接管 `deepscientist-write`
  - 接管 `deepscientist-finalize`
  - 检测是否被上游 skill 重同步覆盖
  - 支持一键重覆写
- 已经开始把医学论文写作习惯前移成显式约束：
  - 方法学完整性与复现信息前移到写作 contract
  - 结果部分按研究问题组织，而不是按图表逐张复述
  - 因果/机制解释边界必须单独交代
- 建立了独立的 policy / template / adapter / controller 目录结构，便于后续继续迁移和去耦

## 接下来计划实现什么

后续会优先把已经在真实课题中验证过的能力，逐步迁移进来：

- public-data sidecar：自动寻找并接入合适的公开数据扩展分析
- ToolUniverse adapter：功能分析、机制解释、知识检索外挂
- 更适合医学任务的 study / portfolio / startup brief 模板
- DeepScientist adapter 分层：把 quest 路径、mailbox、journal、control API 从 controller 核心里拆出去
- policy/config 外置化：把术语红线、命名规则、AMA/投稿规则从实现里拆成可配置策略
- 基于通用 LLM 的医学专用智能体研究线路

## 它现在应该怎么理解

可以把它理解成：

- `MedAutoScience`：你真正面对的项目和入口
- `DeepScientist`：底层科研执行引擎
- `Codex`：协调执行、做外层治理和纠偏

也就是说，未来换电脑、换具体课题、甚至换底层执行引擎时，医学用户首先接触的仍然应该是 `MedAutoScience`，而不是某个具体疾病 workspace。

## 部署方式

这一部分主要写给 Codex 或其他 AI 执行者看。目标不是“手工看文档慢慢装”，而是让 AI 读完后能在一台新电脑上把环境搭起来。

最小部署流程：

1. clone 仓库到本机工作目录，例如 `med-autoscience`
2. 确认本机有 `Python >= 3.12`
3. 准备好 `DeepScientist` 与 `Codex` 可用环境
4. 先让 `DeepScientist` 完成一次 skill 同步，确保本机已生成 `~/.codex/skills/deepscientist-write` 等标准 skill 目录
5. 复制 profile 模板，创建一个本地 profile，指向具体医学研究 workspace
6. 在 profile 中声明医学 overlay 开关与目标 skill 集
7. 运行 `doctor` 检查 profile 和路径是否有效
8. 运行 `bootstrap`，统一安装并检查医学 overlay

最小可执行命令：

```bash
git clone <repo-url> med-autoscience
cd med-autoscience
cp profiles/workspace.profile.template.toml profiles/my-study.local.toml
# edit profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli show-profile --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile profiles/my-study.local.toml
PYTHONPATH=src python3 -m med_autoscience.cli overlay-status --profile profiles/my-study.local.toml
```

如果 `doctor` 输出中这些都为 `true`，说明这套平台至少已经能正确看到目标医学 workspace：

- `workspace_exists`
- `runtime_exists`
- `studies_exists`
- `portfolio_exists`
- `deepscientist_runtime_exists`

更技术化的部署说明见 [bootstrap/README.md](bootstrap/README.md)。

说明：

- `profiles/*.local.toml` 属于本地私有配置，不应提交到公开仓库
- 仓库中只保留模板文件，不保留任何真实用户路径或具体课题路径
- `bootstrap` / `install-medical-overlay` 当前要求 `DeepScientist` 已先把标准 skill 同步到本机；`MedAutoScience` 负责在这些标准 skill 之上加医学特化覆盖，而不是替代 `DeepScientist` 本体
- 当前默认前移接管的 stage 是：`scout`、`idea`、`decision`、`write`、`finalize`

## 仓库结构

```text
src/med_autoscience/      Python package and CLI
profiles/                 Workspace profiles
policies/                 Publication and governance policies
templates/                Startup and study templates
controllers/              Controller migration targets
adapters/                 Runtime adapters
src/med_autoscience/overlay/  Medical skill overlay installer
bootstrap/                Deployment notes for AI executors
tests/                    Repo-level tests
```
