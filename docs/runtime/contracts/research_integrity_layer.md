# Research Integrity Layer Contract

Owner: `MedAutoScience`
Purpose: `publication_integrity_gate_input_contract`
State: `active_contract`
Machine boundary: 机器字段以 `contracts/research-integrity-layer.json` 为准；本文只解释 Research Integrity Layer 如何被 MAS 和 OPL 消费。该层不写 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、owner receipt、typed blocker、human gate、runtime queue 或 provider attempt。

## 目标

Research Integrity Layer 把三类投稿前质量问题固定成可复用、可测试、可接入 OPL connector 的 gate input：

- `Reference Authenticity Gate`：核实引用文献是否真实存在、identifier 是否一致、metadata 是否冲突、是否存在 retraction/update 信号。
- `Claim-Citation Support v2`：把 claim span、citation ref、evidence ref 和 reference attestation 绑定，区分 direct support、partial support、background only、unsupported 和 contradicted。
- `Manuscript Consistency / Meta Review`：检查摘要、结果、表格、图、display-to-claim map、单位、人群、时间窗、逻辑叙述和 reporting guideline checklist 是否一致。

这不是新增一个 publication authority。它只产生 evidence / gate input / blocker candidate；真正的 publication quality、owner receipt、typed blocker、human gate、artifact authority 和 package freshness 仍由 MAS owner surfaces 消费后决定。

## 流程地位

默认触发点：

- AI reviewer-backed `publication_eval/latest.json` materialization 之前。
- submission package closeout 之前。
- manuscript、reference manager refs、display-to-claim map 或 evidence refs 发生变化时。
- reviewer route-back 要求 claim、citation、reference 或 numeric consistency proof 时。

触发后输出三类 surface：

| Surface | 作用 | 硬门候选 |
| --- | --- | --- |
| `reference_verification_attestation` | 文献真实性和 provenance 核查 | contradicted、retracted |
| `claim_citation_support_matrix_v2` | claim 与 citation/evidence/attestation 绑定 | unsupported、contradicted、依赖 unresolved/contradicted/retracted reference |
| `manuscript_consistency_meta_review` | 全稿数字、逻辑、display 与 guideline 一致性审查 | blocked |

`needs_review`、`unresolved`、`partial_support`、`background_only` 默认只进入 review candidate，除非被 MAS policy 升级。Research Integrity Layer 自身不能把 candidate 写成 typed blocker，也不能阻断 current owner action。

## OPL / MAS 边界

OPL 持有通用基座：

- Crossref、PubMed、OpenAlex、Semantic Scholar、publisher 和 Crossmark connector transport。
- cache、rate limit、retry/dead-letter、provider receipt、attestation store 和 generic gate runner。
- generated / hosted workbench projection 与 operator drilldown。

MAS 持有医学与发表 authority：

- 文献是否能支撑医学 claim、source tier、claim restraint 和 clinical relevance。
- manuscript consistency policy、publication gate consumption、AI reviewer / auditor judgment。
- owner receipt、typed blocker、human gate、artifact mutation、submission readiness 和 publication readiness。

因此 connector 成功、cache 命中、attestation 存在或 meta review clear 都不能直接声明 publication-ready 或 submission-ready；它们只能作为 MAS owner surface 的输入证据。

## 工程形态

实现应保持为确定性 pure builders：

- `src/med_autoscience/research_integrity/reference_authenticity.py`
- `src/med_autoscience/research_integrity/claim_citation_support_v2.py`
- `src/med_autoscience/research_integrity/manuscript_consistency.py`

builders 接收已经取得的 provider evidence payload，不直接联网。真实网络、密钥、限速、缓存和重试属于 OPL connector runtime；MAS 只比较 payload、解释医学风险并输出 gate input。

## 验收

最小结构验收：

```bash
rtk scripts/run-pytest-clean.sh tests/test_research_integrity_reference_authenticity.py tests/test_research_integrity_claim_citation_support_v2.py tests/test_research_integrity_manuscript_consistency.py
```

吸收后标准验收：

```bash
rtk scripts/run-pytest-clean.sh tests/test_research_integrity_reference_authenticity.py tests/test_research_integrity_claim_citation_support_v2.py tests/test_research_integrity_manuscript_consistency.py tests/test_citation_integrity_projection.py tests/test_paper_mainline_claim_support.py tests/test_ai_reviewer_publication_eval_workflow.py tests/test_medical_publication_surface.py
rtk make test-meta
rtk scripts/verify.sh
```

这些命令只能证明 repo/source/control-plane 与 contract behavior；不能替代真实 paper-line owner receipt、publication verdict、submission authority、current-package freshness 或 production readiness。
