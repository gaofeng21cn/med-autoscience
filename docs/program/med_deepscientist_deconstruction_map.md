# MedDeepScientist Deconstruction Map

这份文档冻结两件事：

1. `MedDeepScientist` 在迁移期继续承担什么角色
2. 新的优化任务为什么默认进入 `MedAutoScience`

当前主线目标已经明确为单项目收敛：研究入口、研究治理、医学论文质量提升、长时间自治能力提升，默认都应服务 `MedAutoScience` 这一条主线；`MedDeepScientist` 继续保留为迁移期 companion，职责集中在 oracle / intake / parity / legacy support。

## 当前固定边界

- `MedAutoScience`：唯一研究入口、study / workspace authority owner、医学论文质量 owner、长时间自治 owner、repo-tracked operator surface owner
- 上游 `Hermes-Agent`：目标外层 managed runtime substrate owner；当前仓内通过 repo-side seam / adapter 暴露 substrate-facing contract
- `MedDeepScientist`：迁移期 controlled research backend，只保留 oracle / intake / parity / inner execution 相关角色
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
| 迁移期行为等价对照 | `MedDeepScientist` | 这是 oracle / parity lane，本质上服务 cutover proof |
| 上游能力 intake、兼容比较、迁移缓冲 | `MedDeepScientist` | 这是 intake buffer，本质上服务审计式吸收 |
| 旧 quest / workspace / artifact 兼容读取 | `MedDeepScientist` 与 `MedAutoScience` 协作 | `MedDeepScientist` 保留 reference truth，`MedAutoScience` 负责最终 reader 入口 |

默认规则是：凡是会成为未来日常开发、运维、质量治理、自治治理的一部分，都先落到 `MedAutoScience`；凡是只服务迁移期对照、上游 intake、行为等价 proof 的内容，才继续留在 `MedDeepScientist`。

## 2. MedDeepScientist 的长期收敛角色

`MedDeepScientist` 的长期方向收敛为下面三类角色：

1. `behavior oracle`
   - 为 `MedAutoScience` 提供行为等价对照、golden trace replay、真实研究回归参考
2. `upstream intake buffer`
   - 承接上游能力 intake、差异审计、兼容比较，再决定哪些能力值得被 `MedAutoScience` 吸收
3. `parity / legacy companion`
   - 在 controlled cutover 完成前，继续为旧 quest、旧 workspace、旧 artifact、迁移期 recovery proof 提供参考面

这意味着 `MedDeepScientist` 在迁移后期仍然可能存在，它的主要职责集中在：

- 继续提供行为等价对照
- 继续承担上游 intake 与兼容比较
- 继续为旧 quest / workspace / artifact 提供迁移期参考面
- 继续服务 controlled cutover 前的 parity 证明

只有当 `MedAutoScience` 在某项能力上已经具备明确 owner、repo-tracked contract、测试 proof、真实 study proof 时，该能力才允许从 `MedDeepScientist` 升级为 `MedAutoScience` owned。这里表达的是受控迁移顺序，不代表当前已经物理迁移完成。

## 3. 更适合放在 MedAutoScience 主线的投入

下面这些投入，默认更适合持续建设在 `MedAutoScience` 主线：

| 投入 | 更合理的落点 | 理由 |
| --- | --- | --- |
| 独立 operator frontdoor、独立日常入口文档 | `MedAutoScience` | 未来单项目开发和运维需要统一入口 |
| 独立医学论文质量治理面 | `MedAutoScience` | 研究设计、claim gate、publication hygiene 需要和 study authority 同源 |
| 独立长时间自治治理面 | `MedAutoScience` | 恢复、接管、升级、停机、人工决策都属于 outer-loop owner |
| 独立 progress / watch / status 汇报面 | `MedAutoScience` | 用户和维护者需要一套统一可见性真相 |
| 独立长期主线文档与 onboarding | `MedAutoScience` | 文档入口需要直接描述目标主线，并持续保留迁移期 companion 说明 |
| 独立 feature polish 只为维持日常使用舒适度 | `MedAutoScience` | 这类投入会产生重复维护与再次迁移成本 |

仍然值得留在 `MedDeepScientist` 的投入，只有三类：

1. 提高 oracle 置信度的投入
2. 提高 intake / parity / replay 质量的投入
3. 为旧研究状态提供更稳的读取、对照、迁移参考的投入

## 4. 能力吸收时的判断标准

对任何一项来自 `MedDeepScientist` 的能力，判断顺序固定为：

1. 这项能力未来是否属于 `MedAutoScience` 日常运行、质量治理、自治治理的一部分
2. `MedAutoScience` 是否已经有明确 owner 和 repo-tracked contract
3. 是否已经有 parity proof、回归 proof、真实 study proof
4. 吸收后是否形成更轻的双面维护和更清晰的 owner 结构

只要前两项成立，默认路线就是吸收到 `MedAutoScience`。
只要第三项和第四项还没成立，`MedDeepScientist` 就继续保留迁移期 oracle / intake / parity 角色。

## 5. 当前 enforcement surface

这张解构地图当前至少由下面这些 repo-tracked surface 共同约束：

- `docs/project.md`
- `docs/architecture.md`
- `docs/runtime/runtime_backend_interface_contract.md`
- `docs/runtime/runtime_handle_and_durable_surface_contract.md`
- `docs/program/merge_and_cutover_gates.md`
- `docs/program/external_runtime_dependency_gate.md`
- `tests/test_runtime_contract_docs.py`
- `make test-meta`

`merge_and_cutover_gates` 负责定义什么时候某个 tranche 可以吸收、什么时候运行面可以继续 cutover；这份文档负责定义新任务的默认主体和 `MedDeepScientist` 的迁移期角色。两者一起使用，才能保持“目标主线明确”和“迁移顺序受控”同时成立。

## 6. 当前仍需诚实保留的迁移期语义

当前迁移期的稳定判断如下：

1. `MedDeepScientist` 还没有物理退场
2. `MedAutoScience` 已经是默认优化主体
3. `MedDeepScientist` 仍然需要保留 oracle / intake / parity / legacy companion 角色
4. physical migration、runtime core ingest、controlled cutover 仍需继续经过独立 gate 与真实 study proof
