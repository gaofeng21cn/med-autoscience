# Controllers

这个目录用于说明 `MedAutoScience` 中的外层治理控制器迁移状态。

当前已经完成最小代码迁移的能力有：

1. publishability gate
2. medical publication surface
3. submission minimal exporter
4. runtime watch controller
5. study delivery sync
6. data assets controller

对应的 Python 实现在包内：

- `src/med_autoscience/controllers/publication_gate.py`
- `src/med_autoscience/controllers/medical_publication_surface.py`
- `src/med_autoscience/controllers/submission_minimal.py`
- `src/med_autoscience/controllers/runtime_watch.py`
- `src/med_autoscience/controllers/study_delivery_sync.py`
- `src/med_autoscience/controllers/data_assets.py`

对应测试：

- `tests/test_publication_gate.py`
- `tests/test_medical_publication_surface.py`
- `tests/test_submission_minimal.py`
- `tests/test_runtime_watch.py`
- `tests/test_study_delivery_sync.py`
- `tests/test_data_assets.py`

当前迁移策略是：

- 先把已经在真实医学课题中跑通过的 controller 以最小切片迁入新 repo
- 先保住行为和测试
- 再做第二轮去耦，把 policy、adapter、runtime protocol 从 controller 里拆出去

后续优先顺序：

1. DeepScientist adapter 分层
2. policy/config 外置化
3. workspace-local thin entry scripts
4. publication profile 驱动更细粒度规则

## 完整交付契约

`study_delivery_sync` 已经是 `MedAutoScience` 的一等 controller，它负责把 `submission_minimal` 和 `finalize` 阶段产出搬到 `studies/<study-id>/{manuscript,artifacts}/final` 下。对于已经形成 `submission_minimal` 的 finalized paper bundle，下游的 `finalize` skill 由 overlay 注入后会自动调用 `study_delivery_sync(stage="finalize")`，因此新的医学课题在进入正式论文交付收口时，会自动完成浅路径正式交付同步，而不再依赖 workspace 里 legacy 的手工路径。
