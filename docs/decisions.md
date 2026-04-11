# 关键决策记录

## 2026-04-11：统一 docs 骨架与分层

- 决策：以 `project / architecture / invariants / decisions / status` 作为 docs 核心骨架，并将其余文档收口到 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/`。
- 理由：避免文档平铺，确保入口明确、角色清晰、可维护。
- 影响：删除冗余的 `documentation-governance.md`，统一文档规则入口。

## 2026-04-11：OMX 退役并归档

- 决策：OMX 只作为历史材料保留在 `docs/history/omx/`，`.omx/` 禁止作为当前 workflow 入口。
- 理由：避免历史工具状态干扰 repo-tracked 真相。
- 影响：OMX 相关材料仅保留为参考，不进入当前运行路径。
