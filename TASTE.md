# TASTE

Owner: `gaofeng`
Purpose: 统一长期协作项目的维护开发判断偏好。
State: `active_preference`
Machine boundary: 本文是人读协作偏好；项目事实、接口约束、验收结论和机器真相以源码、contracts、docs、runtime 输出和 repo-native 验证为准。

## 读法

`TASTE.md` 记录长期判断标准，帮助 `AGENTS.md`、项目文档和后续迭代保持一致。它适合放在长期维护的应用、agent、工具、服务、文档或研究项目根目录。

`AGENTS.md` 定义 agent 工作方式；`TASTE.md` 定义维护开发偏好；项目 `docs/`、`contracts/` 和源码定义项目事实。跨项目复用时，本文保持简短稳定，各仓文档补充本地边界。

## 总则

上位原则是 `AI-first / executor-first / purpose-first`：系统为最强执行者提供清晰目标、上下文、工具、权限、质量门、交接边界和可验证输出，让模型、工具和知识面的进步直接转化为产出能力。程序负责搭台、约束边界和承载审计；开放式推理、创作、评审、诊断和修订由合适的执行者完成。研究、写作、产品和交付型工作必须把实质推进作为一等目标：先产出可审阅、可接力、可验证的下一版结果，再用评审、质量门和人工决策拉高质量。

OPL 持有通用 lifecycle substrate：stage attempt、queue、retry/dead-letter、resume、attempt ledger、locator/index、restore/retention shell、generic memory/artifact transport、observability 和 App/workbench shell。Domain agent 持有领域真相与不可声明化 authority；对 MAS 这类医学研究 agent，study truth、quality verdict、publication route、artifact mutation、memory accept/reject、source readiness、owner receipt 和 typed blocker 必须留在 MAS。通用 substrate 可以运输、索引和展示 refs，不能把 transport / lifecycle / ledger evidence 升格成医学 authority。

## 原则

1. **AI 执行优先**

   复杂知识工作由 agent executor 完成。系统提供清晰目标、上下文、工具、权限、质量门和交接边界，让更强模型、更好 prompt、更好 skill 和更完整知识面直接转化为能力提升。

2. **目的优先，反推设计**

   架构、流程、文档、接口和读面都先从用户要达成的目的反推：要产出什么可用结果，谁负责下一步，缺什么证据、决策、交接或阻塞说明。现有目录、历史实现、工具偏好、状态面板、中间指标和兼容入口只能作为迁移输入，不能反过来定义长期设计。凡不能直接服务目的、不能减少协作成本、也不能产出可验证下一步的设计面，应优先合并、收薄、下沉到诊断细节、归档或删除。

3. **阶段推进任务**

   大型任务以阶段作为可观察、可恢复、可审计的推进单位。阶段应足够粗，能让执行者在一次工作尝试内完成一个真实工作包，而不是把写作、实现、评审、修订和交接拆成互相等待的小状态链。每个阶段明确目标、输入输出、工具、知识、质量门、交接方式和验收记录；阶段收尾必须留下实质结果、交接记录、阻塞说明、人工决策或停止决策，不能只留下状态刷新、解释文本或下一轮同义返工。

4. **进度优先，质量跟随**

   默认优化目标是最快形成下一版可评审、可使用或可交接的结果。质量门用于发现差距、限制高风险操作和决定下一次修订方向，不能把系统困在无限预检、审查、状态解释或阻塞分类循环里。除安全、合规、权限、人工决策和不可逆变更外，质量问题应尽量转化为带范围、预算和验收标准的后续修复工作，而不是阻断所有前进。用户可见进度必须优先统计产物、分析、决策、交付或交接的实质变化；工具维护、索引刷新、投影整理和状态核算作为运维进展单独列账。

5. **函数承担边界职责**

   程序函数承担校验、物化、索引、路由、持久化、格式转换、权限检查、投影和辅助执行职责。审稿、质量判断、路线判断、修订生成和交付裁决由明确的评审、决策或质量门流程承接，避免把开放式判断藏进零散函数和隐式后处理。

6. **目标态快速落地**

   目标明确时，按目标架构快速、干净、可回退地推进。能直接完成一版产物或一个明确交接增量时，优先让执行者完成，不先堆控制面、状态枚举或中间证明。行为保持一致，diff 保持小而清楚；结构治理、文档收敛、命名清理、接口收薄和明确迁移优先完成，长周期证据作为独立尾项管理。

7. **责任边界明确**

   项目、模块、数据、产物、权限、决策、发布和质量结论都应有明确责任方。共享能力尽量上收到共同层，领域判断和交付裁决留在对应 owner；展示、路由、汇总和审计面只承接投影职责，不能变成第二真相源。

   历史系统的 resident daemon、GitOps、interactive artifact UX 或 WebUI 体验可以作为 provenance、fixture 或 OPL-owned product direction 退役；不能因此降低 domain agent 的核心科研审计能力。研究 evidence pack、negative / failed-path ledger、decision trace、artifact lineage / reproducibility refs、owner receipt 和 stable typed blocker 是研究推进的最低审计链。合同落地之后，下一层完成口径必须推进到 read-model 能投影这些 ref family、schema validation 能 fail closed、真实 canary 能给出可审计证据；不能把“contract landed”长期停留为完成声明。

8. **单一来源派生多入口**

   关键动作、阶段、描述符、合同和路由元数据由 canonical source 统一表达。命令行、API、UI、自动化、文档、报表和状态面从同一来源派生，保持接口、文档和投影一致。

9. **历史面及时退役**

   当前责任面已替代的旧模块、旧入口、别名、facade、wrapper、兼容测试和过时文档，在迁移条件成立后进入删除、归档或退役标记。历史信息保留为来源说明，当前入口保持单一。

10. **薄入口与清晰结构**

   入口保持稳定而薄，复杂逻辑进入按职责命名的模块。源码、测试和文档表达真实边界；目录结构让维护者快速识别语义包、合同、核心实现、适配层、诊断和历史材料。

11. **文档治理分层**

   文档服务导航、边界、状态、决策和交接。每份长期文档都有明确 owner、purpose、state 和 machine boundary；README、docs、AGENTS、TASTE、contracts 各自持有单一职责。

12. **最小充分验证**

    验证强度与风险匹配。行为不变、文档治理、结构收薄和命名清理采用最小充分验证；生产声明、权限边界、数据或产物写入、发布、质量结论和跨系统责任边界使用更重的回执、截图、发布记录、责任链或长时间运行证据。验证不能变成反进度机制：非终局阶段优先验证“是否产生了可接力结果和明确下一责任方”，终局 readiness 才要求完整质量/发布证据。

## 迁移

复制到相关项目时，通常只调整 `Owner`、项目名和少量本地例子。原则数量按实际需要确定。项目如需局部差异，应在本仓 `docs/decisions.md`、`docs/invariants.md`、contract 或更深层 `AGENTS.md` 写清适用范围。

<!-- OPL_FLOW_MANAGED_START -->
OPL Flow managed surface: maintenance_preferences
Plugin: opl-flow
Plugin version: 0.1.0
Profile pointer: contracts/opl-native-profile.json
本块只声明 OPL Flow 工作流 profile 指针；repo-specific 规则、项目事实、contracts、source、tests 和 runtime 输出继续归本仓既有 owner。
请只通过 OPL Flow repo_profile sync 更新本块；本块外内容由目标 repo 自己维护。
<!-- OPL_FLOW_MANAGED_END -->
