# 关键决策记录

## 2026-04-26：初稿质量升级扫描进入 study charter 与 reviewer-first route-back

- 决策：`study_charter.paper_quality_contract` 固定新增 first-draft quality contract；写作 route 在判断 draft ready 前必须扫描已验证数据资产是否支持更强的时间点、角色/人群、中心/地理、指南对应、亚组/关联分析和现实采用约束叙事。若当前初稿过轻且不改变锁定 claim 边界，默认 route back 到 `analysis-campaign` 做有限补充分析。
- 理由：近期 manuscript 修改反馈暴露出一个系统性问题：初稿如果只按已有结果描述成稿，容易漏掉数据资产本身已经能支撑的更强 paper shape。把这类反馈上收到 MAS 合同层，可以在初稿前阻断“描述性够用”的低质量出口。
- 影响：后续 `survey_trend_analysis`、写作 route、reviewer-first 检查与 evidence/review 合同都必须先问“数据资产还能否支撑更强且可验证的论文形态”，再决定写作、有限补充分析或 human gate。

## 2026-04-26：OPL Runtime Manager 作为薄运行管理层接入 MAS projection

- 决策：MAS 与 OPL 的长线对齐采用 `OPL Runtime Manager -> external Hermes-Agent runtime substrate -> MAS domain entry/projection` 的分层口径。MAS 只暴露 task registration、runtime_control projection、status/artifact locator、approval/wakeup boundary 与现有 durable truth surface；`OPL Runtime Manager` 只负责上层管理、索引、doctor/repair/resume 与 native helper catalog，不成为 MAS 研究 truth 或执行器 owner。
- 理由：这能先获得长期托管、唤醒、健康检查和跨域状态索引的收益，同时保留 MAS 自己的 study authority、publication gate 与 evidence/review ledger。若未来需要自有长期常驻 sidecar，也能沿 Runtime Manager 的 adapter/projection contract promotion，而不重写 MAS domain truth。
- 影响：后续涉及 OPL handoff、runtime_control、product-entry manifest、status projection 或 hosted lane 的文案，都必须明确 `OPL Runtime Manager` 是 OPL 侧 thin manager over external substrate；MAS durable truth surface 仍是唯一研究真相。

## 2026-04-21：公开主语固定为独立 domain agent，单一 app skill 承接稳定 surface，OPL 只做上层 federation

- 决策：`Med Auto Science` 的对外第一身份固定为“可被 Codex 或其他通用 agent 直接调用的独立 medical research domain agent”；其单一 MAS app skill 承接稳定 callable surface；`OPL` 只承担 family-level session/runtime/projection 编排与 shared modules/contracts/indexes。
- 理由：公开主语直接决定用户入口与 owner 语义。将 MAS 固定为独立 domain agent，并把稳定 surface 收口到单一 app skill，才能避免把 MAS 误写成 OPL 内部模块，也避免把桥接载荷写成第一主语。
- 影响：README 与核心 docs 必须明确 domain agent、单一 app skill、CLI/workspace commands 和 durable surface 的主次关系；`OPL handoff`、`product-entry manifest` 与 `gateway / harness` 术语保留为内部集成或架构边界语言，不作为对外第一身份。

## 2026-04-11：统一 docs 骨架与分层

- 决策：以 `project / architecture / invariants / decisions / status` 作为 docs 核心骨架，并将其余文档收口到 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/`。
- 理由：避免文档平铺，确保入口明确、角色清晰、可维护。
- 影响：删除冗余的 `documentation-governance.md`，统一文档规则入口。

## 2026-04-11：OMX 退役并归档

- 决策：OMX 只作为历史材料保留在 `docs/history/omx/`，`.omx/` 禁止作为当前 workflow 入口。
- 理由：避免历史工具状态干扰 repo-tracked 真相。
- 影响：OMX 相关材料仅保留为参考，不进入当前运行路径。

## 2026-04-11：冻结 runtime backend interface

- 决策：`MedAutoScience` controller 只通过 `runtime backend interface contract` 访问 managed runtime backend，不再把 `med-deepscientist` 具体实现名作为 controller 判定真相。
- 理由：为 Hermes 等新 backend 接入提供稳定 contract，先完成 backend abstraction，再进入 controlled cutover。
- 影响：`runtime_binding.yaml` 增加 backend-generic 字段；显式声明但未注册的 backend 必须 fail-closed 阻断。

## 2026-04-11：目标 runtime 方向优先于旧 substrate 延长线

- 决策：后续新增投入默认服务“上游 `Hermes-Agent` 承担外层 runtime substrate”这条目标形态，而不是继续把旧默认 substrate 深磨成长期产品方向。
- 理由：历史基线和过渡实现仍然有价值，但它们应作为迁移桥、兼容层与回归基线存在，不能反向决定主线目标。
- 影响：所有后续 tranche 都必须明确区分“当前 repo-verified baseline”与“长线目标”，并保持 display 独立支线不被主线误伤。

## 2026-04-11：当前仓内的 `Hermes` 只代表 repo-side seam，不代表上游集成已落地

- 决策：仓内保留的 `Hermes` 命名，只能表示 repo-side outer-runtime seam / shim / contract owner，不得写成“上游 `Hermes-Agent` 已成为当前 runtime owner”。
- 理由：当前真实长时执行仍通过受控 `MedDeepScientist` backend 完成；文档与命名必须诚实反映这一点。
- 影响：后续所有 runtime 文档都必须把“目标中的上游 `Hermes-Agent`”与“当前仓内的 repo-side seam”拆开表述；display / paper-facing asset packaging 独立线继续排除在当前 tranche 外。

## 2026-04-12：固定 runtime substrate 与 research executor 分层

- 决策：`Hermes-Agent` 在这条主线里优先承担 runtime substrate / orchestration owner，而不是立刻替代 `MedDeepScientist` 内部所有研究执行脑。
- 理由：当前真正高风险的不是“没有统一执行脑”，而是“没有统一长期在线 runtime substrate”。若在外层 runtime ownership 尚未稳定前，就强制把 backend 内部的 `Codex + skills` 执行生态整体替掉，最容易出现功能降级。
- 影响：后续解构 `MedDeepScientist` 时，必须按 executor route 逐类迁移，并用显式 contract + proof 决定是否替换；不允许把“接入 Hermes”偷换成“已完成单步执行器替换”。

## 2026-04-20：方向锁定后的质量与自治默认收口到 MAS

- 决策：方向锁定之后，普通科研推进、论文质量判断、reviewer concern 排序、证据充分性判断与 `bounded_analysis` 一类有限补充分析推进，默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计。
- 理由：长时间自治和医学论文质量需要同一 owner、同一 study truth 和同一审计边界，`MAS` 已经持有 study authority、workspace authority、证据推进与人工接手点，适合承担默认裁决权。
- 影响：后续 program、status、runtime 与 eval 文档都要按这个 owner 边界写作；`MDS` 继续承担迁移期 research backend、行为等价 oracle 与上游 intake buffer。

## 2026-04-20：study charter 承载质量总合同

- 决策：study charter 成为医学质量总合同入口，统一冻结研究问题、claim、证据强度、有限补充分析边界、review 与 submission hygiene 约束；`paper evidence ledger` 与 `review ledger` 作为该合同的执行记录与审阅记录。
- 理由：论文质量提升依赖一份前置、持续、可审计的合同，后续 evidence/review ledger 围绕这份合同推进，才能把设计、分析、审阅和投稿收口到同一条 `MAS` 主线。
- 影响：后续涉及 evidence、review、submission hygiene、bounded analysis 的 owner 叙事，都要显式回指 study charter contract，而不是分散写成独立局部机制。
