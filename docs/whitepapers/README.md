# 白皮书

Owner: `MedAutoScience`
Purpose: `whitepaper_source_root`
State: `active`
Machine boundary: 本目录只保存公开白皮书正文源。HTML、PDF、v2 verification 与页面渲染由 OPL 唯一 renderer 生成，作为本地 ignored output 或 source SHA 绑定的 Actions artifact，不作为 main 分支源码长期跟踪。

MAS 白皮书采用 OPL-family 统一本地生成路径：

- 正文源放在 `docs/whitepapers/`。
- 领域配置是 `contracts/whitepaper_profile.json`；版式、构建、验证和公开字节回读由 OPL 的 canonical generic runner 持有。
- 从 OPL checkout 运行 `node --experimental-strip-types scripts/run-domain-whitepaper.ts --repo-root <MAS repo> --profile contracts/whitepaper_profile.json`。
- 本地 HTML/PDF/v2 verification 生成到 ignored 的 `docs/site/latest/whitepapers/`，视觉证据生成到 ignored 的 `tmp/pdfs/`。
- `push main` 只在 Actions 构建 immutable bundle；不会自动发布。
- 只有从 `main` 手动运行 `MAS Whitepaper` workflow 并选择 `publish=true` 才发布同一 bundle，随后执行公开 HTML/PDF exact-byte readback。
- 发布回读生成 `publication-receipt.json` Actions artifact；不在仓库跟踪第二份 verification 或 receipt。

验证和发布证据边界见 [白皮书验证与发布回执](../delivery/whitepapers/README.md)。

当前源文档：

- [mas-whitepaper.md](./mas-whitepaper.md)

公开 latest：

- [在线阅读](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.html)
- [PDF](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.pdf)
