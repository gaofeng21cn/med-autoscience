# 运行面切换验收

本文只定义真实 study/runtime 迁移的验收边界。源码合并见 [主线集成](./mainline_integration_and_cleanup.md)。源码验证通过不授权生产运行切换。

实际切换前，必须明确目标 study、当前执行 owner、用户授权、写集和回退入口。读取 OPL 当前 StageRun/Attempt、workspace inventory、MAS lifecycle、canonical artifact 与 owner receipts；不能从旧日志推断当前执行者，不能对同一 study 创建重复 writer。

迁移输入必须记录当前 source/artifact、identity 与 provenance。复制或重建产物须验证内容完整性和 owner 授权；历史数据导入不能自动获得当前 source readiness、quality 或 publication authority。

在获授权且可回退的 study 上验证新入口的启动、暂停、恢复、retry 与 human gate。暂停、已交付暂停和停止状态必须保留 [生命周期门禁](../../source/study_lifecycle_control.md)，当前质量债、审阅结果和未完成 finding 不得因迁移丢失。

切换完成以目标侧 same-identity runtime readback、MAS owner result、canonical artifact refs 和无越权写入证据为准。需要论文进展或 publication/submission ready 时分别补充独立审阅和对应 owner verdict。

MDS controlled-fork、旧 Hermes gateway、旧 CLI alias、site-packages 补丁与 retired behavior-equivalence 文件都不是当前迁移入口。外部来源只按 [外部引用边界](../runtime-governance/external_runtime_dependency_gate.md) 使用。
