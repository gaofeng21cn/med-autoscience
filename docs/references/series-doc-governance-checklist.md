# 系列项目文档治理清单

## 目标

本清单用于把 `Med Auto Science` 放进 `One Person Lab`、`Med Auto Science`、`Med Auto Grant`、`RedCube AI` 这组系列项目的统一文档管理口径里做巡检。
它服务跨仓 docs intake、回归与持续对齐，不替代核心五件套、`docs/runtime/**`、`docs/program/**`、`docs/capabilities/**` 或 runtime / product-entry contract。

## 一、默认入口

- `README.md` / `README.zh-CN.md` 是默认公开首页。
- `docs/README.md` / `docs/README.zh-CN.md` 是默认 docs 索引。
- 外部读者先走公开入口；AI / 维护者先走核心五件套，再进入 `docs/runtime/**`、`docs/program/**`、`docs/references/**` 与 `docs/policies/**`。

## 二、核心五件套

- `docs/project.md`
- `docs/status.md`
- `docs/architecture.md`
- `docs/invariants.md`
- `docs/decisions.md`

这五件套必须位于 `docs/` 根目录，并被 `docs/README*` 显式链接。
任何涉及当前主线、formal entry、runtime boundary、outer substrate owner、product-entry truth、display side line 与 medical research authority 的变化，都不能只改 runtime/program/reference 文档，必须同步更新对应核心文档。

## 三、公开层与内部层

- `README*` 与 `docs/README*` 继续承担双语公开入口。
- `docs/runtime/**`、`docs/program/**`、`docs/capabilities/**`、`docs/references/**` 继续承担 repo-tracked operator docs；默认中文维护，除非明确提升到公开双语面。
- `docs/policies/**` 继续承担稳定内部规则。
- `docs/history/omx/` 只保留历史归档入口，不重新承担当前 workflow。
- 长期规则要冻结进核心文档、policy、reference 或 contract surface，不继续只靠 `AGENTS.md` 口头维持。

## 四、系列一致性检查

- 文档必须把 `Med Auto Science` 写成医学 `Research Ops` domain gateway 与 `Domain Harness OS`，而不是 `OPL` 顶层 gateway 或已经完成的 upstream Hermes runtime owner cutover。
- 系列项目名称与角色要与四仓当前真相同步：`One Person Lab` 是顶层 gateway，`Med Auto Grant` 是 author-side `Grant Ops`，`RedCube AI` 是 visual-deliverable / `Presentation Ops`。
- 若提到 `Hermes-Agent`，只能指上游外部 runtime 项目 / 服务；repo-side seam、adapter、pilot、helper 都不能被写成“已接入 Hermes-Agent”。
- 默认公开入口、runtime/program/capabilities operator docs、stable policies 与历史档案必须继续分层，不把参考或历史重新挤进公开默认入口。
- 修改 docs skeleton、公开入口、runtime/product-entry contract、mainline wording 或 phase pointer 时，必须同步更新相关测试。

## 五、默认验证

- 默认 docs 审计入口：`scripts/verify.sh meta`
- 同义验证入口：`make test-meta`
- 默认 smoke：`scripts/verify.sh`
- 若验证命令、docs index、runtime/product-entry contract surface 有变化，继续同步 `Makefile`、`scripts/verify.sh`、`README*` 与 `tests/test_*`
