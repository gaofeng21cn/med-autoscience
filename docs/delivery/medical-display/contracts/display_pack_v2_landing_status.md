# Display Pack v2 落地状态

Owner: `MedAutoScience`
Purpose: `display_pack_v2_landing_status_and_e2e_path`
State: `active_delivery_contract_status`
Machine boundary: 人读落地状态与 E2E 使用路径。机器真相继续归 `contracts/display-pack-contract.v2.json`、`contracts/publication_figure_quality_contract.json`、`contracts/medical_figure_spec_contract.json`、`contracts/figure_polish_lifecycle_contract.json`、对应 source validators、`paper/build/display_pack_lock.json`、submission manifest、真实 paper artifact refs、visual-audit receipt、owner receipt 和 publication gate。

本文件回答三个问题：

- Display Pack v2 当前哪些能力已经在 MAS 内落地；
- 一篇真实 MAS paper 应如何从 display intent 走到 locked refs、visual audit、submission manifest；
- 哪些目标已由 OPL repo 的 Pack OS consumer smoke 承接，哪些 generic substrate 仍不归 MAS 关闭。

## 当前完成度

当前完成度是 `MAS Display Pack v2 domain landing complete, OPL Pack OS consumer smoke landed, generic substrate remains outside MAS`。

已落地的 MAS 域内能力：

| 层级 | 当前状态 | 机器真相 |
| --- | --- | --- |
| Pack descriptor contract | `landed` | `contracts/display-pack-contract.v2.json` 要求 `display_pack.toml` 的 pack identity、version、source、owner、license、templates、style/QC/AI/golden/exemplar/provenance 和 `opl_handoff` 字段。 |
| Template descriptor contract | `landed` | `templates/<template_id>/template.toml` 要求 full template id、kind、paper/audit family、renderer、input schema、QC/style refs、exports、execution mode、entrypoint、goldens 和 exemplar refs。 |
| Paper-level figure quality refs | `landed` | `contracts/publication_figure_quality_contract.json` 索引 `figure_intent`、`figure_spec`、style refs、visual audit receipt、figure polish lifecycle 和 AI illustration receipt。 |
| Medical figure grammar | `landed` | `contracts/medical_figure_spec_contract.json` / `paper/figure_spec.json` 绑定 intent、Display Template、figure kind、medical semantics 和 panel roles。 |
| AI/VLM polish lifecycle | `landed` | `contracts/figure_polish_lifecycle_contract.json` / `paper/figure_polish_lifecycle.json` 固定从 `draft_rendered` 到 `publication_manifested` 的有序前缀。 |
| Deterministic E2E path | `landed` | `medautosci publication display-pack-e2e` 从 paper intent/spec、style/overrides 和 Display Pack renderer 生成 artifacts、layout QC、visual-audit receipt、polish lifecycle、artifact manifest、display pack lock 和 publication manifest。 |
| Lock and submission handoff | `landed` | `paper/build/display_pack_lock.json#/publication_figure_quality_refs` 记录 surface path、present/missing 状态和 hash；submission manifest 保留同一 refs block。 |
| OPL Pack OS MAS consumer | `landed_in_opl_repo` | OPL repo 的 `opl pack os mas-display-smoke --contract <mas_repo>/contracts/display-pack-contract.v2.json --json` 可消费 MAS Display Pack v2 contract 并输出 generic pack lock/audit smoke receipt。 |
| OPL generic Pack OS substrate | `outside_mas_open_tail` | generic install、registry、version resolution、cache、distribution、asset inventory、Workbench display 和 lifecycle transport 不归 MAS repo 关闭。 |

当前 Display Pack v2 不是“模板市场已完成”，也不是“OPL Pack OS 已内置到 MAS”。它表示 MAS 已有 paper-facing display pack descriptor、paper-level quality refs、deterministic E2E render/QC/publication-manifest path、visual audit / polish lifecycle 和 submission refs preservation 的可验证下界；OPL 侧已有一个通用 Pack OS consumer smoke，但通用 Pack OS substrate 仍由 OPL 长线继续扩展。

## 目标态

目标态分两层：

1. MAS 持有医学展示 domain authority：模板包 descriptor、医学 figure grammar、paper-level display quality refs、visual-audit / AI/VLM polish lifecycle、figure/table generated artifact refs、publication quality owner receipt 和 forbidden authority boundary。
2. OPL 持有通用 Pack OS substrate：generic pack install、registry、version resolution、lock projection、asset inventory、Workbench display shell、跨 domain pack 分发和 lifecycle transport。

MAS 只把 `opl_handoff` 暴露成 refs-only handoff boundary。OPL repo 已经有带测试的 `mas-display-smoke` consumer projection，可以读取 MAS contract 并生成 generic pack lock/audit smoke receipt；这只关闭 consumer-smoke 层，不关闭通用 install / registry / cache / distribution substrate。

## E2E 使用路径

一篇 MAS paper 的 Display Pack v2 路径按下面顺序读取：

| 步骤 | Surface | 完成信号 | 不授权内容 |
| --- | --- | --- | --- |
| 1 | `config/display_packs.toml` / `paper/display_packs.toml` | 论文声明启用 pack、source 和 exact version。 | 不授权图已生成或 publication-ready。 |
| 2 | `display_pack.toml` / `templates/<template_id>/template.toml` | pack/template descriptor 通过 contract，template 绑定 renderer、schema、QC 和 style refs。 | 不替代 source/data/statistics truth。 |
| 3 | `paper/figure_intent.json` | 每个 paper display 绑定 claim ref、data ref、template id 和 kind。 | 不修改 claim、data 或 artifact authority。 |
| 4 | `paper/figure_spec.json` | MAS-native grammar 绑定 intent、template、figure kind 和医学语义。 | 不是 Vega-Lite runtime、renderer 或 publication verdict。 |
| 5 | deterministic render + QC | `medautosci publication display-pack-e2e` 生成 figure refs、PDF/PNG/layout sidecar、layout QC、artifact manifest 和 display pack lock。 | gate clear 只是下界，不等于视觉完成。 |
| 6 | `paper/figure_visual_audit_receipt.json` | VLM/human/hybrid 审阅真实渲染图，记录 findings、impact、layer、promotion decision 和 verification plan。 | 不签 publication quality，也不授权 artifact mutation。 |
| 7 | `paper/figure_polish_lifecycle.json` | lifecycle 以有序前缀记录 draft、QC、visual audit、revision、audit clear、manifested。AI/VLM event 必须带 `model_ref` 或 `reviewer_ref`。 | AI/VLM event 不能 `mutates_data=true`，不能 `carries_publication_verdict=true`。 |
| 8 | `paper/build/display_pack_lock.json` | lock 保存 pack source/version/hash 和 `publication_figure_quality_refs` 的 path/status/hash。 | lock 不是 publication verdict、source readiness 或 artifact authority。 |
| 9 | `paper/build/display_pack_publication_manifest.json` / `paper/submission_minimal/submission_manifest.json` | publication manifest 和 submission manifest 保留 lock 中的 figure-quality refs block、audit refs 和 artifact refs。 | refs preservation 不等于 submission-ready。 |
| 10 | MAS owner receipt / publication gate | 独立 reviewer/auditor、publication gate、owner receipt、typed blocker 或 human gate 给出下一步。 | Display Pack surface 不能代签 MAS owner authority。 |

## 最小示例

最小结构示例见 [Display Pack v2 E2E Skeleton](../examples/display_pack_v2_e2e_skeleton.md)。该示例只说明字段关系和 authority boundary，不作为 fixture、golden、真实论文证据或测试输入。

## MAS / OPL 边界

MAS 保留：

- paper display intent、medical figure grammar、visual audit receipt、AI/VLM polish lifecycle 和 AI illustration hard boundary；
- figure/table generated artifact refs、layout/readability QC refs、display pack lock refs 和 submission manifest refs preservation；
- publication quality、artifact mutation、source readiness、owner receipt、typed blocker、human gate 和 route-back authority。

OPL 可以承接：

- generic pack install / registry / version resolution；
- lock projection、asset inventory、workbench display 和 lifecycle transport；
- refs-only handoff、owner receipt refs、typed blocker refs、pack/version refs 和 audit refs 的展示或运输。
- 已落地的 `mas-display-smoke` consumer 可以读取 MAS Display Pack v2 contract，输出 generic pack lock/audit smoke receipt。

OPL 不能写 MAS publication truth，MAS 也不把 Display Pack v2 contract 写成 OPL generic Pack OS substrate 已完成。

## AI/VLM Audit Lifecycle

AI/VLM 只进入 display quality loop：

1. deterministic render 后，VLM/human/hybrid 审阅真实图像；
2. `figure_visual_audit_receipt` 记录具体 finding；
3. `figure_polish_lifecycle` 把 finding、revision 和 audit-clear 事件绑定到 artifact refs 与 display-pack lock refs；
4. 可复用缺陷向 renderer contract、layout/readability QC、style profile 或 golden regression 下沉；
5. publication verdict 继续由 MAS independent reviewer / publication gate / owner receipt / typed blocker 承接。

AI-generated illustration 只允许 `illustration_shell` 候选，并且 `scientific_claim_carried=false` 是硬边界。证据型 figure 必须走 deterministic renderer/template/data/QC 路径和 visual audit，不用 AI illustration 承载科学 claim。

## 外部项目吸收顺序

外部 display / visualization / paper-figure 项目只能按以下顺序吸收：

1. `link_only_exemplar`：记录公开论文图面或 gallery 的 link-only 参考，不复制脚本、图片、截图或运行时。
2. `style_or_audit_hint`：把可复用的风格、可读性或审计问题写入 style notes、visual-audit guide 或 promotion decision。
3. `template_gap_candidate`：只有真实 MAS paper demand 证明现有 template/QC 不足时，才进入 active board / backlog。
4. `display_pack_descriptor_candidate`：新模板必须有 pack/template descriptor、input schema、renderer family、QC/style refs、golden/exemplar refs 和 authority boundary。
5. `landed_template_or_pack`：只有通过 descriptor validation、materialization、QC、visual audit、lock、submission manifest preservation 和 repo-native verification，才写成 landed。
6. `opl_pack_os_handoff`：OPL `mas-display-smoke` consumer 已可消费 MAS contract；generic install/registry/version/cache/distribution 需求继续进入 OPL Pack OS substrate tail，不能在 MAS 文档中写成 MAS 已落地。

外部项目不能直接成为 MAS runtime、publication owner、quality gate、artifact authority、data/statistics source、claim truth 或 dispatch blocker。

## 不得声明

- 不得声明 Display Pack v2 lock、visual audit clear 或 polish lifecycle 等于 publication-ready、submission-ready、paper closure、domain-ready 或 production-ready。
- 不得声明 `figure_spec.json` 是 renderer、Vega-Lite runtime、data/statistics mutation surface 或 publication verdict。
- 不得声明 AI/VLM audit、style reference 或 illustration receipt 能携带科学 claim、修改 evidence mark 或替代 independent reviewer/auditor。
- 不得声明 OPL Pack OS substrate 已由 MAS repo 落地；当前只存在 OPL repo 的 `mas-display-smoke` consumer smoke。
- 不得把 link-only external exemplar 写成 MAS template、golden、runtime dependency 或 copied asset。

## 验证口径

修改 Display Pack v2 机器合同或 validators 时，最小验证为：

```bash
rtk ./scripts/run-pytest-clean.sh tests/test_display_pack_v2_contract.py tests/test_display_pack_v2_figure_quality_refs.py tests/test_figure_polish_lifecycle_contract.py tests/test_medical_figure_spec_contract.py tests/test_publication_figure_quality_contract.py -q
rtk make test-meta
rtk ./scripts/verify.sh
rtk git diff --check
```

纯文档状态或示例说明变更可按 `documentation_review_only` 处理，但仍应运行 `rtk git diff --check`；若改动触及合同名、测试名或完成度声明，应至少跑上述 focused pytest 以确认引用没有漂移。
