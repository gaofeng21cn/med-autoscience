# MedDeepScientist Upstream Source Provenance

Owner: `MedAutoScience`
Purpose: `deepscientist_historical_source_attribution`
State: `historical_reference`
Machine boundary: 本页保存 2026-04-20 来源辨析，不证明当前 upstream 或 MAS 实现。

## 来源与原创内容

| 上游历史材料 | 学到的研究方法 | MAS 自己的转换 |
| --- | --- | --- |
| `DeepScientist/docs/en/14_PROMPT_SKILLS_AND_MCP_GUIDE.md`、`06_RUNTIME_AND_CANVAS.md` | 阶段分工与 durable outputs | 统一 Stage/route YAML、医学 evidence/review 合同 |
| `DeepScientist/src/skills/baseline/SKILL.md` | 最轻可信 comparator、attach/import/reproduce/repair、确认或 waiver | cohort、endpoint、time horizon、临床解释和显式 refresh |
| `DeepScientist/src/skills/analysis-campaign/SKILL.md` | 有界问题、单 slice 也可形成 campaign、聚合结果 | 医学分析预算、charter 与证据约束 |
| `DeepScientist/src/skills/write/SKILL.md` | outline/reviewer-first、claim-evidence mapping、证据不足 route-back | 医学报告规范、稿件审阅与 submission 边界 |
| `DeepScientist/src/skills/finalize/SKILL.md` | claim ledger、supported/partial/deferred、resume 与 closure | MAS publication/artifact authority |
| `DeepScientist/src/skills/decision/SKILL.md` | 明确 action/reason/evidence/next Stage | 医学 human gate、claim 边界与 owner decision |

表中路径属于当时的外部 source tree，不是本仓可执行入口。
来源采集元数据保留在 [source_provenance.json](./source_provenance.json)。
当前 Stage、专业能力和 runtime owner 分别由 MAS pack、ScholarSkills 和 Framework 持有；
MDS base skill、overlay/controller 和旧 gate implementation 均不作为默认依赖。

## 历史提交定位

| MAS 历史提交 | 来源性质 |
| --- | --- |
| `e6d5cb1` | upstream route/evidence 主题的 MAS 合同提炼 |
| `392edd8` | upstream-grounded Stage discipline；当时 charter 重复镜像随后收回 |
| `d3d7f77`、`3058e13` | analysis-campaign 方法的 MAS 执行与 charter 转换 |
| `027bef3` | MAS human-gate 治理扩展 |
| `004aa6d`、`75b7deb`、`ae2400e` | reviewer-first 方法的旧 publication enforcement |

这些提交只用于追溯，不能证明相关旧模块仍存在或应被恢复。
新学习的 intake、验证和回写规则只由
[Continuous Learning](./deepscientist_continuous_learning_policy.md) 持有。
