# MAS Console Display Provenance

Status: `retired provenance`
Owner: `MedAutoScience documentation`
Purpose: `retired_console_display_provenance`
State: `history_pointer`
Machine boundary: 本文是人读退役记录。当前机器真相归 OPL `current_control_state` / provider attempt projection、MAS Progress Portal payload、owner receipt、typed blocker 和相关 contracts；本文不定义 active CLI、read model、HTML artifact、terminal owner 或 soak runner。

## Current Boundary

MAS 不再提供私有 runtime console、conversation read model、terminal/log observation shell 或 Portal/Console combined soak。相关物理模块、CLI 和 tests 已退役且不得以 compatibility alias、wrapper、facade 或旧路径恢复。

当前分工：

- MAS Progress Portal 只展示 study progress、route/decision、owner receipt、typed blocker、artifact/source refs 和 OPL handoff。
- Runtime session、worker/run、terminal/log tail、event stream、attempt state、terminal input/resize/detach 和 operator drilldown 归 OPL runtime/workbench layer。
- 旧 MDS WebUI、历史 MAS console clean-room parity、terminal attach MVP 和 soak 记录只作为 provenance 读取。

## Retired Provenance

退役前的 console/display 材料可在 git history 或 `docs/history/runtime/` 的对应记录中查阅。读取这些材料时必须按历史记录解释，不得把其中的 command、artifact path、read-model name 或 focused lane 写回 active docs/contracts/tests。

Forbidden resurrection:

- 不恢复 MAS 私有 console CLI。
- 不恢复 MAS 私有 console/read-model modules。
- 不恢复 Portal/Console combined soak runner。
- 不保留 `live-console` / `runtime_conversation` / `portal_console_soak` compatibility alias。
- 不把 terminal/log runtime drilldown 写成 MAS owner surface。
