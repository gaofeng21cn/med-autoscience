# MAS Current Development Lines

Owner: `MedAutoScience`
Purpose: `current_development_line_index`
State: `active_support`
Machine boundary: 本文只做当前维护线索引；结构完成度归 `mas-ideal-state-gap-plan.md`，运行与论文事实归 OPL/MAS owner surfaces。

## 当前结论

Repo/source/control-plane 结构已关闭。当前不再有“迁移 MAS 私有 runtime”的开发线；
后续变更只能落入以下三类。

| Line | Owner | 允许范围 |
| --- | --- | --- |
| Declarative domain evolution | MAS | Stage、prompt、knowledge、quality gate、action/schema、医学 policy |
| Shared platform evolution | OPL | generated surfaces、StageRun/Attempt、workspace/source/artifact/memory locator、package/provider/lifecycle/App shell |
| Live owner evidence | MAS + OPL | 真实 paper artifact、independent Review、owner receipt、publication/release readback |

## 维护门

- 新通用能力先检查 OPL Pack / Connect / Runway / Ledger / Workspace / Console 是否已有 owner surface。
- MAS 新程序面只允许一个已登记的医学 authority function；新增候选必须证明无法声明化或上收。
- primary skill 与 plugin carrier 必须字节一致。
- source allowlist、no-resurrection scan、source closure、interfaces/conformance/default-callers/residue 必须保持关闭。
- Live Evidence 缺失只形成后置证据项，不得恢复 MAS-local wrapper、diagnostic runtime 或 persistence。

## 当前 evidence tail

真实 StageRun、provider long-soak、paper semantic delta、independent reviewer receipt、
publication/submission owner verdict 与 release/install readback 仍按各自 authority surface
验收。它们不是 repo 结构 backlog。
