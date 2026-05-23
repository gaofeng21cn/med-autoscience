# OPL Unique Control Plane Canary Registry

Owner: `MedAutoScience`
Purpose: `mas_duplicate_runtime_retirement_canary_registry`
State: `active_support`
Machine boundary: 本文是人读说明。可执行 registry truth 以 `contracts/unique_control_plane_canary_registry.json` 和 `med_autoscience.controllers.unique_control_plane_canary_registry` 为准。

## 当前边界

该 registry 服务 `MAS duplicate runtime retirement / OPL unique control plane canary`。它只把 DM002/DM003 暴露过的 currentness、stale dispatch、provider terminal sync、owner precedence、paper delta missing、quality authority stale 风险整理成 OPL Agent Lab 可执行回归素材。

MAS 在这里不声明自有 control plane。OPL 是 canonical control plane owner；MAS 继续持有医学 study truth、publication quality verdict、artifact authority、owner route facts 和 owner receipt authority。

## Agent Lab 输出

Agent Lab 消费 registry 后必须输出 executable regression/work order。work order 明确：

- `can_modify_mas_repo=true`
- `can_write_study_truth=false`
- `can_authorize_quality_verdict=false`

允许修改面限定在 canary/contract/docs/test 素材。`runtime_control/owner_route.py`、`domain_action_request_materializer.py` 和 `domain_owner_action_dispatch.py` 是本 registry work order 的 forbidden patch refs。

## 覆盖证明

`contracts/unique_control_plane_canary_registry.json` 的 `coverage_proof` 证明四组 refs 均被 registry 覆盖：

- MAS fixture refs
- OPL transport fixture refs
- owner-route regression refs
- no-forbidden-write proof refs

该证明用于防止把旧 incident registry 语义复活成 MAS 内部重复 runtime owner。
