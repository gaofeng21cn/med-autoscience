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
- `OPL` 是 stage-led、以 Agent executor 为最小执行单位的完整智能体运行框架，可作为 MAS 的外部依赖和托管运行层；它承担 family-level session/runtime/projection、stage attempt、queue、wakeup、approval/retry/dead-letter 与 shared modules/contracts/indexes 编排，不把 `MedAutoScience` 改写为内部模块或研究 owner。
- `Stage` 是 OPL/MAS 共同理解的大型任务步骤，`Codex CLI` 是 stage 内默认 concrete executor 和最小执行单元；OPL-hosted production path 必须依赖 Temporal-backed provider transport/record/dispatch stage attempt。Hermes legacy provider 或 local carrier 只能作为 legacy/proof/dev/CI/offline diagnostic 语境，不能生成 MAS 医学研究 truth，也不能替代 OPL Full online readiness。
- `OPL Runtime Manager` 只能作为 OPL 侧薄 adapter/projection layer 管理外部 runtime substrate 与高频索引；不得成为 MAS 的 scheduler kernel、session store、memory store、study truth、publication gate、artifact authority 或 concrete executor owner。
- OPL native helper 与高频状态索引只能缓存、探测和投影 MAS 已暴露的 durable truth surface，不得替代 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`、`study_charter`、evidence ledger 或 review ledger。
- `MedAutoScience` 的对外稳定 capability surface 固定为本地 CLI、workspace commands / scripts、durable surface 与 repo-tracked contract，并由单一 MAS app skill 承接。
- AI-first 质量判断必须由 AI reviewer / author artifact 持有；schema、gate、scorecard、audit 只能持有结构、证据引用、机械完整性与阻塞投影。缺少 `assessment_provenance.owner=ai_reviewer` 的 `publication_eval/latest.json` 不得驱动 reviewer-first ready、bundle-only remaining、finalize-ready 或 submission-facing 质量闭环。
- `allow_write` 必须按写面拆语义：publication gate 的 `allow_write=false` 只阻止下游投稿包、bundle、submission proofing、`current_package` 和 delivery mirror 写入；MAS managed runtime worker 在 controller-authorized analysis-campaign/write work unit 下仍可修改 canonical `paper/` 修订面。前台 Codex App 或 manual agent 的 supervisor-only 限制不得被解释成 MAS 自己派发的 worker 也不能写 canonical paper。
- 已达投稿包、submission-ready 或 finalize 里程碑后收到用户、导师或审稿稿件反馈时，反馈本身就是同一 study 的重新激活信号；旧 stopped/submission-ready/finalize 状态不得被解释为前台直接修改 `manuscript/current_package/` 的许可，必须先写入 durable revision intake，再通过 MAS-controlled relaunch/resume 接管 canonical paper surface 并重新生成投影包。
- `MDS` 只能作为显式可选的 runtime/native/review event source、backend audit、explicit archive import reference、upstream intake 或行为等价 oracle；MAS 的 `StudyTruthKernel` 持有用户可见 `canonical_next_action`、publication gate 解释、package authority 解释和 delivery state。任何 truth/gate/status 事故必须同时落 reducer rule、fixture test 与 runbook entry。
- `MDS` 只能作为显式可选 runtime health probe / native runtime event source；MAS 的 `RuntimeHealthKernel` 持有 `canonical_runtime_action`、worker liveness 判断、retry budget、runtime escalation 与 allowed controller actions。任何 liveness/recovery 事故必须同时落 reducer rule、fixture test 与 runbook entry。
- `study_macro_state/latest.json` 是用户宏观状态的唯一 read model；用户可见投影固定从 `writer_state/user_next/reason` 派生。`study-progress`、MCP、workspace cockpit、product-entry-status 和外部 operator 面不得从 legacy top-level 状态字段重新解释当前状态；缺少 canonical macro state 或出现 writer 冲突时必须 fail-closed 为 `inspect/conflict`，重新生成 canonical projection。
- `owner_route` 是 `scan -> consume -> execute-dispatch -> rescan` 的唯一执行票据。request handoff、default executor dispatch 和执行端都必须通过 `route_epoch/source_fingerprint/next_owner/allowed_actions/idempotency_key` 校验；旧 dispatch 文件不能绕过 workspace-level consumer latest。
- Runtime health append 只有在显式 `source_signature` 相同的情况下幂等返回 existing event；没有 source signature 的 recover/launch attempt 仍代表新的真实尝试并消耗 retry budget。
- 文件生命周期治理不得从 cleanup plan 反向推断 study truth。只有 `writer_state=parked`、`user_next=none`、`reason=stop_loss`、`details.reopen_allowed=false` 的 materialized macro state 才能让终局止损文件生命周期 plan 标记 runtime history 精简候选；物理 apply 仍要求 manifest、sha256、restore index 与 restore proof。
- SQLite lifecycle store 只做 sidecar index、read model、receipt 和幂等检索，不替代 paper/manuscript/package、publication eval、controller decision、user intervention memory、restore metadata 或 dataset manifest 这类文件 authority。
- `mas_mds_architecture_owner_boundary_report` 是当前 architecture owner boundary fitness function。entry projection、observability、MDS backend/oracle 或 runtime adapter 不得声明或替代 `study_truth`、`runtime_health`、`scientific_quality`、`medical_writing_quality`、`publication_readiness`、`submission_authority`、`artifact_authority` 或 `user_visible_next_action`。
- 后续 MDS / DeepScientist 相关能力只能沿 owner matrix + strangler refactor + architecture fitness functions 进入。重新打开默认 dependency、未带 provenance/parity proof 的 physical absorb、未带 rollback surface 的 owner switch、以及用 MDS mechanical oracle 替代 MAS AI reviewer / controller authority 的变更都必须 fail-closed。
- 大型 public data 默认保持 remote-only；只有在 durable study charter 或 analysis plan 明确具体用途、体积预算、复用位置与清理/保留策略后，才允许下载或物化完整资产。停题、止损或短期无明确用途时，应清理本地镜像并保留 registry / mutation log 作为可追溯入口。

## 文档与结构

- `docs/project.md`、`docs/architecture.md`、`docs/invariants.md`、`docs/decisions.md`、`docs/status.md` 是核心骨架。
- 文档按 `active/`、`public/`、`product/`、`runtime/`、`delivery/`、`source/`、`policies/`、`specs/`、`references/`、`history/` 分类收口，不得平铺堆放；旧 `program/` 与 `capabilities/` 只作为 `docs/history/**` 中的迁移来源或 provenance 目录名出现。
- `contracts/` 是机器可读 contract root；模块边界 contract 归入 `contracts/modules/`，叙述性说明留在 `docs/`。
- `docs/**` 是中文内部开发与维护参考；稳定路径优先使用无语言后缀 `.md` 承载中文 canonical 内容。
- 根层 `README*` 是否保留公开双语入口，由产品分发和 public 需求单独决定。

## 验证

- 统一验证入口为 `scripts/verify.sh`。
- 不带参数的 `scripts/verify.sh` 是本地 smoke 入口，负责 sanity 与 fast tests，不代表完整回归。
- `scripts/verify.sh regression` 是显式回归入口，默认由 advisory/nightly 承接。
- `scripts/verify.sh ci-preflight <base-ref>` 是 push CI 入口，必须基于 repo-tracked preflight contract 展开变更面检查，并与 build 共同保护 `main` / `development`。
- `regression`、`display`、`submission`、`family` 与 `meta` lane 由 advisory/nightly 承接，不回灌到 push quick-checks。
- `smoke`、`ci-preflight` 与 `full` 的耗时预算只用于观察和提醒；duration drift 与相对基线百分比变化通过 advisory run log、summary artifact、只读 history summary 或 release/full 记录暴露，不得成为 push quick-checks 的新增阻塞项。
- 修改 machine-readable contract surface、测试入口或运行语义时，至少补跑 `make test-meta`；纯叙述性 docs-only 变更按 `documentation_review_only` 处理。
- Python / pytest 验证必须通过 clean runner 路由缓存、bytecode 与 `uv sync` project venv；开发 checkout 不应产生 `.venv`、`__pycache__`、`.pytest_cache` 或 `*.egg-info` 副产物。
