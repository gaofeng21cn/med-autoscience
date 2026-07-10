# MAS Bootstrap

Owner: `MedAutoScience`
Purpose: `bootstrap_boundary`
State: `current_reference`
Machine boundary: 本文解释 package/environment handoff。可执行真相归 OPL installer/environment substrate、MAS contracts 与 generated interfaces。

## 结论

MAS 不再提供 repo-local workspace initializer、editable import bootstrap、Python/R environment builder 或 Codex plugin installer。

当前 bootstrap 是两部分：

1. MAS 声明 domain pack、actions、schemas 与环境 requirements。
2. OPL 发现 package，生成 interfaces，并准备 hosted runtime/environment。

## Package discovery

OPL 读取：

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/action_catalog.json`
- `contracts/generated_surface_handoff.json`
- `agent/`

canonical domain id 是 `mas`。`med-autoscience` 仅作为 repo/package/plugin locator。

## Python packaging

依赖通过标准 packaging/`uv sync` 或 OPL workspace override 安装。MAS import 不改写 `sys.path`、package `__path__` 或 `sys.modules`，也不尝试在 import 时发现 sibling checkout。

## Runtime environment

MAS 的环境声明在 `contracts/runtime_environment_requirements.json`。当前 `analysis-display` profile 包含 R 与 Bioconductor requirement；环境 owner 是 OPL Framework。

标准 handoff：

```bash
opl env prepare \
  --domain mas \
  --profile analysis-display \
  --platform <platform> \
  --requirement-profile contracts/runtime_environment_requirements.json \
  --artifact-root <artifact_root> \
  --apply \
  --json

opl env run \
  --domain mas \
  --profile analysis-display \
  --artifact-root <artifact_root> \
  -- <command>
```

Requirement profile 或 prepare success 不等于 MAS domain ready、paper progress、visual quality 或 production ready。

## Generated interfaces

CLI、MCP、Skill、product-entry、status 与 workbench 由 OPL 从 action catalog/schema 生成或托管。MAS 不提供第二套 installer、parser、JSON-RPC transport 或 hosted shell。

Direct Codex 使用 repo-tracked primary skill；plugin 分发使用受控 carrier mirror。两者 currentness 由 capability map/carrier projection contract 约束，不由 bootstrap 脚本复制。

## Workspace boundary

Study workspace lifecycle、locator、StateIndex、retention/restore 与 hosted workbench 归 OPL。MAS domain handlers 可以读取受权 refs并写 MAS-owned truth/receipt surface，但不得创建通用 workspace/platform authority。

## 验收

- OPL 能解析 descriptor、pack、22-action catalog 与 schemas；
- OPL 能解析 runtime requirement profile；
- MAS import 不依赖 checkout path mutation；
- generated interfaces 不依赖 repo-local installer/workspace initializer；
- runtime/paper/readiness claim 仍由 fresh live/readback/owner evidence 证明。

## 相关入口

- [Project](../docs/project.md)
- [Architecture](../docs/architecture.md)
- [Contracts](../contracts/README.md)
- [Runtime boundary](../docs/runtime/contracts/runtime_boundary.md)
