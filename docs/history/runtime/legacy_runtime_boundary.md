# Legacy Runtime Boundary

Owner: `MedAutoScience`
Purpose: `runtime_history_record`
State: `history_provenance`
Machine boundary: 人读 runtime 历史/provenance 记录。当前 runtime truth 继续归 `docs/runtime/`、contracts、source、CLI/API payload、sidecar receipts、runtime/controller durable surfaces 和 owner receipts。

这里记录 `MedAutoScience` 早期 adapter 边界为何被退休，以及当前正式运行时真相源。

当前正式约束：

- `med-deepscientist` 是唯一 authoritative runtime
- production code 只允许依赖 `runtime_protocol` / `runtime_transport`
- 不重新引入第二套 legacy adapter 真相源

这意味着，`MedAutoScience` 不再把 legacy adapter namespace 当成正式控制面。

具体来说：

- quest 的调度、运行图推进、stage 切换，统一由 `MedDeepScientist runtime` 负责
- `scout / idea / decision / write / finalize` 这些 stage 实际读取的 `SKILL.md`，由 `MedAutoScience` 通过 overlay 安装和重覆写
- controller、policy、profile 则负责把医学规则、Agent-first 约束、发表门槛和交付 contract 前移到这些 stage 的执行面

因此，修订 `scout / idea / finalize` 这类 stage，并不是另起一套 runtime，而是在正式协议边界内控制运行行为：

- runtime 继续用 `MedDeepScientist`
- stage 行为改由 `MedAutoScience` overlay 注入
- intake / 升级时，尽量不碰 runtime core，只重覆写我们自己的 stage overlay
