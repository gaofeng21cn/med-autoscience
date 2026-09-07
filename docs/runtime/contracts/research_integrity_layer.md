# Research Integrity Layer

Owner: `MedAutoScience`
Purpose: `publication_integrity_gate_input_contract`
State: `active_contract_support`
Machine boundary: 机器字段以 `contracts/research-integrity-layer.json`、Stage quality-cycle policy 与 OPL Connect receipt contract 为准。本文不写 study truth、publication verdict、owner receipt、typed blocker、human gate、artifact body、runtime queue 或 provider state。

## 当前形态

Research Integrity 不是 MAS 私有 runtime 或 validator service。当前链路固定为：

```text
OPL Connect exact provider receipt
  -> OPL host 注入当前 StageAttempt
  -> MAS declarative knowledge / quality-gate requirements
  -> independent reviewer or re-reviewer judgment
  -> MAS owner consumption
```

OPL Connect 持有 provider discovery、credential、retry、cache、currentness 与 receipt transport。MAS 持有医学 citation acceptance、claim restraint、reference authenticity、manuscript consistency 与 publication authority。Connector success 只能形成 evidence input，不能直接形成医学 verdict 或 ready claim。

## Gate 输入

- reference identity、identifier、metadata、retraction/update 与 source-currentness refs；
- claim span、citation ref、evidence ref、support class 与 limitation refs；
- manuscript、table、figure、display-to-claim、population、endpoint、time window 与 reporting-guideline consistency refs；
- exact artifact hash、review rubric、StageRun/Attempt lineage 与 no-context-inheritance evidence。

这些输入由 `agent/knowledge/`、`agent/quality_gates/`、Stage prompt 与 `contracts/research-integrity-layer.json` 声明，不由 MAS-local provider adapter、cache、queue、read model 或 validator implementation 生成。

## 输出与 authority

Reviewer / re-reviewer 只在 `route_impact.stage_quality_cycle.outcome` 返回 `pass`、`repair_required`、`quality_debt`、`blocked` 或 `human_gate`，并携带 findings 与 evidence refs。Attempt 不生成 receipt verdict；OPL StageRun controller 校验 identity、lineage 与 exact hashes 后物化 review receipt。

只有 MAS owner surface 能把这些结果消费成 publication/submission decision、owner receipt、typed blocker、human gate、artifact mutation authorization 或 route-back。Provider receipt、review input、tests green 与 docs 均不能替代该 authority。

## Provider 与投稿资源

需要联网核验已知 DOI/PMID/PMCID 时，MAS 只返回
`opl_connect_reference_verification` request，消费 host 注入的 exact provider receipt。
静态 `provider_evidence` 可以作为纯输入，但不证明联网 transport 或 currentness。
广义文献发现由 literature specialist 与 OPL Connect search 提供。

Frontiers CSL 使用 package-bundled 文件或 host exact path；
Word 稿件/补充模板使用 host-provisioned exact path。
缺失时返回 `opl_pack_provision_submission_resource` request，无网络 fallback。
这些资源规则由 `contracts/submission-resource-requirements.json` 持有。

## 验证

```bash
scripts/verify.sh full
```

跨仓还必须在冻结 OPL Framework 上读取单仓 `interfaces`、`conformance`、`default-callers`、`residue-decisions` 与 `source-closure`。这些结构证据不等于 live paper 或 publication ready。
