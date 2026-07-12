# Research Integrity Layer Contract

Owner: `MedAutoScience`
Purpose: `publication_integrity_gate_input_contract`
State: `active_contract`
Machine boundary: 机器字段以 `contracts/research-integrity-layer.json` 为准；本文只解释 Research Integrity Layer 如何被 MAS 和 OPL 消费。该层不写 study truth、`publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package`、owner receipt、typed blocker、human gate、runtime queue 或 provider attempt。

## 目标

Research Integrity Layer 的目标态不是 MAS 只消费人工已有的 `provider_evidence`。流程是：review / publication gate 的 stage hook 触发 MAS 的 `research-integrity-reference-verification` domain action；缺少 evidence 时，由 OPL Connect `connect references verify` 调用 provider、执行 retry/cache 并返回只读 receipt，MAS 再把 receipt 交给 Research Integrity Gate 生成 gate input。

这不是独立的专业 skill。OPL Connect 持有 Crossref/OpenAlex/Semantic Scholar/Crossmark/Publisher provider transport、凭证、retry、cache 和 receipt；外部 provider source system 仍是 metadata/status 的事实来源。MAS 持有医学 citation acceptance、reference authenticity、claim support 和 gate-input 组装，不能把 connector receipt 包装成 live provider truth 或 publication-ready 结论。

Research Integrity Layer 把三类投稿前质量问题固定成可复用、可测试、可接入 OPL connector 的 gate input：

- `Reference Authenticity Gate`：核实引用文献是否真实存在、identifier 是否一致、metadata 是否冲突、是否存在 retraction/update 信号。
- `Claim-Citation Support v2`：把 claim span、citation ref、evidence ref 和 reference attestation 绑定，区分 direct support、partial support、background only、unsupported 和 contradicted。
- `Manuscript Consistency / Meta Review`：检查摘要、结果、表格、图、display-to-claim map、单位、人群、时间窗、逻辑叙述和 reporting guideline checklist 是否一致。

这不是新增一个 publication authority。它只产生 evidence / gate input / blocker candidate；真正的 publication quality、owner receipt、typed blocker、human gate、artifact authority 和 package freshness 仍由 MAS owner surfaces 消费后决定。

## 流程地位

默认触发点：

- AI reviewer-backed `publication_eval/latest.json` materialization 之前。
- submission package closeout 之前。
- review / publication gate stage hook 需要联网 citation proof 时。
- manuscript、reference manager refs、display-to-claim map 或 evidence refs 发生变化时。
- reviewer route-back 要求 claim、citation、reference 或 numeric consistency proof 时。

触发后输出三类 surface：

| Surface | 作用 | 硬门候选 |
| --- | --- | --- |
| `reference_verification_attestation` | 文献真实性和 provenance 核查 | contradicted、retracted |
| `claim_citation_support_matrix_v2` | claim 与 citation/evidence/attestation 绑定 | unsupported、contradicted、依赖 unresolved/contradicted/retracted reference |
| `manuscript_consistency_meta_review` | 全稿数字、逻辑、display 与 guideline 一致性审查 | blocked |

MAS 同时暴露聚合消费面：

- `build_research_integrity_gate_input_bundle(...)` 把上述三类 surface 聚合为 `research_integrity_gate_input_bundle`。
- `MedAutoScienceDomainEntry.dispatch({"command": "research-integrity-gate-input", ...})` 是当前 service-safe callable entry；它接受 builder-native 字段，也接受 `reference` / `references`、`claim` / `claims`、`manuscript`、`provider_evidence` 等易用别名。
- `MedAutoScienceDomainEntry.dispatch({"command": "research-integrity-reference-verification", ...})` 接受顶层 `provider_evidence` 和已提供的 `provider_receipts`，并把 receipt root 的 `provider_evidence`、`references[].provider_evidence`、`opl_connect_reference_verification.provider_evidence` 归一化为同一 gate input；缺少 evidence 时通过 OPL Framework carrier 调用 `opl connect references verify`，不在 MAS 内实现 provider HTTP。
- `MedAutoScienceDomainEntry.dispatch({"command": "research-integrity-review-publication-gate-stage-hook", ...})` 是 Review / Publication Gate 的 mandatory hook 输入面；它触发 `research-integrity-reference-verification` 并返回包含 `stage_obligation`、`stage_launch_required_input`、`target_stage_ids`、OPL Connect receipt contract 和 `manuscript_consistency_meta_review` 的 `research_integrity_gate_input_bundle`。这些字段不声明 live owner consumption。
- 该层固定从属于 `PaperMission -> submission authority -> owner gate / typed blocker` 主线：Research Integrity 只能提供 gate input / blocker candidate，不能自起并行主线，不能绕过 submission authority，也不能脱离 owner gate / typed blocker 单独收口。
- `family_action_catalog` 暴露 `research_integrity_gate_input` read-only descriptor，供 OPL generated / product-entry / MCP descriptor 消费；该 action 的 `mcp_public_runtime=false`，不声明公开 runtime 执行器。

当前非 live gate-input 达标条件：每条 reference 至少有一个 provider crosscheck 得到 `verified`，或被明确标成 `unresolved`、`needs_review`、`contradicted`、`retracted` 之一；不能因 lookup 缺失而静默通过。无论 evidence 来自 MAS domain lookup 还是显式提供的 generic connector input，它都只是 gate input，不是权威 live citation verification；任何 live truth claim 仍需要对应 external provider invocation/readback 与 MAS owner surface consumption。

`needs_review`、`unresolved`、`partial_support`、`background_only` 默认只进入 review candidate，除非被 MAS policy 升级。Research Integrity Layer 自身不能把 candidate 写成 typed blocker，也不能阻断 current owner action。

## 理想触发链

稳定目标链路是：

1. `review_and_quality_gate` 与 `finalize_and_publication_handoff` 的 manifest extension 声明 RI hook，OPL generated stage control plane 在 `stage_contract.mandatory_pre_gate_checks` 暴露同一内容给 launch/readback consumer。
2. OPL Connect 根据 stage hook 请求查询已配置 provider，返回 canonical read-only receipt；MAS 不实现 provider transport。
3. MAS Research Integrity Gate 消费 provider evidence、reference refs、claim refs、citation refs、display refs 和 manuscript facts，生成 `research_integrity_gate_input_bundle`，并保留输入 source refs 供 owner surface 追溯。
4. AI reviewer 或 publication gate consumer 把该 bundle 当作 quality input，在 MAS owner surface 内决定 receipt、typed blocker、route-back 或 human gate。

该链路的 stage hook 目标是 `review_and_quality_gate` 与 `finalize_and_publication_handoff`。当前合同固定 non-live callable、stage obligation、stage launch / readback pre-gate check、trigger chain、payload shape 和 forbidden-write boundary；provider lookup runtime、stage hook 执行与 live owner consumption 仍必须由 external provider invocation/readback 和 MAS owner surface 的新鲜证据证明。

## 完成度边界

本层允许声明：

- RI gate-input callable / descriptor / contract 已同步。
- `review_and_quality_gate` 与 `finalize_and_publication_handoff` 的 mandatory RI hook 已在 machine-readable contract、manifest extension、hook payload 和 OPL generated `stage_contract.mandatory_pre_gate_checks` 中同步。
- RI payload 可作为 AI reviewer / publication gate 的输入证据。
- forbidden writes 已被合同、action catalog 和 domain entry 边界声明。

本层不能声明：

- live provider truth、provider receipt 或 MAS owner consumption 已产生。
- `publication_eval/latest.json`、`controller_decisions/latest.json`、`current_package` 已更新。
- owner receipt、typed blocker、human gate、publication-ready 或 submission-ready 已成立。

## OPL / MAS 边界

OPL 持有通用基座：

- generated / hosted stage attempt、workbench projection、operator drilldown 和通用 connector discovery/sync。
- reference provider invocation、credential、retry、cache、normalized metadata 和 receipt transport；其结果仍只作为 MAS domain action 的输入。

MAS 持有医学 evidence 归一化、reference authenticity、claim-support 与 gate-input 组装。它不写 provider attempt、runtime queue、cache 或 transport receipt，不形成第二套 provider truth。

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
- `src/med_autoscience/research_integrity/gate_bundle.py`
- `src/med_autoscience/research_integrity/provider_lookup.py`
- `src/med_autoscience/research_integrity/stage_hooks.py`

目标工程形态分两段：

- OPL Connect 负责 provider transport 并返回 canonical receipt；外部 provider source system 保持 metadata/status 的事实来源。
- MAS pure builders 消费 receipt/evidence payload、比较 metadata、解释医学风险并输出 gate input。

domain entry 只做字段归一化和 builder 调用，不创建独立专业 skill、provider cache、runtime queue、provider attempt 或 authority receipt。

## 验收

最小结构验收：

```bash
rtk make test-paths -- tests/test_research_integrity_*.py tests/test_domain_entry_contract.py
```

吸收后标准验收：

```bash
rtk make test-paths -- tests/test_research_integrity_*.py tests/test_domain_entry_contract.py tests/test_citation_integrity_projection.py tests/test_paper_mainline_claim_support.py tests/test_ai_reviewer_publication_eval_workflow.py tests/test_medical_publication_surface.py
rtk make test-meta
rtk scripts/verify.sh
```

这些命令只能证明 repo/source/control-plane 与 contract behavior；不能替代真实 paper-line owner receipt、publication verdict、submission authority、current-package freshness 或 production readiness。
