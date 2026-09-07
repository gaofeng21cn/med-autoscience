# ARK Research Workflow Intake

Owner: `MedAutoScience`
Purpose: `ark_pattern_provenance`
State: `support_reference`
Machine boundary: 本页保存外部来源及模式取舍，不证明本地 runtime 或功能完成。

## 来源

历史检查对象为 `kaust-ark/ARK` commit
`01cab1048cc78fa4d33e8274e4f963a44d70dc48`，包括 README、ARCHITECTURE、
`ark/memory.py`、`ark/pipeline.py`、`ark/citation.py`、
`ark/figure_manifest.py` 和 `skills/builtin/*`。

## 模式与当前 owner

| 模式 | MAS 的使用位置 |
| --- | --- |
| goal anchor 与有界 review/repair | Stage charter、独立 Review 和 finding lineage |
| API-first citation 与禁止伪造 | Framework Connect provider receipt，加 MAS source/claim judgment |
| figure manifest 与页面压缩 | canonical artifact lineage、ScholarSkills 和视觉审阅 |
| no-progress 与真实运行 closeout | Stage 的可消费 delta、质量债和真实 evidence |
| human intervention | 实际权限、身份、不可逆操作或缺失决策的明确 gate |
| citation refresh | 受影响 source/review scope 的 owner route-back |

上述模式通过当前声明式 Stage、knowledge 和 quality policy 使用。
旧 reviewer-issue builder、ARK projection 和 citation queue 实现均不提供当前入口。
不引入 ARK runtime、SQLite authority、conda project owner 或 Telegram/dashboard；
外部 score、示例和 workflow 不能成为 MAS publication authority。

采纳证据分层见 [Learning Closure](../../runtime/control/external_learning_adoption_closure.md)。
