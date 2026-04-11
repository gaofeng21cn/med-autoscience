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

## 2026-04-11：Hermes 成为 repo-tracked 默认 outer runtime substrate owner

- 决策：repo 内默认的 outer runtime substrate owner 切到 `Hermes`；`MedAutoScience` 继续是唯一研究入口与 research gateway，`MedDeepScientist` 明确降级为 controlled research backend。
- 理由：旧 `Codex-default host-agent runtime` 不再是长期产品方向；需要把主线 truth 从“继续深化旧 host-agent runtime”切回 `Hermes-backed outer runtime + controlled research backend` 的稳定拓扑。
- 影响：默认 `managed_runtime_backend_id` 切到 `hermes`；`runtime_binding.yaml` 与相关 status surface 需要同时写出 `runtime_backend_*` 与 `research_backend_*` 元数据；display / paper-facing asset packaging 独立线继续排除在当前 tranche 外。
