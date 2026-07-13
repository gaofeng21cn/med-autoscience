# Latest Published Docs

Owner: `MedAutoScience`
Purpose: `latest_public_docs_output_boundary`
State: `active_support`
Machine boundary: `docs/site/latest/` 是 OPL canonical renderer 的本地 ignored 输出目录，不作为 main 分支源码长期跟踪。源文档归 `docs/whitepapers/`，领域配置归 `contracts/whitepaper_profile.json`；v2 verification 与 publication receipt 分别归构建 bundle 和 Actions publication artifact。

MAS 当前只维护一份 latest 用户可读公开文档，不为每个 release 保存一套白皮书。

MAS 不维护 repo-local wrapper 或 renderer。如需本地复核，从 OPL checkout 调用唯一 generic runner：

```bash
cd <OPL repo>
node --experimental-strip-types scripts/run-domain-whitepaper.ts \
  --repo-root <MAS repo> \
  --profile contracts/whitepaper_profile.json
```

本地 ignored 输出：

- `docs/site/latest/whitepapers/mas-whitepaper.html`
- `docs/site/latest/whitepapers/mas-whitepaper.pdf`
- `docs/site/latest/whitepapers/mas-whitepaper.verification.json`
- `tmp/pdfs/mas-whitepaper/rendered/`

不要提交这些派生产物。`push main` 只构建并上传 source SHA 绑定的 immutable bundle；不自动发布。维护者从 `main` 手动运行 `MAS Whitepaper` workflow 且选择 `publish=true` 后，发布 job 下载 build job 的同一 bundle、更新 latest，再对公开 HTML/PDF 做 exact-byte readback 并上传 `publication-receipt.json`。

公开 latest：

- [在线阅读](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.html)
- [PDF](https://gaofeng21cn.github.io/med-autoscience/latest/whitepapers/mas-whitepaper.pdf)

证据归属见 [白皮书验证与发布回执](../delivery/whitepapers/README.md)。
