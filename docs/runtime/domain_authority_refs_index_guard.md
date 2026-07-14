# Domain Authority Refs / StateIndex Boundary

Owner: `MedAutoScience`
Purpose: `state_index_no_resurrection_guard`
State: `active_support`
Machine boundary: 通用 index、storage、lifecycle、restore 与 read model 归 OPL。MAS 机器真相归 declarative pack、canonical artifacts 与 registry-bound authority result。

## 当前结论

MAS-local StateIndex、SQLite lifecycle、body-free adapter、inspection/replay helper 与 index projection builder 已全部退役。MAS active source 不保留 generic index implementation；OPL 从 generated/hosted boundary 消费 MAS 声明和 authority refs。

允许进入 OPL StateIndex / Ledger 的只是 locator 与 body-free refs，例如：

- StageRun、Attempt、artifact、source、rubric 与 package closure refs；
- MAS owner receipt、typed blocker、human gate、route-back 与 quality-debt refs；
- archive、checksum、migration 与 restore provenance refs。

它们不能让 OPL 写医学 truth、artifact body、memory body、publication verdict或 owner receipt，也不能让 MAS 获得 queue、attempt、session、retry、storage 或 lifecycle authority。

## 当前入口

- `contracts/memory_descriptor.json`
- `contracts/state_index_kernel_adoption.json`
- `contracts/generated_surface_handoff.json`
- `contracts/functional_privatization_audit.json`
- [私有控制面退役记录](../history/standard-agent-private-control-plane-retirement.md)

旧 database 文件、pilot receipt 或 adapter 名只允许在 Git/history/archive provenance 中出现。发现 active import、callable、CLI alias、contract binding 或 generated default caller 时，视为 no-resurrection regression，直接删除并回到 OPL owner surface；不得恢复兼容 wrapper。

## 验证

`tests/test_standard_agent_boundary.py`、repo hygiene、source closure、default-callers 与 residue-decisions 共同证明 repo-source boundary。它们不证明 OPL live StateIndex、paper progress、publication ready 或 production ready。
