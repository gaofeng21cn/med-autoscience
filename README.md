# MedAutoScience

`MedAutoScience` 是一个面向医学用户的自动科研 overlay 平台。

它的职责不是替代 DeepScientist，而是把医学研究真正关心的用户入口放到最外层：

- 研究 workspace 的接入
- publication gate / manuscript gate / runtime watch
- study / portfolio / startup brief 模板
- 与 DeepScientist、ToolUniverse、公开数据 sidecar 的对接

当前仓库是第一版骨架，目标是把已有的医学自动科研治理能力，从某个具体课题目录中抽离成一个独立、可迁移、可开源演化的项目。

## 当前定位

- `DeepScientist`：自动科研执行引擎
- `Codex`：总协调与外层治理执行者
- `MedAutoScience`：医学用户直接面对的主入口

## 当前已提供

- 独立 Python package
- `medautosci doctor`
- `medautosci show-profile`
- workspace profile 机制
- 当前 NF-PitNET workspace 的示例 profile
- 首批 policy / template / adapter / controller 文档骨架

## 快速开始

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src python3 -m med_autoscience.cli doctor --profile profiles/nfpitnet.local.toml
```

## 目录

```text
src/med_autoscience/      Python package and CLI
profiles/                 Workspace profiles
policies/                 Publication and governance policies
templates/                Startup and study templates
controllers/              Controller migration notes
adapters/                 Runtime adapters
bootstrap/                Bootstrap and deployment notes
tests/                    Repo-level tests
```

## 当前接入实例

当前示例 profile 指向：

- `/Users/gaofeng/workspace/Yang/无功能垂体瘤`

后续不同疾病 / 数据项目只需要新增新的 profile 文件，不需要复制整个 repo。

