# Real-Study Relaunch Verification

这份文档记录 `research-foundry-medical-mainline` 在 `P2 delivery plane contract map and artifact-surface freeze` 之后，对真实锚点 study 做的最小受控 relaunch / verify 结果。

它不是：

- `real-study` 已经可无人值守跑通到投稿的声明
- `end-to-end harness` 或 `cutover` 已开启的声明
- 对 external workspace truth 的越权改写授权

## 1. Scope

当前只验证：

1. 正式 managed 入口仍是 `ensure-study-runtime`
2. `controller / router / transport / record / audit / delivery` 在真实 study 上可达
3. delivery/publication plane 遇到真实 paper-facing 缺口时继续 fail-closed
4. 缺口被严格区分为 repo-side gap 还是 external workspace-side gap

## 2. Anchor

- profile: `dm-cvd-real-study`
- workspace: `DM-CVD-Mortality-Risk`
- study: `001-dm-cvd-mortality-risk`
- quest: `001-dm-cvd-mortality-risk-reentry-20260331`

选择理由：

- `doctor` / `show-profile` / `study-runtime-status` 均能稳定解析
- `startup_boundary_gate=ready_for_compute_stage`
- `runtime_reentry_gate=ready`
- study-owned `paper/submission_minimal/` 已存在，可直接验证 delivery mirror

## 3. Executed path

实际执行的最小正式命令序列：

```bash
uv run --python 3.14 python -m med_autoscience.cli doctor --profile .omx/local/profiles/dm-cvd-real-study.local.toml
uv run --python 3.14 python -m med_autoscience.cli show-profile --profile .omx/local/profiles/dm-cvd-real-study.local.toml --format json
uv run --python 3.14 python -m med_autoscience.cli study-runtime-status --profile .omx/local/profiles/dm-cvd-real-study.local.toml --study-id 001-dm-cvd-mortality-risk
uv run --python 3.14 python -m med_autoscience.cli ensure-study-runtime --profile .omx/local/profiles/dm-cvd-real-study.local.toml --study-id 001-dm-cvd-mortality-risk
uv run --python 3.14 python -m med_autoscience.cli medical-publication-surface --quest-root <quest_root> --apply
uv run --python 3.14 python -m med_autoscience.cli publication-gate --quest-root <quest_root> --apply
uv run --python 3.14 python -m med_autoscience.cli watch --quest-root <quest_root> --apply
uv run --python 3.14 python -m med_autoscience.cli sync-study-delivery --paper-root <study_root>/paper --stage submission_minimal
```

## 4. Verified outputs

### 4.1 Controller / router / transport / record

`ensure-study-runtime` 成功写出或刷新：

- `studies/001-dm-cvd-mortality-risk/artifacts/runtime/last_launch_report.json`
- `quest/artifacts/reports/startup/hydration_report.json`
- `quest/artifacts/reports/startup/hydration_validation_report.json`

并把 relaunch 结果收口为：

- `decision=blocked`
- `reason=resume_request_failed`
- `quest_status=waiting_for_user`

这不是 transport 旁路；而是正式 managed entry 在真实 runtime 上产出的 durable stop point。

### 4.2 Audit plane

真实 audit 结果表明：

- `medical_reporting_audit = clear`
- `medical_literature_audit = clear`
- `medical_publication_surface = blocked`
- `publication_gate = blocked`

当前阻塞不是 repo 里的 silent fallback，而是外部 quest paper truth 被明确 fail-closed：

- `methods_section_structure_missing_or_incomplete`
- `endpoint_provenance_note.md` 缺失

### 4.3 Delivery plane

`sync-study-delivery --stage submission_minimal` 成功把 controller-authorized `paper/submission_minimal/` materialize 到：

- `studies/001-dm-cvd-mortality-risk/manuscript/`
- `studies/001-dm-cvd-mortality-risk/manuscript/submission_package/`
- `studies/001-dm-cvd-mortality-risk/manuscript/submission_package.zip`
- `studies/001-dm-cvd-mortality-risk/manuscript/delivery_manifest.json`

因此本轮已确认：

- authority source 继续停留在 controller-authorized `paper/` surface
- human-facing mirror 继续只是 `manuscript/` projection
- delivery plane 没有把 shell surface 反向抬升成 authority root

## 5. Repo-side gap closed in this round

真实 relaunch 暴露了一个 repo-side gap：

- `runtime_watch --apply` 在同一扫描里先跑 `publication_gate`，再跑 `medical_publication_surface`
- 这会导致第一次扫描里出现 `publication_gate=clear` 与 `medical_publication_surface=blocked` 的不一致快照

本轮已把该 gap 收紧为正式 contract：

- `runtime_watch` 必须在同一扫描内先评估 `medical_publication_surface`，再评估 `publication_gate`
- 同一扫描里的 gate verdict 不能忽略刚刚暴露出的 publication-surface blocker

## 6. External workspace-side blocker

当前真正阻塞继续推进 real study 的问题已经明确属于 external workspace-side truth：

1. quest paper `draft.md` 的 `Methods` 结构不满足正式方法学小节要求
2. quest paper 缺 `endpoint_provenance_note.md`
3. runtime 还存在待人工处理的 interaction，因此 quest 保持 `waiting_for_user`

这些问题若要继续推进，必须改 external workspace / quest paper durable surface；它们不是 `med-autoscience` repo 内的 authority contract 漂移。

## 7. Current verdict

当前可以稳定表述为：

- real-study relaunch 正式入口、audit gate、delivery mirror 都已在真实 anchor 上得到验证
- repo-side runtime_watch coherence gap 已补齐
- 当前 remaining blocker 已被严格收敛为 external workspace-side truth gap
- 本轮不自动继续写 external workspace，也不把它误写成 repo-side runtime 未成熟

## 8. Handoff after absorb

`real-study relaunch and verify` absorbed 到 `main` 之后，当前 repo-side 唯一合法下一棒是：

- [`docs/integration_harness_activation_package.md`](./integration_harness_activation_package.md) 所定义的 `Phase 6 / Integration Harness And Cutover Readiness`

其含义是：

1. repo 继续只做 integration harness 的 activation package 与最小 repo-native baseline
2. external workspace-side blocker 继续保持 external 分类，不得混写成 repo-side runtime contract 回退
3. `end-to-end study harness`、`cutover`、`behavior-equivalence` 仍需单独门控，不因 real-study absorbed 而自动打开
