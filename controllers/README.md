# Controllers

这个目录用于说明 `MedAutoScience` 中的外层治理控制器迁移状态。

这些 controller 默认首先服务于 Agent 调用面，而不是人手工操作面。

也就是说：

- controller 是平台级稳定机器接口
- CLI 只是 controller 的薄包装
- 人类主要审核 controller 产出的 report、summary、delivery 和审计日志

当前已经完成最小代码迁移的能力有：

1. publishability gate
2. medical publication surface
3. submission minimal exporter
4. runtime watch controller
5. study delivery sync
6. data assets controller
7. MedDeepScientist upstream upgrade check

对应的 Python 实现在包内：

- `src/med_autoscience/controllers/publication_gate.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/controllers/submission_minimal.py`
- `src/med_autoscience/controllers/runtime_watch.py`
- `src/med_autoscience/controllers/study_delivery_sync.py`
- `src/med_autoscience/controllers/data_assets.py`
- `src/med_autoscience/controllers/data_asset_updates.py`
- `src/med_autoscience/controllers/med_deepscientist_upgrade_check.py`

对应测试：

- `tests/test_publication_gate.py`
- `tests/test_medical_publication_surface.py`
- `tests/test_submission_minimal.py`
- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_data_assets.py`
- `tests/test_data_asset_updates.py`
- upgrade-check 的专用测试模块

当前迁移策略是：

- 先把已经在真实医学课题中跑通过的 controller 以最小切片迁入新 repo
- 先保住行为和测试
- 再做第二轮去耦，把 policy、adapter、runtime protocol 从 controller 里拆出去

对于数据资产层，当前已经区分两类 controller 能力：

- `data_assets`
  - 负责 layout 初始化、状态汇总、public registry 校验、impact 评估、private release diff
- `data_asset_updates`
  - 负责统一的 Agent mutation 入口、mutation log 写入，以及 mutation 后的 refresh 汇总

对于 `MedDeepScientist` 运行时升级，当前 controller 采取的是“先审计、后升级”的策略：

- `med_deepscientist_upgrade_check`
  - 不直接执行升级
  - 先统一检查 repo 配置、Git 状态、workspace contract 和医学 overlay 状态
  - 输出机器可读 decision，供 Agent 判断是否进入真实升级流程

后续优先顺序：

1. MedDeepScientist runtime protocol / transport 分层
2. policy/config 外置化
3. workspace-local thin entry scripts
4. publication profile 驱动更细粒度规则

## 完整交付契约

`study_delivery_sync` 已经是 `MedAutoScience` 的一等 controller，它负责把 `submission_minimal` 和 `finalize` 阶段产出搬到 `studies/<study-id>/{manuscript,artifacts}/final` 下。对于已经形成 `submission_minimal` 的 finalized paper bundle，下游的 `finalize` skill 由 overlay 注入后会自动调用 `study_delivery_sync(stage="finalize")`，因此新的医学课题在进入正式论文交付收口时，会自动完成浅路径正式交付同步，而不再依赖 workspace 里 legacy 的手工路径。
