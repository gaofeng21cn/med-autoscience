# MAS AI-first Research OS Architecture

本文件冻结 MAS/MDS 长线目标架构。目标不是把所有代码一次搬完，而是一次性固定 owner、authority、contract 与验收门槛，然后按可验证能力逐步吸收。

## Target

- MAS 是唯一 research owner、quality owner、publication owner、artifact owner 与用户可见 truth owner。
- MDS 收敛为 replaceable backend / behavior oracle / upstream intake buffer。
- 机械系统只持有 evidence、status、completeness、blocker、projection 与 replay。
- AI reviewer artifacts 持有科学质量、医学写作质量、publishability 与 submission-facing readiness。

## Operating Layers

1. MAS Core：持有 study truth、quality truth、publication truth、artifact truth。
2. Quality OS：把 study charter、evidence ledger、review ledger、pre-draft readiness、AI reviewer-backed publication eval 串成质量闭环。
3. Runtime OS：把长时研究任务压成可暂停、可恢复、可重放、可审计的 durable workflow。
4. Artifact OS：从 canonical source 重建 manuscript、figures、tables 与 submission package。
5. Evaluation OS：把历史返工转成 calibration corpus、quality regression 与 AI-first drift audit。
6. Observability OS：面向维护者暴露 drift、trace、route-back、cache freshness、artifact stale 和 runtime recovery。
7. MDS Deconstruction：能力按 parity proof 吸收，不按目录搬迁。

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

任何 MDS 能力进入 MAS 前必须满足：MAS-side consumer contract 存在、parity proof 存在、质量门槛不降级、rollback surface 存在、旧 MDS surface 不持有质量 authority。
