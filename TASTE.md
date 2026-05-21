# TASTE

Owner: `gaofeng`
Purpose: 统一 OPL family 与相关项目的维护开发判断偏好。
State: `active_preference`
Machine boundary: 本文是人读协作偏好；项目事实、接口约束、验收结论和机器真相以源码、contracts、docs、runtime 输出和 repo-native 验证为准。

## 读法

`TASTE.md` 记录长期判断标准，帮助 `AGENTS.md`、项目文档和后续迭代保持一致。它适合放在 OPL Framework、App、Foundry Agent、shell adapter 和相关工具仓根目录。

`AGENTS.md` 定义 agent 工作方式；`TASTE.md` 定义维护开发偏好；项目 `docs/`、`contracts/` 和源码定义项目事实。跨项目复用时，本文保持简短稳定，各仓文档补充本地边界。

## 总则

OPL family 的上位原则是 `AI-first / executor-first / Codex-first`：系统为最先进的 AI 执行器提供 stage、上下文、工具、权限、质量门、回执和投影，让 AI 能力进步直接转化为智能体能力进步。框架负责搭台、约束边界和承载审计；开放式推理、创作、评审、诊断和修订由 AI executor 完成。

## 原则

1. **AI 执行优先**

   复杂知识工作由 agent executor 完成。系统提供清晰目标、上下文、工具、权限、质量门和交接边界，让更强模型、更好 prompt、更好 skill 和更完整知识面直接转化为能力提升。

2. **Stage 推进任务**

   大型任务以 stage 作为可观察、可恢复、可审计的推进单位。每个 stage 明确目标、输入输出、工具、知识、质量门、handoff 和 receipt；stage 内由 selected AI executor 自主完成专家工作。

3. **函数承担边界职责**

   程序函数承担校验、物化、签收、投影、guard、locator 和 native helper 职责。审稿、质量判断、路线判断、修订生成和交付裁决作为独立 AI stage、review attempt 或 domain-owned quality gate 承接。

4. **目标态快速落地**

   目标明确时，按目标架构快速、干净、可回退地推进。行为保持一致，diff 保持小而清楚；结构治理、文档收敛、命名清理、接口收薄和明确迁移优先完成，长周期证据作为独立尾项管理。

5. **Owner 边界明确**

   Framework、App、domain agent、shell、artifact、truth 和 authority 都有唯一 owner。共享能力上收，领域真相和交付裁决留在 domain owner；投影、generated surface、read model 和 UI 承接展示、路由和审计职责。

6. **单一来源派生多入口**

   关键 action、stage、descriptor、contract 和 routing metadata 由 canonical source 统一表达。CLI、MCP、Skill、product-entry、sidecar、status、workbench 和 read model 从同一来源派生，保持接口、文档和投影一致。

7. **历史面及时退役**

   当前 owner surface 已替代的旧模块、旧入口、alias、facade、wrapper、兼容测试和过时文档，在迁移条件成立后进入删除、归档或 tombstone。历史信息保留为 provenance，当前入口保持单一。

8. **薄入口与清晰结构**

   入口保持稳定而薄，复杂逻辑进入按职责命名的模块。源码、测试和文档表达真实边界；目录结构让维护者快速识别语义包、合同、authority implementation、adapter、diagnostic 和 history。

9. **文档治理分层**

   文档服务导航、边界、状态、决策和交接。每份长期文档都有明确 owner、purpose、state 和 machine boundary；README、docs、AGENTS、TASTE、contracts 各自持有单一职责。

10. **最小充分验证**

    验证强度与风险匹配。行为不变、文档治理、结构收薄和命名清理采用最小充分验证；生产声明、权限边界、artifact mutation、release、quality verdict 和 owner authority 使用更重的 receipt、截图、release、owner-chain 或 long-soak 证据。

## 迁移

复制到相关项目时，通常只调整 `Owner`、项目名和少量本地例子。原则数量按实际需要确定。项目如需局部差异，应在本仓 `docs/decisions.md`、`docs/invariants.md`、contract 或更深层 `AGENTS.md` 写清适用范围。
