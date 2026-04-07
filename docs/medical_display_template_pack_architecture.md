# 医学绘图模板包架构设计

## 文档定位

本文是 `med-autoscience` 医学绘图模板包化的权威设计文档。

它要解决的不是“再加几个模板”，而是把以下两件事正式拆开：

1. 论文配图模板库的持续扩充、迭代、分享与版本升级；
2. `med-autoscience` 主仓库作为绘图宿主平台的稳定内核开发。

本文用于回答：

- 模板库为什么要从当前代码内嵌形态中拆出来；
- 未来模板库应该如何作为独立可发布的模板包存在；
- 模板包可以带到什么程度；
- `med-autoscience` 平台内核和模板包生态的边界如何划分；
- 第一阶段怎么尽快落地，而不是长期停留在概念层。

相关文档：

- 平台主线与阶段推进：[medical_display_platform_mainline.md](./medical_display_platform_mainline.md)
- 论文家族路线图：[medical_display_family_roadmap.md](./medical_display_family_roadmap.md)
- 当前军火库总账：[medical_display_arsenal.md](./medical_display_arsenal.md)
- 军火库扩充历史：[medical_display_arsenal_history.md](./medical_display_arsenal_history.md)
- 当前模板目录：[medical_display_template_catalog.md](./medical_display_template_catalog.md)
- 当前工程审计面：[medical_display_audit_guide.md](./medical_display_audit_guide.md)
- 当前实施计划：[medical_display_template_pack_implementation_plan.md](./medical_display_template_pack_implementation_plan.md)

## 一句话结论

以后医学绘图模板库不再只是主仓库里的内嵌注册表，而应升级为“独立可发布的模板包生态”。

`med-autoscience` 主仓库负责：

- 包发现与安装；
- 依赖解析与版本锁定；
- 统一执行适配；
- 统一审计、投稿链路与 AI-first 视觉复核。

模板包负责：

- 模板声明；
- 绘图代码；
- 计算逻辑；
- 示例与 golden case；
- 外部高水平论文范例吸收；
- 视觉审计记录与版本迭代。

## 为什么现在必须拆

当前模板真相主要仍然嵌在代码里：

- `src/med_autoscience/display_registry.py`
- `src/med_autoscience/display_schema_contract.py`
- `src/med_autoscience/display_template_catalog.py`

这种方式在早期是合理的，因为当时最重要的是先把审计真相钉死，让模板、契约、渲染、质控和投稿链路统一收口。

但随着模板库继续扩张，这种结构开始产生四个问题：

1. 模板库迭代和平台主线开发强耦合。
   - 想扩一个模板，往往要同时碰 registry、schema、catalog、docs、tests。
2. 别人难以在不理解整个主仓库内核的前提下贡献模板。
   - 这不利于实验室内部协作，也不利于未来生态共享。
3. 模板库版本与平台版本无法清楚分离。
   - 现在很难说某篇论文究竟依赖的是“哪个模板包版本”，只能说依赖了某个仓库状态。
4. 学习高水平期刊图面的扩库动作，和主仓库稳定性维护动作被混在一起。
   - 这会让“军火库扩充”与“平台内核收敛”相互干扰。

因此，下一阶段的正确方向不是继续把所有模板逻辑都塞回中心注册表，而是把模板库升级为独立层。

## 设计目标

### 1. 模板库独立版本化

模板库应能独立发布、独立升级、独立回滚，而不要求每次都和主仓库主线开发绑在一起。

### 2. 模板包可共享

未来模板包既可以由 `fenggaolab.org` 官方维护，也可以由其他团队或个人提供，并通过本地目录、Git 仓库或 Python 包方式接入。

### 3. 包可以带代码

模板包不是纯静态资产包。

它可以包含：

- 模板 manifest；
- 绘图代码；
- 预处理和统计计算逻辑；
- QC 扩展；
- 示例输入；
- golden case；
- 高水平期刊范例；
- 视觉审计记录。

### 4. 平台仍保持严谨宿主角色

允许包自带代码，不等于允许包绕开宿主平台的统一链路。

`med-autoscience` 仍应保留：

- 统一 materialize 入口；
- 统一 publication / manuscript safety；
- 统一 catalog contract；
- 统一 submission package contract；
- 统一 AI-first 视觉审计闭环。

### 5. 模板保下限，AI-first 抬上限

模板包负责提供论文图的稳定下限。

最终图是否达到投稿级，仍由 AI-first 视觉审计与再修订闭环决定。

因此：

- 模板包进入正式生成链路是允许的；
- 但“包可用”不等于“图已最终投稿就绪”；
- 上限仍是平台统一治理的问题，不是靠把模板包管死来解决。

## 非目标

第一阶段不追求以下事情：

1. 不直接做完整的模板市场、评分系统或远端运营平台。
2. 不要求第一阶段就把所有现有模板的实现逻辑重写一遍，但迁移范围仍应是当前内置模板库的全量迁移。
3. 不要求第一阶段就支持任意语言、任意执行环境。
4. 不允许通过模板包重新引入静默修补、不可审计后处理或 heuristic 兜底。

## 总体分层

### 一、宿主平台内核

`med-autoscience` 以后应明确退到“宿主平台”角色。

职责包括：

- 发现模板包；
- 安装模板包；
- 解析依赖；
- 锁定版本；
- 装载模板；
- 调度执行；
- 统一收集生成产物；
- 统一跑 publication gate；
- 统一跑 submission packaging；
- 统一落盘 provenance；
- 统一触发 AI-first 视觉审计。

### 二、模板包生态层

模板包负责表达和实现具体绘图能力。

职责包括：

- 声明包元数据；
- 声明模板元数据；
- 提供绘图和计算代码；
- 提供 QC 扩展；
- 提供 exemplar / golden case / examples；
- 提供版本和兼容性信息；
- 提供包级 README、变更记录和维护责任。

### 三、军火库治理层

军火库相关文档不再只是“当前平台里注册了哪些模板”，而应记录：

- 当前有哪些包；
- 哪些能力已进入稳定军火库；
- 它们来自哪些论文；
- 它们提升了哪个 paper family；
- 它们当前是否已被真实论文证明。

## 命名与标识

### 1. 包标识

包使用反向域名风格命名：

`<namespace>.<pack_name>`

内置官方包使用：

`fenggaolab.org`

例如：

- `fenggaolab.org.medical-display-core`
- `fenggaolab.org.medical-display-survival`
- `fenggaolab.org.medical-display-omics`

### 2. 模板标识

模板从第一阶段起就全面使用完整名字，不保留新旧并行模式。

格式为：

`<pack_id>::<template_id>`

例如：

- `fenggaolab.org.medical-display-core::roc_curve_binary`
- `fenggaolab.org.medical-display-core::kaplan_meier_grouped`

说明：

- 当前系统里的 `template_id`、`shell_id`、`table_shell_id` 字段可以保留原字段名；
- 但字段值应直接升级为完整带命名空间的标识；
- 不再维持平面短名作为正式运行真相。

## 分发与安装模型

第一阶段同时支持三种来源：

1. 本地目录包
   - 适合本地快速迭代和 owner lane 开发。
2. Git 仓库包
   - 适合团队共享、外部分发、按 commit/tag 锁定。
3. Python 包
   - 适合作为标准化发布外壳，通过 `pip` 或私有 index 安装。

这里的关键设计是：

- “仓库式模板包”是原生格式；
- “Python 包”是分发外壳；
- 一个模板包既可以被当作原生仓库加载，也可以被打包成 Python 包发布。

## 官方推荐索引与显式源声明

第一阶段不做完整模板市场，但要支持“显式源声明 + 官方推荐索引”。

建议增加两个层次的配置：

### 1. 仓库级默认配置

建议文件：

`config/display_packs.toml`

职责：

- 声明默认启用的模板包；
- 声明官方推荐包源；
- 提供宿主平台默认军火库。

### 2. 论文级依赖配置

建议文件：

`paper/display_packs.toml`

职责：

- 覆盖或追加论文专用模板包；
- 锁定具体版本或来源；
- 明确该论文真实依赖了哪些包。

### 3. 论文级解析锁文件

建议文件：

`paper/build/display_pack_lock.json`

职责：

- 记录本次 materialize / submission 实际解析到的包、版本、来源、commit、安装方式；
- 作为可审计 provenance；
- 用于复现和对账。

## 包目录结构

第一阶段建议采用如下原生目录布局：

```text
<pack-root>/
  display_pack.toml
  README.md
  CHANGELOG.md
  pyproject.toml                # 可选；当作 Python 包发布时使用
  src/
    <python_module>/            # 可选；插件式执行代码
  scripts/
    ...                         # 可选；子进程式执行入口
  templates/
    <template_name>/
      template.toml
      examples/
      goldens/
      exemplars/
      audit/
  tests/
    ...
```

说明：

- `display_pack.toml` 是包级清单；
- `templates/<template_name>/template.toml` 是模板级清单；
- `src/` 用于 Python 插件式执行；
- `scripts/` 用于子进程式执行；
- `examples/` 保存最小输入样例；
- `goldens/` 保存 golden regression 基线；
- `exemplars/` 保存高水平论文图面学习来源与说明；
- `audit/` 保存视觉审计记录、已知问题、修正决策。

## 为什么清单格式选 TOML

第一阶段建议统一使用 TOML，而不是 YAML。

原因很具体：

1. Python 标准库已有 `tomllib`，读取成本低；
2. 不需要为了加载清单再引入 YAML 依赖；
3. TOML 足够表达包和模板元数据；
4. 配置、锁定和依赖声明更适合 TOML 这类结构化配置格式。

因此：

- 包清单：`display_pack.toml`
- 模板清单：`template.toml`
- 依赖声明：`config/display_packs.toml`、`paper/display_packs.toml`

## 包级清单设计

建议 `display_pack.toml` 至少包含以下字段：

| 字段 | 含义 |
| --- | --- |
| `pack_id` | 完整包名，例如 `fenggaolab.org.medical-display-core` |
| `version` | 包版本 |
| `display_api_version` | 兼容的宿主平台模板包 API 版本 |
| `summary` | 包简介 |
| `maintainer` | 维护者 |
| `license` | 许可证或内部使用声明 |
| `source` | 包来源说明 |
| `entrypoint_mode` | 默认执行模式，`python_plugin` 或 `subprocess` |
| `python_module` | 默认 Python 模块入口，可选 |
| `recommended_templates` | 推荐模板列表 |
| `paper_family_coverage` | 包主要覆盖哪些论文家族 |

## 模板级清单设计

建议 `templates/<template_name>/template.toml` 至少包含以下字段：

| 字段 | 含义 |
| --- | --- |
| `template_id` | 包内模板短名 |
| `full_template_id` | 完整模板名，格式为 `<pack_id>::<template_id>` |
| `kind` | `evidence_figure`、`illustration_shell`、`table_shell` |
| `display_name` | 人类可读名称 |
| `paper_family_ids` | 对应哪些论文家族 |
| `audit_family` | 对应哪个工程审计家族 |
| `renderer_family` | 渲染器家族或执行器类型 |
| `input_schema_ref` | 输入契约引用 |
| `qc_profile_ref` | QC 契约引用 |
| `required_exports` | 必须导出的格式 |
| `execution_mode` | `python_plugin` 或 `subprocess` |
| `entrypoint` | 执行入口 |
| `paper_proven` | 是否已有真实论文证明 |
| `golden_case_paths` | golden case 路径 |
| `exemplar_refs` | 高水平论文图面来源 |

## 执行模型

第一阶段同时支持两种执行路径。

### 1. 插件式执行

适合：

- 依赖简单；
- 希望直接复用宿主进程上下文；
- 需要更紧密接入平台内部对象的模板。

典型入口形式：

`python_module:function`

### 2. 子进程式执行

适合：

- 依赖较重；
- 需要隔离运行环境；
- 自带复杂统计或绘图流程；
- 未来可能不止 Python 一种实现语言。

典型入口形式：

- 可执行脚本
- `python -m ...`
- 其他可审计命令入口

### 3. 两种执行的统一要求

无论是插件还是子进程，都必须服从统一宿主契约：

- 输入必须是结构化、可审计的；
- 输出必须写回统一的 generated surface；
- 产物必须能进入统一 catalog contract；
- 产物必须经过统一的 publication / manuscript safety；
- provenance 必须进入锁文件与报告面。

## 代码边界

模板包允许带代码，但代码边界必须清楚。

### 包可以做什么

- 绘图；
- 预处理；
- 统计计算；
- 局部 QC；
- 生成 sidecar；
- 提供包内 golden regression。

### 包不能绕开什么

模板包不得绕开宿主平台的统一约束：

- figure/table catalog 必填字段；
- generated output 的固定落盘位置；
- publication gate；
- submission minimal / submission manifest；
- AI-first 视觉审计闭环；
- manuscript-facing forbidden-term / safety 约束。

也就是说，模板包可以强，但不可以私自变成另一套不可审计的投稿系统。

## 军火库与主线如何正式拆开

包化之后，未来会出现两条清晰独立的线：

### 1. 军火库扩库线

目标：

- 学习高水平期刊图面；
- 形成新模板包或升级现有模板包；
- 更新 exemplar、golden、audit 和历史文档；
- 让更多论文图式进入可复用能力层。

这条线的主要变更应落在：

- `display_pack.toml`
- `template.toml`
- 模板包代码
- 模板包示例与 golden
- 军火库文档

### 2. 平台内核主线

目标：

- 升级宿主平台装载能力；
- 升级统一 contract、QC、publication gate；
- 升级 dependency resolution、lock、provenance；
- 升级 AI-first 视觉审计闭环；
- 升级 submission 和 catalog 消费层。

只有当现有平台承载不了新模板包需求时，才应该动这一层。

## 与现有军火库文档的关系

包化之后，现有文档仍然保留，但角色更清楚：

- [medical_display_arsenal.md](./medical_display_arsenal.md)
  - 记录当前军火库全貌；
  - 不等于宿主平台代码清单；
  - 以后更多体现“包级能力账本”。
- [medical_display_arsenal_history.md](./medical_display_arsenal_history.md)
  - 记录扩库历史；
  - 应追加“新增了哪个包 / 提升了哪个包版本 / 学自哪篇论文”。
- [medical_display_template_catalog.md](./medical_display_template_catalog.md)
  - 以后改为“当前装载模板包后生成的活动模板目录”；
  - 不再暗示所有模板都必须内嵌在主仓库注册表里。

## 一次性迁移原则

本次迁移采用“直接切换，不做长期新旧并行”。

原因：

1. 当前真实项目数量有限，迁移成本可控；
2. 长期维持双标识只会制造管理负担；
3. 既然架构已经明确，就应尽早把完整包名变成唯一正式真相。

因此第一阶段就应：

- 把当前内置模板库全量归入 `fenggaolab.org` 命名空间；
- 把 catalog、tests、paper inputs、submission manifests 中的平面模板名升级为完整模板名；
- 把 `001/003` 作为首轮强验收锚点，而不是作为迁移范围边界；
- 提供一次性迁移工具，而不是维持长期别名系统。

## 分阶段落地方案

### Phase 1：宿主平台最小包化骨架

目标：

- 定义 `display_pack.toml` 与 `template.toml`；
- 实现本地目录包装载；
- 实现完整模板名解析；
- 让 catalog 能从包清单生成，而不是只读中心注册表。

产出：

- 包加载器
- 最小依赖解析器
- namespaced template ID 支持

### Phase 2：内置核心包迁移

目标：

- 建立 `fenggaolab.org.medical-display-core`；
- 把当前内置模板库全量迁入该包；
- 保持现有 `001/003` 真实论文基线可重新 materialize，并作为首轮强验收锚点。

产出：

- 第一个内置官方模板包
- 现有模板一次性命名空间迁移
- 当前内置模板库的全量包化迁移完成

### Phase 3：Git 包与 Python 包支持

目标：

- 支持从 Git 仓库装载模板包；
- 支持从 Python 包装载模板包；
- 形成官方推荐索引。

产出：

- `config/display_packs.toml`
- `paper/display_packs.toml`
- `paper/build/display_pack_lock.json`

### Phase 4：执行模型全面打通

目标：

- 同时支持插件式与子进程式模板执行；
- 把 provenance、catalog、publication gate、submission chain 全部串通。

产出：

- 统一执行适配层
- 统一 provenance 落盘
- 包级 execution contract

### Phase 5：军火库线正式独立运转

目标：

- 外部高水平论文图面学习不再必须先改主线代码；
- 新能力优先通过模板包演进；
- 主线只在需要新宿主 API 时才升级。

产出：

- 模板包生态开始独立运转
- 主线开发与扩库开发正式解耦

## 最短落地路径

如果目标是“尽快开始，而不是继续停在规划”，最短路径应是：

1. 先定义 `display_pack.toml` / `template.toml` / repo-level / paper-level 配置格式；
2. 实现本地目录包加载器；
3. 新建内置核心包 `fenggaolab.org.medical-display-core`；
4. 把当前内置模板库全量迁到核心包；
5. 一次性把现有模板标识切到完整包名；
6. 让 `medical_display_template_catalog.md` 从活动模板包重新生成；
7. 用 `001/003` 做首轮强验收，确认 materialize / submission / publication 相关链路重新跑通；
8. 再补 Git 包与 Python 包接入；
9. 最后再把论文级 lock 与 provenance 收严。

换句话说，最快的路线不是先做模板市场，而是先把“一个内置核心包 + 一个本地目录包加载器”跑通。

## 完成判据

这套架构真正落地，至少要看到以下结果：

1. 内置模板不再只能在中心注册表里定义；
2. `fenggaolab.org` 命名空间正式成为内置模板真相；
3. 论文 materialize / catalog / submission 能消费完整模板名；
4. 至少支持一个本地目录包和一个 Git 包；
5. 包版本和来源能进入 paper-level provenance；
6. 军火库扩库不再默认等价于主仓库内核升级。

## 当前建议

当前最正确的下一步，不是继续抽象讨论，而是直接进入 Phase 1：

- 先做模板包最小骨架；
- 先完成内置核心包的全量迁移；
- 先让完整命名空间模板名在现有 `001/003` 路径上重新跑通。

做到这一步，这条线就真正从“概念上的模板包化”进入“可持续扩库的包生态起点”。
