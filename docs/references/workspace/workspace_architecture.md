# MAS Workspace Architecture

Owner: `MedAutoScience + OPL Workspace`
Purpose: `workspace_owner_boundary_reference`
State: `current_reference`
Machine boundary: Workspace locator、quest/StageRun lifecycle、StateIndex、restore/retention与 hosted workbench归 OPL；医学 study/source/artifact truth与 owner results归 MAS。

## Object model

```text
workspace
  data/datasets              domain data assets
  studies/<study_id>         canonical study/paper artifacts
  memory/portfolio           MAS-authorized reusable memory
  refs                       source/reference materials
  artifacts                  shared domain artifacts

OPL state root
  package locks/receipts
  workspace and quest bindings
  StageRun/Attempt ledgers
  StateIndex/restore/retention refs
  hosted status/workbench projections
```

OPL state root不是 MAS truth source；MAS workspace也不是 generic runtime state root。两者通过 explicit locator、content digest、lineage ref与 receipt连接。

## Identity

- `workspace_root`：病种/研究组合的长期 domain workspace。
- `study_id`：一条具体研究线或论文主线。
- `stage_run_invocation_id` / `stage_run_id`：OPL durable execution identity。
- `attempt_id` / execution session：Stage 内 producer/reviewer/repairer/re-reviewer identity。
- artifact/source/package refs：exact bytes与 currentness binding。

这些身份不能通过目录猜测，也不能把 volatile currentness observation混入 durable StageRun identity。

## Lifecycle

Workspace创建、登记、scope activation、locator、restore与retention由 OPL Workspace/Pack管理。MAS通过 Stage prompt、schemas与 owner result声明需要哪些 study/source/artifact refs；不得创建 workspace-local scheduler、SQLite lifecycle、runtime service、environment builder或 status shell。

## Data and artifact authority

- OPL可索引 locator、hash、lineage、receipt与 blocker refs，不读取或改写未授权 body。
- MAS持有医学 data/source readiness、canonical paper/artifact mutation、memory accept/reject与 publication authority。
- Provider/package/storage receipt只证明对应 transport/materialization事实，不等于医学 acceptance。
- Literal zero consumable artifact在 diagnostic尝试后是 hard stop；成功物化的 failure/no-output diagnostic本身可以是 consumable progress artifact。

## Generated surfaces

OPL从 MAS V2 catalog与 descriptor生成 CLI/MCP/Skill/product-entry/status/workbench。Workspace不安装或调用 MAS-local wrapper；professional Skills由 OPL Pack按 workspace/quest scope materialize。

## Legacy intake

旧 `.ds/`、workspace-local Git/quest Git、LaunchAgent/systemd/cron、runtime SQLite、private wrapper与 archived reports只按 provenance/restore/cleanup输入读取。它们不能选择当前 Stage、证明 provider running或授权 physical mutation。

## Verification

结构使用 MAS fast/meta与 OPL pack/interfaces/conformance/source-closure验证；workspace可运行、paper progress、restore成功与 artifact ready必须用对应 fresh locator/receipt/owner evidence验证。
