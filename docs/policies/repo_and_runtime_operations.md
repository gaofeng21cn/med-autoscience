# 仓库 CI、主线集成与运行治理

Owner: `MedAutoScience`
Purpose: `repo_ci_cutover_and_external_runtime_operations`
State: `active_policy`
Machine boundary: 可执行真相归 `.github/workflows/`、`scripts/verify.sh`、`Makefile`、contracts、OPL provider/runtime readback 与 MAS owner receipts。

## 源码验证与 CI Preflight

```bash
scripts/verify.sh
scripts/verify.sh full
```

- **Lane 分工**：默认 `source` lane 执行 Git tracked-path hygiene（`scripts/repo_hygiene_audit.py`，校验精确 `src/med_autoscience/` 文件集与 retired path 拦截，不扫描或删除 ignored `.venv`/cache）、冲突标记检查与 `make test`（经 `uv export --frozen --only-group dev` 与隔离运行全量 `pytest tests -q`，Framework Python 由 `OPL_FRAMEWORK_PYTHON_ROOT` 提供）；`full` 额外调用 OPL `workspace source-hygiene` 与 carrier `--check`。
- **CI Topology**：`ci.yml`（Ubuntu PR/main push/手动 `source`）、`qualification.yml`（周度/手动 macOS `full`、Framework hosted interface readback 与 wheel/sdist build）、`codeql.yml`（安全分析）、`whitepaper.yml`（手动复用 Framework 白皮书构建，`publish: false`）。定位回归可直接跑 pytest path，不新增私有 lane manifest 或 wrapper；结构 drilldown 使用 OPL `quality details`。
- **证据边界**：CI/test green 只证明对应 repo lane，不证明 OPL runtime ready、provider running、paper progress、quality/publication ready、artifact mutation authorization 或 production ready。

## 主线集成与临时工作区清理

每个写集只有一个 owner；复杂或可能重叠的改动使用独立 worktree，不覆盖已有未提交内容。提交前复核实际 diff 并运行对应验证入口；集成后若改变被验证行为只重跑受影响检查，不重复浪费全量构建，并用 Git readback 证明目标分支包含结果（仅在明确授权时推送远端）。自有临时 worktree 与分支依据当前 `git worktree list`、分支包含关系与任务状态清理，不依赖旧前缀保护表或历史 mailbox。

## 真实 Study 运行面切换验收

源码验证通过不授权生产运行切换。实际切换前必须明确目标 study、当前执行 owner、用户授权、写集与回退入口，并读取 OPL 当前 StageRun/Attempt、workspace inventory、MAS lifecycle、canonical artifact 与 owner receipts（不从旧日志推断执行者或创建重复 writer）。复制或重建产物须验证内容完整性和 owner 授权；暂停、交付暂停和停止状态须保留 [Study 生命周期控制](../source/study_lifecycle_control.md) 门禁，质量债、审阅结果与未完成 finding 不得丢失。切换完成以目标侧 same-identity runtime readback、MAS owner result、canonical artifact refs 与无越权写入证据为准。

## 稳定运行功能面核对

MAS 已退役 repo-local CLI/MCP/installer/workbench wrapper（[约束](../invariants.md#退役与兼容)），人工核对仅检查当前公开表面，不把旧命令、docs、focused tests、queue empty 或 package import 当作 ready（未证明前保持 `not_proven`）：

| 功能面 | 当前入口 | 必须核对 | 不证明 |
| --- | --- | --- | --- |
| Public Stage execution | `contracts/action_catalog.json` 六个 Stage action | action/schema/Stage manifest 绑定、workspace/study identity、StageRun receipt | runtime live、paper progress、quality verdict |
| Stage tool use | Stage Tool Affordance Boundary | capability refs、permission/write scope、forbidden authority、tool result refs | tool success 等于 stage completion |
| Authority evaluation | host-only closed-registry callables | `contracts/domain_handler_registry.json` 纯函数绑定、无 user surface、output shape | public command、provider attempt、publication verdict |
| Environment & Runtime | OPL `env prepare/run` 与 current-control/Attempt readback | requirement profile、execution receipt、same-identity live attempt、lease、liveness | MAS domain ready、paper delta |
| Publication / Quality | MAS `publication_eval/latest.json`、quality gate/owner receipt | current study identity、source/artifact refs、owner authority | submission completed unless separately receipted |

## 外部运行依赖与 MDS 来源边界

- **External runtime 定位**：外部服务/executor 不是 MAS 默认可用性的前置。MDS/DeepScientist 与 external workspace 只允许作为 historical backend audit、explicit archive import、upstream learning/provenance 或 parity oracle（来源元数据见 [source_provenance.json](../references/med-deepscientist/source_provenance.json)，旧分类不定义当前实现清单）。它们不得恢复为 MAS 默认 runtime、默认 diagnostic、WebUI、quality owner、artifact authority 或 publication gate；缺 external evidence 时保持 `evidence_required`。
- **禁止错误推导**：external service reachable 不等于 paper progress，executor attempt completed 不等于 quality/publication ready，historical backend parity 不等于 current runtime ready，archive import 不等于 canonical artifact authority，external workspace state 不得覆盖 MAS study truth；吸收外部方法须记录 source ref、许可、保留范围、当前接收 owner 与可验证结果（医学方法进入 MAS/ScholarSkills，通用运行/UI 进入对应平台 owner）。

相关参考：[架构概览](../architecture.md)、[Runtime 边界](../runtime/runtime_boundary.md)、[当前验证边界](../status.md)。
