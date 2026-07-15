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

两个命令等价并运行完整 collection。所有 Python 入口通过当前 lockfile 的标准
`uv run --frozen` 环境执行，不导出 requirements，也不维护第二套 isolated runner。

## CI topology

| Workflow/lane | 用途 |
| --- | --- |
| `macOS CI` | push/PR 完整 repo verification、OPL hosted interface readback 与 `uv build` |
| `OPL Quality Advisory` | OPL quality details |
| `full` | 本仓完整 pytest collection |

## Lane semantics

- `full` 是唯一 repo verification lane；全套足够小，不再维护行为不清晰的子集。
- 结构 drilldown 由 OPL `quality details` 提供，不安装第二个结构分析工具。

Repo hygiene 只检查 Git tracked path、精确 MAS source morphology 与 retired active
surface；它不会扫描或删除 ignored `.venv`、cache、egg-info 或用户本地环境。

## Evidence boundary

CI/test green 只证明对应 repo lane。它不证明 OPL runtime ready、provider running、
paper progress、quality/publication ready、artifact mutation authorization 或 production
ready。这些 claim 必须由 fresh live readback、artifact 与 owner receipt 证明。

## 维护

定位回归时可以直接运行 pytest path；不新增 lane manifest、strict alias、runner
wrapper 或兼容 target。结构信号统一交给 OPL。
