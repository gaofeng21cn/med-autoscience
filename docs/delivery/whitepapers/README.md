# 白皮书验证与发布回执

Owner: `MedAutoScience`
Purpose: `whitepaper_verification_and_publication_receipt_boundary`
State: `active_support`
Machine boundary: 本文只解释白皮书验证与发布证据的归属。正文与 Profile 是 tracked source；v2 verification、HTML、PDF、页面渲染和 publication receipt 是按 source SHA 生成的 Actions artifact 或本地 ignored output，不是 main 分支的长期真相源。

MAS 不再跟踪一份手工刷新的 verification JSON。旧 `mas-whitepaper-verification.json` 只证明过往某次构建，无法证明当前 source、线上文件或发布状态，已从 current surface 删除。

## Build 证据

OPL 唯一 renderer 从同一份 Markdown 与 Profile 生成不可变 bundle。bundle 包含：

- `mas-whitepaper.html`
- `mas-whitepaper.pdf`
- `mas-whitepaper.verification.json`
- 用于视觉检查的 rendered pages

本地输出位于 ignored 的 `docs/site/latest/whitepapers/` 与 `tmp/pdfs/mas-whitepaper/rendered/`。GitHub Actions 将同一 bundle 上传为 source SHA 绑定的候选 artifact；这些派生产物不提交到 `main`。

## Publication 证据

`push main` 只构建候选 artifact，不自动发布。只有维护者从 `main` 手动运行 `MAS Whitepaper` workflow 并显式选择 `publish=true`，才会经过 `whitepaper-production` environment，下载 build job 的同一 bundle 并更新 `gh-pages`。

发布后，OPL verifier 按 v2 verification 对公开 HTML/PDF 做 exact-byte readback，并生成 `publication-receipt.json`。该 receipt 作为 GitHub Actions artifact 保存，不回写仓库；它才是对应 workflow run 的发布回读证据。Profile、文档、测试通过或候选 artifact 均不能单独替代 publication receipt。

## 本地复核

如需本地构建，从 OPL checkout 调用 canonical generic runner：

```bash
cd <OPL repo>
node --experimental-strip-types scripts/run-domain-whitepaper.ts \
  --repo-root <MAS repo> \
  --profile contracts/whitepaper_profile.json
```

MAS 不维护 repo-local wrapper、renderer 或发布脚本。
