# 关键决策记录

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
