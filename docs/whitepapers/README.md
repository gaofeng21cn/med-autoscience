# 白皮书

Owner: `MedAutoScience`
Purpose: `whitepaper_source_root`
State: `active`
Machine boundary: 本目录只保存公开白皮书正文源。生成的 HTML/PDF 位于本地 `docs/site/latest/whitepapers/`，不作为 main 分支源码长期跟踪；verification JSON 位于 `docs/delivery/whitepapers/`。

MAS 白皮书采用 OPL-family 统一本地生成路径：

- 正文源放在 `docs/whitepapers/`。
- 版式和生成逻辑复用 `scripts/opl-whitepaper-builder.ts`。
- MAS wrapper 是 `scripts/build-mas-whitepaper.ts`。
- 当前用户可读 HTML/PDF 生成到 `docs/site/latest/whitepapers/`。
- 发布时只发布 latest 副本，不维护每个 release 一套白皮书。

当前源文档：

- `mas-whitepaper.md`
