# Light External Pattern Intake Runbook

Owner: `MedAutoScience`
Purpose: `operator_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 external-pattern intake runbook。机器真相继续归 MAS `agent/` pack、contracts、controller/read-model output、owner receipts、typed blockers、AI reviewer / auditor records、publication eval、controller decisions、真实 workspace artifacts 和 OPL current-control。本文不引入 Light runtime，不安装或路由 Light skills，不写 study truth、knowledge truth、review verdict、publication gate、paper body、artifact body、memory body、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 适用范围

本 runbook 用于 operator 把 Light 这类外部科研技能包的可复用模式吸收成 MAS-native 的 stage-quality、knowledge、reviewer briefing 和 advisory repair hint 规则。它服务当前 work unit 的 `next owner delta`：让下一 owner 更快拿到 verified refs、撞车风险、审稿拒稿预演和 fresh evidence gate，而不是把外部项目变成 MAS 的 runtime、router、knowledge authority 或 quality gate。

本 runbook 的 source-of-truth intake 是 `/tmp/light0305-light-intake` 下的 `README.md`、`CONVENTIONS.md`、`ROUTER.md`、`skills/light-idea-generation/SKILL.md`、`skills/light-idea-critique/SKILL.md`、`skills/light-self-review/SKILL.md`、`_verification_log/*.md`、`code_assets/` 和 `databases/`。这些材料只作为 external pattern evidence 读取；其中的技能名、知识库路径、评分模板、API 状态、库版本和项目记忆都不是 MAS current truth。

## Intake 结论

| Light pattern | MAS classification | MAS owner surface | 落地读法 |
| --- | --- | --- | --- |
| verified skill / template / code-asset / evidence-log discipline | `adopt_template` | stage-quality pack、knowledge briefing、source readiness、reviewer briefing | 每个可复用 skill/template/code asset 必须带来源、核验方式、适用范围、license/API drift 风险和 fresh verification ref；缺 ref 时只能作为 advisory gap。 |
| core collision check | `adopt_template` | idea / scout / analysis-campaign stage-quality、AI reviewer briefing | 对研究 idea、核心结论、核心方法做“最像前作”检索和阴性证据记录；命中实质等价时生成 route-back / repair hint 或 stable typed blocker，不能靠措辞继续声称新颖。 |
| reviewer refusal rehearsal | `adopt_template` | reviewer OS、publication-route briefing、route decision | 在进入写作、修订或 publication gate 前预演 top refusal reasons，并把可反驳证据、未化解 refusal 和 repair target surface 写成 reviewer briefing refs。 |
| self-review fresh-evidence gate | `adopt_template` | operator closeout、stage-quality closeout、owner receipt readiness | 声称完成、通过、修好或 ready 前必须有当前轮 fresh evidence；旧日志、agent 自报、上次测试或“应该可用”只算 diagnostic。 |
| Light 27-skill router / 常驻技能编排 | `reject` | OPL generated/default caller boundary | MAS 不复制 Light router，不把 skill count、技能路由表或常驻技能作为 MAS stage-runtime route。MAS stage/action/quality gate 继续由 MAS pack 和 OPL generated surfaces 表达。 |
| `db09` 项目状态 / Light 知识库 | `reject` | MAS study truth / memory authority boundary | Light `db09` 或其他知识库不能成为 MAS study truth、publication-route memory body、evidence ledger、review ledger 或 source readiness truth；最多作为 external pattern provenance。 |
| review score / weighted verdict | `watch_only` | reviewer briefing / calibration support | 分数可以帮助 reviewer briefing 排序或校准，但不能关闭 AI reviewer verdict、publication gate、quality gate、publication-ready 或 artifact authority。 |
| external API / library field tables | `watch_only` | source readiness / knowledge prefetch | 只作为可核查端点和 drift watch hint；实际 MAS source readiness 必须 fresh 读取当前 live API、official docs、workspace source refs 或 MAS-owned verified materialization。 |

## Operator 读取规则

Light intake 进入 MAS 时只允许产生四类 advisory ref：

- `verified_asset_ref`：记录模板、脚本、代码资产、API 字段或库行为的来源、核验命令、日期、license / auth / rate-limit 风险和适用边界。
- `collision_check_ref`：记录核心机制 / 核心结论关键词、检索库、最像前作、delta、阴性证据和 novelty risk。
- `refusal_rehearsal_ref`：记录 reviewer 可能拒稿的 top reasons、当前可反驳证据、未化解 gap 和 repair target surface。
- `fresh_evidence_gate_ref`：记录本轮验证命令、exit code、失败计数、diff / artifact refs 和结论是否被 fresh evidence 支撑。

这些 ref 可以进入 `stage_knowledge_packet`、reviewer briefing、route-back briefing、`next_forced_delta` advisory detail、repair candidate board、source readiness note 或 stop-loss candidate。它们不能直接写 paper progress、quality closure、publication verdict、artifact mutation authorization、memory accept/reject verdict、source readiness verdict 或 owner receipt success。

## Progress-first 使用规则

Light-derived advisory 只优化当前 delta 的选择和 briefing，不创造新 progress 类别。

- 当当前 `current_executable_owner_action` 已有 owner、action、work unit、required output surface、source refs 和 forbidden write boundary，且 Light-derived advisory 缺失或陈旧时，operator 继续推进 owner action；缺 advisory 不阻塞不相关 dispatch。
- 每个 work unit 的 Light-derived advisory 预算必须有上限。默认只读取当前 delta 需要的最小 Light evidence：一个模式对应的 skill / verification log / asset 证据即可；不得为补齐外部知识库或完整 27-skill map 延迟 owner admission。
- 只有当前 delta 的 route-required ref 缺失，且缺失会影响 source/data/evidence、owner-route identity、forbidden write boundary、irreversible mutation 或 reviewer/publication hard gate 时，才能生成 typed blocker。typed blocker 必须命名缺失 ref family，例如 `collision_check_ref_required`、`fresh_evidence_gate_ref_required`、`verified_asset_ref_required` 或 `refusal_rehearsal_ref_required`，并指明解除 owner。
- Light review score、skill self-check、template completeness、API endpoint freshness 或 db09 memory 缺失本身不是 hard gate。它们只在当前 MAS owner route 明确要求同类 ref，且缺失会导致无法形成 safe owner output 时，才升级为 typed blocker。

## Stage 落点

| MAS stage / surface | 怎么用 Light pattern | 输出边界 |
| --- | --- | --- |
| `scout` / `idea` | 用 core collision check 约束“最像前作”和真实 gap；用 verified source discipline 记录检索库、HTTP / API 状态和阴性证据。 | 产出 idea / route advisory、collision risk 或 route-back，不产出 novelty verdict closure。 |
| `analysis-campaign` | 用 verified code-asset discipline 要求统计脚本、指标、模板和对照库有核验 ref；没有 ref 时提示 repair target。 | 产出 analysis repair hint 或 source readiness note，不授权 artifact mutation。 |
| `review` / AI reviewer briefing | 用 refusal rehearsal 列 top refusal reasons、未化解 CRITICAL 和 reviewer evidence snippets。 | 产出 reviewer briefing、route-back 或 typed blocker，不替代独立 reviewer / auditor invocation。 |
| `decision` / route owner | 用 bounded advisory 选择 next owner delta、stop-loss candidate 或 human gate suggestion。 | 产出 route advisory，不关闭 publication gate、quality gate 或 memory verdict。 |
| operator closeout | 用 fresh-evidence gate 校验“完成 / 通过 / 修好”声明是否有当前轮证据。 | 产出 closeout evidence ref；无 fresh evidence 时降为 diagnostic 或 blocker，不伪造 success receipt。 |

## 风险与 mitigation

| 风险 | 失败形态 | Mitigation |
| --- | --- | --- |
| 控制面污染 | Light router、skill count、评分模板或外部 process 被写成 MAS current work-unit reducer / route owner。 | 只允许 advisory refs 进入 MAS；current owner、route、dispatch、typed blocker 和 owner receipt 继续由 MAS controller / OPL current-control 产生。 |
| 第二 truth source | `db09`、knowledge base、verification log 或 external API table 被当作 study truth、source truth、publication truth 或 memory authority。 | 外部材料只保留 provenance / briefing；study truth、source readiness、memory accept/reject、review verdict 和 artifact authority 必须回到 MAS-owned surfaces。 |
| 过度审查拖慢推进 | 为补齐 collision、refusal、self-review 或全技能 map 阻塞 unrelated owner action。 | 执行预算上限；缺 advisory 默认 observability / platform repair；只有 route-required ref 缺失且影响 hard gate 时 typed blocker。 |
| 外部 API 漂移 | 2026-06-06 实测 endpoint、license、rate-limit 或导入路径被后续 upstream 变更。 | 使用前 fresh 读取 official docs / live endpoint / local verified materialization；旧 Light log 只能说明历史证据，不支撑当前 source readiness。 |
| review score 误授权 | weighted score、rubric verdict 或 self-review checklist 被当作质量/发表 gate。 | 分数只做 briefing / calibration；AI reviewer verdict、publication gate、quality receipt、owner receipt 或 typed blocker 才能改变 authority state。 |

## 不再走的路径

- 不安装 Light，不调用 Light runtime，不把 Light 作为 MAS hosted backend。
- 不复制 Light 的 27-skill 路由、常驻技能编排或 `ROUTER.md` 作为 MAS route table。
- 不把 Light `db09`、知识库、项目卡或 decision log 写成 MAS study truth、publication-route memory body、evidence ledger、review ledger 或 source readiness。
- 不把 Light review score、加权 verdict、self-review checklist 或 refusal rehearsal 写成 AI reviewer pass、publication-ready、quality closure、artifact authority 或 paper progress。
- 不为补齐 external-pattern advisory 重跑同义 read-model/currentness reconcile，或阻塞与该 advisory 无关的 current owner dispatch。
