# AI-first Quality Boundary Policy

Owner: `MedAutoScience`
Purpose: `quality_judgment_authority`
State: `active_policy`
Machine boundary: Stage quality-cycle policy、Review receipts、MAS owner result 和真实 artifact 持有质量事实。

## 判断 owner

医学意义、可发表性、claim restraint、读者理解和视觉叙事由独立 reviewer 判断。
程序验证 identity、Schema、allowed writes、资源完整性、引用及 exact bytes；
不能用 regex、score、固定模板、章节覆盖或截图通过率签发质量 verdict。

Producer 同线程内检查只构成 refinement。正式 reviewer、repairer 与 re-reviewer
使用独立 Attempt/session；Framework 校验角色与输入闭包并生成正式 Review receipt，
MAS 消费它作领域判断。Meta Review 负责跨 Stage 缺陷归属；Final Handoff
仅机械运输 exact reviewed bytes。

## 证据与投影

Schema pass、tool success、provider completion、coverage、package existence 或 UI 状态
都不授权 publication/submission。机械检查可以指出缺失文件、错误 identity、
stale 输入或损坏 provenance；主观文体与医学质量仍由 reviewer 解释。

Review currentness 必须按实际受影响 scope 判断，不能以单个路径、全局 hash 或
旧 ready 标签替代。具体 evaluation、revision finding consumption 与 generation
binding 由 [Quality Loop](../../runtime/control/progress_first_quality_loop.md) 持有。

## 反馈与自进化

反馈指向最窄 canonical owner：方法和数据问题回到分析/证据 Stage，表述问题回到
authoring，跨 Stage 问题由 Meta Review 路由。不可在 reviewer 会话内顺手修正文稿。
专业要求按研究类型选择，不能把预测模型目标套到表型或治疗缺口论文。

Agent Lab / OMA 可以消费机制缺陷和回归证据，不能把 suite pass、developer patch
或外部专家建议写成当前 study verdict。真实稿件仍需 fresh independent Review
与 MAS owner acceptance。内部事故、debug 和修复历史只进入诊断与机制学习，
不能成为医学结果或论文叙事。

外部 Skill、persona、工具或 workflow 只提供专业输入，不能获得 MAS evidence、
memory、quality、publication 或 artifact authority。
