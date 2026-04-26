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
- 当前目标形态是 `Codex-default host-agent runtime` 加 `MAS` 自己的稳定 capability surface；可选 hosted runtime carrier（例如 `Hermes-Agent`）只能作为显式附加层或 reference-layer 材料出现，不得改写默认入口语义。
- `MedAutoScience` 对外第一身份固定为独立 medical research domain agent；其单一 MAS app skill 承接稳定 capability surface。`OPL` handoff、product-entry manifest 与其他机器可读桥接只作为集成或参考层存在，不得改写第一主语。
- `OPL` 只承担 family-level session/runtime/projection 与 shared modules/contracts/indexes 编排，不把 `MedAutoScience` 改写为内部模块或研究 owner。
- `OPL Runtime Manager` 只能作为 OPL 侧薄 adapter/projection layer 管理外部 runtime substrate 与高频索引；不得成为 MAS 的 scheduler kernel、session store、memory store、study truth、publication gate、artifact authority 或 concrete executor owner。
- OPL native helper 与高频状态索引只能缓存、探测和投影 MAS 已暴露的 durable truth surface，不得替代 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_charter`、evidence ledger 或 review ledger。
- `MedAutoScience` 的对外稳定 capability surface 固定为本地 CLI、workspace commands / scripts、durable surface 与 repo-tracked contract，并由单一 MAS app skill 承接。
- AI-first 质量判断必须由 AI reviewer / author artifact 持有；schema、gate、scorecard、audit 只能持有结构、证据引用、机械完整性与阻塞投影。缺少 `assessment_provenance.owner=ai_reviewer` 的 `publication_eval/latest.json` 不得驱动 reviewer-first ready、bundle-only remaining、finalize-ready 或 submission-facing 质量闭环。
- 已达投稿包、submission-ready 或 finalize 里程碑后收到用户、导师或审稿稿件反馈时，反馈本身就是同一 study 的重新激活信号；旧 stopped/submission-ready/finalize 状态不得被解释为前台直接修改 `manuscript/current_package/` 的许可，必须先写入 durable revision intake，再通过 MAS/MDS relaunch/resume 接管 canonical paper surface 并重新生成投影包。

## 文档与结构

- `docs/project.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/status.md` 是核心骨架。
- 文档按 `capabilities/`、`program/`、`runtime/`、`references/`、`history/omx/` 分类收口，不得平铺堆放。
- 对外文档必须提供中英双语镜像；内部技术与规划文档默认中文。

## 验证

- 统一验证入口为 `scripts/verify.sh`。
- 修改 docs/contract surface 或运行语义时，至少补跑 `make test-meta`。
