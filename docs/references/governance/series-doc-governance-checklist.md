# 系列项目文档治理清单

Owner: `MedAutoScience`
Purpose: `Support OPL-series and MAS documentation governance review.`
State: `support_reference`
Machine boundary: Human-readable governance reference only; active truth remains in the MAS active gap plan, canonical docs, contracts, source, tests, read models, and receipts.

## 目标

本清单用于把 `Med Auto Science` 放进 `One Person Lab`、`Med Auto Science`、`Med Auto Grant`、`RedCube AI` 这组系列项目的统一文档管理口径里做巡检。
它服务跨仓 docs intake、回归与持续对齐，不替代核心五件套、`docs/runtime/**`、`docs/active/**`、`docs/delivery/**` 或 runtime / product-entry contract。

## 一、默认入口

- 根层 `README*` 是产品分发与公开首页入口；是否继续保留双语由 public/product 需求单独判断。
- `docs/README.md` 是默认 docs 索引，承载中文 canonical 文档入口。
- 外部读者先走公开入口；AI / 维护者先走核心五件套，再进入 `docs/runtime/**`、`docs/active/**`、`docs/references/**` 与 `docs/policies/**`。

## 二、核心五件套

- `docs/project.md`
- `docs/status.md`
- `docs/architecture.md`
- `docs/invariants.md`
- `docs/decisions.md`

这五件套必须位于 `docs/` 根目录，并被 `docs/README.md` 显式链接。
任何涉及当前主线、formal entry、runtime boundary、outer substrate owner、product-entry truth、display side line 与 medical research authority 的变化，都不能只改 runtime/program/reference 文档，必须同步更新对应核心文档。

## 三、公开层与内部层

- `docs/**` 默认只维护中文 canonical 内容；稳定路径优先使用无语言后缀 `.md`。
- 根层 `README*` 的公开语言策略单独由产品分发和 public 需求决定，不要求 `docs/**` 维护双语镜像。
- `docs/runtime/**`、`docs/active/**`、`docs/delivery/**`、`docs/references/**` 继续承担 repo-tracked operator docs；默认中文维护。
- `docs/policies/**` 继续承担稳定内部规则。
- `docs/history/omx/` 只保留历史归档入口，不重新承担当前 workflow。
- 长期规则要冻结进核心文档、policy、reference 或 contract surface；不要把 `AGENTS.md` 继续当第二真相源。

## 四、系列一致性检查

- 文档必须把 `Med Auto Science` 写成独立医学研究 `Foundry Agent` 与 `OPL-compatible package built on OPL Framework`，由 MAS 持有医学研究 truth、quality verdict、runtime owner、artifact/publication authority。`Domain Harness OS` 只能作为内部 controller/runtime/eval/delivery 边界语言或历史定位参考出现，不能作为公开第一身份、当前默认 runtime target 或 upstream Hermes cutover 完成声明。
- 系列项目名称与角色要与四仓当前真相同步：`One Person Lab` 是 stage-led、以 Agent executor 为最小执行单位的完整智能体运行框架与 shared runtime/contracts owner，`Med Auto Grant` 是 author-side `Grant Ops`，`RedCube AI` 是 visual-deliverable / `Presentation Ops`。
- 若提到 `Hermes-Agent`，只能指上游外部 runtime 项目 / 服务；repo-side seam、adapter、pilot、helper 都不能被写成“已接入 Hermes-Agent”。
- 根层公开入口、docs 中文 canonical 层、active/runtime/delivery operator docs、stable policies 与历史档案必须继续分层，不把参考或历史重新挤进公开默认入口。
- 修改 docs skeleton、公开入口、runtime/product-entry contract、mainline wording 或 phase pointer 时，必须同步更新相关测试。

## 五、默认验证

- 默认本地 smoke：`scripts/verify.sh`
- 默认 push CI 入口：`scripts/verify.sh ci-preflight <base-ref>` 加 build
- 默认 nightly/advisory 回归入口：`scripts/verify.sh regression`
- 默认 docs 审计入口：`scripts/verify.sh meta`
- 同义验证入口：`make test-meta`
- `display`、`submission`、`family` 与 `meta` 继续由 advisory/nightly 承接，不作为 push quick-checks 的固定负载
- 若验证命令、docs index、runtime/product-entry contract surface 有变化，继续同步 `Makefile`、`scripts/verify.sh`、`README*` 与 `tests/test_*`
