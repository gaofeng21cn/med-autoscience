# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `ideal_state_gap_plan`
State: `active_support`
Machine boundary: 本文是人读 gap / completion plan。机器真相继续归 `contracts/`、源码、CLI/MCP/API 行为、product-entry manifest、sidecar receipt、runtime/controller durable surfaces、真实 workspace 与 generated artifact proof。
Date: `2026-05-14`

## 结论

本文对照 [MAS 理想目标态](../references/positioning/mas_ideal_state.md)，只维护 MAS 自己的当前差距、完善顺序、与 OPL 的 owner 边界和通用能力上收清单。OPL、MAG、RCA、One Person Lab App 与 MDS/DeepScientist 的具体完善计划不在本文维护；它们分别回到 OPL family 文档或各自仓库的理想态 / status / active surface。

MAS 当前已经具备独立 medical research domain agent 的主要边界：direct MAS app skill path、CLI/MCP/product-entry/controller、stage-led autonomy、publication-route memory、sidecar export/dispatch、functional closure projection、OPL production proof ingestion、owner receipt contract、legacy residue tombstone proof 和 body-free OPL/Aion projection 都已进入 repo surface。当前差距集中在真实 paper-line production evidence，而不是 descriptor 或定位。

MAS 的单仓计划只维护医学领域真相和 domain package 薄程序面。薄程序面包括 descriptor、contract/schema、sidecar/thin adapter、projection builder、domain transition spec/table、quality gate、artifact locator、receipt schema、tests 和 domain entry；它们服务 OPL 发现、托管、审计和投影，不构成第二套 generic framework/runtime。

OPL 系列项目的全局主参考是 `/Users/gaofeng/workspace/one-person-lab/docs/active/opl-family-development-reference.md`。涉及跨仓总顺序、shared primitive owner、App/workbench 通用目标和旧兼容面退役纪律时，以该主参考和 OPL docs 为准。

## 总体差距矩阵

| 目标面 | 当前实际 | 差距 | 完善方向 |
| --- | --- | --- | --- |
| MAS domain authority pack | 医学 stage pack、publication-route memory、AI reviewer / quality rubric、artifact authority、owner receipt schema 和 projection builder 已成主线 | 仍有部分 runtime / workbench / lifecycle 需求容易继续在 MAS 内复制 | MAS 只保留医学研究路线、质量 judgment、artifact authority 和 domain package 薄程序面；通用外围转成 OPL primitive 需求。 |
| OPL-hosted paper-line apply | OPL provider proof 可被 MAS 读取；sidecar dispatch 能回到 MAS owner chain 并返回 receipt / typed blocker | 真实 provider-hosted paper-line guarded apply 还没有连续产出 MAS owner apply receipt、artifact delta、AI reviewer update、route decision 或 human gate/resume 证据 | 用 DM002、DM003、Obesity 等真实 paper line 跑 guarded apply；每条线返回 owner receipt、typed blocker、stop-loss 或 human gate，而不是把 provider completion 写成 paper closure。 |
| Publication-route memory | Markdown body、seed index、workspace pack、inventory、typed closeout proposal、router receipt 和 body-free OPL/Aion projection 已落地 | accepted/rejected writeback receipt 还需要在更多真实 paper line 上泛化；memory body 仍不能复制到 OPL | 继续由 MAS workspace/runtime owner 接受或拒绝 writeback；OPL/App 只展示 locator、consumed refs、receipt refs、freshness 和 grouping。 |
| Artifact lifecycle | MAS 已暴露 artifact locator、lifecycle apply request、guarded apply proof 和 no-forbidden-write 边界 | 真实 workspace 的 cleanup / restore / retention receipt 还需要按 owner 授权闭合 | OPL 可提供 lifecycle ledger、restore/retention shell 和 operator projection；artifact mutation permission 与 canonical package authority 仍由 MAS receipt 给出。 |
| Workbench / route map | MAS 已有 route map、decision trail、Stage Review Page / Index、Portal/Workbench projection 方向 | 普通用户仍需要更清晰地看到 paper route、阻塞、转向、owner、safe action 和证据来源 | MAS 输出 domain-owned route nodes/edges、decision rationale、source refs、review/artifact refs；OPL/App 提供通用 route graph、attention queue 和 action routing shell。 |
| State transition / decision table | `study-state-matrix` 已投影 MAS-owned JSON/Markdown `domain_transition_table` / read-model oracle，覆盖 publication gate blocker、AI reviewer re-eval、artifact delta guarded apply、human gate、stop-loss、truth conflict/fail-closed、active runtime watch、delivered package handoff 和 unclassified fail-closed；OPL 已有 generic transition runner / matrix runner 与 MAS-like fixture | 真实 paper-line transition receipt scaleout 与 OPL runner 接入仍未闭合；transition read model 不能替代 live provider apply 或 publication closure evidence | MAS 继续扩展 domain transition table 和 oracle fixtures，再以 domain spec 接入 OPL runner；OPL 只执行 spec，不解释 publication verdict。 |
| OPL generic runner / transport handoff | OPL fresh read model 已显示三仓 descriptor/stage/memory resolved，并能投影 attempt query / generic projection shell；OPL generic transition runner 基础已存在 | OPL runner 到 provider attempt bridge、周期性 provider SLO execution、App workbench 产品化和真实 lifecycle apply 仍未成为可依赖 runtime substrate | MAS 只提供医学 transition spec、owner receipt、typed blocker、route/quality/artifact refs；`study-state-matrix` 已把 spec 与 matrix 机器面落下，`product-entry manifest` / `sidecar export` 只提供 descriptor，等待 OPL runner hardening / SLO / workbench / lifecycle 壳成熟后接入，不在 MAS 内复制通用实现。 |
| Legacy contraction | MDS default dependency、Hermes-first/local scheduler 默认语义和 legacy active-path 已有 tombstone / no-active-default-caller 证据 | 物理删除仍需 replacement proof、no-active-reference 和 provenance 安全 | MDS/DeepScientist 保持 archive/oracle/intake reference；替代面成立后逐项 tombstone 或删除，不把旧面补成 active runtime。 |

## MAS 后续执行顺序

1. `paper_line_provider_apply`
   继续用真实 paper line 证明 `OPL provider -> MAS sidecar -> MAS owner chain`。完成信号是 MAS owner receipt、artifact delta、gate replay、AI reviewer update、route decision、human gate、stop-loss 或 stable typed blocker。
2. `authority_pack_hardening`
   把 stage policy、prompt/skill、publication-route memory、AI reviewer、quality gate、route decision 和 artifact authority 收紧到 MAS owner surface；不在 MAS 内新增通用 queue、generic memory service、通用 workbench 或通用 lifecycle OS。
3. `domain_transition_table_hardening`
   维护已落地的 MAS-owned domain transition table / read-model oracle，把更多真实 paper-line transition receipt 纳入 coverage。OPL runner 可用后，只接入这份 MAS-owned spec，不让 OPL 重写医学判断。
4. `opl_primitive_handoff`
   将通用需求转成 OPL owner primitive：provider workflow、queue/human gate transport、generic transition runner hardening、memory locator/index、artifact lifecycle、route graph shell、attention queue、observability/SLO、repair command projection 和 App grouping。MAS 不在本仓新增第二套 scheduler、attempt ledger、transition runner、App workbench 或 lifecycle OS。
5. `memory_and_lifecycle_live_receipts`
   在真实 workspace 中继续产生 accepted/rejected memory receipts、cleanup/restore/retention guarded apply receipts 和 artifact mutation permission receipts。
6. `legacy_physical_cleanup`
   有 replacement proof 和 no-active-reference 后，再清理旧 MDS/Hermes/local/default compatibility residue；没有证据时只保留 history/provenance/tombstone 语境。

## 当前不能写成

- 不能写成 OPL provider proof 等于 MAS paper closure。
- 不能写成 MAS production-hosted paper automation 已闭合。
- 不能写成 OPL 持有医学研究路线、publication-route memory body、publication quality、artifact authority 或 current package。
- 不能写成 MDS/DeepScientist 回到 MAS 默认 backend 或 OPL active Foundry Agent。
- 不能写成 MAS 还需要维护一套通用 agent OS；通用 runtime / lifecycle / workbench 能力应进入 OPL / shared family layer。
