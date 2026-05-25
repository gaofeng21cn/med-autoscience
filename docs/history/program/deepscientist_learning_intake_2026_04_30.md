# DeepScientist Learning Intake 2026-04-30

Owner: `MedAutoScience`
Purpose: `program_history_record`
State: `history_provenance`
Machine boundary: 人读 program/process 历史记录。当前执行顺序、gap、runtime truth 和 owner boundary 继续归 active owner docs、核心五件套、contracts、source、runtime/controller surfaces 和 owner receipts。

这份记录对应维护者触发的“学习一下 DeepScientist 最近更新”。本轮按 [DeepScientist Latest-Update Learning Protocol](../../references/med-deepscientist/deepscientist_latest_update_learning_protocol.md) 执行：fresh upstream audit、decision matrix、MDS/MAS owner surface 分类、落地、验证、吸收回 main。

## Fresh Upstream Range

- upstream_range: `d22165e..1f042ef`
- upstream_head: `1f042ef` `docs: expand provider setup guidance`
- MDS comparison before landing: `main@0ed3be9` vs `upstream/main@1f042ef`
- MDS local code landing: `none`
- MAS contract/template landing: this document plus meta-test coverage

Refresh note:

- `med-deepscientist` had fetched `upstream/main@1f042ef` during the audit.
- A later `backend-upgrade-check --refresh` attempt returned `blocked_refresh_failed` because GitHub SSH/HTTPS refresh failed from the workstation.
- The non-refresh gate over existing refs returned `upgrade_available` and recommended `run_controlled_fork_intake_workflow`.

## Decision Matrix

| Upstream lesson | Owner surface | Decision | Landing / verification target |
| --- | --- | --- | --- |
| academic outline artifact gates (`64e7643`) | `eval_hygiene` + `workspace_projection` | `adopt_contract` | MAS records outline readiness as a publication-quality contract lesson: paper outlines should expose paper idea, scoped claims, method abstraction, evaluation plan, analysis plan, evidence grounding, and language firewall before drafting. |
| paper-outline workflow (`77cbb00`) | `controller_charter` + `eval_hygiene` | `adopt_template` | MAS maps `paper_view` / `evidence_view` into its existing outline-first medical write overlay discipline, without importing upstream product/runtime code wholesale. |
| paper quality review prompts (`bf7f408`) | `eval_hygiene` | `adopt_template` | MAS adopts the reviewer-risk lesson: mature papers need novelty boundary, reviewer objections, falsification criteria, and analysis-count adequacy reminders before “strong manuscript” claims. |
| runner evidence packet sidecars (`8451c14`, `a29f8a3`, merge `28b4831`) | `runtime` | `watch_only` / `already_covered` | MDS local main already has context-budget telemetry, evidence packet cache, delta compaction, runner tool budget caching, read telemetry, artifact deltas, and progress-marker telemetry. No MAS contract change required. |
| runtime log hygiene and runner diagnostics (`ef78200`, `f3a8262`, merges `eac31af`, `d4fe0a2`) | `runtime` | `watch_only` / `already_covered` | MDS local main already has runtime storage hygiene and runner failure taxonomy. Revisit only if a concrete MAS runtime-watch failure points to a missing diagnostic surface. |
| explorer payload reduction (`e7901cd`) | `workspace_projection` | `watch_only` | Useful product/runtime-size idea, but current MAS/MDS context pressure is already handled through evidence packets and delta compaction. |
| Kimi / Claude / OpenCode / provider docs and setup guidance (`242efa4`, `1f042ef`) | none | `reject` / `watch_only` | Provider breadth stays under Codex profile compatibility and upstream product docs. It does not become MAS owner truth. |
| UI paper tool cards, onboarding, settings responsiveness, tooltips, continuation notice (`26d5d43`, `aea7c05`, `f20ce61`, `1e9eb34`, `10cb5cf`) | none | `reject` | These are upstream product-shell changes, not MAS behavior / contract / packet lessons. |
| WeChat QR / marketing docs (`68776ed`) | none | `reject` | Marketing/community assets do not enter MAS learning mainline. |

## MAS Learned Contract

本轮 MAS 真正学习到的是一条 paper-quality owner lesson：

`outline readiness` 不能只等于“有 section list”。医学论文线在进入大规模 drafting / finalize 前，应能回答：

1. `paper_view`: 读者应该记住的一句话、问题-缺口-方法-主结果-边界、1-3 个 scoped claims、method intuition、evaluation plan、reviewer-facing analysis plan。
2. `evidence_view`: 真实数据、run、路径、表格、复现细节和 appendix-only 信息应留在 evidence / reproducibility surface，不应泄漏成主文叙事。
3. `reviewer risk`: 成熟论文应记录 novelty boundary、closest neighbor、reviewer objections、claim falsification criteria，以及 analysis-count target / waiver。
4. `language firewall`: 用户指令、agent route、worktree、quest、artifact id、local endpoint / batch shorthand 等运行态 provenance 只能约束路线或进入附录复现细节，不能成为 manuscript prose。

这条 lesson 落在 MAS 的 `eval_hygiene` 与 `controller_charter`，并被现有 `medical-research-write` / publication gate / evidence-review surface 消费。MDS 本轮继续只作为 upstream intake buffer 和 future callable-surface candidate，不新增医学质量 owner。

## Watch / Reject Rationale

本轮明确不吸收以下上游面作为 MAS 主线：

- Provider runner / setup breadth：Claude、Kimi、OpenCode、provider setup docs 都不改变 MAS 的医学研究 owner truth。
- UI product shell：paper tool cards、onboarding、settings、tooltip、continuation notice 属于 upstream product surface。
- 大块 MDS `artifact.service` 实现：该文件与受控 fork 已显著分叉。直接搬入会扩大风险；下一步如需要，应该先定义 MAS consumer contract，再做小而可测的 MDS callable validation slice。

## Verification

MAS meta verification for this record:

```bash
uv run pytest -q tests/test_deepscientist_learning_policy.py::test_2026_04_30_intake_records_paper_outline_quality_lessons
```

Expected MDS paired verification:

```bash
git diff --check
```

## Completion Meaning

This intake round is considered learned at the MAS owner layer when:

- `MDS`: records the fresh upstream classification and explains why no MDS code slice was absorbed.
- `MAS`: records the paper-outline / reviewer-risk / language-firewall lesson as owner truth and guards the intake record with meta-test coverage.

The mainline lesson is not “copy upstream paper tools”. The mainline lesson is that MAS paper-quality governance needs a stronger outline-readiness contract before drafting and finalize claims.
