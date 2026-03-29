# DeepScientist Adapter

这里负责定义 `MedAutoScience` 如何与 DeepScientist 对接。

第一版约束：

- 不修改 DeepScientist core
- 通过 workspace profile 和外层 controller 接入
- 允许未来替换执行引擎，而不破坏用户入口

这意味着，`MedAutoScience` 当前不是去接管 `DeepScientist` 的 runtime 内核，而是接管它的外层行为表面。

具体来说：

- quest 的调度、运行图推进、stage 切换，仍然由 `DeepScientist runtime` 负责
- `scout / idea / decision / write / finalize` 这些 stage 实际读取的 `SKILL.md`，由 `MedAutoScience` 通过 overlay 安装和重覆写
- controller、policy、profile 则负责把医学规则、Agent-first 约束、发表门槛和交付 contract 前移到这些 stage 的执行面

所以，修订 `scout / idea / finalize` 这类 stage，并不是“绕开 DeepScientist 另起一套”，而正是当前这套集成方式里最稳定、最升级友好的控制点：

- runtime 继续用 `DeepScientist`
- stage 行为改由 `MedAutoScience` overlay 注入
- DeepScientist 升级时，尽量不碰 core，只重覆写我们自己的 stage overlay
