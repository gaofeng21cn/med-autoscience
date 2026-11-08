# Artifact Retention Operations Boundary

Owner: `MedAutoScience + OPL Workspace`
Purpose: `artifact_retention_owner_boundary`
State: `active_support`
Machine boundary: Generic retention/restore/cleanup执行归 OPL；MAS只持有医学 artifact分类、mutation authorization与 owner result。

## Current split

OPL可以生成 retention plan、checksum、manifest、restore proof、archive locator与 lifecycle receipt，并在获得合法 authorization后执行 scoped cleanup。MAS声明哪些对象是 canonical source、data release、audit evidence、human handoff、derived projection或 cache，并决定医学 artifact/body是否允许变更。

OPL receipt不能替代：

- MAS artifact mutation authorization；
- publication/export/submission verdict；
- source readiness或 memory accept/reject；
- current package freshness。

## Safe operations

- cache / regenerated projection只有在 exact target hash、rebuild source与 restore/readback条件齐全时才能删除；
- canonical source、data release、audit log与 human handoff默认保留；
- cold archive必须有 manifest、checksum、restore command与 verified restore proof；
- terminal stop-loss也不自动授权删除 authority surface；
- workspace物理操作必须由 OPL lifecycle owner执行并记录 receipt，MAS不得保留 repo-local cleanup apply、SQLite compactor、storage adapter或 wrapper。

## Stage interaction

StageAttempt只能返回 artifact/lineage/repair refs与 owner-gate request。需要 mutation时由 MAS owner明确授权；需要 retention/restore时由 OPL执行并回传 receipt。任何 plan、dry-run、index entry或 file existence都不能计为 paper progress或 quality closure。

## Verification

Repo boundary由 standard-agent tests、source closure与 no-resurrection scan保护。真实 cleanup/restore需 exact hash、receipt与 readback；未执行的 plan不能写成完成。
