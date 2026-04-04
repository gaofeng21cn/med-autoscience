# Workspace Autoscience Rules

这份规则用于描述 `MedAutoScience` 在具体医学 workspace 中的默认运行原则。

它是 workspace 侧摘要，平台级的总操作模型见：

- [platform_operating_model.md](platform_operating_model.md)

## 默认目标

- 以 Q2+ 医学论文为第一目标
- MedDeepScientist 做执行层
- Codex 做总协调和外层治理
- ToolUniverse 只在功能分析 / 知识检索需要时挂接

## 默认约束

- 优先选择高可塑性、可继续优化证据面的研究路线
- 在弱结果方向上尽快止损，而不是默认把流程跑完
- 数据、门控、交付等状态更新优先通过平台 controller 完成
- 人类主要看 summary、report、draft、final delivery，不手工维护底层 registry

当前这份规则是从 NF-PitNET workspace 中抽出的第一版通用摘要，后续会继续规范化。
