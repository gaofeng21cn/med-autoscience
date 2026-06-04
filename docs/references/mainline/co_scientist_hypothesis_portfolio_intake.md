# Co-Scientist Hypothesis Portfolio Intake

Owner: `MedAutoScience`
Purpose: `external_research_pattern_intake`
State: `active_reference`
Machine boundary: 本文是人读 external intake 叙事。机器真相继续归 `agent/` pack、`contracts/`、源码、runtime/controller durable surfaces、study workspaces、owner receipts、AI reviewer / auditor record、publication gate 和 artifact authority。

本文把 Google / Nature Co-Scientist 论文与公开说明中可学习的科研 agent pattern 吸收到 MAS-native contract-first 叙事中。它不引入 Co-Scientist runtime、不复制外部 agent 编排、不把外部 ranking metric 写成 MAS 质量门；机器落点以 MAS `agent/` semantic pack、generated contracts、focused tests 与 OPL refs-only projection contract 为准。当前外部依据是 Nature 2026 论文 [Accelerating scientific discovery with Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y)、Google Research 2025 说明 [Accelerating scientific breakthroughs with an AI co-scientist](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) 与 arXiv 预印本 [Towards an AI co-scientist](https://arxiv.org/abs/2502.18864)。

## 可吸收启发

Co-Scientist 的可学习点不是“让 ranking agent 决定科学真相”，而是把开放式科研探索组织成可审计的 hypothesis portfolio：

- 多 agent 分工围绕 generation、reflection、ranking、evolution、proximity、meta-review 展开，让候选假设经历生成、批判、去重、改写和综述。
- tournament / Elo / proximity 等机制把候选假设排序、聚类和去重，帮助人和 reviewer 看见探索空间、相邻路线、明显弱项和下一轮 refinement。
- 系统围绕 scientist-provided goal 和 prior evidence 生成 proposal，强调 hypothesis 与证据、可检验性、实验/分析计划和人工专家判断的关系。
- 公开材料把 human scientist / expert validation 保留在闭环内；自动 ranking 只是优先级和比较信号，不是发表、临床或医学质量 verdict。

MAS 吸收的是这组 contract shape：`hypothesis portfolio -> evidence pack -> independent reviewer / human gate -> owner receipt or stable typed blocker`。它适合进入 MAS `idea`、`analysis-campaign`、`review`、`decision` 与 paper-line quality loop，不适合变成 MAS 私有 runtime 或 OPL generic quality owner。

## MAS-native 落点

MAS 新增方向应表述为 `hypothesis portfolio / evidence pack`，并落在 MAS 自己的医学 owner surfaces：

- `hypothesis portfolio`：记录候选研究假设、临床/流行病学动机、source refs、可检验分析路径、排除理由、相邻/重复候选、失败路径和下一 owner。它是 study-line exploration artifact，不是 publication verdict。
- `evidence pack`：把被推进的候选假设连接到 source refs、analysis refs、negative / failed-path ledger refs、decision trace refs、artifact lineage / reproducibility refs、claim-evidence map、reviewer input refs 和 typed blocker refs。缺关键 ref family 时必须 fail closed 或 route back。
- `portfolio ranking`：Elo、pairwise debate score、proximity cluster、novelty/prior plausibility score、citation/source coverage score都只能作为 advisory projection。它们可以影响探索顺序、reviewer briefing 和 next-candidate selection，不能关闭 source readiness、quality gate、publication gate、human gate 或 artifact authority。
- `meta-review / expert review`：MAS 必须保留独立 reviewer / auditor invocation、human/PI gate 和 publication gate。executor 自评、ranking 结果、scorecard、queue completion 或 projection freshness 不能替代独立质量判断。
- `owner closeout`：每次 hypothesis portfolio 进入论文路线、analysis campaign、write sprint 或 publication route 后，必须产出 MAS owner receipt、AI reviewer / auditor record、human gate decision、publication gate result、artifact authority receipt，或命名缺失 ref family 与 route-back owner 的 stable typed blocker。

## MAS / OPL 边界

该方向按现有 MAS/OPL 分工吸收：

- MAS 持有医学 truth、source readiness、hypothesis portfolio 语义、evidence pack 质量、claim restraint、publication quality、artifact authority、memory body accept/reject、human/expert decision 和 owner receipt。
- OPL 持有 runtime/projection/generated surfaces：stage attempt、queue、wakeup、retry/dead-letter、resume、attempt ledger、refs-only projection、generic lifecycle/index、App/workbench shell 与 generated caller surfaces。
- OPL 可以展示 hypothesis portfolio refs、ranking/proximity advisory fields、evidence pack availability、missing ref family、typed blocker 和 owner receipt refs。OPL 不能写候选假设正文、接受医学结论、宣布 source readiness、关闭 publication quality、授权 artifact mutation 或替代 human/expert gate。
- ranking/Elo/proximity 的正确机器读法是 `advisory_selection_signal`。任何下游若缺 MAS owner receipt、independent reviewer/auditor record、human gate 或 publication gate，都必须继续显示 pending / blocked / route-back，而不是把最高分候选写成 ready。

## Adoption 分类

| Pattern | 分类 | MAS/OPL owner | 本地叙事落点 | Stop condition |
| --- | --- | --- | --- | --- |
| Hypothesis portfolio with evidence refs | `adopt_contract` | MAS | `idea` / `analysis-campaign` / `review` stage output 与 research evidence pack | 候选缺 source refs、可检验路径、decision trace 或 route-back owner |
| Pairwise debate / Elo ranking | `adopt_template` | MAS advisory, OPL projection | exploration ordering、reviewer briefing、candidate comparison read model | 被用于关闭 quality/publication/human gate |
| Proximity clustering / duplicate suppression | `adopt_template` | MAS advisory, OPL projection | 相似假设聚类、重复路线合并、negative-path ledger | 被用于删除未审阅候选或覆盖医学判断 |
| Evolution / refinement loop | `adopt_contract` | MAS | 候选修订、failed-path reason、next owner handoff | refinement 缺证据增量或绕过 reviewer gate |
| External Co-Scientist runtime import | `reject` | none | 仅作外部参考 | 需要引入外部 runtime、外部 authority 或无法审计的 provider body |

## 当前落地口径

本 intake 已按 MAS contract-first 顺序落到 semantic pack、generated standard pack / stage control plane descriptor、focused tests 与 OPL refs-only hypothesis portfolio projection contract。后续扩展仍必须先定义 owner、refs、forbidden writes、receipt/blocker、schema fail-closed 和 generated projection，再补 fixtures/tests。不能先把 Co-Scientist 词面、Elo 数值或 proximity 文案写进 runtime 判断，再用文档解释边界。

后续 runtime-facing Stage / Route 重构规格见 [Co-Scientist Stage / Route 重构设计与执行规格](../../runtime/designs/coscientist_stage_route_restructure.md)。该规格承接本文的外部模式 intake，但只有在落到 `agent/` semantic pack、machine-readable contracts、source/read-model、focused tests、owner receipts、typed blockers 或 runtime evidence 后，才算实际实现。
