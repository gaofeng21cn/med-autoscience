# OPL Dependency Environment Substrate 目标架构

Owner: `OPL Framework`
Purpose: `mas_display_dependency_environment_consumer_design`
State: `consumer_design`
Machine boundary: 本文是 MAS 仓内记录的 OPL runtime environment substrate consumer 设计，用于约束 MAS display pack 如何声明 dependency intent、消费 receipt/run-context 并保持 false-ready 边界。canonical substrate contract 与可执行 readback 位于 OPL 主仓 `contracts/opl-framework/runtime-environment-substrate-contract.json` 与 `opl runtime env * --json`；本文不是 OPL materializer landed 证据，也不是 MAS live/runtime ready、publication truth、artifact authority、owner receipt 或 typed blocker。

## 目标结论

依赖环境是 OPL Agent OS 的通用基座能力，不是 domain renderer、skill 或模板自己的职责。Domain pack 只声明依赖需求；OPL 负责解析、锁定、prepare、缓存、诊断和生成 managed run context；domain runtime 只消费 OPL 提供的环境回执并执行自己的领域任务。

对 MAS medical display 来说，这意味着 R/ggplot2 模板可以直接选择最优 R 包和系统依赖，不需要为了“环境难装”退回低质量实现。对 OPL 来说，这是一套可复用的 substrate：写书、绘图、数据分析、PDF/Office 生成、图片处理和其他 domain pack 都可以共享同一环境准备机制。

## 为什么不能留在模板里

如果每个 renderer 自己安装依赖，会产生四类问题：

- 模板代码被环境治理污染，无法专注图形质量。
- 同一论文多张图无法共享环境 fingerprint，难以复现。
- 缺系统库、缺权限、lock stale 和视觉质量问题混在一起，MAS 无法给出正确 typed repair route。
- 智能体现场临时修包会拖慢进度，并引入不可审计的隐式升级。

正确边界是：renderer 失败只应该反映 renderer / data / style / layout 问题；依赖缺失应该在 render 前由 OPL doctor 识别并路由。

## 通用能力面

| Surface | 输入 | 输出 | 责任 |
| --- | --- | --- | --- |
| `opl runtime env inspect` | dependency intent refs、目标平台、policy | descriptor / materialization boundary readback | 读取需求边界，不安装。 |
| `opl runtime env lock` | descriptor / resolver plan | runtime lock projection | 固定版本、系统需求、channel、container digest 的目标边界。 |
| planned materialize / prepare | lock ref | prepared environment、cache refs、receipt | 后续创建或复用环境。 |
| `opl runtime env doctor` | lock 或 prepared env ref | missing dependency / permission / platform diagnostics | 诊断并分类修复路线。 |
| `opl runtime env run-context` | prepared receipt、profile ref | argv prefix、env vars、binary path、fingerprint | 给 domain runtime 一个可执行上下文。 |
| `opl runtime env cache status` | lock hash、cache policy | cache hit/miss/eviction readback | 复用环境，避免每次重建。 |

这些 surface 可以由不同底层实现承接：`renv`、`pak sysreqs`、`uv`、conda / pixi、versioned biomedical containers、digest-pinned Docker image 或混合 profile。OPL 对外暴露统一合同，不把底层工具泄漏给 domain agent。

## 合同对象

最小对象族：

- `DependencyRequirementProfile`：domain pack 声明依赖需求。
- `DependencyEnvironmentLock`：OPL 解算后的可复现环境锁。
- `DependencyEnvironmentReceipt`：OPL 已准备环境或失败诊断的回执。
- `DependencyRunContext`：domain runtime 执行 renderer / tool 时消费的环境上下文。
- `DependencyEnvironmentDoctorFinding`：缺包、缺 binary、缺系统库、权限不足、平台不支持、lock stale、cache corrupt 等结构化 finding。

这些对象都只能携 refs、fingerprint、版本和诊断，不携 paper body、artifact body、memory body、publication verdict 或 owner receipt body。

## MAS medical display 接入

MAS 侧目标接入点：

- `renderer_dependency_profile.json` 升级为 OPL 可消费的 `DependencyRequirementProfile`，其中 R/ggplot2 evidence renderer 声明基础 R 包，cohort/reporting-flow shell 另声明 `ggconsort`-capable profile；该 profile 把 `ggconsort` 声明为 GitHub source dependency `tgerke/ggconsort`。
- `display_pack_agent.preflight` 查询 dependency receipt；缺失时返回 `opl_pack_substrate_issue`、`dependency_lock_refresh_required` 或 `human_or_admin_gate_required`。
- `display_pack_render` 只消费 `DependencyRunContext`，不直接依赖 host PATH / site library，也不在 renderer 内安装 R 包或拉取 GitHub source。
- `display_pack_lock.json`、render receipt 和 publication manifest 保存 dependency lock / receipt refs。
- visual audit 继续审图，不审依赖；依赖回执不能替代视觉审计。
- `cohort_flow_figure` 当前 checked-in renderer 是 R/ggplot2 + `ggconsort` subprocess renderer；`ggconsort` 来自 dependency intent 中的 GitHub source `tgerke/ggconsort`，必须由 OPL prepare 交付 managed run context 后再执行。缺 prepared receipt / run-context 时，MAS fail closed 到 dependency route；不能在 renderer 内安装依赖，也不能把任何 fallback 输出写成已使用 `ggconsort`。

详细 medical-display 消费设计见 `docs/delivery/medical-display/contracts/display_dependency_environment_os_target.md`。

## OPL 基座优化原则

1. 默认快路径优先：有 cache hit 时不重建环境；lock 未变时只做 cheap doctor。
2. 显式更新：依赖升级必须走 lock refresh，不允许 renderer 静默升级。
3. 可诊断失败：环境失败必须分类到 dependency / system / permission / platform / cache / stale lock，而不是只暴露 stderr。
4. 可复用：同一 pack profile 在一篇论文或多个 stage 中共享 environment fingerprint。
5. 可降噪：普通 agent 不需要理解 renv、uv、conda 或 Docker 细节，只看 prepared / missing / needs admin / stale lock。
6. 权限分层：系统包安装、container daemon、外部网络或管理员权限必须是 OPL policy 或 human/admin gate，不由 domain renderer 请求。
7. 证据不越界：prepared environment 证明环境可用，不证明科学正确、图达标、论文可投。

## 晋级门槛

MAS consumer slice 当前可以通过 display preflight/render 消费 prepared receipt 与 run-context refs；OPL substrate 仍是 `contract_and_readback_skeleton`。晋级到 runtime materialized ready 前需要 OPL repo 给出：

- 可执行 CLI 或 API surface 覆盖 resolve / lock / prepare / doctor / run-context / cache。
- focused tests 覆盖 R-first、Python、mixed profile、missing package、missing system requirement、permission required、stale lock、cache hit/miss。
- MAS display pack preflight/render 使用 dependency receipt 和 run-context 的集成测试。
- `ggconsort` GitHub source dependency `tgerke/ggconsort` 的 resolve / lock / prepare / cache / run-context readback。
- 至少一个 R/ggplot2 evidence renderer 通过 prepared environment 完成 render，并记录 session/package versions。
- contracts / docs / generated surfaces 明确 forbidden authority：不能写 MAS truth、不能签 publication readiness、不能替代 visual audit 或 owner receipt。
