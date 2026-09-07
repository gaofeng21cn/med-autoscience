# 项目定位

Med Auto Science 是 OPL 家族中的医学研究 domain agent：canonical agent/package id 为 `mas`，machine domain id 为 `medautoscience`，仓库与 Codex Plugin locator 为 `med-autoscience`。

MAS 将研究问题、数据、分析、证据、稿件和独立审阅组织成可持续推进的研究线。MAS 持有医学 study、quality、publication、artifact、memory 与 owner receipt authority；Framework 持有通用执行、生命周期和生成接口，专业能力由 required dependency `mas-scholar-skills` 提供。

实现形式是 declarative medical research pack、OPL generated/hosted surfaces 与 registry-bound authority functions。本文只说明产品定位；组件关系见 [架构](./architecture.md)，使用入口见 [README](../README.zh-CN.md)，当前证据边界见 [状态](./status.md)。
