# AutoSci / OmegaWiki Learning Intake

Owner: `MedAutoScience`
Purpose: `autosci_pattern_provenance`
State: `support_reference`
Machine boundary: 本文只记录 external pattern provenance。当前机器面归 MAS declarative pack、MAS ScholarSkills、OPL-hosted execution、Review receipts与 owner results。

## 来源

Clean-room intake 基于 `skyllwt/AutoSci` observed commit `d89cc72a884a2d091b6fac5719f30b4c64d2c6bd`。保留的模式是 typed knowledge graph、proposal-before-ingest、negative-result memory、experiment lifecycle receipts、independent reviewer mapping与 artifact render QA。

## 当前吸收方式

- typed entity/citation/provenance edges只作为 MAS knowledge/evidence refs；
- candidate proposal不写 MAS truth，ingest/source mutation必须经过当前 Stage与 owner authority；
- failed/eliminated ideas只有通过 MAS memory accept/reject boundary才进入 reusable memory；
- experiment design/deploy/monitor/collect/eval由 OPL Runway receipts承载，结果语义由 MAS判断；
- independent Review必须使用独立 Attempt/session与 exact artifact hashes；render success不等于 artifact quality或 publication ready。

MAS 不保留 AutoSci worker、daily cron、SSH runner、project DB、wiki runtime、permission shim、projection builder或 self-review gate。Pattern已通过 declarative Stage/knowledge/quality policy表达；需要专业能力时路由 MAS ScholarSkills，需要通用 execution时路由 OPL。

## Verification

结构回归使用 fast/meta、standard-agent boundary与冻结 Framework admission。真实 experiment/source/artifact progress必须有 fresh OPL receipt、independent Review与 MAS owner result。
