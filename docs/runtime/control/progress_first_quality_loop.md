# Progress-First Quality Loop

Owner: `MedAutoScience`
Purpose: `review_currentness_and_revision_consumption`
State: `active_runtime_support`
Machine boundary: `contracts/stage_quality_cycle_policy.json`、generation/review schemas、
MAS owner receipt 与 Framework currentness evaluation 持有机器事实。

## 质量债与推进

Stage Review 的角色、三轮修复预算及 decisive Attempt 规则由
[Stage / Route / Handoff](../stage_route_handoff_standard.md) 持有。
预算耗尽且已有可消费产物时，领域 Attempt 明确剩余缺陷、受影响 scope、
下一 owner 与 route，Framework 物化 `completed_with_quality_debt`。
质量债不授权 publication、submission、export 或 ready；真实 identity、authority、
安全、human gate 和不可消费输入仍 fail closed。

这里解释质量证据怎样失效、复用和消费，不提供私有 current-work-unit、
repair-batch materializer 或独立 controller。

## Review Scope Currentness

Generation manifest v2 保留完整 root generation ledger，并为 medical、statistical、reference、display、publication 和 exact-byte-package lane 输出 MAS-owned `opl_epistemic_review_scope`。每个 scope 使用 Framework `opl_epistemic_review_currentness_contract` / `opl-epistemic-review-currentness-contract.v2` 合同与 `opl_epistemic_review_scope` / `opl-epistemic-review-scope.v2` scope ABI 的 `epistemic_provenance` / `trusted_local_workspace` 语义；MAS 只声明真实 artifact、claim、provenance nodes、reviewed nodes 与 dependency edges，OPL Framework 持有通用 schema validation、dependency currentness 与 scope-budget enforcement。每个 member 的稳定 `member_id` 是 opaque domain identity，不从 path/ref/hash 推导；host 不得自选、删减或重写 scope。

`review_scope_sha256` 只定位 policy、node identity/role 与 dependency topology，不包含 locator、byte hash 或 size，也不构成医学、统计、引用或内容 authority。ref/hash/size 继续用于 snapshot 定位、stale hint、去重和 exact-byte transport。`exact_byte_package` 是同一 epistemic contract 下的 package scope，只包含 docx、PDF、supplement、zip member/allowlist 等 package content/wrapper；checklist、status、evaluation、projection、receipt 等 governance-only surface 不进入该 authority。`release_integrity` 与论文 review 分离，只保留给 `contracts/mas_validator_release_set_receipt.json` 所代表的 MAS 软件包发布。

Review currentness v2 逐 lane 记录 `fresh` 或 `reused_unchanged_scope`，并必须消费 Framework `opl_epistemic_review_currentness_evaluation`，精确绑定当前 scope id、kind 和 reviewed dependency closure。analysis data/code/parameter/result、claim、reference source 或 citation linkage 的实质变化只让声明其 transitive dependency 的 lane stale；layout/render、package 或 governance-only delta 不会让 medical/statistical/reference content verdict stale，hash/locator-only drift也不会自行失效 review。缺失 evaluation、closure 不匹配、把 closure 内实质变化伪装为 ignored change，均 fail closed；不能因 topology locator 不变而复用旧 verdict。

fresh receipt 仍必须绑定当前 generation、manifest、candidate admissions 与 OPL immutable reviewer-input snapshot 的 exact members；reviewer 在判断期间不得回读 live locator。reuse 保留 origin generation、manifest、review request、review receipt 和 candidate receipt provenance，并要求稳定 member identity/role、当前 rubric、snapshot owner metadata 及 Framework semantic currentness 全部成立；不再使用统一 generation/source signature 或 origin candidate aggregate digest。MAS 一次聚合全部 affected lanes。普通 stale 形成 lane-specific route-back/quality debt而不是 provider liveness failure；已消费 `reviewer_revision` 的 stale review 在现有三次 scope budget 内返回 `route_back`，3/3 后以 `review_scope_budget_exhausted` 完成并保留 quality debt。

ScholarSkills 只提供 manuscript/statistical/reference/display/submission 等质量规则和 page-hash evidence candidate，不拥有 generation signature、currentness 或 loop scheduling。page hash 与 artifact hash 可用于 cache/stale hint，但 cache hit 不得产生 verdict、owner receipt、typed blocker 或 readiness。OPL Framework 可解释通用 node/edge currentness 和执行 managed Attempt budget，但不能推断未声明的医学依赖、签 MAS verdict 或写 domain truth；MAS handler消费 Framework evaluation 后签 route-back、quality debt 或 owner result。

## Revision Consumption Binding

每个 generation 必须用 `mas_revision_consumption_binding` 明确记录“本轮没有可消费 revision”或“已消费 revision”。后者由 MAS-owned `mas_revision_consumption_receipt` 绑定 mission/generation/host attempt/output、全部 exact revision-intake refs、OPL review receipt、完整 finding lineage、逐 finding closure 以及 consumed-ref 闭包；`finding_closure_review` 必须同时绑定 repair-map 与 re-review-result hash。owner receipt 只投影这份 exact receipt 及其闭包，不把 OPL generic finding lineage 当作已经被 MAS 消费。缺 binding、finding 尚未全部 closed 属于 progress-first quality debt；缺失 consumed ref，或 receipt hash、mission、generation、host identity、authority boundary 被篡改属于 `invalid_host_input`。该 receipt 的 authority 全为 false：它记录消费事实，不签 review verdict、owner acceptance、publication/submission，也不能创建 typed blocker。
