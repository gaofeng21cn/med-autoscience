# Latest Published Docs

Owner: `MedAutoScience`
Purpose: `latest_public_docs_output_boundary`
State: `active_support`
Machine boundary: `docs/site/latest/` 是本地生成的公开文档输出目录，不作为 main 分支源码长期跟踪。源文档继续归 `docs/whitepapers/`、`docs/public/`、`docs/product/`、`docs/delivery/` 和对应 verification 记录。

MAS 当前只维护一份 latest 用户可读公开文档，不为每个 release 保存一套白皮书。

生成命令：

```bash
node --experimental-strip-types scripts/build-mas-whitepaper.ts
```

生成输出：

- `docs/site/latest/whitepapers/mas-whitepaper.html`
- `docs/site/latest/whitepapers/mas-whitepaper.pdf`

不要提交 `docs/site/latest/`。需要线上访问时，从本地生成结果发布 latest 副本。
