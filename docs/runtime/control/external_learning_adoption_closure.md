# External Learning Adoption Closure Runbook

Owner: `MedAutoScience`
Purpose: `external_learning_landing_runbook`
State: `active_runtime_support`
Machine boundary: 本文是人读 external-learning landing runbook。机器真相继续归 MAS `agent/` pack、contracts、source、generated/read-model surfaces、owner callables、worker/sidecar outputs、owner receipts、typed blockers、AI reviewer / auditor records、publication eval、controller decisions、真实 workspace artifacts、OPL current-control 和 repo-native verification。本文不引入外部 runtime，不安装外部 worker，不写 study truth、paper body、artifact body、memory body、`publication_eval/latest.json`、`controller_decisions/latest.json`、submission package 或 `current_package`。

## 适用范围

本 runbook 适用于 Co-Scientist、Nature-skills、Academic Research Skills、AutoSci / OmegaWiki、EvoScientist / EvoSkills、ARK、ARIS、PaperSpine、Open Auto Research 和同类自动研究框架的 MAS intake。

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

## 当前框架读法

| framework | landing status | 当前 MAS 读法 | 下一层只允许怎么推进 |
| --- | --- | --- | --- |
| Co-Scientist | `owner_surface_landed` / `read_model_landed`，execution scaleout 只按当前 owner delta 扩面 | hypothesis portfolio / evidence pack / next-delta tournament / bounded candidate / meta-review 已是 progress-first advisory layer，不是 quality authority。 | 扩展 owner action input refs 或 reviewer briefing，不引入 Co-Scientist runtime。 |
| Nature-skills | `owner_surface_landed` / `contract_projection_landed`，具体 worker 不能默认声称 landed | stage-quality pack 和 reviewer/publication 边界已吸收多类 writing、citation、figure、reader、response patterns。 | 缺 ref 时补质量包或 owner request，不复制 vendor runner。 |
| Academic Research Skills | `read_model_landed` / `projection_only_gap` | ARS projection、medical material passport 和 source adapter rejection-log 边界已存在，但完整 claim-support audit worker 仍不能默认算 execution landed。 | 通过 source/material passport owner refs 或 nonblocking sidecar 输出进入当前 work unit。 |
| AutoSci / OmegaWiki | `contract_projection_landed`，source / experiment worker 仍按当前 work unit 单独证明 | typed graph、source discovery、negative memory、experiment lifecycle、reviewer verdict 和 artifact QA 作为 MAS refs / quality-pack contracts 读取。 | 绑定到当前 owner work unit 的 source discovery 或 experiment lifecycle receipts。 |
| EvoScientist / EvoSkills | `sidecar_or_worker_landed` as target architecture；implementation scaleout 不等于 authority | 已固定为 nonblocking current-owner-following sidecar architecture；后续只允许 implementation scaleout。 | 扩展同一 sidecar contract 下的 tool-affordance、observation-memory、failed-path、routing-eval、stop-loss candidates。 |
| ARK | `contract_projection_landed` / `projection_only_gap` | 多个 progress-first contracts 已记录，但 unified owner callable / worker 尚未全部落地。 | 一次只把能解除当前 progress blocker 的 contract 晋级为 owner callable。 |
| ARIS | `history_only_gap` / `projection_only_gap` | 当前主要是 history / aftercare projection / optional review sidecar provenance。 | 只做 typed body-free input/output refs 和 owner receipt / typed blocker import。 |
| PaperSpine | `not_landed_gap` | 当前无稳定 MAS machine surface；只能作为 manuscript-authoring refs gap 读取。 | 吸收为 motivation-spine / writing-rationale / LaTeX-safe audit refs，不能成为 paper-writing authority。 |
| Open Auto Research | `read_model_landed` / `controller_authorized_soak`，publication owner receipt 仍是 gap | read-model / controller-authorized soak 可作 readiness accelerator。 | 保持 read-only / refs-only，加 owner receipts 前不能声明 publication readiness。 |
| Light | `sidecar_or_worker_landed` for MAS materializer refs only | `light-advisory-materialize` 生成基础 verified / collision / refusal / fresh-evidence advisory refs；source / data / citation / PRISMA / figure / experiment / statistics / overclaim / argument / style 等 skill-content refs 只在 payload present 或 route-required 时物化。不引入 Light runtime。 | 继续保持 refs-only、budgeted、fail-open；缺 advisory 或 content template 不阻断 owner action。 |

## Progress-first Friction Guard

外部学习默认是 acceleration layer，不是 admission layer。

- 已存在完整 `current_executable_owner_action` 时，缺外部 advisory 不阻断 dispatch。
- 外部 worker / sidecar / projection 只能生成 refs-only candidate、reviewer briefing、repair hint、gap visibility 或 typed blocker candidate。
- 只有当前 delta 的 route-required ref 缺失，且影响 source/data/evidence、owner-route identity、forbidden write boundary、不可逆 mutation、independent reviewer、publication gate、human gate 或 MAS hard gate 时，才允许升级为正式 typed blocker。
- 正式 typed blocker 必须由 MAS owner surface、OPL Stage Transition Authority、independent reviewer/auditor、human gate 或 typed blocker materializer 产出；sidecar completion 不能自己阻断 ordinary progress spine。

## 不再走的路径

- 不把 `adopt_contract`、reference intake、design doc、score、ranking、checklist、skill inventory 或 external README 写成 landed。
- 不复制外部 runtime、queue、scheduler、worker residency、memory DB、project DB、router、dashboard、Telegram/webapp service 或 slash skill source。
- 不把 external review score、self-review checklist、tool selector score、observation memory、wiki graph、passport、issue DB 或 citation table 写成 MAS truth、quality verdict、publication readiness、artifact authority、memory accept/reject 或 owner receipt。
- 不为补齐外部 intake 重新制造 full lifecycle preflight、read-model reconcile loop 或每步 checklist gate。

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
