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
  shared/memory              local owner/topic bodies when no external knowledge source is bound
  studies/<study_id>/memory  study-specific canonical knowledge when maintained locally
  studies/<study_id>/state   dated study facts when maintained locally
  memory/portfolio/data_assets  rebuildable data-asset governance projections
  refs                       source/reference materials
  artifacts                  shared domain artifacts

OPL state root
  package locks/receipts
  workspace and quest bindings
  StageRun/Attempt ledgers
  immutable consumed-knowledge snapshots
  StateIndex/restore/retention refs
  hosted status/workbench projections
```

OPL state root不是 MAS truth source；MAS workspace也不是 generic runtime state root。两者通过 explicit locator、content digest、lineage ref与 receipt连接。

上述知识目录是无外部资料库时的默认落位，不能定义知识归属或授权范围。用户已有 Obsidian 或其他 Markdown 资料库时，个人、团队和病种主题正文直接绑定原处；项目正文可继续在 Study 工程目录。一个知识对象保留一个主源，Framework 按任务选择并冻结实际使用的版本，不要求先复制到工作区。产品、用户/团队、主题、项目是作用域；方法、政策、时点现状、决策是独立内容性质。完整规则见[知识政策](../../policies/domain_memory_markdown_first_policy.md)。

`memory/portfolio/data_assets/` 是数据资产合同的派生治理面，保留现有实际定位，不充当个人知识库。原始数据、文献、论文与接受决策属于业务资产，清理执行缓存或快照须遵守各自保留要求。

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

结构使用 MAS `scripts/verify.sh`与 OPL pack/interfaces/conformance/source-closure验证；workspace可运行、paper progress、restore成功与 artifact ready必须用对应 fresh locator/receipt/owner evidence验证。
