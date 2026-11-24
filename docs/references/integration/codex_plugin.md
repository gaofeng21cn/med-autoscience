# Codex Plugin Carrier 与 OPL Handoff

Owner: `MedAutoScience`
Purpose: `codex_plugin_carrier_and_opl_handoff_reference`
State: `support_reference`
Machine boundary: 可调用面、generated-surface 与 carrier 边界的机器真相归 `agent/`、`contracts/action_catalog.json`、`contracts/domain_handler_registry.json`、`contracts/generated_surface_handoff.json`、`contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`、`contracts/carrier_projection.json`、`contracts/capability_map.json`、`plugins/med-autoscience/.codex-plugin/plugin.json`、源码、测试及 OPL read-model 输出。

## Primary Skill 与 Plugin Carrier 单源边界

| Surface | 职责 | 不承担 |
| --- | --- | --- |
| `agent/primary_skill/SKILL.md` | MAS 标准 OPL primary skill canonical source（`capability_map.json` 声明 `canonical_source`） | 不直接写 study truth、paper body、owner receipt、typed blocker、publication verdict、current package 或 runtime queue |
| `plugins/med-autoscience/skills/med-autoscience/SKILL.md` | Codex plugin install carrier 的 materialized full skill copy（满足 Codex plugin 安装对真实 `SKILL.md` 的要求） | 不定义第二套 MAS 业务能力，不持有 agent membership/status 权威，不覆盖 canonical source 或写领域真相 |

`plugins/med-autoscience/` 只是 Codex plugin carrier projection，不是 MAS Package identity、完整 installed Package、CLI、MCP server、installer 或 runtime。Codex CLI 是当前默认 executor，Package identity、capabilities、dependency identity、business work item 与 typed views 保持 executor-neutral。仓库采用**单源布局 + 构建期载体物化**：Git 仅在仓根跟踪唯一的 `agent/`、`contracts/`、`src/`、`docs/`、`profiles/`、`runtime/`、`assets/`、`bootstrap/`，而在 `plugins/med-autoscience/` 下只跟踪薄载体壳（`plugin.json`、`.codex-plugin/plugin.json`、`opl-package.json`、`app-contribution-adapter.json`、`bin/mas-app-contribution`、`assets/icon.{png,svg}` 与 `skills/med-autoscience/{SKILL.md,agents/openai.yaml}`；根 `bin/mas-app-contribution` 仅作源码仓转发），不向 Git 提交任何镜像源码/合同/文档副本；repo-local CLI/MCP JSON-RPC、专用 installer 与旧 wrapper 已退役，不得恢复为执行或 proof lane。

需要构建完整的自包含本地载体载荷时，运行 `python3 scripts/materialize_plugin_carrier.py`（调用 `opl pack project-carrier` 依据 `contracts/carrier_projection.json` 将仓根受控资源按需物化至 `plugins/med-autoscience/` 下被 `.gitignore` 忽略的构建期镜像路径，同时保持受控载体元数据与 `SKILL.md` 版本/字节同步；测试、`docs/site/` 与本地数据不进入载荷）。验证阶段先按需物化再运行 `python3 scripts/materialize_plugin_carrier.py --check` 校验字节与权限，同时由 `tests/test_package_contracts.py` 守护 Git 中零镜像副本与薄载体单源一致。Framework 从版本提交读取受控文件生成唯一发布 content lock。

## Generated Surface 与 OPL Handoff 路径

MAS 不再维护 repo-local product-entry builder、status/workbench shell、CLI parser 或 MCP transport。OPL 从 MAS pack 输入编译/托管 CLI、MCP、Skill、product-entry、status 与 workbench：

- **六个公开 Stage action**：`direction_and_route_selection`、`baseline_and_evidence_setup`、`bounded_analysis_campaign`、`manuscript_authoring`、`review_and_quality_gate`、`finalize_and_publication_handoff`，统一通过 `execution_binding` 指向 `agent/stages/manifest.json#<canonical_stage_id>`。
- **六个 host-only authority action 与七个 closed-registry callable**：qualification work-item provisioning、study initialization、study lifecycle reactivation、candidate admission、build-dependency currentness 与 paper mission 仅供 host 内部通过 `contracts/domain_handler_registry.json` 调用（无 CLI/MCP/Skill/product/OpenAI/AI SDK 用户面）；registry 另绑定 `mas.agent-lab-self-evolution-closeout`。非 V2 catalog 成员的旧命令与旧内部名仅作退役 provenance，不得通过文档或兼容层恢复为可执行入口。
- **两条共享集成路径**：Direct MAS app skill（`User/Agent -> MAS primary skill -> OPL generated Stage action -> OPL Stage runtime -> MAS owner surface`）与 OPL stage handoff（`User/Agent -> OPL stage runtime -> StageRun/receipt/projection -> MAS owner surface`）共享相同的 Stage action、V2 closed schemas、study semantics 与 forbidden-write 边界。

使用时序：1) 从 OPL generated/hosted surface 获取 `workspace_root`、`study_id` 与当前 refs；2) 根据研究目标选择六个 Stage action 之一（`requires` 是质量上下文而非固定顺序门）；3) OPL 持有 StageRun/attempt 并在 Tool Affordance Boundary 内调度 ScholarSkills/Connect/Runway/Workspace；4) MAS 纯函数只消费 refs 并返回医学 gate input/result；5) 仅在写范围、authority 与 human gate 同时成立时写入 MAS-owned surface（新 workspace 默认 no root Git / no quest Git）。

## 安装、分发与运行 Owner

仓库存在 plugin carrier 不等于本机已加载或完整 MAS Package 已安装。完整 Package bytes 由 MAS owner 独立发布至自身 GHCR `latest-stable`；Python package 按标准 packaging/`uv sync` 或 OPL workspace override 安装，运行环境由 OPL 依据 `contracts/runtime_environment_requirements.json` 准备。

跨机器生命周期唯一用户入口为：

```bash
opl packages install mas
opl packages update mas
opl packages uninstall mas
```

`mas-scholar-skills` 缺失、禁用或所需能力不可调用时，仅 MAS readiness fail-closed 并进入托管安装/修复，不阻断无关 Package，也不以跨包版本范围/ABI/lock/payload/digest/共享 Release Set 为普通 readiness 门。从源码克隆调试原生 Codex Plugin Carrier 时，可通过 `codex plugin marketplace add "${repo_root}"` 与 `codex plugin add med-autoscience@med-autoscience` 安装验证（或通过 `codex plugin remove` / `marketplace remove` 移除），并通过以下 OPL 入口回读完整 Package 与 hosted work-item 状态：

```bash
opl packages status --package-id mas --json
opl packages status --package-id mas --scope workspace --target-workspace <absolute_path> --json
opl workspace work-item readback --workspace <absolute_path> --work-item <id> --agent mas --profile full
```

若已有同 identity 的受管 StageAttempt，须先读取其 durable 状态与 owner 再通过 Framework 公开入口操作，禁止并行写入同一研究 source 或创建第二 runner。Generated interface parity、scaffold/schema valid 或 carrier install 均只证明结构与发现，不证明 runtime live、paper progress 或 publication ready。
