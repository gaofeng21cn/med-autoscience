# MedDeepScientist Upstream Source Provenance

这份文档固定说明一个边界：

- 哪些 `MAS` 改进是直接从近期 `DeepScientist` 成熟实现学来的
- 哪些只是 `MAS` 为了自身 owner 面做的合同提炼

后续继续吸收前，先读这份 provenance，再决定是“直接学 upstream”还是“明确标注为 MAS 自己的抽象”。

## 1. 当前判断

2026-04-20 这一轮已经落到 `MAS` 的几组改进，来源性质分成两类：

1. 直接学到的成熟内容
2. `MAS` 自己做的制度化转换

两类都可以有价值，语义必须分开维护。

“直接学到的成熟内容”可以继续沿 upstream 同一路径吸收。
“`MAS` 自己做的制度化转换”要按本仓 contract 变更管理，不能写成“这是 upstream 已经有的成熟实现”。

当前 owner boundary 继续按两层维护：

- `DeepScientist` / `MDS` base skill 继续承载通用研究阶段纪律、route semantics、durable output expectations，以及 baseline / analysis / write / finalize / decision 的通用研究方法。
- `MAS` overlay + controller + eval hygiene 继续承载医学研究 owner 面，包括 study charter 质量总合同、medical overlay、evidence / review ledger、journal / submission hygiene、publication gate blocker 与 human gate 边界。
- `MDS` 当前对 `publishability_gate_mode` 和 base skill 本地附加层的清理，服务 authority 去重；清理完成后，`MAS` 继续作为医学质量、投稿规则和医学稿件合同的 repo-tracked owner。

## 2. 直接有 upstream 依据的内容

### 2.1 阶段主线与常见 durable outputs

upstream 已经把主研究阶段固定成：

- `scout`
- `baseline`
- `idea`
- `experiment`
- `analysis-campaign`
- `write`
- `finalize`
- `decision`

并且已经给出每个阶段典型会留下的 durable outputs。

上游证据：

- `DeepScientist/docs/en/14_PROMPT_SKILLS_AND_MCP_GUIDE.md`
- `DeepScientist/docs/en/06_RUNTIME_AND_CANVAS.md`

`MAS` 里对应吸收：

- `e6d5cb1` `Add MAS route and evidence review contracts`
- `392edd8` `Link stage discipline into study charter`
- `cleanup` `remove duplicated charter-stage mirrors`

来源判断：

- 阶段名字、阶段分工、阶段产物类别，属于直接学 upstream
- 把这些内容压成 `MAS` 的 canonical YAML，属于 `MAS` 为 entry/runtime 接面做的必要镜像
- 把它们再重复投影到 study charter，属于多余镜像层，现已回收

### 2.2 baseline 的“轻而可信”路线

upstream `baseline` skill 已经明确：

- 目标是一条可信 comparator line
- 默认走最轻、最可信的 attach / import / reproduce / repair 路线
- 先有 `PLAN.md` 和 `CHECKLIST.md`
- baseline 过线要靠确认或 waiver
- 不要把 baseline 做成无穷复现日记

上游证据：

- `DeepScientist/src/skills/baseline/SKILL.md`

`MAS` 里对应吸收：

- `src/med_autoscience/overlay/templates/medical-research-baseline.block.md`
- `src/med_autoscience/policies/controller_first.py`

来源判断：

- “choose the lightest trustworthy route” 这类核心纪律，属于直接学 upstream
- 医学场景里的 cohort / endpoint / time horizon / clinical interpretability 这些要求，属于 `MAS` 医学化扩写

### 2.3 analysis-campaign 作为独立 follow-up 路线

upstream 已经把 follow-up evidence work 收紧成单独的 `analysis-campaign`：

- 一次 campaign 只回答明确证据问题
- 每个 slice 对应一个清晰问题
- 一条 slice 也算正式 campaign
- campaign 结果要聚合
- 写作导向 campaign 要绑定 outline 和 experiment matrix

上游证据：

- `DeepScientist/src/skills/analysis-campaign/SKILL.md`
- `DeepScientist/docs/en/06_RUNTIME_AND_CANVAS.md`

`MAS` 里对应吸收：

- `src/med_autoscience/overlay/templates/medical-research-analysis-campaign.block.md`
- `src/med_autoscience/study_charter.py` 里的 `bounded_analysis`
- `d3d7f77` `Route bounded analysis through MAS outer loop`
- `3058e13` `Add bounded analysis charter contract`

来源判断：

- `analysis-campaign` 作为独立 route、one-slice campaign、bounded evidence gap 这些内核，属于直接学 upstream
- `bounded_analysis` 预算边界、study charter 挂接、outer-loop 接管，属于 `MAS` 自己的执行化转换

### 2.4 write 的 outline-first / reviewer-first / claim-evidence mapping

upstream `write` skill 已经明确：

- 写作的目标是测试证据能否支撑稳定 narrative
- outline-first
- 证据不足时 route back
- reviewer-first
- claim-evidence map 是正式 durable surface
- draft-ready、submission-ready、quest completion 是不同层级

上游证据：

- `DeepScientist/src/skills/write/SKILL.md`

`MAS` 里对应吸收：

- `src/med_autoscience/overlay/templates/medical-research-write.SKILL.md`
- `docs/policies/evidence_review_contract.md`
- `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`

来源判断：

- outline-first、reviewer-first、claim-evidence traceability、route-back discipline，属于直接学 upstream
- general medical journal profile、submission minimal、医学稿件附加合同，属于 `MAS` 医学化扩写

### 2.5 finalize 的 closure / claim ledger / readiness layering

upstream `finalize` skill 已经明确：

- finalize 是 closure protocol
- 要区分 supported / partial / unsupported / deferred
- 要留下 final claim ledger、limitations、resume packet、final recommendation
- finalization 发现不够稳时要 route back

上游证据：

- `DeepScientist/src/skills/finalize/SKILL.md`
- `DeepScientist/src/skills/write/SKILL.md`

`MAS` 里对应吸收：

- `src/med_autoscience/overlay/templates/medical-research-finalize.SKILL.md`
- `75b7deb` `Harden publication gate surface blockers`
- `ae2400e` `Harden publication gate surface blockers`

来源判断：

- closure、claim ledger、resume packet、route-back 这些主结构，属于直接学 upstream
- 把它们提升成 `publication gate` blocker 和 `MAS` controller surface，属于 `MAS` 自己的 enforcement 转换

### 2.6 decision 作为跨阶段治理动作

upstream `decision` skill 已经明确：

- 它是 cross-cutting control skill
- 每次 consequential decision 都要显式写 verdict / action / reason / evidence / next stage
- 选择最小、最诚实的 next action

上游证据：

- `DeepScientist/src/skills/decision/SKILL.md`

`MAS` 里对应吸收：

- `src/med_autoscience/overlay/templates/medical-research-decision.SKILL.md`
- `src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml`

来源判断：

- `decision` 的角色和 route-back 治理方式，属于直接学 upstream
- human gate boundary、controller owner judgment 这些字段化治理面，属于 `MAS` 自己的制度化转换

### 2.7 当前固定的 owner boundary

| surface family | 当前 owner | 当前口径 |
| --- | --- | --- |
| 通用研究阶段纪律 | `DeepScientist` / `MDS` base skill | 阶段名字、route semantics、common durable outputs、light trustworthy baseline、outline-first、reviewer-first、closure protocol、decision protocol 继续按 upstream learned content 维护 |
| 医学研究合同 | `MAS` study charter + medical overlay | cohort / endpoint / time horizon / clinical interpretability、journal / reporting profile、bounded analysis budget、医学稿件执行要求继续按 `MAS` owner 面维护 |
| 医学稿件审阅与投稿治理 | `MAS` evidence / review ledger + publication gate | reviewer concern 排序、claim-evidence consistency、submission minimal、named blocker、final audit readiness 继续由 `MAS` 的 ledger 与 gate surface 承担 |
| 外环治理与 human gate | `MAS` controller / agent entry contract | direction reset、重大 claim 边界变化、external release、submission authorization、controller decision record 继续按 `MAS` 治理 surface 维护 |

## 3. 已落地主线提交的来源归类

### 3.1 `392edd8` `Link stage discipline into study charter`

归类：`mixed_but_upstream_grounded`

说明：

- study stage purpose / minimum outputs / stop conditions 这些内容，直接对应 upstream stage skills
- 这一提交最初把这些内容 materialize 成 `study_charter.py` 的 `stage_expectations`
- 后续清理已经把这层重复镜像撤回，只保留 upstream-aligned route surface 和 `MAS` 真正需要的质量合同

### 3.2 `e6d5cb1` `Add MAS route and evidence review contracts`

归类：`mas_contract_extraction`

说明：

- route taxonomy 和 evidence/review 主题来自 upstream
- `goal / enter_conditions / hard_success_gate / durable_outputs_minimum / next_routes / route_back_triggers` 这一整套统一字段表，是 `MAS` 自己做的 canonical contract 抽象

这类变更可以保留，维护时必须明确标注为 `MAS` 合同层，而不是 upstream 现成实现。

### 3.3 `027bef3` `refine route contract human gate boundaries`

归类：`mas_governance_extension`

说明：

- upstream 强调 user decision、blocking decision 和 route-back
- 当前这版 `human_gate_boundary` 是 `MAS` 为医学 study authority 和 submission audit 增加的治理字段

它属于 `MAS` 本地治理设计。

### 3.4 `004aa6d` / `75b7deb` / `ae2400e` publication gate blockers

归类：`mas_enforcement_from_upstream_spirit`

说明：

- reviewer-first、claim-evidence consistency、submission readiness 这些要求，upstream 有明确方法论依据
- 把这些要求提升成 `publication gate` 的 named blocker，是 `MAS` 外环 controller 和 eval hygiene 的本地 enforcement

这类变更应继续当成 `MAS` owner 面的落地成果维护。

## 4. 继续吸收时的固定规则

后续每次从 `DeepScientist` 继续学习，固定按下面顺序执行：

1. 先看 upstream 当前 skill / docs / runtime surface
2. 先判断它是成熟实现、提示词风格，还是产品面细节
3. 只有成熟实现，才优先直接学
4. 如果 `MAS` 需要自己做合同化转换，必须明确标成 `MAS extraction`
5. 不把 `MAS extraction` 写成“已经从 upstream 直接吸收”

## 5. 当前最重要的维护含义

从现在开始，`MAS` 对外讲法要保持准确：

- 可以说“这轮阶段分工和通用研究纪律主要学自近期 DeepScientist / MDS base skill”
- 可以说“MAS 已把医学研究 owner 面压成自己的 study charter / overlay / controller / gate 合同”
- 可以说“`MDS` 清理 `publishability_gate_mode` 和 base skill 本地附加层之后，`MAS` 继续承担医学质量、投稿规则和医学稿件审阅边界”

这两句话可以同时成立。

## 6. 下一波吸收的约束

下一波如果继续收紧 `baseline`、`analysis-campaign`、`decision`、`finalize`，优先顺序固定为：

1. 先继续核对 upstream 当前 skill 和相关 runtime surface
2. 优先吸收 upstream 已经稳定的 artifact shape、route semantics 和 stop conditions
3. 只有在 `MAS` 必须接管 owner 面时，才补 narrow 的本地字段化转换

目标是持续学现成的成熟方法，同时让 `MAS` 的 owner 面保持诚实、可验证、可维护。

## 7. 清理后的吸收程度

围绕“每个阶段只回答一个关键问题，然后尽快进入下一步”这条上游更新，当前吸收程度可以直接分成三档：

### 7.1 已基本吸收

- `baseline`
  - 已吸收最轻可信路线、`PLAN.md / CHECKLIST.md`、确认或 waiver gate、尽快 handoff
- `analysis-campaign`
  - 已吸收 bounded evidence gap、one-slice campaign、先问题后切片、结果聚合
- `write`
  - 已吸收 outline-first、reviewer-first、claim-evidence mapping、证据不足就 route back
- `finalize`
  - 已吸收 closure protocol、final claim ledger、resume packet、submission layering
- `decision`
  - 已吸收它是跨阶段治理动作，而不是普通执行阶段

### 7.2 部分吸收

- `scout`
  - 已吸收到问题收敛后尽快给 next route
  - 还没有完全对齐 upstream 那种围绕单一 framing question 的更窄表述
- route/entry contract
  - 已有 canonical route surface
  - 当前仍保留 `MAS` 自己的统一字段表，所以它是“upstream 语义 + MAS 结构化镜像”

### 7.3 已明确回收的多余自创层

- `study_charter.paper_quality_contract.route_discipline`
- `study_charter.paper_quality_contract.stage_expectations`

这两层都属于“对 upstream 阶段纪律再写一份摘要”，没有新增 owner 真相，容易漂移，现已从 charter 中撤回。
