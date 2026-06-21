# Medical Display 依赖环境 OS 目标设计

Owner: `MedAutoScience`
Purpose: `medical_display_dependency_environment_os_target`
State: `target_architecture`
Machine boundary: 本文是人读目标设计。机器合同草案在 `contracts/opl-framework/dependency-environment-substrate-contract.json`；当前 MAS Display Pack 真相仍归 `contracts/display-pack-contract.v2.json`、`display_pack.toml`、`templates/*/template.toml`、`renderer_dependency_profile.json`、Display Pack runtime、真实 render/QC/audit refs、owner receipt 和 publication gate。本文不声明 OPL 依赖环境基座已落地，也不授权 publication-ready、submission-ready、artifact authority 或 study truth mutation。

## 结论

医学绘图依赖环境应该由 OPL 基座统一解决。Display Pack 和模板只声明“需要什么”，不在 renderer 内安装、升级、修补或猜测依赖。OPL 负责把依赖需求解析成锁文件、准备可复用环境、产出 run-context 和可审计回执；MAS 负责把这些 refs 接入 display preflight、render receipt、display lock、visual audit 和 typed repair route。

这条边界解决当前缺口：`renderer_dependency_profile.json` 已能表达 R/ggplot2 模板需要 `Rscript`、`jsonlite`、`ggplot2`、`ggsci`、`Rtsne`、`uwot` 等依赖，但它还只是 pack 局部说明，不是一个可执行的 OPL environment contract。理想状态下，模板作者只选择最合适的 R / Python / SVG / image generation 技术栈；依赖安装、系统包、缓存、锁定、跨平台和诊断由 OPL 负责。

OPL 通用基座设计见 `docs/runtime/designs/opl_dependency_environment_substrate_target.md`；本文只说明 medical display 如何消费该基座。

## 外部经验转译

| 成熟经验 | 可取之处 | 本系统采用方式 |
| --- | --- | --- |
| `renv` | R 项目独立库与 lockfile / restore 语义。 | R/ggplot2 evidence renderer 默认由 OPL 生成 R dependency lock，renderer 只消费已准备的 R library path。 |
| `pak` sysreqs | R 包系统依赖独立解析。 | OPL doctor 区分 R 包缺失和系统库缺失，缺系统库走 OPL substrate / admin gate，不让 R 脚本现场安装。 |
| Bioconductor / Rocker 容器 | 版本化 biomedical R 环境和预构建生态。 | 对 single-cell、omics、survival 等重依赖模板，优先允许 OPL 选 versioned biomedical base image，并在 publication reproducibility 场景 pin digest。 |
| `uv` | Python lock 与 sync 分离，支持 frozen / locked execution。 | 未来确有 Python 优势的模板必须用锁定环境，不再靠 host Python 隐式包。 |
| conda / pixi | 多语言、系统级和 compiled 包环境可锁定。 | R + Python + system library 混合模板交给 OPL mixed profile，不把复杂环境写进 MAS renderer。 |
| Docker digest pinning | 复现型交付需要固定基础镜像 digest。 | publication-grade environment lock 记录 image ref 和 digest；digest 不是质量 verdict，只是环境 provenance。 |

## 目标运行链路

```text
renderer_dependency_profile.json
  -> OPL pack env resolve
  -> dependency_environment_lock.json
  -> OPL pack env prepare / cache / doctor
  -> dependency_environment_receipt.json
  -> OPL pack env run-context
  -> MAS display-pack preflight
  -> renderer execution
  -> render receipt / display_pack_lock / visual audit
```

关键规则：

- `renderer_dependency_profile.json` 是需求声明，不是安装脚本。
- `dependency_environment_lock.json` 固定包、版本、系统依赖、channel / repository、runtime version、container digest 和 resolver version。
- `dependency_environment_receipt.json` 证明环境已准备、包和 binary 检查通过、run-context 可用。
- render 前如果缺 prepared receipt，MAS 应 fail closed 到 `opl_pack_substrate_issue`、`dependency_lock_refresh_required` 或 `human_or_admin_gate_required`，而不是让 R/Python 脚本报错后再猜。
- renderer 可检查包是否存在，但不得 `install.packages()`、`pip install`、`conda install`、`brew install` 或静默升级。

## MAS / OPL 分工

| 层级 | Owner | 职责 | 不得越界 |
| --- | --- | --- | --- |
| Dependency intent | MAS Display Pack | 声明 renderer family、runtime binary、语言包、系统需求、模板适用范围、run-context 需求。 | 不安装依赖，不授权 publication readiness。 |
| Dependency resolve / lock | OPL Dependency Environment OS | 解算依赖、固定版本、记录系统需求、生成 lock。 | 不改 MAS study truth、figure data、统计值或 publication verdict。 |
| Environment prepare / cache | OPL Dependency Environment OS | 创建 R library / Python venv / conda env / pixi env / container runner，复用缓存，产出 receipt。 | 不把 cache hit 写成图质量或论文进展。 |
| Run context handoff | OPL Dependency Environment OS | 提供 binary path、env vars、library path、container runner ref、execution fingerprint。 | 不直接修改 MAS display artifacts。 |
| Render / QC / audit | MAS Display runtime | 消费 run-context，执行 renderer，记录 request/stdout/stderr/artifact/layout/QC/audit refs。 | 不在 renderer 内安装依赖，不用依赖 receipt 替代 visual audit。 |
| Typed repair route | MAS authority + OPL transport | 缺依赖路由到 OPL substrate；缺系统权限路由到 human/admin gate；图形质量问题回到 template/style/QC repair。 | 不把 dependency failure 误归因到模板视觉质量。 |

## Display Pack 声明面

当前 core pack 的 `renderer_dependency_profile.json` 应继续保留，但长期需要升级为 OPL 可消费的声明形状：

```json
{
  "profile_id": "r_ggplot2_evidence_subprocess_v1",
  "execution_mode": "subprocess",
  "renderer_family": "r_ggplot2",
  "runtime_binaries": [{"name": "Rscript", "required": true}],
  "language_packages": {
    "r": [
      {"name": "jsonlite", "role": "render request JSON IO"},
      {"name": "ggplot2", "role": "core grammar"},
      {"name": "ggsci", "role": "journal palettes"}
    ]
  },
  "system_requirements": [],
  "run_context_requirements": {
    "r_lib_path_required": true,
    "session_info_required_in_receipt": true,
    "network_access_during_render": false
  }
}
```

模板作者只维护这个需求声明。OPL 可根据 policy 选择 `renv`、`pak sysreqs`、conda/pixi、container digest 或混合 profile；MAS 不应该在每个 `render.R` 里重复判断依赖环境。

## 回执和锁文件

目标锁文件：

- `paper/build/dependency_environment_lock.json`
- 记录 `lock_id`、target platform、manager、source requirement refs、runtime versions、package records、system requirement records、container image digest、resolver version、repository/channel refs、lock hash。

目标准备回执：

- `paper/build/dependency_environment_receipt.json`
- 记录 `lock_ref`、`lock_sha256`、environment ref、cache key、binary/package/system checks、run-context ref、status、failure class。

目标 render receipt 应引用：

- dependency requirement profile ref；
- dependency lock ref；
- dependency prepare receipt ref；
- run-context fingerprint；
- renderer session info，例如 R version、package versions、R library path hash。

这些 refs 只证明环境可复现和可诊断，不证明科学结论、视觉审计、publication-ready 或 submission-ready。

## 对 MAS 智能体调用的影响

智能体画图时的理想路径应变成：

1. 从 `display_pack_agent.orchestrate` 得到 template / renderer / dependency profile refs。
2. preflight 先查询 OPL dependency receipt；缺失时直接请求 OPL prepare 或返回 typed route，不进入 renderer。
3. render 只消费 OPL run-context；R/ggplot2 模板成为 first-class renderer，不需要把依赖安装逻辑塞进模板。
4. 依赖问题和视觉质量问题分开：缺 `uwot`、`Rtsne`、系统库、字体或容器权限时走 substrate repair；legend 重叠、配色漂移、panel 拥挤时走 template/style/QC/visual audit repair。
5. `display_pack_lock.json` 和 publication manifest 保存 dependency lock/receipt refs，方便一篇论文多张图使用同一个环境 fingerprint。

## 落地门槛

把本文从 `target_architecture` 晋级为 landed，至少需要：

- OPL repo 有 `opl pack env resolve|lock|prepare|doctor|run-context|cache` 可执行面和 focused tests。
- MAS `display_pack_agent.preflight` 能读取 dependency receipt，缺环境时 fail closed 到 typed route。
- MAS render runtime 能消费 OPL run-context，而不是直接依赖 host PATH / site library。
- `display_pack_lock.json`、render receipt 和 publication manifest 保存 dependency lock / receipt refs。
- 至少一个 R/ggplot2 evidence renderer 用 prepared environment 生成图，并在 receipt 中记录 R session/package versions。
- 缺依赖、系统库、权限、lock stale、cache corrupt 的错误类别可区分，并不会被写成 publication quality failure。

## 当前不做

- 不要求每个模板自己实现依赖安装。
- 不为了 Python/R 双栈比较保留重复模板；依赖环境能力服务“使用最优技术栈”，不是鼓励多版本并存。
- 不把 Docker / container 作为默认唯一方案；R-first renderer 可用 host-managed prepared R library，也可在重依赖或 publication reproducibility 场景用 digest-pinned container。
- 不让 OPL dependency receipt 签 MAS owner receipt、typed blocker、publication verdict 或 artifact mutation authority。
