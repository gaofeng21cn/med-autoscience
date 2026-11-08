# Medical Display Visual Audit

Owner: `MedAutoScience`
Purpose: `medical_display_quality_boundary`
State: `active_support`
Machine boundary: MAS 只在 `contracts/capability_map.json` 声明 display capability refs；通用 figure/template catalog 归 MAS ScholarSkills `medical-display-core` canonical catalog。执行归 OPL hosted StageAttempt，质量结果归独立 reviewer/re-reviewer。本文不是 validator 或 renderer。

医学图表交付必须保留 exact artifact/source/data refs、生成参数、content hash、panel/legend/label 语义与 visual-audit evidence。`medical-figure-design` 统筹图形设计，`medical-figure-style` 与 `medical-figure-composer` 提供专业候选与 QA；它们不写 MAS truth、不签 owner receipt，也不授权 publication/export readiness。

OPL 可以托管绘制、导出与 artifact transport，但不能解释医学视觉质量。正式通过、修复、质量债或 hard gate 只能由独立 reviewer/re-reviewer 基于 exact reviewed bytes 和 rubric 给出；MAS owner surface 才能据此形成 domain owner answer。旧 MAS-local figure loader、polish lifecycle、renderer 与 validator 已物理退役。
