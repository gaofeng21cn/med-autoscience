# Life Science Research Learning Intake

Owner: `MedAutoScience`
Purpose: `life_science_source_pattern_provenance`
State: `support_reference`
Machine boundary: 本文只记录 clean-room source discovery pattern。当前执行归 OPL Connect/Runway，专业判断归 MAS Stage、MAS ScholarSkills与 owner authority。

## 来源与可复用模式

Observed source 是 OpenAI `openai/plugins` 的 `life-science-research` package，snapshot `603a6e80711116e3584c33ecb8897548ed03d4f6`。值得保留的模式包括：

- 先规范 gene/protein/disease/variant/compound/tissue/species/accession/pathway identity；
- 选择最小 evidence lanes，只对独立 lane安全并行；
- 对 cohort、ancestry、version、license、rate limit与 dataset citation显式记录 caveat；
- 综合 genetics、omics、biology、chemistry、clinical evidence与 literature时保留 cross-source conflict和 evidence gap。

## 当前 owner mapping

- provider discovery、credential、API/network currentness、retry与 receipt transport归 OPL Connect。
- literature、statistics、data-governance与 specialty judgment通过 MAS ScholarSkills进入当前 StageAttempt。
- source readiness、claim support、clinical relevance、typed blocker与 route-back归 MAS。
- 进入 MAS 的输出只允许 body-free source refs、query fingerprint、currentness/caveat refs、review input与 owner-gate request。

MAS 不保留私有 source adapter、provider runtime、external skill router、cache、database client或 product-entry projection builder。外部 API成功、cache hit、association score、model prediction或 raw payload均不能直接授权医学 truth、source ready、quality或 publication。

## Verification

当前结构门是 `tests/test_standard_agent_boundary.py`、Stage quality-cycle tests、fast/meta与冻结 Framework source-closure/interfaces/conformance readback。真实 source acceptance仍需 MAS owner evidence。
