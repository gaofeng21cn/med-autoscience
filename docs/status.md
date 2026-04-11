# 当前状态

**更新时间：2026-04-11**

## 主线状态

- `P0 runtime native truth` 已完成，上游完成点为 `med-deepscientist main@cb73b3d21c404d424e57d7765b5a9a409060700a`。
- `P1 workspace canonical literature / knowledge truth` 已完成，workspace canonical literature、study reference context 与 quest materialization-only 边界已进入仓库主线。
- `P2 controlled cutover -> physical monorepo migration` 尚未完成；当前 repo-side 已把默认 outer runtime substrate owner 切到 `Hermes`，并把 `MedDeepScientist` 收口为 controlled research backend。

## 当前 tranche

- 旧 `Codex-default host-agent runtime` 已明确退为迁移期对照面，不再作为长期产品方向。
- 当前 runtime / gateway / architecture 主线只推进 `Hermes` substrate、`MedAutoScience` gateway、`MedDeepScientist` controlled backend 这条迁移，不碰 display / paper-facing asset packaging 独立线。
- `runtime_binding.yaml`、`study_runtime_status`、`runtime_watch`、outer-loop controller action 已同步写入 `Hermes` outer substrate 与 `MedDeepScientist` research backend 的分层语义。
- `docs/program/med_deepscientist_deconstruction_map.md` 已冻结三类能力归属：迁入 `Hermes` substrate、暂留 backend、后续吸收/替换。

## 近期关注

- 保持 `MedAutoScience` 对 `MedDeepScientist` native runtime truth 的消费不回退，不再让 controller 覆盖 quest-owned `runtime_events/*`。
- 保持 `runtime backend interface` 已冻结：`MedAutoScience` controller 只认 backend contract，不再把 `med-deepscientist` 模块名当作 managed runtime 判定真相。
- 保持 `Hermes` 作为默认 outer substrate owner 的 repo-side 闭环诚实成立，同时保留 external `Hermes` runtime repo / workspace / daemon truth 仍未进入本仓这一 blocker。
- 维护 workspace canonical literature / reference-context contract，不让 quest-local literature surface 重新退回 authority root。
- 继续按新文档骨架维护状态、contract 与 cutover 计划，避免把已完成 tranche 写成待办，或把未完成 tranche 写成已完成。
