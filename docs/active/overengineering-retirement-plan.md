# MAS Overengineering Retirement Guard

Owner: `MedAutoScience`
Purpose: `retired_overengineering_no_resurrection_guard`
State: `active_support`
Machine boundary: 本文只保留完成后的工程守门；完成度归 `mas-ideal-state-gap-plan.md`，历史过程归 Git/history。

## 结论

OE-01 至 OE-12 的功能/结构项已经全部关闭。MAS 不再持有 StateIndex、installer、
workbench、Tool Arsenal runtime、CLI/MCP glue、runtime health/lifecycle/storage、
next-action control plane 或相应兼容系统。

## Guard

- 能声明在 pack/action/schema 的能力不得新增 Python wrapper。
- generic runtime/index/lifecycle/environment/provider/package/workbench需求直接路由 OPL。
- 已删除 surface 不新增 compatibility shim、alias、facade、registry、rollup、currentness 或聚合测试。
- 结构质量统一消费 Sentrux 与 `opl quality details`；MAS 不维护第二份 line-budget 或测试 lane manifest。
- repo hygiene 只检查 tracked path 与 retired active surface，不扫描或删除 ignored 本地环境。
- medical-display 通用 catalog 唯一 owner 是 ScholarSkills；MAS 只保留 capability refs、Stage quality policy 与 artifact authority。
- history/provenance 不得重新进入 active import、entrypoint、contract caller 或 generated surface target。

Live Evidence 继续独立为 `partial_deferred`；它不改变上述结构关闭结论。
