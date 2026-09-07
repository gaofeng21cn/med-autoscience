# Data Asset Management

Owner: `MedAutoScience`
Purpose: `medical_data_use_and_mutation_policy`
State: `active_policy`
Machine boundary: dataset manifest、study binding、source evidence 与 owner receipts 持有数据事实。
本页不提供私有 data mutation API、scanner 或 runtime gate。

## 准入与使用

数据 release 必须绑定来源、version、真实 outputs、access tier、license、质量结果和
允许用途；空目录或 manifest 本身不能证明数据可用。
私有随访刷新、字段纠错、多中心追加均形成可追溯的新 release，
不静默覆盖正在被 study 使用的 source。

受限原始数据只用于受权审计和 provenance；去标识与标准化 release 必须保留
源字段、转换和质量证据。Study 只使用其明确绑定且允许直接消费的 release。
布局和各事实面归 [数据模型](../../source/medical_data_asset_target_operating_model.md)。

公开数据须有具体研究用途，例如外部验证、cohort extension 或机制支持；
记录 accession、license、access、endpoint、target study 和纳入/拒绝理由。
可选公开数据机会本身不阻断当前研究，只有 study contract 必需条件才成为准入条件。

## 更新与影响

受权 StageAttempt 在 canonical source owner 下执行 mutation，记录输入、产物、
失败和是否完成 projection refresh。Registry 是 manifest/receipt 的派生索引，
不能手写 registry 来绕过数据事实或 authority。

新版本不自动使所有旧研究失效。比较 cohort、变量、endpoint、转换和分析输入的
实质变化，由 MAS 评估受影响研究、既有 Review 和 claim；缺失研究必需数据或
违反 access/identity 边界时 fail closed，普通扩展机会保持 advisory。

共享 release 不接受 study-specific cohort、index event、sensitivity set 或 model matrix
回写；这些产物留在 study analysis tree 并引用 parent release。
归档、移动与删除须经过 [Data Retention](../../runtime/data_asset_storage_retention.md)。

## 外部能力

工具只提供查询、计算或候选解释。ToolUniverse 等外部能力是否可调用由当前
descriptor/carrier 决定，不能替代 MAS source readiness、study binding、
quality/artifact authority 或 Framework provider/runtime owner。
