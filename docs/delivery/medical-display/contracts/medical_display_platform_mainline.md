# Medical Display Mainline

Owner: `MedAutoScience`
Purpose: `medical_display_owner_split`
State: `active_support`
Machine boundary: 当前机器入口是 `contracts/capability_map.json`、`contracts/medical-figure-family-catalog/index.json`、Stage manifest/quality policy、ScholarSkills refs 与 OPL hosted receipts。

Medical display 不再是 MAS 私有平台。MAS 声明医学 figure/table 的 domain context、style/quality refs 与 artifact authority；ScholarSkills 提供专业设计、风格和组合能力；OPL 托管 StageAttempt、工具执行、环境和 artifact transport；独立 Review 产生质量 outcome；MAS owner surface 保留 publication/export/owner-answer authority。

旧 Display Pack adapter、figure loader、polish lifecycle、gallery、renderer 与本地 validator 已删除。它们的历史只存在于 Git provenance，不是 active caller 或兼容接口。
