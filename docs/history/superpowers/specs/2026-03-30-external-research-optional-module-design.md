# External Research Optional Module Design

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

## 背景

当前 `MedAutoScience` 已经把 `portfolio/research_memory/` 上升为 workspace 级显式研究记忆层，但“是否调用外部 AI 做 deep research”仍缺少稳定的受管入口。

这会带来两个问题：

1. agent 容易临时自由发挥，直接自己想 prompt、自己决定存放位置，导致行为不稳定
2. 外部调研如果做了，结果容易只停留在聊天里，不能稳定沉淀为 workspace 可复用资产

用户这次明确要求：

- 外部 AI deep research 必须是可选模块
- 该模块只负责建议与 prompt 脚手架
- 不管用户是否真的去跑外部调研，都不能影响程序继续往下执行

## 问题定义

当前平台缺的是一个“optional enrichment surface”，而不是新的 gate。

也就是说，我们需要：

1. 一个标准 controller / CLI / MCP surface
2. 一个 workspace 级 prompt 落盘位置
3. 一个 workspace 级 external report 回收位置
4. 明确文档化的规则，说明它只是补强层，不是 startup prerequisite

## 目标

把“外部 AI deep research”上升为 `MedAutoScience` 的显性可选模块，并满足：

1. workspace 有统一的 prompt 目录与 external report 目录
2. 平台能一键准备 prompt 文件
3. 平台能检查该模块的当前状态
4. controller-first / scout 文案明确：这是 optional enrichment，不是 gate
5. 外部调研产物有稳定写回位置，后续可以再沉淀回 `portfolio/research_memory` 主资产

## 非目标

本轮不做：

- 自动调用 Gemini / ChatGPT API 去真正执行 deep research
- 把外部调研结果自动解析成最终结论
- 把外部调研模块加入 `startup_boundary_requirements`
- 让 lack of external reports 阻断 runtime 启动

## 设计原则

### 1. 建议层与 gate 层严格分离

本模块参照仓库已有模式：

- `startup_data_readiness`
  - 产出 recommendations，但不是 startup gate 本身
- `sidecar_provider`
  - recommendation / confirmation 与正式 provision 分离
- `portfolio_memory`
  - 负责 scaffold，不负责 compute gate

所以本模块只做建议、脚手架与状态检查，不进入 gate 计算。

### 2. Workspace 级落盘，而不是 study 级误归档

当外部 AI 回答的是：

- 这个疾病当前哪些课题值得做
- 同一批数据还能形成哪些文章
- 哪类研究通常投到哪些期刊

这些结论天然是 workspace 级，不应直接放到单篇 `study/`。

因此原始外部调研报告默认落到：

- `portfolio/research_memory/external_reports/`

而稳定结论再回写到：

- `topic_landscape.md`
- `dataset_question_map.md`
- `venue_intelligence.md`

### 3. Prompt 是 scaffold，不是假装自动研究

平台只负责准备 prompt，并尽量复用现有 workspace 研究记忆：

- `topic_landscape.md`
- `dataset_question_map.md`
- `venue_intelligence.md`

prompt 里要明确：

- `refs/` 只用于理解数据与历史背景，不代表要复现旧代码
- 目标是选题与论文布局，不是重跑 legacy code
- 外部公开数据是可选增强，不是为了堆无意义工作量

## 文件与目录

最小结构：

- `portfolio/research_memory/prompts/`
- `portfolio/research_memory/external_reports/`

标准 prompt 文件命名：

- `YYYY-MM-DD-workspace-topic-opportunity-deep-research-prompt.md`

标准外部报告命名：

- `YYYY-MM-DD-topic-opportunity-scout-<provider>.md`

## 平台能力

新增 controller：

- `med_autoscience.controllers.external_research`

至少提供：

1. `prepare_external_research(...)`
   - 初始化 `prompts/` 与 `external_reports/`
   - 生成 workspace-level prompt 文件
   - 返回建议与后续使用说明
2. `external_research_status(...)`
   - 报告目录、prompt、external reports 的状态
   - 明确 `optional_module_ready`
   - 生成 recommendations，但不产生 blocker

CLI 新增：

- `prepare-external-research`
- `external-research-status`

MCP 可同步暴露同名工具，方便 controller-first surface 保持一致。

## 文案升级

`controller_first` 与 `scout` 要明确：

1. 先读 `portfolio/research_memory/*`
2. 如仍需要额外外部视角，可用 `prepare-external-research`
3. 外部 AI 调研是 optional enrichment，不是 required gate
4. 返回报告后，原始文档放 `external_reports/`，稳定结论再写回主资产

## 当前 workspace 的首轮落地

在 `DM-CVD-Mortality-Risk` 当前 workspace 中，本轮直接落地：

1. `portfolio/research_memory/prompts/`
2. `portfolio/research_memory/external_reports/`
3. 一份面向 Gemini / ChatGPT Deep Research 的 workspace 级 prompt 文件

该 prompt 聚焦：

- 中国 40+ 医院糖尿病多中心临床数据
- 已获取的 NHANES public mortality sidecar
- 如何筛出 1-3 个真正值得做、能长成 SCI 文章的方向
- 第一篇论文如何设计、如何分层选刊、未来 study 如何布局

## 验收标准

1. `prepare-external-research` 能生成 prompt 与目录脚手架
2. `external-research-status` 能返回结构化状态与建议
3. `init-workspace` 默认创建 `prompts/` 与 `external_reports/`
4. `controller_first` / `scout` 文案明确 external research 是 optional enrichment
5. 当前糖尿病 workspace 已有 prompt 文件与 `external_reports/` 目录
6. 现有 startup gate 与 runtime router 行为不受影响
