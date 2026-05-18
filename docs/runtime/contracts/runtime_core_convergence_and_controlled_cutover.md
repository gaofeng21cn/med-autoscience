# Runtime Core Convergence And Controlled Cutover

Status: `active closeout / behavior-equivalence reference`
Owner: `MedAutoScience Runtime OS`
Date: `2026-05-08`

## 1. 当前事实

当前正式状态已经从“外部 MDS 是默认执行依赖”收敛为：

- `MAS Runtime OS` 持有默认 controller-facing runtime owner / substrate。
- 默认 outer supervision scheduler owner 已迁到 OPL `opl_provider_runtime_manager`；默认 adapter 是 `opl_family_runtime_provider`。MAS supervision contract 保留 paper-progress SLO/read-model、domain tick payload、owner receipt、typed blocker 和 safe action refs。MAS-owned `local` scheduler / LaunchAgent install path 已物理退役；公开 CLI 不再暴露 `--manager local`，只保留 tombstone/provenance refs。`Hermes gateway cron` 只在显式选择时作为 optional adapter。
- MAS Runtime Turn Lifecycle Kernel 持有 runner completion 后的状态归一化和下一 turn 调度；正常 `auto_continue` 不再等待 300 秒 supervision tick。
- `med-deepscientist` 不再是 MAS 默认 study/status/progress/cockpit/diagnostic operation 的必需 checkout、daemon、runtime root 或 WebUI。
- `MedDeepScientist` 只保留为 frozen source archive、historical fixture、explicit archive import reference / backend audit / provenance reference。

这完成的是 default independence 和 functional monolith closeout，不是旧 MDS resident daemon 的 full behavior equivalence。行为差异以 [MDS Behavior Equivalence Gap Matrix](../../references/mds-parity/mds_behavior_equivalence_gap_matrix.md) 为准。

## 2. 已关闭的风险

下面这些风险已经关闭到 repo-level guard：

1. 外部 MDS repo / daemon / runtime root 作为默认 MAS operation 依赖。
2. MDS WebUI 作为默认进度可视化入口。
3. profile / doctor-facing 输出把 `med_deepscientist_*` 暴露为默认 workspace truth。
4. quest Git / workspace root Git 作为 runtime lifecycle owner。
5. workspace-local launchd/systemd/cron/docker service 作为 active scheduler 选项。
6. MDS mechanical paper health / coverage / artifact inventory 信号授权 medical quality 或 publication readiness。

## 3. 当前保留的行为差异

当前 MAS 默认实现不是 resident daemon，但已经拆出内外两层：

- MDS 原行为：resident `ThreadingHTTPServer`、WebSocket、session store、background connector / worker / recovery loop。
- MAS 内层行为：Runtime Turn Lifecycle Kernel 在 runner 返回后清理 live flags、drain queued user messages、按 continuation policy 调度下一 turn，并保留 human/terminal gate。
- MAS 外层行为：默认 scheduler cadence 与 provider SLO 由 OPL replacement 承载；MAS-owned local scheduler / LaunchAgent 只保留为显式 legacy diagnostic / cleanup adapter。runtime state、event、owner route 和 progress read-model 由 MAS durable surface 持有。

因此：

- 日常研究推进、turn-to-turn continuation、状态读取、恢复投影、progress/cockpit/Portal 可独立完成。
- 外层 drift detection / stale recovery 现在受 OPL provider SLO / cadence evidence 约束；低延迟 resident callback、WebSocket terminal streaming、connector background delivery、in-memory session continuity 不作为默认 MAS active behavior 保留。
- 需要长时唤醒时，当前正确入口是 OPL provider/runtime manager replacement；MAS `local` adapter 和 Hermes gateway cron 只在显式 diagnostic / optional 路径中使用，不是旧 workspace-local launchd/systemd/cron/docker service。

## 4. Gate 规则

后续 runtime / platform 变更必须遵守：

1. 不重新引入外部 MDS daemon / WebUI / repo checkout 作为默认依赖。
2. 不把 workspace-local launchd/systemd/cron/docker service 恢复为 active scheduler。
3. 不用 `functional_monolith_completion=landed` 掩盖 MDS resident daemon 行为差异。
4. 不让 explicit archive import reference / backend audit transport 参与默认 watch/status/execute/recovery。
5. 不让 SQLite、legacy `.ds` payload、MDS artifact inventory 或 old current_package projection 成为 paper truth / quality truth / delivery authority。

## 5. 结论

`runtime_core_ingest` 和 `functional_monolith_completion` 已按 default-independence 口径 landed。剩余工作不是重开 MDS 吸收主线，而是持续守住：

- MAS Runtime OS 的 owner contract。
- OPL scheduler replacement 是默认路径；MAS supervision contract 保留 domain SLO/read-model 和 legacy local diagnostic / cleanup；Hermes gateway cron 是 explicit optional hosted / provider adapter。
- behavior-equivalence matrix 对 resident daemon 差异的公开记录。
- optional future hosted scheduler / frontend packaging 的独立 gate。

如果未来需要吸收外部 MDS 或 DeepScientist 的新增能力，必须重新走 source provenance、capability classification、MAS owner、authority boundary、tests、parity proof 和 no-history contributor audit。
