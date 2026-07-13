# Repository CI Preflight

Owner: `MedAutoScience`
Purpose: `repository_ci_policy`
State: `active_policy`
Machine boundary: 本文解释 CI lane。可执行真相归 `.github/workflows/`、`scripts/verify.sh`、Makefile、tests与 CI receipts。

## 当前入口

MAS repo验证不依赖已退役的 repo-local product CLI。统一入口是：

```bash
scripts/verify.sh
scripts/verify.sh ci-preflight <base-ref>
scripts/verify.sh regression
scripts/verify.sh meta
scripts/verify.sh family
scripts/verify.sh display
scripts/verify.sh submission
scripts/verify.sh full
```

## CI topology

| Workflow/lane | 用途 |
| --- | --- |
| `macOS CI` | push/PR change-aware `ci-preflight` 与 build |
| `macOS Advisory` | regression、meta、family、submission、display 重 lane |
| `Sentrux Advisory` | advisory structure analysis |
| `full` | release/integration 前完整验证 |

实际 trigger、runner与依赖安装以 `.github/workflows/*.yml` 为准。

## Lane semantics

- default：一次 repo hygiene、line-budget 与 Python compile sanity 后，执行 fast pytest 选集；不会再在 smoke/fast 中重复全仓 line-budget 扫描。
- smoke：只验证最小入口，不证明 broader behavior 或结构预算。
- `ci-preflight <base-ref>`：根据 checked-in change-aware policy选择本次触达面。
- regression：普通行为回归，重型 display/submission/family/meta由独立 lane承担。
- meta：machine contracts、generated interface/entry与 repo governance一致性。
- display/submission/family：各 owner重型验证。
- full：组合所有正式 lane。

## Local policy

- 纯 docs变更至少运行 `git diff --check`、conflict-marker scan与 docs link/path检查。
- 触及 machine contract、action catalog、test entry或 runtime semantics时，按变更面追加 meta/focused/default/full。
- Python/pytest必须经 clean runner，避免把 `.venv`、cache、bytecode或 egg-info写回 checkout。
- Line budget是结构 signal，不替代行为验证，也不代表 runtime/paper readiness。
- `family` 在同一隔离 pytest 进程中收集全部 family boundary case，避免为同一依赖环境重复导出、建环境和收集。

## Evidence boundary

CI/test green只证明对应 repo lane。它不证明 OPL runtime ready、provider running、paper progress、quality/publication ready、artifact mutation authorization或 production ready。这些 claim必须 fresh live/readback/artifact/owner receipt。

## 维护

改 lane时同步 `.github/workflows/`、`scripts/verify.sh`、Makefile与 machine-readable test lane contract。不要为旧 CLI命令保留兼容 preflight wrapper。
