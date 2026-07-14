# External Learning Adoption Closure

Owner: `MedAutoScience`
Purpose: `external_learning_landing_boundary`
State: `active_support`
Machine boundary: 本文是 external-learning 人读治理。机器真相归 `contracts/capability_map.json`、相关 intake contract、MAS declarative pack、MAS ScholarSkills package、OPL generated/hosted surfaces、StageAttempt receipts 与 MAS owner results。

## 结论

外部框架只能提供 pattern、source provenance、candidate refs 与专业 Skill 线索。MAS 不再为 Co-Scientist、Nature-skills、AutoSci、K-Dense、EvoScientist、ARK、ARIS、PaperSpine、PaperOrchestra、OpenScience 或同类项目维护 repo-local worker、sidecar、scheduler、projection builder、runtime adapter、selector、dashboard 或第二 capability catalog。

当前唯一落地链路是：

```text
external source snapshot
  -> refs-only intake / capability mapping
  -> MAS declarative Stage or MAS ScholarSkills professional Skill
  -> OPL-hosted tool and StageAttempt execution
  -> independent Review
  -> MAS owner consumption
```

## Landing 分类

| Status | 含义 | 允许的 claim |
| --- | --- | --- |
| `declarative_ref_landed` | pattern 已进入 MAS Stage、knowledge、quality gate 或 capability mapping | 只可声明 declarative adoption |
| `professional_skill_landed` | 能力由版本化 MAS ScholarSkills Skill 提供并由 OPL materialize | 只可声明 Skill 可发现/可调用 |
| `opl_hosted_surface_landed` | OPL 已提供 generated interface、Connect、Runway、Pack、Ledger 或 Console primitive | 只可声明 framework surface landed |
| `owner_consumed` | MAS owner 已消费 exact refs 并返回 receipt/blocker/human gate/route-back | 可声明对应 owner outcome，不扩张到 production ready |
| `history_only` | 只保留来源、比较或旧实现 provenance | 不可声明 current landed |
| `reject` | 与 owner、authority、security 或 standard-Agent boundary 冲突 | 不进入 active surface |

Contract、reference、prompt、catalog、focused test 或 projection 单独存在时，不能写成 execution landed、paper progress、quality closed 或 owner accepted。

## 当前 owner 路由

- 通用 source/provider/tool discovery、credential、remote compute 与 receipt transport归 OPL Connect / Runway。
- package、Skill materialization、dependency closure、currentness 与 rollback归 OPL Pack。
- writing、review、figure、statistics、tables、literature、submission 与 data-governance 专业能力归 MAS ScholarSkills。
- 医学 source readiness、claim/evidence acceptance、publication、artifact、memory 与 owner result归 MAS。
- OPL 只托管 execution、receipt 与 projection，不写 MAS truth 或 owner verdict。

K-Dense workflow/database/specialist 内容只作为 OPL Stagecraft、Atlas、Connect 与 ScholarSkills 的候选 refs；Nature/AutoSci/OpenScience 等模式只可进入 declarative policy、professional Skill 或 history provenance。缺少 optional advisory 不阻断普通 Stage；命中 source/data/authority/safety/human hard gate 时必须由当前 Stage/owner fail closed。

## No-resurrection

禁止新增或恢复：

- MAS-local external-learning worker/sidecar/runtime；
- repo-local skill router、provider client、cost ledger、session store或 dashboard；
- 可写 study truth、paper/artifact body、memory body、publication eval、current package、owner receipt 或 typed blocker 的外部 adapter；
- 用 audit allowlist 把 reachable private generic behavior 伪装成 minimal authority function。

## 验证

External-learning 变更至少运行 `scripts/verify.sh fast`、`scripts/verify.sh meta` 与 active-machine orphan-ref scan；跨仓继续读取冻结 Framework 的 interfaces/conformance/default-callers/residue/source-closure。Live provider、paper、publication 或 owner claim仍需 fresh receipt/artifact evidence。
