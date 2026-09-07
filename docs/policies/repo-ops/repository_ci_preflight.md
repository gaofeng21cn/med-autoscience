# Repository CI Preflight

Owner: `MedAutoScience`
Purpose: `repository_ci_policy`
State: `active_policy`
Machine boundary: 本文解释 CI 入口。可执行真相归 `.github/workflows/`、`scripts/verify.sh`、Makefile、tests 与 CI receipts。

## 当前入口

```bash
scripts/verify.sh
scripts/verify.sh full
```

两个入口都运行完整 pytest collection。默认 `source` lane 执行 tracked-path hygiene、
冲突标记检查和 `make test`；`full` 额外调用 OPL `workspace source-hygiene`。
Makefile 用 `uv export --frozen --only-group dev` 从 lockfile 导出临时 requirements，
再用 `uv run --isolated --no-project --with-requirements` 运行测试；退出时删除临时文件。
Framework Python authority 由 `OPL_FRAMEWORK_PYTHON_ROOT` 提供，默认指向同级 Framework checkout 的 `python/`。

## CI topology

| Workflow/lane | 用途 |
| --- | --- |
| `ci.yml` | Ubuntu 上的 PR、main push、手动 source verification |
| `qualification.yml` | 每周或手动 macOS full verification、Framework hosted interface readback 与 wheel/sdist build |
| `codeql.yml` | 每月或手动 Actions/Python 安全分析 |
| `whitepaper.yml` | 手动复用 Framework 白皮书构建，`publish: false` |
| `source` | 本仓 hygiene 与完整 pytest collection |
| `full` | source 检查加 OPL source-hygiene readback |

## Lane semantics

- `source` 是默认验证入口；需要 Framework source-hygiene readback 时使用 `full`。
- 本地使用 source 验证当前修改；涉及 Framework 集成时使用 full 和 qualification 对应的接口检查。
  PR 与 main push 都有 source CI，周度 qualification 检查 Framework 集成与 runner 漂移。
- 结构 drilldown 需要时直接使用 OPL `quality details`；MAS CI 不维护 advisory
  workflow 或重复上传诊断 artifact。

Repo hygiene 只检查 Git tracked path、精确 MAS source morphology 与 retired active
surface；它不会扫描或删除 ignored `.venv`、cache、egg-info 或用户本地环境。

## Evidence boundary

CI/test green 只证明对应 repo lane。它不证明 OPL runtime ready、provider running、
paper progress、quality/publication ready、artifact mutation authorization 或 production
ready。这些 claim 必须由 fresh live readback、artifact 与 owner receipt 证明。

## 维护

定位回归时可以直接运行 pytest path；不新增 lane manifest、strict alias、runner
wrapper 或兼容 target。结构信号统一交给 OPL。
