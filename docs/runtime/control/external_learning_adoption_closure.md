# External Learning Adoption Closure Runbook

Owner: `MedAutoScience`
Purpose: `external_learning_landing_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 external-learning landing runbook。机器真相继续归 MAS `agent/` pack、contracts、source、generated/read-model surfaces、owner callables、worker/sidecar outputs、owner receipts、typed blockers、AI reviewer / auditor records、publication eval、controller decisions、真实 workspace artifacts、OPL current-control 和 repo-native verification。本文不引入外部 runtime，不安装外部 worker，不写 study truth、paper body、artifact body、memory body、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 适用范围

本 runbook 适用于 Co-Scientist、Nature-skills、Academic Research Skills、AutoSci / OmegaWiki、EvoScientist / EvoSkills、ARK、ARIS、PaperSpine、PaperOrchestra、Open Auto Research 和同类自动研究框架的 MAS intake。

核心规则：**学合同不等于落地**。外部框架的模式被写进 contract、reference intake 或 design doc，只说明 MAS 接受了一个可复用 shape；只有进入 MAS-owned owner surface、generated/read-model projection、worker/sidecar execution slot、callable/action catalog、quality pack consumer、controller-authorized soak 或等价 repo-native surface，并有测试证明边界，才算 functional landing。

## Landing Definition

每个外部学习项必须标注一个 landing status：

| status | 含义 | 能否说 landed |
| --- | --- | --- |
| `owner_surface_landed` | MAS owner surface、quality pack、source/artifact/reviewer OS 或 callable 已消费该模式。 | 可以，但必须说明 authority boundary。 |
| `read_model_landed` | generated/product-entry/domain-handler/read-model surface 可稳定投影该模式。 | 可以，但只能说 read-model landed。 |
| `sidecar_or_worker_landed` | 有非阻塞 worker、sidecar、soak 或 owner action execution slot，且声明 allowed writes / forbidden authority / outputs。 | 可以，但不能说它关闭 paper progress 或 quality gate。 |
| `contract_projection_landed` | contract 和 projection 存在，但没有独立 owner callable 或 worker scaleout。 | 只能说 projection landed，不能说 execution landed。 |
| `contract_only_gap` | 只有合同或规则，未接入 owner/read-model/worker/callable。 | 不能说 landed。 |
| `projection_only_gap` | 只有薄投影或 descriptor，缺实际 owner/worker 消费。 | 不能说 execution landed。 |
| `history_only_gap` | 只存在历史设计、旧 intake 或 provenance。 | 不能说 current landed。 |
| `not_landed_gap` | MAS 尚无机器面代表该模式。 | 不能说 learned / absorbed / landed。 |
| `watch_only` | 仅作为漂移观察、provenance 或未来参考。 | 不能进入当前运行面。 |
| `reject` | 不进入 MAS 运行面、truth surface、route surface 或 authority surface。 | 不能落地。 |

## 最小落地门槛

外部学习项从 `adopt_contract` 晋级为 landed，至少满足以下条件：

- 有 MAS / OPL owner：明确 MAS 持有 study truth、quality verdict、publication/artifact/memory/source authority，OPL 持有通用 runtime、queue、attempt、lifecycle、workbench、observability。
- 有可消费 surface：owner surface、read-model projection、worker/sidecar slot、callable/action catalog、quality pack、controller-authorized soak 或 generated surface 至少一项真实存在。
- 有输入输出边界：列出 required inputs、accepted refs、output refs、typed blocker candidate 或 owner receipt boundary。
- 有写边界：列出 allowed writes 和 forbidden writes；默认禁止写 study truth、paper body、artifact body、memory body、publication eval、controller decisions、submission/current package、quality verdict、artifact authority。
- 有 friction guard：缺失、失败、超时、低置信或预算耗尽时默认不阻断 `current_executable_owner_action`，除非命中命名 MAS hard gate。
- 有测试或验证：focused tests、generated-surface parity、contract sync check、`make test-meta` 或 `scripts/verify.sh` 覆盖 touched surface。

## Lightweight Executor Receipt Contract

MAS 当前吸收的不是 Docker / OpenHands sandbox runtime，而是 lightweight executor receipt contract。该合同用于把 Codex、`uv` clean runner、本地 process / workspace 级尝试的命令证据、stdout/stderr refs、artifact refs、changed-file refs、耗时、env fingerprint 和 failure class 结构化记录下来，供 owner / reviewer / auditor 读取。

- 默认执行层级是 `L0_host_clean_runner` 与 `L1_process_workspace`。这对应现有 Codex / `uv` clean runner / 隔离 worktree / refs-only builder 的轻量执行管理，不要求引入容器。
- `L3_containerized_sandbox` 只允许作为显式 proof lane，用于证明外部 executor receipt shape 和 no-forbidden-write 边界；它不是 ordinary path，不是 admission gate，也不因缺 Docker、缺 OpenHands 或缺 DinD 阻断当前 owner action。
- MAS 在容器内运行时，默认禁用 Docker / DinD / Docker socket mount 作为隐式授权。Docker socket 存在也只是一条 diagnostic，不会把 receipt adapter 升级成可执行 authority。
- `lightweight_executor_receipt` action catalog 入口只是只读合同 projection；它不执行命令、不启动 Docker、不挂载 Docker socket、不写 owner receipt / typed blocker / publication eval / controller decision / current package / submission package，也不关闭 stage、quality gate 或 publication readiness。

## 当前框架读法

| framework | landing status | 当前 MAS 读法 | 下一层只允许怎么推进 |
| --- | --- | --- | --- |
| Co-Scientist | `owner_surface_landed` / `read_model_landed`，execution scaleout 只按当前 owner delta 扩面 | hypothesis portfolio / evidence pack / next-delta tournament / bounded candidate / meta-review 已是 progress-first advisory layer，不是 quality authority。 | 扩展 owner action input refs 或 reviewer briefing，不引入 Co-Scientist runtime。 |
| Nature-skills | `owner_surface_landed` / `contract_projection_landed`，router/manifest/static-fragment 只按 `adopt_template` 读取；具体 worker 或 generated loader 不能默认声称 landed | stage-quality pack 和 reviewer/publication 边界已吸收多类 writing、citation、figure、reader、response patterns；2026-06-18 上游 `1cb9070fdd94929d5f267ce6585ac87e2cba60b3` 的 short router、`manifest.yaml`、`always_load`、axis-specific static fragments 与 on-demand references 只作为 MAS prompt / skill authoring、quality pack descriptor、Display Pack descriptor 的 manifest-driven loading 模式。 | 缺 ref 时补 MAS 质量包、descriptor field、owner request 或 typed blocker candidate；不复制 vendor runner，不新增第二 selector、默认 skill source、always-on advisory scan 或 Nature-skills runtime。 |
| Academic Research Skills | `sidecar_or_worker_landed` for refs-only claim-support advisory worker | ARS projection、medical material passport 和 source adapter rejection-log 边界已存在；`build_ars_claim_support_advisory` 现在只输出 claim-support、material passport、data-access oversight 和 unsupported-claim gap refs。 | 通过 source/material passport owner refs 或 `run_external_learning_sidecar` 输出进入当前 work unit；没有 owner receipt 前不计 study progress。 |
| AutoSci / OmegaWiki | `sidecar_or_worker_landed` for refs-only source / experiment advisory worker | typed graph、source discovery、negative memory、experiment lifecycle、reviewer verdict 和 artifact QA 作为 MAS refs / quality-pack contracts 读取；`build_autosci_source_experiment_advisory` 只发 source / experiment candidate refs。 | 绑定到当前 owner work unit 的 source discovery 或 experiment lifecycle receipts；没有 owner receipt 前不计 source readiness 或 experiment completion。 |
| EvoScientist / EvoSkills | `sidecar_or_worker_landed` as target architecture；implementation scaleout 不等于 authority | 已固定为 nonblocking current-owner-following sidecar architecture；后续只允许 implementation scaleout。 | 扩展同一 sidecar contract 下的 tool-affordance、observation-memory、failed-path、routing-eval、stop-loss candidates。 |
| ARK | `sidecar_or_worker_landed` for refs-only progress worker | 多个 progress-first contracts 已记录；`build_ark_progress_worker_advisory` 只发 micro-canary、human-decision、real-run closeout、citation lifecycle 和 no-progress evidence refs。 | 一次只把能解除当前 progress blocker 的 candidate ref 晋级为 owner receipt / typed blocker；不引入 ARK queue runtime。 |
| ARIS | `sidecar_or_worker_landed` for refs-only review-import advisory worker | history / aftercare projection / optional review sidecar provenance 已收束；`build_aris_review_import_advisory` 只发 typed input、result import、cross-model reviewer 和 experiment queue hint refs。 | 只做 typed body-free input/output refs 和 owner receipt / typed blocker import；不引入 provider runtime 或 review authority。 |
| PaperSpine | `sidecar_or_worker_landed` for refs-only manuscript authoring advisory worker | `build_paperspine_manuscript_advisory` 只读取 motivation-spine、writing-rationale、evidence-blueprint 和 LaTeX-safe audit ref family，缺 ref 时 fail-open advisory gap。 | 保持 manuscript-authoring advisory refs，不能成为 paper-writing authority、LaTeX build authority 或 publication owner。 |
| PaperOrchestra | `sidecar_or_worker_landed` for refs-only authoring DAG advisory worker | `build_paperorchestra_authoring_advisory` 只读取 authoring DAG、outline plot、literature section 和 autorater ref family，缺 ref 时 fail-open advisory gap。 | 保持 authoring DAG / evaluator advisory refs，不能成为 PaperOrchestra runtime、paper generator、autorater gate 或 publication owner。 |
| Open Auto Research | `read_model_landed` / `controller_authorized_soak`，publication owner receipt 仍是 gap | read-model / controller-authorized soak 可作 readiness accelerator。 | 保持 read-only / refs-only，加 owner receipts 前不能声明 publication readiness。 |
| Light | `sidecar_or_worker_landed` for MAS materializer refs only | `light-advisory-materialize` 生成基础 verified / collision / refusal / fresh-evidence advisory refs；source / data / citation / PRISMA / figure / experiment / statistics / overclaim / argument / style 等 skill-content refs 只在 payload present 或 route-required 时物化。不引入 Light runtime。 | 继续保持 refs-only、budgeted、fail-open；缺 advisory 或 content template 不阻断 owner action。 |

## Progress-first Friction Guard

外部学习默认是 acceleration layer，不是 admission layer。

- 已存在完整 `current_executable_owner_action` 时，缺外部 advisory 不阻断 dispatch。
- 外部 worker / sidecar / projection 只能生成 refs-only candidate、reviewer briefing、repair hint、gap visibility 或 typed blocker candidate。
- 只有当前 delta 的 route-required ref 缺失，且影响 source/data/evidence、owner-route identity、forbidden write boundary、不可逆 mutation、independent reviewer、publication gate、human gate 或 MAS hard gate 时，才允许升级为正式 typed blocker。
- 正式 typed blocker 必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer/auditor、human gate 或 typed blocker materializer 产出；sidecar completion 不能自己阻断 ordinary progress spine。

## 后续优化折回

External-learning 后续优化不再作为 MAS standalone selector / backlog 推进。当前 MAS repo-native callable 入口是 `scientific_capability_registry`，由 action catalog、MCP runtime、CLI/product-entry 和 Agent Tool Arsenal 暴露 `index / resolve / invoke` ABI；hosted OPL ordinary path 仍按 OPL family-level `W3-capability-registry-fail-open` 消费该 ABI。

- `W3-capability-registry-fail-open`：OPL `Atlas + Pack + Stagecraft` 负责 hosted current-delta-bound capability resolver / selector、fail-open policy 和 route-required blocker policy；MAS 只提供 repo-native capability registry ABI 和 domain authority boundary。
- `W4-domain-kernel-manifest`：MAS 负责声明每个 external-learning ref family 的 domain consumption boundary、forbidden authority、owner receipt / typed blocker / reviewer receipt 晋级条件。
- `W7-production-evidence-soak`：只有 ARS claim-support、AutoSci source discovery、ARK micro-canary 等 refs 被真实 owner action 消费并产出 owner receipt、typed blocker、reviewer receipt、human gate 或 route-back evidence 后，才计入 study progress。

因此，MAS 侧不得新增第二 selector、第二 active backlog、always-on sidecar、默认 advisory scan 或独立外部学习调度面；已有 `run_external_learning_sidecar` 继续只是 refs-only worker execution slot，`scientific_capability_registry` 只负责按 `current_owner_delta` 列出、解析或显式调用已落地 refs-only capability。

Nature-skills 2026-06-18 router/manifest 学习项也遵守同一条规则：`manifest.yaml` 的 axes / `always_load` / `references.on_demand` 可以启发 MAS-owned prompt authoring、stage quality pack descriptor、Display Pack descriptor 或 generated product-entry descriptor 的加载声明；不能把 Nature-skills manifest 当成 MAS 默认 skill source，也不能在 MAS repo 内新增独立 router selector。若未来推进实现，只能把缺口落为现有 owner surface 可消费的 descriptor field、quality pack ref floor、route-required ref、typed blocker candidate 或 OPL-hosted capability registry 消费项。

## 不再走的路径

- 不把 `adopt_contract`、reference intake、design doc、score、ranking、checklist、skill inventory 或 external README 写成 landed。
- 不复制外部 runtime、queue、scheduler、worker residency、memory DB、project DB、router、dashboard、Telegram/webapp service 或 slash skill source。
- 不把 external review score、self-review checklist、tool selector score、observation memory、wiki graph、passport、issue DB 或 citation table 写成 MAS truth、quality verdict、publication readiness、artifact authority、memory accept/reject 或 owner receipt。
- 不为补齐外部 intake 重新制造 full lifecycle preflight、read-model reconcile loop 或每步 checklist gate。
- 不把 external-learning 后续优化写成 MAS 私有 selector / resolver / backlog；hosted selector / resolver 归 OPL Capability Registry，MAS repo 只暴露 `scientific_capability_registry` ABI、refs 消费与 authority 晋级边界。

## 验证门槛

Docs-only 更新至少运行：

```bash
rtk git diff --check
rtk rg -n "^(<<<<<<<|=======|>>>>>>>)" docs
```

触碰 machine-readable contract、generated surface、action catalog、owner callable、worker/sidecar 或 tests 时，至少补跑对应 focused tests 和：

```bash
rtk make test-meta
rtk scripts/verify.sh
```
