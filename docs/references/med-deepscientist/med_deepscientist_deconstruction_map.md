# MedDeepScientist Deconstruction Map

这份文档冻结两件事：

1. `MedDeepScientist` 现在还保留哪些价值
2. 新的优化任务为什么默认进入 `MedAutoScience`

当前主线目标已经明确为单项目收敛：研究入口、研究治理、医学论文质量提升、长时间自治能力提升，默认都应服务 `MedAutoScience` 这一条主线；`MedDeepScientist` 不再是默认运行面，而是历史 source archive、parity fixture、legacy diagnostic 和 provenance reference 的组合体。

## 当前固定边界

- `MedAutoScience`：唯一研究入口、study / workspace authority owner、医学论文质量 owner、长时间自治 owner、repo-tracked operator surface owner
- 上游 `Hermes-Agent` / `hermes_agent`：只作为历史学习对象、显式非默认 executor/proof lane 或 backend audit 参考；不再是 MAS 目标外层 managed runtime substrate owner
- `MedDeepScientist`：历史 source archive、parity fixture、legacy diagnostic、provenance reference；只在显式 legacy audit / source-watch / parity 场景下出现
- 旧 `Codex-default host-agent runtime`：迁移期对照面与 regression oracle
- display / paper-facing asset packaging：明确排除在本线之外

## 1. 新优化任务的默认落点

新的优化任务默认进入 `MedAutoScience`，原因固定为三条：

1. 目标形态已经是单项目收敛，新的质量与自治投入应直接服务目标运维面
2. 医学论文质量与长时间自治都依赖 study authority、controller judgment、publication / eval hygiene、operator visibility 这些 shared surface，它们的 owner 在 `MedAutoScience`
3. 把新增能力继续落在 `MedDeepScientist` 独立运维面，会形成重复 owner、重复文档、重复排障路径，随后还要再迁一次

可按下面这张路由表理解：

| 任务族 | 默认主体 | 原因 |
| --- | --- | --- |
| 医学论文质量提升 | `MedAutoScience` | 研究设计、evidence contract、publication gate、reviewer-facing quality bar 都属于医学研究主线 authority |
| 长时间全自动驾驶提升 | `MedAutoScience` | runtime watch、human gate、decision record、progress projection、recovery governance 都属于 outer-loop owner |
| repo-tracked operator docs / mainline docs / control-plane wording | `MedAutoScience` | 这些文档定义日常开发与运维入口，必须和目标主线一致 |
| 历史行为等价对照 | `MedDeepScientist` | 这是 historical parity lane，本质上服务 cutover proof 和 regression oracle |
| 上游能力 intake、兼容比较、迁移缓冲 | `MedAutoScience` 主导，`MedDeepScientist` 只在显式 legacy audit 时提供 source reference | 这是 MAS 侧 intake lane，本质上服务审计式吸收 |
| 旧 quest / workspace / artifact 兼容读取 | `MedAutoScience` 负责最终 reader 入口，`MedDeepScientist` 只提供 legacy source/reference | `MedDeepScientist` 不再是默认 reader 入口 |

默认规则是：凡是会成为未来日常开发、运维、质量治理、自治治理的一部分，都先落到 `MedAutoScience`；凡是只服务历史对照、上游 intake、行为等价 proof 的内容，才保留 `MedDeepScientist` 侧的 source/reference 价值。

## 2. MedDeepScientist 的长期收敛角色

`MedDeepScientist` 的长期方向收敛为下面三类角色：

1. `historical source archive`
   - 为 `MedAutoScience` 提供可追溯 upstream source、snapshot hash、provenance 和 license reference
2. `parity / legacy fixture`
   - 提供历史行为等价对照、golden trace replay、旧路径兼容测试
3. `legacy diagnostic surface`
   - 只在显式 restore/import/backend-audit 场景下被打开，不参与默认运行治理

这意味着 `MedDeepScientist` 仍然可能存在，但它的主要职责已经缩到：

- 继续提供历史 source 与 provenance
- 继续承担 parity / legacy fixture
- 继续为旧 quest / workspace / artifact 提供显式诊断入口

只有当 `MedAutoScience` 在某项能力上已经具备明确 owner、repo-tracked contract、测试 proof、真实 study proof 时，该能力才允许在 `MedAutoScience` 侧吸收或重写。这里表达的是 owner 归属，不代表 `MedDeepScientist` 还承担默认运行职责。

## 3. 更适合放在 MedAutoScience 主线的投入

下面这些投入，默认更适合持续建设在 `MedAutoScience` 主线：

| 投入 | 更合理的落点 | 理由 |
| --- | --- | --- |
| 独立 operator entry、独立日常入口文档 | `MedAutoScience` | 单项目开发和运维入口必须回到 MAS current owner surface；MDS 只保留 historical / parity / provenance 参考 |
| 独立医学论文质量治理面 | `MedAutoScience` | 研究设计、claim gate、publication hygiene 需要和 study authority 同源 |
| 独立长时间自治治理面 | `MedAutoScience` + `OPL` 分层 | 医学 owner route、human gate 语义和 receipt 留在 MAS；generic provider、queue、retry/dead-letter、resume 和 worker residency 归 OPL/Temporal |
| 独立 progress / watch / status 汇报面 | `MedAutoScience` | 用户和维护者需要一套统一可见性真相 |
| 独立长期主线文档与 onboarding | `MedAutoScience` | 文档入口需要直接描述目标主线，并仅保留 historical source / fixture / diagnostic 说明 |
| 独立 feature polish 只为维持日常使用舒适度 | `MedAutoScience` | 这类投入会产生重复维护与再次迁移成本 |

仍然值得留在 `MedDeepScientist` 的投入，只有三类：

1. 提高 historical source / provenance 置信度的投入
2. 提高 parity / replay / legacy fixture 质量的投入
3. 为旧研究状态提供更稳的读取、对照、迁移参考的投入

## 4. 能力吸收时的判断标准

对任何一项来自 `MedDeepScientist` 的能力，判断顺序固定为：

1. 这项能力未来是否属于 `MedAutoScience` 日常运行、质量治理、自治治理的一部分
2. `MedAutoScience` 是否已经有明确 owner 和 repo-tracked contract
3. 是否已经有 parity proof、回归 proof、真实 study proof
4. 吸收后是否形成更轻的双面维护和更清晰的 owner 结构

只要前两项成立，默认路线就是在 `MedAutoScience` 侧吸收或重写。
只要第三项和第四项还没成立，`MedDeepScientist` 就继续保留 historical source / parity fixture / legacy diagnostic 角色。

## 5. 当前 enforcement surface

这张解构地图当前至少由下面这些 repo-tracked surface 共同约束：

- `docs/project.md`
- `docs/architecture.md`
- `docs/runtime/contracts/runtime_backend_interface_contract.md`
- `docs/runtime/contracts/runtime_handle_and_durable_surface_contract.md`
- `docs/policies/repo-ops/merge_and_cutover_gates.md`
- `docs/policies/runtime-governance/external_runtime_dependency_gate.md`
- `tests/test_runtime_protocol_study_runtime.py`
- `tests/test_study_runtime_router.py`
- `make test-meta`

`merge_and_cutover_gates` 负责定义什么时候某个 tranche 可以吸收、什么时候运行面可以继续 cutover；这份文档负责定义新任务的默认主体和 `MedDeepScientist` 的历史/legacy 角色。两者一起使用，才能保持“目标主线明确”和“历史边界诚实”同时成立。

## 6. 当前仍需诚实保留的历史语义

当前稳定判断如下：

1. `MedDeepScientist` 不再是 MAS 默认 operation 的必需 checkout，外部参考仓只保留为 optional source archive / parity fixture / legacy diagnostic surface
2. `MedAutoScience` 已经是默认优化主体
3. `MedDeepScientist` 仍然需要保留 source / parity / legacy diagnostic 角色
4. no-history absorb、default-dependency retirement 和 functional monolith closeout 已落地；未来若再从外部 source 吸收新的 runtime core、UI、diagnostic 或 learning surface，仍需独立 gate 与真实 study proof
