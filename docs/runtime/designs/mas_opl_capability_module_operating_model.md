# MAS / OPL 外挂能力模块运行模型

Owner: `MedAutoScience`
Purpose: `capability_module_operating_model`
State: `active_reference`
Machine boundary: 本文是 MAS 与 OPL 之间能力模块化的长期人读运行模型。机器真相继续归 `agent/`、`contracts/`、OPL Pack / Runway / Console / Vault surfaces、MAS domain handler、owner receipts、typed blockers、runtime artifacts 与具体 capability descriptor。

## 结论

MAS 应保持为医学研究与论文产出的集成总控，而不是把绘图、数据管理、文献管理、统计分析、投稿打包等重能力全部私有实现到仓内。长期形态是：

`MAS research intent -> current_owner_delta -> capability catalog -> module descriptor -> OPL prepare / install / run-context -> module invocation -> artifact refs / receipt -> MAS owner quality gate`

这个模型的目标是同时满足三件事：

- 保持 MAS 对医学研究 truth、论文质量、artifact authority、owner receipt 和 typed blocker 的唯一 authority。
- 让高质量绘图、数据治理、文献整理、统计建模、表格、投稿包等笨重能力可以独立升级、测试、发布和复用。
- 让 OPL 统一管理安装、依赖环境、版本锁、doctor、run-context、artifact refs 和跨 agent 能力复用，避免每个 domain agent 维护第二套基座。

外挂能力模块不是 MAS 的旁路，也不是替代 MAS 的领域大脑。它们提供可调用的专业能力和可审计输出；是否符合当前论文目标、是否能进入 manuscript / figure / package / publication truth，仍由 MAS owner surface 决定。

Stage 主提示词 / policy 与专业 specialist skill 分开维护。MAS 的 `write`、`review`、`figure`、`finalize`、`journal-resolution` 等 stage source 留在 MAS `agent/stages/`、`agent/prompts/`、route / knowledge / quality contract 和 overlay runtime projection；标准 OPL Agent 不需要长期 `stage-bound skill` 概念。专业 specialist skill 默认留在 owning domain / MAS pack 内置，只有当能力有独立依赖、gallery / fixture / receipt、跨 agent 复用和独立发布节奏时才外置。当前八个医学论文专业 Skill 归外部 `mas-scholar-skills` 单源维护，并作为 MAS 默认同步能力进入 workspace / quest 本地 `.codex/skills`。

## 为什么需要模块化

MAS 负责写论文是一项组合型复杂工作。单个子能力已经足够笨重，例如发表级绘图会涉及模板库、配色、版式、图页组织、R / Python / SVG / image generation 运行环境、视觉审计和 gallery 维护。如果这些能力全部成为 MAS 私有代码，长期会产生四个问题：

- MAS 仓库膨胀为多种专业工具的混合体，论文总控逻辑和工具实现互相牵制。
- 每个能力的依赖环境、测试、gallery、benchmark 和升级节奏不同，放在同一仓内会拖慢主流程。
- MAG、RCA、BookForge、OMA 等其他 OPL family agent 无法复用同一能力，只能复制实现。
- MAS agent 调用工具时面对大量底层入口，容易把模板、脚本、诊断工具或展示面误读成 authority。

模块化后的边界更清楚：MAS 只关心当前研究任务需要什么能力、给它什么输入、拿回什么 artifact / receipt、如何审查和纳入论文；能力模块只关心把自己的专业工作做到高下限、高可复现、高可维护。

## 推荐能力模块清单与外迁审计

下列 active 模块适合从 MAS 私有实现中抽离为 OPL 管理的专业 Skill-backed capability modules。它们首先是 descriptor、ref family、checklist、candidate handoff 和 owner-gate 合同；只有已经有稳定专业流程并需要 Codex 主动执行时，才进入 `mas-scholar-skills` active catalog。优先级只表示 MAS 侧清理/外迁顺序，不表示这些模块能写 MAS authority。

| 模块 | ScholarSkills id | Priority | 职责 | MAS 保留的 authority |
| --- | --- | --- | --- | --- |
| Literature Management | `mas-scholar-skills.lit` | `P0` | 检索、筛选、引用库、证据摘要、claim support map、related-work briefing | claim boundary、引用接受/拒绝、evidence ledger acceptance |
| Tables / Reporting | `mas-scholar-skills.tables` | `P0` | Table 1、模型性能表、补充表、报告规范 checklist、journal table style | table 是否进入当前论文、reporting guideline blocker、submission-facing authority |
| Biostatistics / Clinical Analysis | `mas-scholar-skills.stats` | `P0` | 生存分析、回归、校准、ROC、DCA、亚组、敏感性分析、table-ready result | medical question fit、结果是否进入 manuscript、analysis campaign closeout |
| Submission Packaging | `mas-scholar-skills.submit` | `P0` | 期刊格式、cover letter、highlight、graphical abstract、supplement、export package | submission readiness、current package authority、不可逆提交动作授权 |
| Manuscript Writing | `mas-scholar-skills.write` | `P1` | 结构化写作、section rewrite、journal voice、response-to-reviewer draft、claim tightening | manuscript truth、claim 接受/拒绝、publication_eval |
| Quality Review / AI Reviewer | `mas-scholar-skills.review` | `P1` | 独立审稿、publishability audit、claim/evidence/display consistency、revision routing | 最终 quality verdict、route-back owner decision、typed blocker |
| Medical Data Governance | `mas-scholar-skills.data` / `medical-data-governance` | `P1` | 数据资产 manifest、dataset manifest、dictionary/codebook、cleaning/normalization readiness、lineage、version impact、study binding、privacy/access、lifecycle guardrail 支撑 | source readiness verdict、study binding、不可逆 data mutation authorization |
| Medical Display / Figure | `mas-scholar-skills.display` | already governed separately | 证据图、设计图、图页组织、配色、gallery、视觉审计、发表级 figure 初稿 | figure 是否支撑 claim、是否进入论文、artifact mutation 授权、visual quality owner gate |

当前外置形态收敛为八个 active `mas-scholar-skills.*` 模块，均由外部 `mas-scholar-skills` 仓维护并同步给 MAS 的真实专业 Skill 支撑：`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-research-lit`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance`。`omics` 没有稳定 MAS 组学专业 workflow 前不占 active 合同位；通用 source / external-learning intake、source readiness、provider source discovery 和 source truth consumption 归 OPL Framework 或 MAS stage/source surface，不因“不是真 skill”而放进 MAS Scholar Skills 专业 Skill 库占位。MAS 只保留 `scientific_capability_registry` descriptor/readback bridge、refs-only owner-gate request 消费和医学论文 authority。机器 guard 由 `src/med_autoscience/scholarskills_capability_modules.py` 在各模块 descriptor 上暴露 classification / externalization readback，固定 `migration_target=mas-scholar-skills`、`mas_module_authority_owner=false`、`mas_second_truth_allowed=false` 和 `mas_may_write_scholarskills_authority=false`，防止后续把 MAS docs 或 registry readback 写成 ScholarSkills authority owner。

这个清单不是按当前已有代码反推，而是按医学论文生产链条的自然边界设计。模块数量可以扩展，但新增模块必须满足独立 bounded context、独立升级节奏、明确输入输出、明确 authority false flags 和至少一个可验证 gallery / fixture / receipt。

## 能力模块必须暴露的内容

每个可被 MAS 调用的外挂能力模块至少应暴露以下稳定面：

| 面 | 要求 |
| --- | --- |
| capability descriptor | 描述 capability id、版本、owner、适用场景、禁用场景、input / output schema、authority false flags |
| dependency profile | 描述 R / Python / system / model / font / TeX / browser 等依赖，由 OPL prepare 统一解决 |
| invocation entry | MCP tool、skill command、CLI action、render pack 或 generated surface；入口可多个，但 descriptor 只一份 |
| run-context contract | 说明必须绑定的 OPL prepared dependency receipt、profile fingerprint、workspace / artifact root |
| artifact refs | 输出只以 refs / manifest / checksum / preview refs 返回，不把大 body 塞进 control payload |
| execution receipt | 记录输入 fingerprint、依赖 receipt、运行命令、输出 refs、warnings、failure class、style/profile hash |
| quality evidence | 对绘图和表格至少有 gallery / golden / visual audit；对分析至少有 fixture / method check / reproducibility refs |
| authority boundary | 明确不能写 MAS study truth、owner receipt、typed blocker、publication verdict、current package 或 runtime queue |

模块实现可以很专业、很重，但入口必须薄、可发现、可审计。MAS agent 不应记忆某个脚本路径；它应通过 capability catalog 找到能力，通过 descriptor 知道怎样调用，通过 receipt 知道结果是否可消费。

## MAS 与能力模块的协作链路

MAS 调用外挂能力模块时采用六步链路：

1. MAS 从当前论文目标、stage goal、`current_owner_delta` 和 owner route 中形成 domain intent。
2. Capability resolver 在 catalog 中做 soft discovery，找到候选模块、适用理由、缺失输入和风险注记。
3. Invocation gate 做 hard contract check，确认 required refs、allowed writes、dependency run-context、workspace root、artifact target 和 authority boundary。
4. OPL 准备或绑定依赖环境，生成 dependency receipt / run-context，必要时 fail closed 到 `opl prepare` / `opl doctor`。
5. 能力模块执行，输出 artifact refs、manifest、preview、diagnostic 和 execution receipt。
6. MAS owner surface 审查输出是否满足当前论文 claim、quality gate、artifact authority 和 publication route；通过后才进入 manuscript / figure / table / package truth。

这条链路保持“高下限 + 高上限 + 低摩擦”的平衡：模块给出高质量起点和可复现运行面，AI executor 可以在 MAS 授权范围内做局部改造和审稿式打磨，但不能绕过 descriptor、依赖 receipt、artifact refs 和 MAS authority gate。

## Gallery 与人读面的角色

Gallery 是能力模块的重要验收面，但它不是机器 truth。它的职责是让人快速判断能力模块的默认审美、表达方式、覆盖范围和质量下限。

对于 Medical Display / Figure 模块，Gallery 应按“论文表达目的 + 图型类型”组织，而不是按历史 template id 或输入数据来源堆叠。推荐层次是：

- 证据图：生存/风险、模型性能、校准、决策曲线、效应量、分布、相关、降维、组学 landscape。
- 表格：Table 1、模型指标表、补充结果表、审稿/报告规范表。
- 设计图：workflow、graphical abstract、cohort flow、study design、机制示意、panel-level composition。
- 图页组织：multi-panel figure、shared legend、direct labels、clinical triptych、asymmetric genomics figure。

Gallery 应展示模块能稳定生成的代表性输出，并链接 descriptor / manifest / dependency profile / render receipt。它不应展示已退役模板、失败 fallback、同图型重复变体或只换输入名称的水分模板。

## ScholarSkills 全模块纵切

`ScholarSkills` 是 OPL 面向学术产出的能力品牌命名；MAS 侧消费的 active 机器模块 id 固定为 `mas-scholar-skills.<module>`，当前覆盖 `display`、`tables`、`stats`、`lit`、`write`、`review`、`submit` 和 `data` 八个模块。旧 `opl.scholarskills.<module>` id 只允许作为 registry payload 里的 `legacy_id_aliases` / `legacy_id_provenance` readback 保留，不再作为 active capability id 或 module id。MAS 只把这些模块注册为 `scientific_capability_registry` 可发现、可 resolve 的 descriptor/readback bridge；不复制一套 ScholarSkills truth，也不把模块执行器、依赖安装、artifact body mutation 或 OPL runtime queue 搬进 MAS。模块 classification 固定为：active module 均有外部真实专业 Skill 支撑；没有真实专业 Skill 的候选能力先留在 MAS / OPL 对应 owner surface，不在这里伪装成 active Skill。

当前状态是 `registry_summary_and_inventory_readback` + `active_module_descriptor_consumer` + `workspace_or_quest_local_codex_skill_install_readback` + `refs_only_execution_receipt_candidate_consumer` + `file_materialized_package_refs_consumer` + `candidate_artifact_owner_gate_request_readback`：MAS 可以通过 `summary` / `inventory` 低成本读出能力总数、family 分布、descriptor-only / refs-only 计数和 inventory 条目；也可以从 current owner delta 的 `capability_families`、capability id 或显式需求文本发现八个 active ScholarSkills 模块，读取 OPL descriptor、dependency profile、prepared run-context、artifact refs 与 execution receipt expectation refs，并按模块自己的 required ref family 校验 OPL execution receipt candidate。八个 active module 都共享 `input_fingerprint_ref`、`dependency_profile_ref` 和 `prepared_run_context_ref`；Display 追加 `render_cache_ref`、`artifact_manifest_ref`、`visual_audit_or_gallery_preview_ref`；Tables 追加 `table_manifest_ref`、`table_qc_ref`；Stats 追加 `analysis_manifest_ref`、`reproducibility_check_ref`；Lit 追加 `evidence_map_ref`、`citation_manifest_ref`；Write 追加 `draft_section_manifest_ref`、`source_trace_ref`；Review 追加 `reviewer_report_ref`、`route_back_ref`；Submit 追加 `package_manifest_ref`、`submission_checklist_ref`；Data 追加 `data_asset_manifest_ref`、`dataset_manifest_ref`、`data_dictionary_ref`、`codebook_ref`、`cleaning_normalization_readiness_ref`、`derived_variable_registry_ref`、`source_lineage_ref`、`source_readiness_receipt_ref`、`cohort_definition_lock_ref`、`version_diff_impact_ref`、`study_binding_ref`、`privacy_access_tier_ref`、`retention_guardrail_ref`、`storage_tier_ref`、`lifecycle_catalog_ref`、`owner_gate_handoff_ref`。

ScholarSkills 的执行可用性不来自 MAS 程序仓内的 `/med-autoscience/plugins/mas-scholar-skills`。执行面必须由 OPL Connect 把外部 `mas-scholar-skills` source repo 同步为病种 workspace 或 runtime quest 的本地 Codex skill；链路固定为 `MAS 初始化 / profile / doctor / bootstrap readback -> OPL Connect sync-skills -> workspace/quest .codex/skills -> Codex discovery -> specialist candidate refs -> MAS owner gate`：

```bash
opl connect sync-skills --domain mas-scholar-skills --scope workspace --target-workspace <workspace_root> --json
opl connect sync-skills --domain mas-scholar-skills --scope quest --target-quest <quest_root> --json
```

默认同步的本地 Codex skill 是 `mas-scholar-skills`、`medical-research-lit`、`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep` 和 `medical-data-governance`，分别落到 `<workspace_root>/.codex/skills/<skill_id>` 或 `<quest_root>/.codex/skills/<skill_id>`。MAS `profile`、`doctor` 与 `workspace bootstrap` 只暴露 `scholarskills_local_install` readback、命令 argv、target skill path、runtime quest target template 和 no-authority boundary；它们不执行安装、不复制 plugin、不写 Yang authority、runtime authority、owner receipt、typed blocker、human gate、publication eval、controller decision、runtime queue 或 provider attempt。MAS 程序仓若存在 `plugins/mas-scholar-skills`，只能视为 dev/review mirror 或退役来源，不是论文执行可用的默认 source。

MAS Scholar Skills 的 source of truth 在外部 `mas-scholar-skills` repo：聚合入口是 `skills/mas-scholar-skills/SKILL.md`，真实专业 Skill 是 `skills/medical-research-lit/SKILL.md`、`skills/medical-manuscript-writing/SKILL.md`、`skills/medical-manuscript-review/SKILL.md`、`skills/medical-figure-design/SKILL.md`、`skills/medical-statistical-review/SKILL.md`、`skills/medical-table-design/SKILL.md`、`skills/medical-submission-prep/SKILL.md` 和 `skills/medical-data-governance/SKILL.md`，模块 catalog snapshot 是 `contracts/scholar-skills-capability-modules.json`。MAS 的 `write`、`review`、`figure`、`data/cohort` 等 stage 主提示词留在 MAS overlay / stage owner surface，只消费外部专业 skill 和 refs-only catalog；不得在 MAS 侧手工维护第二套模块列表、专业 skill 正文、gallery inventory、dependency truth 或 runtime readiness 结论。若外部 contract 更新，MAS 侧只更新消费边界、链接和不越权读法，不能把同步后的 descriptor/readback 写成 owner acceptance。

### 罕见专科外部技能库策略

八个核心专业 Skill 是 MAS 的默认科学技能面。Codex discovery helper `external-scientific-skills` 只把罕见专科缺口路由到 OPL Connect external-skills；它是薄入口，不承载 K-Dense 全量能力或第二技能库，也不能让 K-Dense、外部 README 或同步目录成为 MAS source of truth。

允许触发 external-skills 的条件必须可追溯到当前 work unit：用户显式命名工具/数据库，核心 Skill route-back 指出缺口，stage policy 判断八个核心 Skill 无法覆盖，或联网、云计算、敏感数据、外部凭据路径需要 policy / approval。典型缺口包括 `scanpy` 单细胞分析、`pydeseq2` 差异表达、pathway enrichment、Nextflow 工作流、RDKit 化学信息学、PyHealth 医疗 ML 等。

调用链只允许 `search -> inspect -> sync`：先搜索候选外部 Skill，检查 descriptor、依赖、权限、数据路径、输出 refs 和 authority false flags，再把选中的 specialist 同步到 workspace / quest。同步后的 specialist 只能产生 refs-only candidate、execution receipt candidate、owner-gate request 或 route-back hint；MAS owner gate 仍决定是否接受为论文 truth、artifact authority、quality verdict、typed blocker、human gate 或 `current_package` 变化。

### K-Dense BYOK 可复用模式

K-Dense BYOK 对 MAS / OPL 的价值是产品和运行模式参考，不是 runtime 迁移目标。MAS 不接入 Pi SDK backend、不依赖 K-Dense app、不复制它的 skill / workflow / database catalog，也不把它的 OpenRouter Fusion panel 当成 reviewer gate。Codex CLI 仍是 OPL harness；K-Dense 相关输出通过 `build_kdense_byok_pattern_advisory`、`build_kdense_byok_catalog_surfaces` 和 `build_kdense_byok_runtime_surfaces` 进入 refs-only / no-authority candidate、recipe、catalog 或 briefing。

`contracts/kdense_byok_external_intake.json#/repo_native_projection_builders` 固定当前 repo-native builder 边界。Catalog projection builder 覆盖 Stagecraft recipe catalog、Atlas source-ref catalog、Codex specialist roster 和 workspace artifact preview；runtime projection builder 覆盖 attempt replay / lab notebook、cost ledger、connector doctor、remote compute receipt schema、human-gate form schema、Console activity / timeline 和 Fusion watch-only briefing。两者都是 MAS 可消费的 projection surface，不是 K-Dense runtime、本地 web app、外部 connector credential、OPL App UI、owner receipt、paper progress、publication readiness 或 `current_package` authority。

| K-Dense source pattern | OPL landing owner | MAS 使用方式 |
| --- | --- | --- |
| 326 workflow templates | OPL Stagecraft | 抽象成 recipe catalog 候选：stage goal、required inputs、placeholder schema、suggested capability hints、expected artifact refs 和 stop condition。Stagecraft 只把 recipe 作为当前 owner delta 的 JIT route context，不新增 MAS selector 或 workflow truth。 |
| 229 database refs | OPL Atlas / Source | 抽象成 source-ref candidate catalog：数据库 id、领域、类别、URL、credential / policy notes 和 source readiness precheck。MAS 只把它作为 source discovery 输入，source readiness verdict 仍由 MAS owner surface 产出。 |
| 21 scientific specialists | Codex specialist roster / reviewer lanes | 映射为可命名的 specialist lane，例如 citation、statistics、methodology、reproducibility、peer-review。执行与审阅必须保持独立 invocation / context / receipt；specialist report 只是 reviewer/auditor candidate。 |
| file tree、file preview、bioinformatics preview、LaTeX editor、PDF viewer | OPL Workspace / Ledger / Console | Workspace 管文件拓扑和 upload/download，Ledger 管 artifact refs、manifest、checksum、compile log，Console 管 preview 和 operator drilldown。文件存在、PDF render 或 LaTeX compile 不等于 artifact authority。 |
| cost ledger / spend cap | OPL Ledger / Console | agent、specialist、compute 成本分账为 budget receipt，Console 只展示预算和风险；预算信息不能替代研究质量、paper progress 或 owner gate。 |
| interview form | MAS human-gate schema / OPL Console | 结构化问题、推荐选项、自由文本和附件可作为 human-gate 输入 shape；只有 MAS human gate / owner route 消费后才改变 truth 或 route。 |
| MCP / Modal hooks | OPL Connect / Runway | Connect 管 MCP trust、secret scope、tool health；Runway 管 remote execution receipt、file-in/out、timeout、cost 和 fail-open / fail-closed policy。MAS 不把这些 connector 写成 domain authority。 |
| OpenRouter Fusion | watch-only reviewer briefing | 仅用于多模型 judgment 的提示形态参考；因为无本地工具、不可复现且 panel source 不完整，不能关闭 independent reviewer gate、quality verdict 或 publication readiness。 |

Display gallery 在 ScholarSkills 中只作为 compact human review package。允许进入 workspace / quest local install 或对外 review 索引的 refs 是：

- `gallery/medical-display/medical_display_gallery.pdf`
- `gallery/medical-display/medical_display_gallery_reference.md`
- `gallery/medical-display/display_pack_gallery_status.md`
- `gallery/medical-display/display_pack_gallery_quality_audit.md`
- `gallery/medical-display/gallery_manifest.json`
- `gallery/medical-display/gallery_snapshot.json`

这些 refs 用于人工快速判断默认图型覆盖、审美下限、quality-audit notes 和 manifest/snapshot provenance。它们不是 publication-ready、visual audit receipt、owner acceptance、artifact authority 或 paper truth。workspace / quest local install 不复制 MAS `outputs/display-pack-gallery/` build workspace、render caches、single-figure PNG/SVG/HTML exports、dependency locks、run-context files、临时 layout sidecar 或其他大规模 gallery 中间产物；需要真实论文图件时，必须回到 MAS Display Pack / paper-local artifact workflow 和 owner gate。

MAS consumer 接受 OPL candidate envelope 内的 `execution_receipt_refs` 嵌套对象，也接受少量兼容 alias，例如 `dependency_prepared_receipt_ref` 映射到 `dependency_profile_ref`。对于 OPL `materialize` 产生的文件化 package，MAS owner-consumption helper 还接受明确文件输入：`execution_receipt_path` 指向 `execution_receipt_candidate.json`，或 `materialized_package_manifest_path` 指向包含 `execution_receipt_candidate_path` / `artifact_manifest_path` / `written_files` / `sha256` / `authority_flags` 的 `manifest.json`。MAS 只读取这些 JSON，把 `artifact_manifest_path` 映射到对应模块的 manifest ref family，并把 `written_files`、`sha256`、authority false flags、源文件路径和规范化后的 `candidate_artifacts` 记录为 `materialized_package_consumption` readback；MAS consumer 自身 `mas_consumer_written_files=[]`。candidate artifact readback 只携带 `kind`、`ref`、`sha256`、`authority=false`、readiness notes 和 missing inputs；若 package 里包含 artifact body，MAS 可计算 body sha256 作为候选指纹，但 owner gate request 不把 body 升格为 MAS artifact authority。repo-native CLI 入口是：

```bash
medautosci scientific-capability-registry \
  --mode owner-consumption \
  --capability-id mas-scholar-skills.<module> \
  --current-owner-delta-json '<json>' \
  --materialized-package-manifest-path <opl-package>/manifest.json
```

该 CLI 只调用同一 owner-consumption evidence builder，成功时输出 refs-only evidence；当文件化 package 的 execution receipt refs 完整、authority flags 全部为 false、且 `written_files` 没有 MAS authority 写入碰撞时，输出会附带 `owner_gate_request`、`owner_gate_handoff` 和 `required_owner_response_shapes`。这些字段只是给 MAS 后续 owner surface 审查的机器 readback/request 层，`non_authoritative_request=true`，并逐个列出 candidate artifact 的 `kind`、`ref`、`sha256`、`authority=false`、readiness notes 和 missing inputs，方便 owner 后续接受、拒绝或 route back；它们显式保持 `counts_as_paper_truth=false`、`counts_as_owner_receipt=false`、`can_authorize_publication_readiness=false`、`can_write_owner_receipt=false` 和 `can_write_typed_blocker=false`。module id mismatch、truthy package authority flag、truthy candidate artifact authority claim 或 forbidden `written_files` 会 fail closed 并非零退出，不能生成 owner gate request。

文件化消费路径必须 fail closed：`authority_flags` 中任何 MAS authority 写入能力为 `true`，或 `written_files` 声称写入 `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、paper/package truth、owner receipt、typed blocker 或 human gate，均不能被包装成 owner-consumption evidence。该消费路径只输出 `execution_receipt_status`、observed / missing ref families 和 refs-only owner-consumption evidence；即使 refs 齐全，也只表示候选 artifact evidence 可被 MAS owner gate 后续审查，不能写成 full runtime ready、paper progress、publication readiness、current package authority 或 owner receipt。候选图、表、统计结果、文献证据图谱、文稿段落、review 报告、投稿包和数据清单只有经过 MAS owner gate 消费后，才可能进入论文 truth。

### OpenScience local-first workspace 可复用模式

OpenScience main `f120290` 对 MAS / OPL 的价值是 local-first research workspace pattern，不是 runtime 迁移目标。当前已落地 contract policy、runbook 和 `build_openscience_artifact_provenance_advisory` refs-only sidecar worker；MAS 不接入 OpenScience Electron / WebUI runtime，不复制它的 skill catalog，不把 `science_artifact` MCP 当作 MAS truth、artifact authority、owner receipt、typed blocker、publication gate 或 source readiness verdict。可学习内容必须落在基座 / Stage / 专业 Skill / 工具的明确 owner 上：

| OpenScience pattern | OPL substrate owner | MAS / ScholarSkills owner | 边界 |
| --- | --- | --- | --- |
| project-local artifact graph | Vault / Workspace / Ledger | Stage / Display / Reviewer 消费 artifact/source refs | graph 只给 refs、lineage、hash 和 provenance；不能写 artifact body、paper body 或 artifact authority。 |
| `claimType` + `graphWarnings` | Pack / Stagecraft 负责 check descriptor 与 invocation policy | Quality / Reviewer / ScholarSkills review 负责 refs-only claim-warning check | 推荐第一落点：claimType + graphWarnings refs-only check；warning 只能生成 reviewer briefing、route-back candidate 或 evidence gap，不直接生成 quality verdict。 |
| annotation-to-source regeneration | Workspace / Ledger 持 annotation refs、source locator 和 regeneration receipt | Stage / Source / Quality 把 annotation 还原成 source/data/evidence repair hint | 推荐第一落点：annotation-to-source-regeneration；只有当前 delta route-required ref 涉及 source / data / evidence 时才可能升级 blocker candidate。 |
| project-local ledger pointer / hash | Vault / Ledger / Console | Stage / Reviewer 只读取 pointer/hash provenance | 推荐第一落点：project-local ledger pointer/hash；hash 证明 candidate provenance，不证明 owner acceptance、paper progress 或 current package freshness。 |
| skill pack governance | Pack / Connect / Stagecraft | ScholarSkills 只消费专业 skill descriptor / no-authority flags | 不复制 OpenScience skill catalog；Pack / Connect 只吸收 dependency、permission、allowed scope 和 stage use policy。 |
| native viewer / workspace affordance | Console / Workspace | Display / Reviewer 可读取 watch-only preview refs | viewer 只是 operator display pattern；不接入 Electron / WebUI，不把 preview 当 publication readiness、source readiness 或 visual quality owner gate。 |

Progress-first 读法固定为：OpenScience advisory、worker、projection 或 native viewer 缺失 / 失败，不阻断 ordinary MAS owner action。只有当前 delta 的 route-required ref 涉及 source / data / evidence，或 candidate 指向 forbidden write、independent reviewer、publication gate、human gate，才允许形成 typed blocker candidate；正式 typed blocker 仍由 MAS owner surface、OPL Stage Transition Authority、independent reviewer / auditor、human gate 或 typed blocker materializer 签出。

### ScholarSkills acceptance matrix

| Acceptance item | Capability-surface status | Evidence surface | Remaining live / authority tail |
| --- | --- | --- | --- |
| registry summary / inventory readback | `done_for_repo_operability_surface` | `scientific_capability_registry summary / inventory` 和 MCP `scientific_capability_registry` modes 暴露 `mas_scientific_capability_registry_summary`、`mas_scientific_capability_inventory`、capability ids、family/counts、refs-only / descriptor-only 标记和 no-authority boundary，方便 OPL App / Agent Tool Arsenal 做低运维发现。 | 只证明 MAS repo capability inventory 可读；不证明外部 skill 已安装、OPL provider 已执行、package 已生成、owner gate 已接受或任何论文 truth 已变化。 |
| 八个 active module descriptor discovery | `done_for_repo_capability_surface` | `scientific_capability_registry index / resolve` 可发现 `mas-scholar-skills.display`、`tables`、`stats`、`lit`、`write`、`review`、`submit`、`data`，并返回 module descriptor、required ref families、dependency/run-context refs 和 no-authority boundary；非 Display descriptor 还返回 `externalization_guard`，声明 migration priority、`mas-scholar-skills` target 和 MAS 非 authority owner。 | 不证明 OPL Pack 已安装依赖、Runway 已执行 provider、Console 已展示 live run、MAS 持有 ScholarSkills truth，或任何模块产物被 MAS owner 接受。 |
| workspace / quest local Codex skill install readback | `done_for_mas_command_shape_and_readback` | MAS `profile_to_dict`、`doctor`、`workspace bootstrap` 与 `scientific_capability_registry` 暴露 `scholarskills_local_install`，给出 workspace / quest `opl connect sync-skills --domain mas-scholar-skills` argv、`mas-scholar-skills`、`medical-research-lit`、`medical-manuscript-writing`、`medical-manuscript-review`、`medical-figure-design`、`medical-statistical-review`、`medical-table-design`、`medical-submission-prep`、`medical-data-governance` 的目标 `.codex/skills/<skill_id>` path / template、外部 source repo ref 和 no-authority flags。 | 只证明 MAS 侧 install/readback contract 已落地；不证明 OPL worker 已实现 sync、skill 已实际安装、provider 已运行、产物已生成或 MAS owner gate 已接受。 |
| Display gallery compact review package | `done_for_human_review_refs_boundary` | `mas-scholar-skills` 传播 compact gallery review refs：PDF、reference、status、quality audit、manifest、snapshot；MAS `docs/delivery/medical-display/examples/` 只保留 paper-local example / E2E boundary docs，`outputs/display-pack-gallery/` 是可再生成本地 build output。 | Gallery review refs 不证明 publication readiness、artifact authority、visual audit receipt、paper truth 或 owner acceptance；workspace / quest install 不复制大规模 gallery build workspace、render caches、单图 exports、dependency locks 或 run-context files。 |
| refs-only execution receipt candidate consumer | `done_for_refs_only_receipt_consumer` | owner-consumption helper 校验 module-specific required ref families、execution receipt expectation refs、authority false flags、missing refs 和 fail-closed collision。 | 不写 owner receipt、typed blocker、human gate、publication eval、controller decision、paper truth、artifact authority 或 `current_package`。 |
| file-materialized package refs consumer | `done_for_file_package_consumption` | `--materialized-package-manifest-path` 可读取 OPL materialized package manifest、`execution_receipt_candidate.json`、artifact manifest path、`written_files`、`sha256` 和 authority flags，并归一为 `materialized_package_consumption` readback。 | 不声明 package body 是 MAS artifact authority；只把 refs 和 hashes 交给后续 owner gate。 |
| candidate artifact owner-gate request | `done_for_owner_gate_request_readback` | 完整 refs-only package 会输出 `owner_gate_request`、`owner_gate_handoff`、candidate artifact kind/ref/sha256/readiness notes、required owner response shapes 和 no-forbidden-write proof。 | 这只是 MAS owner gate 的非权威 request/handoff；真实 owner acceptance、route-back、stable typed blocker、human gate 或 quality receipt 仍需 live owner surface。 |
| PaperMission submission milestone candidate | `done_for_non_authority_candidate_package_surface` | `paper-mission package-candidate` 可物化 `owner_consumption_request.json`、`owner_blocker_packet.json`、`submission_milestone_checklist.json`、`paper_facing_candidate_delta.json` 和 5 个 paper-facing candidate artifact JSON；`milestone_kind=submission_milestone_candidate`，`can_claim_submission_ready=false`。 | 可计为候选论文产物能力面；不能声明 submission-ready、publication-ready、current package、owner receipt、typed blocker authority file、human gate 或 governed paper progress。 |

## 与 OPL 十大品牌模块的关系

外挂能力模块不是 OPL 的第十一个品牌模块。它们是 OPL 十大品牌模块共同管理和使用的 capability 实例。品牌模块定义 framework 的 bounded contexts；能力模块是被这些 bounded contexts 管理、安装、发现、调用、审计和改进的专业资产。

| OPL 品牌模块 | 在能力模块体系中的职责 |
| --- | --- |
| OPL Charter | 固定 no-second-truth、authority false flags、domain owner boundary 和不可越权原则 |
| OPL Atlas | 持 capability catalog、领域标签、适用场景、fit metadata、gallery index 和发现入口 |
| OPL Workspace | 管理 workspace / source / artifact root、locator、stage artifact unit 和文件拓扑 |
| OPL Pack | 持 descriptor、ABI、pack compiler、安装包、版本锁、validate / doctor / generated surfaces |
| OPL Stagecraft | 决定 stage 内什么时候使用能力、如何把 capability recipe 放进 stage policy 和 agent prompt |
| OPL Runway | 执行 durable invocation、绑定 run-context、处理 retry / dead-letter / fail-open / fail-closed route |
| OPL Ledger | 保存 refs-only evidence、artifact manifest、execution receipt、lineage、audit trail 和 provenance |
| OPL Console | 向 operator / MAS agent 展示可用能力、调用状态、doctor 缺口、gallery 和 owner next action |
| OPL Foundry Lab | 对能力模块做 benchmark、visual audit、regression、外部学习吸收和升级评估 |
| OPL Connect | 接入外部 MCP、skill、CLI、GitHub 项目、模型服务、浏览器或第三方工具 |

因此，这次构造方式确实是 OPL 基座能力提升，但提升的是“跨 domain agent 的 capability substrate”，不是新增一个并列品牌。OPL Pack / Atlas / Stagecraft / Runway / Ledger / Console / Connect / Workspace / Foundry Lab / Charter 分别承担一部分，组合后让 MAS、MAG、RCA、BookForge 等 agent 都能调用同一批高质量专业能力。

## MAS 不应外置的内容

不是所有东西都应该 skill / MCP 化。以下内容必须留在 MAS domain authority 内：

- study truth、quest truth、paper mission truth。
- publication quality verdict、AI reviewer owner verdict、submission readiness。
- owner receipt、typed blocker、human gate、route-back owner decision。
- artifact mutation authorization、current package authority、publication_eval / controller_decisions truth。
- source readiness verdict、memory body accept / reject、claim boundary 和医学解释。

能力模块可以生成候选图、候选表、候选分析、候选文本、候选 review、候选 package；但这些候选只有经过 MAS owner gate 才能成为当前论文 truth。

## 迁移原则

从当前 MAS 仓迁移到外挂能力模块时，按以下规则处理：

- 先按自然能力边界抽离，不按历史目录或 template id 抽离。
- 有明确专业价值、独立依赖、独立 gallery / benchmark 或跨 agent 复用价值的模块，优先外挂化。
- 只服务 MAS authority 的薄函数保留在 MAS，例如 receipt signer、typed blocker materializer、publication gate owner adapter。
- 旧模板、旧脚本、旧 wrapper 若没有 active descriptor、gallery evidence、receipt 或迁移价值，直接退役，不保留兼容别名。
- 新能力默认通过 OPL dependency environment substrate 安装和运行；模块自身不维护私有安装、修包或 host fallback。
- 文档只说明边界和导航；机器可调用 truth 必须进入 descriptor、contract、catalog、receipt 或 generated surface。

## 验收标准

该模型真正落地时，至少应能证明：

- MAS agent 可以从当前论文 intent 发现一个能力，而不是记忆脚本路径。
- OPL 可以安装或准备该能力的依赖环境，并返回稳定 run-context。
- 缺依赖、profile mismatch、缺 required refs 或越权写入时，调用 fail closed 到明确 owner 或 OPL doctor。
- 能力模块输出 artifact refs、manifest、receipt 和 gallery preview，而不是只写散落文件。
- MAS owner gate 可以消费或拒绝该输出，并留下 owner receipt、typed blocker、route-back 或 quality review refs。
- 同一能力可被其他 OPL family agent 复用，而不需要复制 MAS 私有实现。

这组标准是能力模块化的完成口径。单纯把代码移到另一个目录、把模板放进 skill、或在文档里列一个 capability 名字，都不构成功能落地。
