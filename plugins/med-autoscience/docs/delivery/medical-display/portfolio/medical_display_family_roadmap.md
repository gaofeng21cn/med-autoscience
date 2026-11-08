# Medical Display Research Families

This reference organizes medical figure needs by the question a paper answers. It is not a template inventory, implementation backlog, or evidence that a particular renderer is available.

| Research family | Question | Typical evidence |
| --- | --- | --- |
| Prediction and decision | Does the model support the intended clinical decision? | Discrimination, calibration, thresholds, decision utility |
| Survival and time-to-event | How do risk and events vary over time? | Survival, cumulative incidence, horizon-specific calibration and uncertainty |
| Effects and heterogeneity | How large and consistent are effects? | Effect estimates, confidence intervals, subgroup and interaction evidence |
| Representation and geometry | Which structure is supported by the data? | Embeddings, clusters, trajectories, stability and coverage |
| Matrix patterns | How do variables vary across samples or groups? | Missingness, expression, correlation and cross-group patterns |
| Model explanation | Which inputs support predictions? | Global/local explanations, support domain, subgroup failure analysis |
| Biology and omics | Which biological interpretation is supported? | Pathways, variants, expression, multiomic context with provenance |
| Cohort and study design | Who was studied, and where can results generalize? | Cohort flow, denominators, baseline balance, center coverage and transportability |

These families can overlap in one paper. They guide medical intent; ScholarSkills owns concrete templates, schemas, renderers and the canonical catalog. Read the installed provider's catalog before selecting a template. A historical template name or past anchor-paper result does not establish current availability.

A new figure capability is justified by a current paper question that existing capabilities cannot express, or by a reproducible defect in the selected capability. Route implementation to ScholarSkills and medical interpretation to MAS. Do not queue higher-order composites solely because a previous template was completed.

[Visual audit](../contracts/medical_display_audit_guide.md) evaluates the actual paper output. Catalog presence, successful rendering, layout QC and past golden images do not authorize scientific claims, artifact mutation, publication or submission.
