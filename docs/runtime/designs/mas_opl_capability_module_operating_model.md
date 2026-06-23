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

## 为什么需要模块化

MAS 负责写论文是一项组合型复杂工作。单个子能力已经足够笨重，例如发表级绘图会涉及模板库、配色、版式、图页组织、R / Python / SVG / image generation 运行环境、视觉审计和 gallery 维护。如果这些能力全部成为 MAS 私有代码，长期会产生四个问题：

- MAS 仓库膨胀为多种专业工具的混合体，论文总控逻辑和工具实现互相牵制。
- 每个能力的依赖环境、测试、gallery、benchmark 和升级节奏不同，放在同一仓内会拖慢主流程。
- MAG、RCA、BookForge、OMA 等其他 OPL family agent 无法复用同一能力，只能复制实现。
- MAS agent 调用工具时面对大量底层入口，容易把模板、脚本、诊断工具或展示面误读成 authority。

模块化后的边界更清楚：MAS 只关心当前研究任务需要什么能力、给它什么输入、拿回什么 artifact / receipt、如何审查和纳入论文；能力模块只关心把自己的专业工作做到高下限、高可复现、高可维护。

## 推荐能力模块清单

下列模块适合从 MAS 私有实现中抽离为 OPL 管理的 capability modules。它们可以是 skill、MCP server、display pack、domain pack、CLI bundle 或多入口组合，但都应暴露统一 descriptor 与 receipt。

| 模块 | 职责 | MAS 保留的 authority |
| --- | --- | --- |
| Medical Display / Figure | 证据图、设计图、图页组织、配色、gallery、视觉审计、发表级 figure 初稿 | figure 是否支撑 claim、是否进入论文、artifact mutation 授权、visual quality owner gate |
| Data Management | 数据资产 release、manifest、schema、lineage、脱敏、source readiness 支撑 | 数据是否可用于当前 study、source readiness verdict、study binding、不可逆 mutation 授权 |
| Literature Management | 检索、筛选、引用库、证据摘要、claim support map、related-work briefing | claim boundary、引用是否支撑论文论证、evidence ledger 接受/拒绝 |
| Biostatistics / Clinical Analysis | 生存分析、回归、校准、ROC、DCA、亚组、敏感性分析、table-ready result | 统计结论是否符合医学问题、结果是否进入 manuscript、analysis campaign closeout |
| Omics / Bioinformatics | 单细胞、bulk RNA、CNV、突变、通路、富集、降维、marker / landscape 等 workflow | 生物学解释、source readiness、claim restraint、result-to-figure / result-to-text gate |
| Tables / Reporting | Table 1、模型性能表、补充表、报告规范 checklist、journal table style | table 是否进入论文、reporting guideline blocker、submission-facing authority |
| Manuscript Writing | 结构化写作、section rewrite、journal voice、response-to-reviewer draft、claim tightening | 论文 truth、AI reviewer verdict、publication_eval、current package authority |
| Quality Review / AI Reviewer | 独立审稿、publishability audit、claim/evidence/display consistency、revision routing | 最终 quality verdict、route-back owner、typed blocker、human/PI gate |
| Submission Packaging | 期刊格式、cover letter、highlight、graphical abstract、supplement、export package | submission readiness、current package authority、不可逆提交动作授权 |
| External Method Skill Intake | 从成熟开源项目、论文方法、代码库、手工模板中学习并形成可调用模块 | 是否纳入 MAS ordinary path、是否成为 default capability、authority false flags |

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

## ScholarSkills / Scholar Display 首个纵切

`ScholarSkills` 是 OPL 面向学术产出的能力品牌命名；在 MAS 内的第一个消费纵切是 `Scholar Display`，机器模块 id 固定为 `opl.scholarskills.display`。MAS 侧只把它注册为 `scientific_capability_registry` 可发现、可 resolve 的 descriptor/readback bridge，并通过既有 Display Pack surface 复用 `contracts/display-pack-contract.v2.json`、`display_pack_agent` 与 display artifact refs；不复制一套 ScholarSkills truth，也不把 Display Pack 运行逻辑搬进新的 registry。

当前状态是 `first_vertical_descriptor_consumer` + `refs_only_execution_receipt_candidate_consumer`：MAS 可以从 current owner delta / capability family 发现 Scholar Display，读取 OPL dependency profile、prepared run-context、render cache、doctor 与 execution receipt expectation refs，并按 `input_fingerprint_ref`、`dependency_profile_ref`、`prepared_run_context_ref`、`render_cache_ref`、`artifact_manifest_ref`、`visual_audit_or_gallery_preview_ref` 校验 OPL Scholar Display execution receipt candidate 的 required ref family。该消费路径只输出 `execution_receipt_status`、observed / missing ref families 和 refs-only owner-consumption evidence；即使 refs 齐全，也只表示候选 artifact evidence 可被 MAS owner gate 后续审查，不能写成 full runtime ready、paper progress、publication readiness、current package authority 或 owner receipt。候选图、gallery preview、display lock、render receipt 和 visual audit receipt 只有经过 MAS owner gate 消费后，才可能进入论文 truth。

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
| OPL Vault | 保存 refs-only evidence、artifact manifest、execution receipt、lineage、audit trail 和 provenance |
| OPL Console | 向 operator / MAS agent 展示可用能力、调用状态、doctor 缺口、gallery 和 owner next action |
| OPL Foundry Lab | 对能力模块做 benchmark、visual audit、regression、外部学习吸收和升级评估 |
| OPL Connect | 接入外部 MCP、skill、CLI、GitHub 项目、模型服务、浏览器或第三方工具 |

因此，这次构造方式确实是 OPL 基座能力提升，但提升的是“跨 domain agent 的 capability substrate”，不是新增一个并列品牌。OPL Pack / Atlas / Stagecraft / Runway / Vault / Console / Connect / Workspace / Foundry Lab / Charter 分别承担一部分，组合后让 MAS、MAG、RCA、BookForge 等 agent 都能调用同一批高质量专业能力。

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
