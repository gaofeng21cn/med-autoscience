# ARIS Algorithm Sidecar Design

## 背景

当前 `MedAutoScience` 已明确采用：

- `DeepScientist` 作为主 runtime
- `MedAutoScience` 作为医学主控与审计层
- `controller -> overlay -> adapter` 作为稳定扩展链路

这条链路适合长期 quest、医学治理、可审计状态与正式交付，但不适合承担高频、重实验、强算法创新导向的纯 AI 研究闭环。

对影像、病理、通用多模态等医学 AI 课题而言，真正的瓶颈往往不是“能否把研究流程跑起来”，而是：

- 在明确任务约束下做算法调研
- 形成合理的创新假设
- 快速落成实验计划与实现
- 用多轮 review 驱动方法收敛
- 把“为什么别人做不了、我们为什么能做”沉淀成可写入论文的证据

`ARIS` 的公开定位更接近一套面向纯 AI/ML 研究的 workflow / skill 方法论，而不是另一套长期 runtime。
因此，它不适合作为 `DeepScientist` 的替代品，但适合作为 `MedAutoScience` 体系中的算法创新 sidecar。

## 问题

如果继续把所有算法创新任务都压在 `DeepScientist` 主 runtime 上，会出现三个问题：

1. 医学主控、运行时状态、长期审计与算法创新闭环混在一起，系统边界不清
2. 高算力、高迭代频次的算法研究会拖慢主 quest 的推进效率
3. 即使实验分数提升，也未必沉淀出足够强的论文叙事证据，难以回答：
   - 之前方法为什么不行
   - 当前创新点到底解决了什么瓶颈
   - 改进来自机制创新还是偶然调参

## 目标

建立一个 `ARIS algorithm sidecar` 方案，使得：

- `DeepScientist` 继续担任主 runtime
- `ARIS` 只在明确需要算法创新的课题分支上工作
- `ARIS` 的工作严格受主控冻结的任务契约约束
- `ARIS` 不只回传分数，而是回传可写入论文主线的算法创新证据包
- `ARIS` 在独立 sidecar 工作目录运行，不污染主 quest 的正式审计表面
- `MedAutoScience` 可以通过稳定的导入契约把 sidecar 结果纳入正式写作与交付链路

## 非目标

- 不把 `ARIS` 伪装成第二个主 runtime
- 不修改 `DeepScientist core`
- 不让 `ARIS` 接管医学 framing、数据资产治理或正式投稿交付
- 不允许 sidecar 直接绕过主线 controller 把自由文本写进正式产物层
- 本轮不追求支持所有研究类型；优先服务明确需要算法创新的医学 AI 任务

## 设计结论

### 1. `ARIS` 的产品角色

`ARIS` 在本项目中的角色固定为：

- `algorithm innovation sidecar`
- `constrained experiment engine`
- `paper-facing innovation evidence producer`

它不是：

- 主 runtime
- 通用 quest 调度器
- 医学治理层

### 2. 适用课题范围

第一阶段优先覆盖这类课题：

- 医学影像分类 / 分割
- 病理 / WSI
- 通用多模态融合

但路由条件不按“数据模态名称”硬编码，而按“是否明确需要算法创新”判断。

### 3. 触发模式

采用：

- `自动推荐 + 人工确认`

也就是：

1. 主控先判断当前 quest 是否符合算法创新型路线
2. 若符合，则明确提出建议切入 `ARIS sidecar`
3. 只有用户确认后，才创建并启动 sidecar

不允许静默自动切换。

### 4. 科研逻辑边界

采用：

- `受约束的算法创新 sidecar`

具体边界如下。

#### 主控负责

- 冻结医学问题
- 冻结数据契约
- 冻结评价契约
- 判断是否值得进入算法创新路线
- 决定是否继续 / 停止
- 接收并消费 sidecar 结果
- 组织正式写作与交付

#### `ARIS` 负责

- 在既定任务约束内做算法调研
- 形成候选创新假设
- 选择最终方法设计
- 生成实验计划
- 实现代码、跑实验、做 review loop
- 产出论文可用的创新证据与写作反馈

#### `ARIS` 不负责

- 改题
- 改终点
- 改人群定义
- 改数据资产 contract
- 改主任务定义
- 直接决定课题是否继续
- 直接进入正式写作交付面

## 输入契约

主控在启动 sidecar 前，必须冻结一份 `ARIS input contract`。

最小字段包括：

- `problem_anchor`
  - 临床问题
  - 研究对象
  - 终点
  - 主任务类型
- `data_contract`
  - 数据版本
  - 可用模态
  - train / val / test 划分
  - 外部验证要求
  - 已锁定的预处理边界
- `evaluation_contract`
  - 主指标
  - 次指标
  - 必比 baseline
  - 统计要求
  - 算力预算
- `innovation_scope`
  - 允许在算法层创新
  - 不允许修改问题定义与数据契约
- `writing_questions`
  - 之前方法为什么做不了
  - 当前任务的关键瓶颈是什么
  - 我们的方法为什么理论上能解决这个瓶颈
  - 哪些实验可以证明创新点是必要的
- `optional_context`
  - reference paper
  - base repo
  - 既有失败记录
  - 预设 backbone 或模块约束

没有冻结输入契约时，不允许启动 sidecar。

## 输出契约

`ARIS sidecar` 的成功标准不是“更高分数”，而是“形成可验证的算法创新证据，并能反哺主线论文叙事”。

因此，正式输出必须至少覆盖以下工件。

### 算法研究工件

- `algorithm_scout_report`
- `innovation_hypotheses`
- `final_method_proposal`
- `experiment_plan`
- `experiment_results_summary`
- `review_loop_summary`

### 论文反馈工件

- `prior_limitations`
- `why_our_method_can_work`
- `claim_to_evidence_map`

其中：

- `prior_limitations` 负责回答现有方法为什么做不到
- `why_our_method_can_work` 负责回答当前创新为什么有机制上的合理性
- `claim_to_evidence_map` 负责把论文 claim 映射到实验与证据，防止事后编故事

所有正式输出都必须能稳定回溯到：

- 冻结后的输入契约
- 被采纳的方法标识
- 对应的实验结果摘要

## 工作目录与正式审计面

### 1. sidecar 运行目录

`ARIS` 在 quest 下的独立目录运行：

- `runtime/quests/<quest-id>/sidecars/aris/`

这一层允许保留 `ARIS` 原生工作流文件体系，例如：

- `CLAUDE.md`
- `IDEA_REPORT.md`
- `AUTO_REVIEW.md`
- `REVIEW_STATE.json`
- `refine-logs/*`
- 实验实现代码与日志

这层是 sidecar 的运行现场，不是主线正式审计面。

### 2. 正式导入目录

主线只认导入后的规范化工件：

- `runtime/quests/<quest-id>/artifacts/algorithm_research/aris/`

建议固定这些正式文件：

- `input_contract.json`
- `algorithm_scout_report.md`
- `innovation_hypotheses.md`
- `final_method_proposal.md`
- `experiment_plan.md`
- `experiment_results_summary.md`
- `review_loop_summary.md`
- `prior_limitations.md`
- `why_our_method_can_work.md`
- `claim_to_evidence_map.md`
- `sidecar_manifest.json`

### 3. `sidecar_manifest.json` 最小 schema

- `schema_version`
- `sidecar_id`
- `provider`
- `status`
- `input_contract_hash`
- `input_contract_path`
- `selected_method_id`
- `primary_metric`
- `best_result`
- `artifacts_generated`
- `source_sidecar_root`
- `imported_at`

## 导入原则

导入 `ARIS` 结果时，采用强约束而不是软引用：

1. 主控先写入 sidecar 输入契约
2. `ARIS` 只在独立工作目录运行
3. 主控通过专门 controller / adapter 导入 sidecar 结果
4. 若缺少关键文件或契约不一致，则拒绝导入
5. 只有导入成功后的正式工件，才允许被主线写作与交付消费

导入后的正式目录必须保留被冻结的 `input_contract.json` 快照，不能只保留 hash。

特别要求：

- 如果 `claim_to_evidence_map` 无法和实验结果对齐，必须 fail-fast
- 不允许用自由文本“解释性补充”代替缺失证据
- 不允许把 sidecar 内部临时草稿直接当作正式写作依据

## 路由条件

主控可以推荐 `ARIS sidecar` 的条件包括：

- 当前课题明确需要算法创新
- 任务定义已经收敛
- 数据契约与 split 已冻结
- 评价指标明确
- 至少存在可比较 baseline、reference paper 或 base repo 之一
- 算力预算允许算法探索

下列情况不建议切入：

- 医学问题本身仍未收敛
- 数据 contract 不稳定
- 当前更需要数据治理、外部验证或证据组织，而不是算法创新
- 任务本质不是模型创新问题

## Sidecar 状态机

建议最小状态机如下：

1. `not_candidate`
   - 当前 quest 不满足算法创新推荐条件
2. `recommended`
   - 主控判断可推荐 `ARIS`
3. `awaiting_user_confirmation`
   - 已提出建议，等待用户确认
4. `contract_frozen`
   - 输入契约已冻结，允许创建 sidecar
5. `running`
   - `ARIS` 正在执行调研 / 方法 / 实验 / review
6. `result_ready`
   - sidecar 已形成候选结果包
7. `imported`
   - 正式工件已导入主线审计面
8. `accepted_by_mainline`
   - 主线决定采纳 sidecar 结果进入论文叙事
9. `rejected_or_stopped`
   - 因结果弱、契约不符或用户决策而停止

其中：

- `result_ready` 不等于主线自动采纳
- `imported` 只表示工件可审计
- 是否进入正式论文主线，仍由主控和人类审核共同决定

## 与主线写作的关系

`ARIS` 结果必须能回流到主线写作逻辑，而不只是挂一个“best score”。

主线至少要能从 sidecar 导入结果中稳定消费这些问题：

1. 当前创新点到底针对什么瓶颈
2. 为什么历史方法在这个任务上不足
3. 为什么当前方法理论上更有机会解决问题
4. 哪些实验证明核心创新是必要的
5. 哪些结果只是工程优化，哪些结果才属于论文主 claim

如果 sidecar 无法回答这些问题，即使指标提升，也不应默认成为主论文路线。

## 方案比较

### 方案 A：让 `ARIS` 只做 plan 后执行

优点：

- 最容易接
- 最稳

缺点：

- 无法充分利用 `ARIS` 的算法调研与方法创新能力
- 主控仍需承担大量纯 AI 研究工作

### 方案 B：受约束的算法创新 sidecar

优点：

- 主控保留医学 framing
- `ARIS` 负责其真正擅长的算法调研与实验收敛
- 边界清楚
- 结果更容易反哺论文叙事

缺点：

- 需要清晰的输入输出契约
- 需要单独的导入层

### 方案 C：算法型课题几乎全包给 `ARIS`

优点：

- 迁移激进

缺点：

- 容易把医学课题拉成纯 AI 论文逻辑
- 破坏 `MedAutoScience` 的主控定位

### 结论

采用方案 B。

## 高层实现分层

本轮实现应优先保持以下分层：

- 主 runtime：`DeepScientist`
- 医学主控：`MedAutoScience controllers / policies / overlays`
- 算法 sidecar：`ARIS adapter / controller / import surface`

建议最小能力拆分为：

- `algorithm sidecar recommendation`
- `ARIS input contract generation`
- `ARIS workspace provisioning`
- `ARIS result import`
- `mainline artifact consumption`

而不是先做一个笼统的“多 runtime 平台”。

## 验收标准

1. 主控可以根据任务特征推荐 `ARIS sidecar`
2. 推荐后必须等待用户确认，不能静默切换
3. sidecar 启动前必须冻结输入契约
4. `ARIS` 在独立工作目录运行，不污染主 quest 正式表面
5. 主线存在独立、规范化的 `algorithm_research/aris` 审计目录
6. sidecar 输出不仅包含实验结果，还包含论文叙事反馈工件
7. `claim_to_evidence_map` 缺失或不一致时，导入必须失败
8. 主线写作层可以只依赖导入后的正式工件，而不直接读取 sidecar 原始目录
9. `DeepScientist` 继续作为主 runtime，不因接入 `ARIS` 而退化为旁路组件
