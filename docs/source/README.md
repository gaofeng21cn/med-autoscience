# 数据与研究工作区

本目录负责 MAS 数据、study workspace 与业务生命周期的语义。机器来源是 domain descriptor、数据合同、workspace inventory、canonical manifests 和 MAS owner receipts；通用运行、存储与 provider transport 归 OPL。

- [数据资产模型](./medical_data_asset_target_operating_model.md)：release body、manifest、lineage 与 study binding。
- [Study 工作区](./study_workspace_target_state.md)：canonical manuscript、Stage evidence 与 submission projection 的职责。
- [Study 生命周期](./study_lifecycle_control.md)：暂停、交付暂停、停止与重新激活。
- [存储与保留](../runtime/data_asset_storage_retention.md)：数据资产与运行缓存分账。
- [文献与知识](../runtime/contracts/workspace_knowledge_and_literature_contract.md)：共享来源、study 采用与执行副本。

联网文献查询由 OPL Connect 提供；MAS 不维护 Semantic Scholar、PubMed、CrossRef 或 PMC 私有 adapter。Provider receipt 只证明查询和传输；文献真实性、claim support 与 source acceptance 由 MAS 解释，专业方法通过 ScholarSkills 调用。

外部方法的来源与采纳理由留在 [参考资料](../references/README.md)，不在本索引累计外部项目、已实现投影或执行 backlog。
