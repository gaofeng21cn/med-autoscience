# 白皮书

Owner: `MedAutoScience`
Purpose: `whitepaper_source_root`
State: `active`
Machine boundary: 本目录只保存公开白皮书正文源。生成的 HTML/PDF 位于本地 `docs/site/latest/whitepapers/`，不作为 main 分支源码长期跟踪；verification JSON 位于 `docs/delivery/whitepapers/`。

MAS 白皮书采用 OPL-family 统一本地生成路径：

- 正文源放在 `docs/whitepapers/`。
- 领域配置是 `contracts/whitepaper_profile.json`；版式和验证由 OPL 的通用 runner 持有。
- 从 OPL checkout 运行 `node --experimental-strip-types scripts/run-domain-whitepaper.ts --repo-root <MAS repo> --profile contracts/whitepaper_profile.json`。
- 当前用户可读 HTML/PDF 生成到 `docs/site/latest/whitepapers/`。
- 发布时只发布 latest 副本，不维护每个 release 一套白皮书。

当前源文档：

- `mas-whitepaper.md`
