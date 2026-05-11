# MAS AI-first Research OS Architecture

本文件冻结 MAS/MDS 长线目标架构。目标不是把所有代码一次搬完，也不是新增文档 wording gate，而是固定 owner、authority、contract 与 proof 口径，然后按可验证能力逐步吸收。

本文是人工可读架构说明。文档线只负责把当前能用的系统说明、长线目标和证据缺口讲清楚；不新增测试程序约束文档措辞，不修改 preflight contract。

## Target

- MAS 是唯一 research owner、quality owner、publication owner、artifact owner 与用户可见 truth owner。
- MDS / DeepScientist 收敛为 source provenance、historical fixture、explicit archive import、backend audit、upstream intake 与 parity oracle reference；它不再被写成未来默认 backend。
- 机械系统只持有 evidence、status、completeness、blocker、projection 与 replay。
- AI reviewer workflow 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。

## Current Operational Reading

当前可运行化落点集中在五件事：

1. Pre-draft quality runtime：在写作前暴露研究问题、数据资产支撑、reporting guideline、display-to-claim map 和 manuscript-native prose 约束。
2. AI reviewer workflow：由 AI reviewer 读取 manuscript、evidence ledger、review ledger 与 study charter，再写回 publication-facing 质量判断。
3. Artifact rebuild proof：manuscript、figures、tables 与 submission package 从 canonical source 重建，交付判断依赖可回放产物链。
4. Operations state：`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json` 与 `controller_decisions/latest.json` 投影当前阶段、阻塞、恢复点和下一步。
5. Real-paper soak：用真实论文线验证长期自治、质量闭环、AI reviewer 判断、产物重建和 human gate 是否持续成立。

真实论文 soak 仍是主要证据缺口。目标层的 Evaluation OS、Observability OS 或 MDS Deconstruction 不能仅因写入本文就被表述成已经完全落地。

## Operating Layers

1. MAS Core：持有 study truth、quality truth、publication truth、artifact truth。
2. Quality OS：把 study charter、evidence ledger、review ledger、pre-draft readiness、AI reviewer-backed publication eval 串成质量闭环。
3. Runtime OS：把长时研究任务压成可暂停、可恢复、可重放、可审计的 durable workflow。
4. Artifact OS：从 canonical source 重建 manuscript、figures、tables 与 submission package。
5. Evaluation OS：把历史返工转成 calibration corpus、quality regression 与 AI-first drift audit；当前属于目标层，需由真实论文 soak 与质量回归证据逐步证明。
6. Observability OS：面向维护者暴露 drift、trace、route-back、cache freshness、artifact stale 和 runtime recovery。
7. MDS Deconstruction：能力按 MAS-side consumer contract、parity proof、quality non-regression 和 rollback surface 吸收；原 MDS corpus 保留 archive/reference/oracle 角色，不按目录搬迁，也不回流为默认 runtime。

## External Basis

- ISO/IEC/IEEE 42010：stakeholder、concern、viewpoint、decision record。
- NIST AI RMF：govern / map / measure / manage。
- EQUATOR：reporting guideline 前置进入写作合同。
- FAIR：证据与数据资产可查、可取、可互操作、可复用。
- Durable execution：长时任务必须能从 restore point 恢复。
- OpenTelemetry：trace、metric、log 分离为 observability 信号。
- G-Eval：AI reviewer 用结构化 rubric 和 provenance contract。
- Google SRE toil elimination：重复论文返工是系统 toil，必须通过设计消除。

## Absorb Gate

任何 MDS 能力进入 MAS 前必须满足：MAS-side consumer contract 存在、parity proof 存在、质量门槛不降级、rollback surface 存在、旧 MDS surface 不持有质量 authority、runtime authority、publication authority 或 artifact authority。

## Non-Goals

- 不新增文档 wording gate。
- 不修改 tests。
- 不修改 dev / preflight contract。
- 不把 MDS 写成第二 owner。
- 不把目标层能力写成未经真实论文 soak 证明的当前事实。
