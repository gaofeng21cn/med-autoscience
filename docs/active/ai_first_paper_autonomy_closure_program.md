# AI-first Paper Autonomy Closure

Owner: `MedAutoScience`
Purpose: `paper_autonomy_acceptance_contract`
State: `active_support`
Machine boundary: 本文只定义真实论文线验收；机器事实归 workspace artifacts、independent Review receipts、MAS authority results 与 OPL StageRun/readback。

## 目标

AI-first autonomy 表示 Codex Attempts 能在 declared Stage 内形成可消费论文增量，
独立 Review 能发现并路由质量问题，MAS owner surface 能给出可信 owner answer，
OPL 能持久、幂等地执行和投影这条链路。

它不要求 MAS 维护 controller、queue、provider、scheduler、workbench 或第二套
runtime。MAS 的医学 judgment 与 OPL 的 transport/runtime truth 始终分离。

## 可关闭的结果

一次真实 paper-line验收必须以以下之一终止：

- accepted owner receipt + reviewed artifact semantic delta；
- route-back + exact defect owner / evidence refs；
- stable typed blocker；
- legitimate human gate；
- completed-with-quality-debt + consumable artifact + blocked ready claims。

Provider completion、queue empty、tests green、projection current、candidate package或
单次 dry-run都不是 paper progress。

## Quality independence

- executor和 reviewer/auditor必须是独立 Attempt/session/receipt。
- reviewer审阅 exact artifact/source/rubric hashes。
- ordinary observation不重开循环；required finding必须进入 repair closure。
- publication/export/submission/ready claim 必须由对应 owner verdict关闭。

## Evidence tail

Repo结构已关闭；本文件剩余工作只来自真实 paper lines：StageRun replay、provider
long-soak、artifact delta、Review receipt、owner acceptance、publication/submission
readback。缺失 evidence时输出 typed blocker或保持未验证，不恢复 MAS-local runtime。
