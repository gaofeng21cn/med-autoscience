# Research Foundry Medical Mainline Consistency Audit

日期：`2026-04-05`  
角色：`reviewer lane`  
范围：`plans / docs / reports / context surfaces`

## 审计结论

当前主线的大方向已经基本一致：

- 顶层唯一主线是 `research-foundry-medical-mainline`
- 当前活跃 phase 是 `harness authority convergence`
- 当前唯一活跃子线是 `publication eval minimal schema`
- 后续固定顺序仍是：
  1. `charter-parameterized input contract`
  2. `delivery plane contract map`
  3. `real-study relaunch`

但在 `docs / .omx reports / context intake` 之间，仍存在几处会误导后续执行的残余漂移。

## 已对齐的 truth

1. `.omx/context/CURRENT_PROGRAM.md`
   - 已把当前唯一 immediate focus 固定为 `publication eval minimal schema`。
2. `.omx/reports/research-foundry-medical-mainline/LATEST_STATUS.md`
   - 已把 display-only / monorepo-only 叙事收束为统一 mainline。
3. `.omx/plans/prd-research-foundry-medical-mainline.md`
   - 已明确 inherited sublines、固定 phase 顺序，以及当前唯一活跃子线。
4. `docs/research_foundry_medical_mainline.md`
   - 已把 `publication / display` 放回 `delivery / publication plane`，并给出当前 immediate next step。

## 仍需收紧的漂移点

### 1. `docs/open_harness_os_freeze_plan.md` 仍保留 pre-reset 叙事

该文档仍写着“当前仓库同时存在两条活跃主线”：

- `docs/open_harness_os_freeze_plan.md:15-25`

这与当前 program/report truth 已固定的“唯一顶层主线 = `research-foundry-medical-mainline`；旧 display / monorepo 仅作为 inherited truth surface 保留”不一致。

同一文档还写着：

- `docs/open_harness_os_freeze_plan.md:134-136`：`runtime escalation record` 尚未完成 clean integration 收口

但当前 intake / reports 已明确：

- `.omx/context/publication-eval-minimal-schema-20260405T111942Z.md:31-32`
  - `runtime escalation record` 已完成 clean-worktree validation 与 clean integration commit
- `.omx/reports/research-foundry-medical-mainline/LATEST_STATUS.md`
  - `runtime escalation` 已被吸收为 inherited truth

**结论：** `open_harness_os_freeze_plan.md` 目前是最明显的 stale stable doc，容易把执行面重新带回“双主线并行”理解。

### 2. 当前 intake 已要求的最小 planning artifacts 仍缺失

最新 intake 明确把当前子线的优先落盘面写成：

- `.omx/plans/prd-publication-eval-minimal-schema.md`
- `.omx/plans/test-spec-publication-eval-minimal-schema.md`

见：

- `.omx/context/publication-eval-minimal-schema-20260405T111942Z.md:16-19`

但实际检查结果：

- `.omx/plans/prd-publication-eval-minimal-schema.md`：`missing`
- `.omx/plans/test-spec-publication-eval-minimal-schema.md`：`missing`

**结论：** 当前 plans / context / report 的下一步方向已经对齐，但 handoff 所需的最小 PRD / test-spec 锚点还没有真正落盘。

### 3. `docs/research_foundry_medical_mainline.md` 的 phase wording 仍略宽

该文档在 Phase 1 中写的是：

- `docs/research_foundry_medical_mainline.md:197-199`
  - 先把 `publication-eval`、`startup projection`、`charter parameterization` 收紧到可实现状态

但在同文档后文又明确：

- `docs/research_foundry_medical_mainline.md:221-229`
  - 当前唯一活跃收敛子线是 `publication eval minimal schema`
  - 其后才是 `charter-parameterized input contract` 与 `delivery plane contract map`

**结论：** 这不是硬冲突，但会给 reviewer / executor 留下“Phase 1 允许并行推进多个 authority 子线”的解释空间，建议收紧 wording，避免弱化“当前唯一活跃子线”的执行纪律。

### 4. `OPEN_ISSUES.md` 把下一子线内容混入当前缺口

当前 `OPEN_ISSUES.md` 写的是：

- `.omx/reports/research-foundry-medical-mainline/OPEN_ISSUES.md:7-10`
  - `verdict schema`
  - `gap schema`
  - `recommended action schema`
  - `charter-parameterized input contract`

但最新 intake 仍把 `charter-parameterized input contract` 放在当前子线之后：

- `.omx/context/publication-eval-minimal-schema-20260405T111942Z.md:16-19`
- `.omx/context/publication-eval-minimal-schema-20260405T111942Z.md:63-68`

**结论：** 这里更像是“下一子线依赖提醒”，而不是“当前子线交付内容”。若不收紧 wording，后续容易把 scope 从 publication-eval minimal schema 提前扩张到 charter parameterization。

## 建议的最小修正顺序

1. 先补 `.omx/plans/prd-publication-eval-minimal-schema.md`
2. 再补 `.omx/plans/test-spec-publication-eval-minimal-schema.md`
3. 同步收紧 `.omx/reports/research-foundry-medical-mainline/OPEN_ISSUES.md` 的措辞，避免把下一子线提前并入当前 scope
4. 最后更新 `docs/open_harness_os_freeze_plan.md`，把“双活跃主线”与 `runtime escalation record` 状态改成当前主线 truth

## Reviewer Verdict

- 主线方向：`PASS`
- 当前 phase / 子线对齐：`PASS`
- 计划 handoff 完整性：`PARTIAL`
- stable docs 去陈旧化：`PARTIAL`
- 是否适合继续当前子线：`YES`
- 下一步：继续 `publication eval minimal schema`，不要提前跳到 `charter-parameterized input contract`
