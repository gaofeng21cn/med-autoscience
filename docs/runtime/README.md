# Runtime 文档入口

Owner: `MedAutoScience`
Purpose: `runtime_boundary_index`
State: `active_index`
Machine boundary: MAS 只声明 domain Stage、policy、quality 与 authority inputs/results；StageRun、Attempt、Temporal、queue、session、retry、StateIndex、lifecycle、provider transport 与 hosted read model归 OPL。

## 当前结论

MAS 没有 repo-local runtime control plane。当前链路只有：

```text
MAS declarative pack
  -> OPL generated interface / hosted StageRun
  -> decisive Codex Attempt
  -> OPL controller materializes transition
  -> MAS owner consumes domain result
```

`src/med_autoscience/` 只保留 package init、三个 registry-bound authority handler 与 CSL assets。旧 scheduler、runner、queue、session store、lifecycle/SQLite、StateIndex、status/workbench、provider/package transport、NextAction、PaperRecovery 与 private validator只在 Git/history provenance 中读取。

## 当前入口

- [Runtime boundary](./contracts/runtime_boundary.md)：OPL runtime 与 MAS authority 的总边界。
- [Research Integrity Layer](./contracts/research_integrity_layer.md)：OPL Connect receipt、declarative gate 与 independent Review 的输入链。
- [Stage / Route / Handoff](./stage_route_handoff_standard.md)：六 Stage、decisive Attempt 与 controller materialization。
- [External learning closure](./control/external_learning_adoption_closure.md)：外部模式只能进入 refs、Skill、OPL hosted surface 或 owner consumption。
- [Domain Authority Refs / StateIndex boundary](./domain_authority_refs_index_guard.md)：禁止 MAS-local index/lifecycle 复活。
- [Study truth kernel](./projections/study_truth_kernel.md)：body-free projection 与 false-authority 边界。

## 目录职责

| 目录 | 角色 |
| --- | --- |
| `contracts/` | runtime-facing owner split、receipt/input shape 与 false-authority boundary |
| `control/` | 当前 Stage/route/owner consumption 规则；不得承载私有 runner |
| `projections/` | body-free read model；不得授权 domain action或 mutation |
| `designs/` | 尚有当前设计价值的支撑材料；已完成或退役内容进入 history |

## 验收边界

Repo/source/control-plane 结构用 fast/meta、repo hygiene、source closure、interfaces、conformance、default-callers 与 residue-decisions 验证。Live runtime、paper progress、publication、submission 或 production claim必须有 fresh StageRun/Attempt、independent Review receipt、MAS owner result与真实 artifact evidence。

## 历史

旧 runtime implementation、private control plane、MDS daemon、workspace-local service 与迁移记录归 [history/runtime](../history/runtime/)。History 只解释来源，不恢复 active caller或兼容面。
