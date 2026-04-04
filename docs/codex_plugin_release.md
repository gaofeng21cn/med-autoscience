# MedAutoScience Codex Plugin 发布说明

`MedAutoScience` 现已提供面向 Codex 的本地插件形态。

这不是把 `MedAutoScience` 重写成仅供 Codex 使用的新系统，而是在保留现有运行层、controller、profile、overlay 和 Python CLI 的前提下，新增一层面向 Codex 的原生接入表面。

## 用途

这个 Codex plugin 主要用于三件事：

1. 让 Codex 更自然地发现并调用 `MedAutoScience`
2. 让常用研究运行入口具备统一的 plugin / skill / MCP 表面
3. 在不破坏现有外部兼容性的前提下，为 Codex 提供更稳定的集成方式

当前插件已经提供：

- plugin manifest
- repo-local / home-local plugin 目录形态
- plugin skill
- plugin-local MCP manifest
- 只读 MCP server，覆盖 doctor、profile、overlay、runtime watch、data assets status、startup data readiness、MedDeepScientist upgrade check

## 设计边界

这个插件是薄入口，不是新的运行核心。

仍然保留为一等接口的能力有：

- `medautosci`
- `medautosci-mcp`
- `src/med_autoscience/controllers/`
- `src/med_autoscience/overlay/installer.py`
- `profiles/*.local.toml`

因此，这个插件不会降低 `MedAutoScience` 对其他框架、其他 agent 或外部包装层的兼容性。

## 安装方式

### 当前仓库内使用

在仓库根目录执行：

```bash
bash scripts/install-codex-plugin.sh
```

该脚本会：

- 以 editable 方式安装当前仓库
- 提供 `medautosci` 和 `medautosci-mcp`
- 在 `~/plugins/med-autoscience` 建立 home-local plugin 链接
- 在 `~/.agents/skills/med-autoscience` 建立 skill 发现链接
- 在 `~/.agents/plugins/marketplace.json` 写入插件入口

它不会替你安装 `MedDeepScientist` runtime；研究运行前仍需本机准备 `med-deepscientist` 并把 profile 指向该 checkout。

执行后请重启 Codex。

### 换一台电脑

最可靠的流程是：

1. clone 本仓库
2. 进入仓库根目录
3. 运行 `bash scripts/install-codex-plugin.sh`
4. 重启 Codex

## 文件位置

仓库内的关键文件如下：

- `plugins/med-autoscience/.codex-plugin/plugin.json`
- `plugins/med-autoscience/.mcp.json`
- `plugins/med-autoscience/skills/med-autoscience/SKILL.md`
- `src/med_autoscience/mcp_server.py`
- `src/med_autoscience/codex_plugin_installer.py`
- `scripts/install-codex-plugin.sh`

## 兼容性说明

Codex plugin 是新增入口，不替代现有运行层。

如果你已经通过以下任一方式接入 `MedAutoScience`，这些方式仍然成立：

- 直接调用 Python 包
- 调用 `medautosci`
- 调用 controller 模块
- 通过 profile + overlay 绑定具体 workspace

插件化带来的变化是“Codex 更容易接入”，不是“其他入口被废弃”。
