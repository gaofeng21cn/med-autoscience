# AGENTS 只管工作方式

## 适用范围

本文件适用于仓库根目录及其所有子目录；若更深层目录存在 `AGENTS.md`，以更近者为准。

## 工作方式

- `Med Auto Science` 是独立医学研究 domain agent，也可以作为 `OPL` stage-led 智能体运行框架中的 admitted domain agent 被托管。`Stage` 表示大型研究步骤，Agent executor 是 stage 内最小执行单位；`Codex CLI` 是当前第一公民 executor，其他 executor adapter 只能显式接入且不承诺行为效果等价。MAS 持有医学研究 truth、quality verdict、publication/study/artifact authority、runtime-facing owner surface 和 owner receipt；通用 runtime、queue、attempt ledger、state-machine runner、workspace/source/artifact/memory locator、lifecycle shell 与 App/workbench shell 归 OPL Framework / shared family layer。
- MAS 的理想形态是标准 OPL Agent：`Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions`。当前仓内已存在的 scheduler、runner、SQLite/lifecycle、workspace/source intake、memory/artifact transport、Portal/workbench、CLI/MCP/product-entry/sidecar/status wrapper 只能作为迁移输入；不能因为已有 active caller 就写成长期合理私有平台。
- 文档和开发计划先设理想态，再找差距；差距不是妥协清单。为了标准 OPL Agent 目标态，可以革命式重构 MAS 并完全抛弃旧模块、旧接口、旧测试、旧目录和旧文案，不以兼容为理由保留历史污染面。
- `MDS / DeepScientist` 的当前角色是 MAS 显式声明的 source provenance、historical fixture、explicit archive import、backend audit、upstream learning 和 parity oracle reference。
- 保持变更可审查、可回退，避免不必要的大范围改动。
- 能删就别加；能复用现有模式就别新起抽象；没有明确必要不要新增依赖。
- 不采用降级处理、兜底方案、临时补丁、启发式方法、局部稳定化手段，避免以非严谨通用算法的后处理补救作为主策略。
- repo-tracked 源码与测试默认都应保持文件边界清晰，优先控制在 `1000` 行以内；超过 `1500` 行应视为明确的拆分信号，而不是继续堆叠实现。
- 新增能力或继续重构时，优先采用稳定薄入口加 `parts/`、`cases/`、`modules/` 等子模块拆分；不要把新逻辑继续堆回单个超长文件。
- 若文档提到 `Hermes-Agent`，只能指上游外部 runtime 项目 / 服务；仓内的 seam、shim、adapter 或过渡 scaffold，不得写成“已接入 Hermes-Agent”。
- 一旦目标 runtime topology 已明确，新增投入默认服务目标形态；旧 substrate 只允许作为迁移桥、兼容层或回归基线存在。
- 私有功能面是例外而不是默认。保留在 MAS 的程序面必须是医学 truth、publication quality、artifact mutation、memory accept/reject、source readiness、owner receipt signing 或 domain-native helper 这类无法声明化的最小 authority function，并写清接口、active caller、不能上收原因、receipt/blocker/ref 输出边界和退役门。
- `family shared modules / shared boundary refactor` 是当前允许推进的 lane；它服务四仓复用、shared helper 收口与 future monorepo readiness。
- external runtime gate、workspace / human gate 与对象边界仍然约束 `physical migration / monorepo absorb / runtime core ingest / controlled cutover`；`monorepo / runtime core ingest / controlled cutover` 继续作为后置长线推进。
- 已被当前 owner surface 替代的模块、接口、CLI alias、wrapper、facade、聚合测试和文档入口，默认迁移 active caller 后直接退役；需要来龙去脉时只保留 history/tombstone/provenance，不新增 compatibility shim、别名或兼容测试。

## 运行语义一致性

为保持 repo-tracked contract 与文档一致性，以下术语必须在变更中保持一致：

- 运行形态：`Codex-default host-agent runtime`、`CLI`、`MCP`、`controller`、`Auto-only`
- 关键身份：`program_id`、`study_id`、`quest_id`、`active_run_id`
- durable surface：`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`runtime_escalation_record.json`、`controller_decisions/latest.json`

## 文档分层与生命周期治理

以下五份是 docs 的稳定核心，保持在 `docs/` 根目录：

- `docs/project.md`
- `docs/architecture.md`
- `docs/invariants.md`
- `docs/decisions.md`
- `docs/status.md`

- `README*` 与 `docs/README*` 是默认对外与默认入口文档。
- `docs/docs_portfolio_consolidation.md` 是当前文档组合治理入口；维护者应先读核心五件套，再按该文件判断新增、更新、归档或 tombstone。
- 每份长期文档都必须能说明 `owner`、`purpose`、`state`、`machine boundary`；缺少任一信号时，先补入口或归位，再继续扩写。
- 文档治理按内容生命周期判断，文件名和目录名只作为辅助信号；同一文档内的当前事实、活跃执行、support lane、closeout evidence 与历史叙事应分别归入当前 owner doc、active/support/reference 层或 history/tombstone 语境。
- 入口文档应先呈现当前状态、活跃层级、新旧关系和下一跳；已完成计划、旧校准记录和历史路线进入 evidence/provenance 层。
- `docs/**` 默认只维护中文 canonical 内容；稳定路径优先使用无语言后缀 `.md`。
- 根层 `README*` 是否保留公开双语入口，由产品分发和 public 需求单独决定。
- MAS 采用 OPL-family canonical docs taxonomy：`active/public/product/runtime/delivery/source/policies/specs/references/history`。目录按长期生命周期职责保留，不按当前文件数量判断。
- `docs/active/`：当前执行、当前计划、当前差距、active baton 与 program lifecycle portfolio；旧 `docs/program/` 已物理退役，`human_doc:*` 只保留语义 ID。
- `docs/public/`：MAS 对外公开叙事和用户第一阅读层；不承载 study truth。
- `docs/product/`：MAS app skill、direct product entry、operator/workbench-facing 指南。
- `docs/runtime/`：runtime contracts、control surfaces、read models、display/projection 与活跃设计；完成或退役计划进入 `docs/history/runtime/`。
- `docs/delivery/`：manuscript、package、submission/export、medical-display 等交付与能力族支撑；旧 `docs/capabilities/medical-display/` 已迁入 `docs/delivery/medical-display/`。
- `docs/source/`：study workspace、source readiness、external intake 与 source truth consumption 支撑。
- `docs/policies/`：稳定内部规则和长期运行边界，默认中文维护。
- `docs/specs/`：当前仍有效技术规格索引；新增 active spec 前先确认是否更适合 runtime/policies/references 或 machine contract。
- `docs/references/`：背景、定位、审计、MDS parity、workspace 与非活跃参考。
- `docs/history/`：历史归档，仅作 provenance、tombstone 和历史参考入口。
- `docs/history/superpowers/`：存量 repo-tracked 历史设计材料归档；新增本地 AI/Superpowers 过程草稿默认保持未跟踪。
- `README*`、`docs/**` 与参考文档是人读面。代码、测试、contracts、dashboard 或 runtime 不得把 prose path、Markdown 章节或文案当成稳定机器接口；确需关联人读材料时，使用 durable JSON/schema/source surface 或 `human_doc:*` / `program:*` / `policy:*` / `runtime:*` 语义 ID。
- MAS 的 study、publication、runtime 与 display 真相优先归属 stable runtime / controller / contract / generated artifact surface；文档只做解释、导航、治理与 provenance，不制造第二真相源。

## 本地工具状态

- 项目级 `.codex/` 与 `.omx/` 已退役，不再作为仓库本地状态入口。
- 如需保留历史 session、prompt、log 或 hook 状态，应迁入用户级 `~/.codex/` 归档。

## Worktree 规则

- 大改动、长链路工作、并行多 AI 开发，默认先从当前 `main` 开独立 worktree，在 worktree 内实现和验证。
- 共享根 checkout 只用于轻量阅读、评审、吸收验证后提交、push 和清理。
- 需要多条 lane 时创建多个 worktree，不要把多条长线塞进同一工作目录。
- worktree 内实现和验证完成后，应尽快吸收回 `main`，并清理对应 worktree、分支与临时状态。

## 验证规则

- 统一验证入口：`scripts/verify.sh`。
- 默认最小验证：`scripts/verify.sh`（内部运行 `make test-fast`）。
- full lane：`scripts/verify.sh full`（内部运行 `make test-full`）。
- 修改 machine-readable contract surface、测试入口或运行语义时，至少补跑 `make test-meta`；纯叙述性 docs-only 变更按 `documentation_review_only` 处理。
- 叙述性 `README*`、`docs/**` 和参考文档不作为脚本/测试的断言对象；可以测试 machine-readable contract、schema、CLI/API 行为、生成产物结构与路径，但不要用测试固定文档措辞、章节或状态文案。
- 默认 Python / pytest 验证必须经由 `scripts/run-python-clean.sh` 或 `scripts/run-pytest-clean.sh`，把 bytecode、pytest cache、`uv sync` project venv 和安装/同步副产物导向仓库外部；禁止把 `.venv`、`__pycache__`、`.pytest_cache` 或 `*.egg-info` 写回开发 checkout 后再靠清理兜底。
