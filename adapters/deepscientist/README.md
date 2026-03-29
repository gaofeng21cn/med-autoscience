# DeepScientist Adapter

这里负责定义 `MedAutoScience` 如何与 DeepScientist 对接。

第一版约束：

- 不修改 DeepScientist core
- 通过 workspace profile 和外层 controller 接入
- 允许未来替换执行引擎，而不破坏用户入口

