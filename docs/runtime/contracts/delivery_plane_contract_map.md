# Delivery Plane Contract Map

Owner: `MedAutoScience`
Purpose: `Explain delivery and publication authority without creating a stage controller.`
State: `active_runtime_support`
Machine boundary: Delivery/publication verdict belongs to MAS; semantic stage routing belongs to Codex CLI; runtime transport belongs to OPL.

Delivery artifacts, manuscript packages, display assets、publication evaluation 和 submission materials 都是 Codex 可消费的 stage inputs。缺少 format、manifest、receipt、review 或 quality evidence 时：

- 记录 quality debt 与 repair/route-back context；
- 保留当前 readable artifact；
- 允许 Codex 进入任意 declared stage；
- 关闭 publication-ready、export-ready、submission-ready 与 owner-accepted 声明。

只有 source/data authority、owner identity、权限/凭据、安全、不可逆 mutation、明确 human authority，或完全没有可读取 artifact 时，才允许硬停止。Delivery plane 不生成 next stage、controller action、transition table 或强制 dispatch。
