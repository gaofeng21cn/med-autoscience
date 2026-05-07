# MDS Capability Parity Matrix

MDS 的长线角色是 replaceable backend / behavior oracle。MAS 吸收 MDS 能力时按 capability 推进，不按目录搬迁。

MDS 不能授权 medical quality。医学论文质量、publication readiness、controller decision 与最终 package state 都由 MedAutoScience 持有；MDS 只能提供可替换 backend 行为、机械检查信号、legacy fixture 和 parity oracle。

## Capability Matrix

| Capability | MDS role | MAS owner | Parity proof | Medical quality authority |
| --- | --- | --- | --- | --- |
| runtime execution | backend | Runtime OS | runtime execution replay and recovery regression suite | blocked for MDS |
| artifact inventory | behavior oracle | Artifact OS | artifact inventory projection parity fixtures | blocked for MDS |
| paper contract health | mechanical oracle | Quality OS | backend preflight parity without quality-ready authority | blocked for MDS |
| manuscript coverage | mechanical oracle | Quality OS | mechanical coverage fixtures with AI preflight required | blocked for MDS |
| prompt stage discipline | behavior oracle | Quality OS | stage prompt contract parity and prompt-only gate audit | blocked for MDS |
| memory / lesson store | behavior oracle | Evaluation OS | lesson intake and incident learning parity fixtures | blocked for MDS |

## Parity Proof Requirements

### runtime execution

- MAS contract: `study_runtime_status` / `runtime_watch` 持有 runtime decision 与 recovery visibility。
- MDS oracle: MDS quest execution trace 只能作为 backend behavior fixture 被 replay。
- Proof: MAS recovery decision 必须匹配或显式 supersede replayed MDS behavior。

### artifact inventory

- MAS contract: MAS artifact inventory 是 consumer-facing projection owner。
- MDS oracle: MDS artifact layout 只作为 legacy inventory compatibility fixture。
- Proof: MAS inventory 保留 discoverability，同时不把 delivery authority 交给 MDS。

### paper contract health

- MAS contract: publication gate 与 controller decisions 持有 paper readiness。
- MDS oracle: MDS contract checks 只是 mechanical preflight observation。
- Proof: MDS health signal 不能把 paper 提升为 medical-quality ready。

### manuscript coverage

- MAS contract: AI review 与 publication eval 持有 medical manuscript quality。
- MDS oracle: MDS coverage count 只是 mechanical completeness signal。
- Proof: Coverage parity 可以触发 review request，不能授权 final quality。

### prompt stage discipline

- MAS contract: MAS controller stage 持有 allowed prompt transition。
- MDS oracle: MDS stage prompt 只提供 behavior example 与 violation fixture。
- Proof: parity import 后 MAS stage discipline 仍然 explicit、auditable。

### memory / lesson store

- MAS contract: MAS incident learning 持有 reusable lessons 与 operator-visible memory。
- MDS oracle: MDS lessons 是 parity 和 regression case 的 intake material。
- Proof: lesson 被作为 evidence 导入，不能作为 autonomous quality decision。

## Cutover Rule

每个能力都必须先有 MAS consumer contract、MDS behavior oracle fixture、quality gate not relaxed 证明、rollback surface，以及旧 MDS authority surface 的 oracle-only 标记或退休记录。

MDS paper contract health 和 manuscript coverage 永远不能授权医学论文质量 ready；它们只提供 backend preflight 或 mechanical oracle 信号。

## Manifest Projection

`inspect_med_deepscientist_repo_manifest(...)` 可以暴露 parity / deconstruction summary，帮助 operator 知道当前 MDS fork 是否是受控 backend/oracle 参考面。这个 projection 不会把 MDS 提升成 quality owner；其中的 medical quality authority owner 固定为 `MedAutoScience`，且 `medical_quality_authority_granted_to_mds=false`。
