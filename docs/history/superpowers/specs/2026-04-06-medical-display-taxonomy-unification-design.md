# Medical Display Taxonomy Unification Design

> **Status:** proposed and user-approved at the design level
> **Scope:** unify the long-horizon product taxonomy and the current audited engineering taxonomy for the medical display system
> **Tracking rule:** this spec lives under `docs/superpowers/specs/` as local design state and remains untracked by repo policy

## Goal

Resolve the current taxonomy split across README, roadmap intent, audited display docs, and generated template catalog so the project can:

1. keep a stable long-horizon display-platform target;
2. continue expanding through real-paper delivery rather than checklist-driven template filling;
3. avoid future drift where product language, engineering audit language, and template inventory language silently replace each other.

## Problem Statement

The current display documentation split did not happen because one side is wrong. It happened because three different classification needs were allowed to collapse into each other:

1. **Paper-semantic classification**
   - Answers: "What question is this figure/table trying to answer in a paper?"
   - This is what the original `A-H` list captures.
2. **Engineering audit classification**
   - Answers: "What renderer, input shape, QC risk, and layout contract should govern this artifact?"
   - This is what the current audited display guide and generated catalog naturally evolved toward.
3. **Publication packaging classification**
   - Answers: "How does this artifact exist in the submission/package surface?"
   - This covers shells, tables, and manuscript-facing export surfaces.

Because these three purposes were never explicitly separated, several docs started behaving as if each one defined the whole system:

- `README*.md` started describing the platform target.
- `docs/medical_display_audit_guide.md` started describing the implemented engineering truth.
- `docs/medical_display_template_catalog.md` started exposing generated inventory.

Those three views are all useful, but they are not the same layer.

## Design Decision

Adopt a **three-layer mapping model** instead of forcing all docs into one flat taxonomy.

### Layer 1: Paper Family

This is the top-level product and roadmap layer.

It answers:

- What kind of paper question is being answered?
- What kind of scientific/clinical evidence is being presented?
- What display families should the platform eventually cover?

This layer should use the original `A-H` family model as the stable long-horizon north star.

The `A-H` list is not a closed list. It is the first authoritative roadmap frame. It may expand later, but it should not drift casually based on renderer implementation details.

### Layer 2: Audit Family

This is the engineering governance layer.

It answers:

- Which templates share the same input contract shape?
- Which templates share renderer or layout structure?
- Which QC profiles and failure modes are common?
- Which audited changes must move together?

This layer may split more finely than `A-H`, because engineering risk and paper semantics do not map one-to-one.

Examples:

- `A. 预测性能与决策类` may map to both `Prediction Performance` and `Clinical Utility`.
- `H. 队列与研究设计证据类` may map to `Generalizability`, `cohort_flow_figure`, and table/shell families.

### Layer 3: Template Instance

This is the concrete implementation layer.

It answers:

- What is the exact template ID?
- Which input schema contract does it use?
- Which renderer family materializes it?
- Which QC profile governs it?
- Which exports and manuscript surfaces does it produce?

This is where individual templates such as `kaplan_meier_grouped` or `binary_calibration_decision_curve_panel` live.

## Why This Is Better

### 1. It keeps the long-horizon target stable

The top-level platform goal should not change just because:

- a renderer is split;
- a schema is refactored;
- a QC profile becomes more specific;
- a shell/table route is added.

The `A-H` layer can stay stable while the engineering layer keeps improving.

### 2. It keeps engineering truth honest

The audit layer should be free to classify templates by:

- input structure;
- renderer family;
- layout risk;
- QC contract;
- packaging boundaries.

That is what makes it maintainable. Forcing it to mimic paper semantics exactly would make the engineering layer less truthful and harder to use.

### 3. It preserves the correct expansion order

The project should not expand by mechanically finishing a checklist of all planned templates.

Instead, it should expand by:

1. using real paper delivery as the forcing function;
2. turning recurring needs into audited templates;
3. pushing those templates back into the stable platform taxonomy.

This means the roadmap remains ambitious, but implementation remains evidence-driven.

### 4. It makes maintenance and reporting legible

After unification, progress can be reported in three clean ways:

1. **Roadmap progress**
   - which `A-H` families are covered well enough;
2. **Engineering audit progress**
   - which audit families are stable, partial, or weak;
3. **Inventory progress**
   - how many audited templates, shells, and tables exist now.

That is more honest and more useful than trying to force a single count to answer all three questions.

## Proposed Documentation Roles

### 1. New top-level roadmap doc

Create a new authoritative roadmap doc:

- `docs/medical_display_family_roadmap.md`

Responsibilities:

- define the `A-H` paper families;
- explain what paper question each family answers;
- describe current state per family: `implemented`, `partial`, `planned`;
- map each paper family to one or more audit families;
- serve as the primary long-horizon reference for future OMX prompts.

This doc should become the stable product-facing and planning-facing entry point.

### 2. Existing audit guide stays engineering-facing

Keep:

- `docs/medical_display_audit_guide.md`

Responsibilities:

- define the current audited engineering surface;
- list implemented audit families;
- define engineering contract expectations and authoritative source files;
- explain what counts as "implemented" in the strict audited sense.

This doc should explicitly state that it is not the top-level roadmap taxonomy.

### 3. Existing catalog stays generated inventory

Keep:

- `docs/medical_display_template_catalog.md`

Responsibilities:

- enumerate the currently registered templates;
- expose renderer, schema, QC, and export metadata;
- remain generated from code truth.

This doc should not be treated as the roadmap.

### 4. README becomes narrative only

`README.md` and `README.zh-CN.md` should:

- explain the platform goal;
- reference the roadmap doc and audit guide;
- stop behaving like an alternate taxonomy source.

README should point to the truth rather than define a competing one.

## Proposed Mapping Strategy

The long-horizon platform taxonomy should use the original `A-H` families:

1. 预测性能与决策类
2. 生存与时间事件类
3. 效应量与异质性类
4. 表征结构与数据几何类
5. 特征模式与矩阵类
6. 模型解释类
7. 生物信息与组学证据类
8. 队列与研究设计证据类

Current audited engineering families should be treated as mapped implementation families, including:

- Prediction Performance
- Clinical Utility
- Time-to-Event
- Data Geometry
- Matrix Pattern
- Effect Estimate
- Model Explanation
- Model Audit
- Generalizability
- Publication Shells / Tables

The important rule is:

- `A-H` is the long-horizon target model;
- engineering families are implementation governance;
- they do not compete for top-level authority.

## Expansion Strategy After Current Figure QA Recovery

The next long-horizon platform step should **not** be "finish every planned template first."

It should be:

1. finish the currently reopened real-paper figure QA blockers;
2. reopen the display platform as a long-horizon family roadmap problem;
3. continue template expansion through real paper needs and real acceptance criteria;
4. fold each successful paper-proven capability back into the `A-H -> audit family -> template` structure.

This keeps the platform grounded in real publication quality rather than abstract completeness.

## Expected Benefits For OMX Control

Once this structure is formalized, OMX prompts can stop oscillating between:

- "fix this paper's figures"
- "expand generic templates"
- "count how many templates are done"

Instead, prompts can stay aligned to a stable hierarchy:

1. current paper-delivery blocker;
2. corresponding paper family;
3. corresponding audit family gap;
4. concrete template/QC work to close.

That will make long-horizon execution more stable and reduce the run-stop-run-stop pattern.

## Immediate Follow-On Work

After this design is accepted, the next planning outputs should be:

1. create `docs/medical_display_family_roadmap.md`;
2. define the explicit `A-H -> audit family -> template` mapping table;
3. revise README references so roadmap, audit guide, and generated catalog stop competing;
4. rewrite the OMX long-horizon display prompt so it targets:
   - current real-paper blockers first;
   - paper-driven template expansion second;
   - roadmap convergence continuously.

## Non-Goals

This design does not:

- force the engineering audit layer to mimic `A-H` exactly;
- require immediate implementation of every planned template;
- declare the `A-H` list permanently closed;
- replace real-paper acceptance with abstract catalog completeness.

## Final Summary

The real problem is not "too many categories."
The real problem is that paper semantics, engineering audit logic, and template inventory were never explicitly separated.

The proposed solution is to make those layers explicit:

- `A-H` as the stable product/roadmap layer;
- audit families as the engineering governance layer;
- template instances as the concrete implementation layer.

That makes the project easier to reason about, easier to maintain, and much easier to drive through long-horizon OMX prompts without losing the real-paper quality bar.
