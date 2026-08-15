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
- OPL Framework 将 MAS 与其余四篇白皮书组成统一品牌 bundle，并从 One Person Lab 的公开入口发布和回读。
- 发布回读生成 `publication-receipt.json` Actions artifact；不在仓库跟踪第二份 verification 或 receipt。

## 证据边界

OPL renderer 从同一份 Markdown 与 Profile 生成 HTML、PDF、v2 verification 和
rendered pages。它们在本地是 ignored output，在 CI 是 source SHA 绑定的候选
artifact；Profile、测试通过或候选 artifact 都不能单独证明已发布。

`push main` 只构建候选。Framework 的五篇白皮书统一发布工作流绑定各仓精确
source ref，形成同一品牌 bundle，更新 One Person Lab 的 `gh-pages`，对公开
HTML/PDF 做 exact-byte readback，并把 `publication-receipt.json` 保存为 Actions
artifact。仓库不跟踪手工刷新的 verification 或 publication receipt。

本地复核从 OPL checkout 调用唯一 runner：

```bash
node --experimental-strip-types scripts/run-domain-whitepaper.ts \
  --repo-root <MAS repo> \
  --profile contracts/whitepaper_profile.json
```

不要提交 `docs/site/latest/whitepapers/` 或 `tmp/pdfs/mas-whitepaper/rendered/`
中的派生产物。

当前源文档：

- [mas-whitepaper.md](./mas-whitepaper.md)

公开品牌入口：

- [在线阅读](https://gaofeng21cn.github.io/one-person-lab/latest/whitepapers/mas-whitepaper.html)
- [PDF](https://gaofeng21cn.github.io/one-person-lab/latest/whitepapers/mas-whitepaper.pdf)
