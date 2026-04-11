# 不可变约束（Invariants）

以下约束是仓库运行语义的最低不变集，任何变更都不得破坏。

## 运行与真相

- repo-tracked contract 与 durable surface 是唯一权威，不得被本地工具状态替代。
- 项目级 `.codex/` 与 `.omx/` 已退役，不得再作为当前 workflow 入口。
- 如需保留历史 session、prompt、log 或 hook 状态，应迁入用户级 `~/.codex/` 归档。
- formal-entry matrix 固定为 `CLI`（默认入口）/ `MCP`（协议层）/ `controller`（控制面）。
- 能力表达遵循 `policy -> controller -> overlay -> adapter` 主链路，避免旁路。

## 工程与方法

- 不采用降级处理、兜底方案、临时补丁、启发式方法、局部稳定化手段，避免以非严谨通用算法的后处理补救作为主策略。
- 重大变更必须在独立 worktree 中完成，保持可追溯与可回滚。
- 一旦目标 runtime topology 已明确，新增投入默认服务目标形态；旧 substrate 只允许作为迁移桥、兼容层或回归基线存在。
- 当前目标形态是上游 `Hermes-Agent` 承担外层 runtime substrate、`MedAutoScience` 保持唯一研究入口、`MedDeepScientist` 逐步收敛为 research backend；不得再把当前 repo-side seam 写成“已接入 Hermes-Agent”。

## 文档与结构

- `docs/project.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/status.md` 是核心骨架。
- 文档按 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/` 分类收口，不得平铺堆放。
- 对外文档必须提供中英双语镜像；内部技术与规划文档默认中文。

## 验证

- 统一验证入口为 `scripts/verify.sh`。
- 修改 docs/contract surface 或运行语义时，至少补跑 `make test-meta`。
