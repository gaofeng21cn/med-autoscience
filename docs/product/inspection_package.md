# Inspection Package

Owner: `MedAutoScience`
Purpose: `human_inspection_boundary`
State: `active_contract_explanation`
Machine boundary: 可执行规则归 action catalog、inspection schemas、artifact authority 与 owner receipts；本文只解释边界。

## 用途

Inspection package 把当前可检查的 manuscript/evidence/display refs 提供给人工审阅。它是只读/导出型 inspection surface，不是 publication 或 submission authority。

标准 action 是 `export_inspection_package`；interface 由 OPL 从 action catalog/schema 生成，MAS handler 返回受 authority boundary 约束的结果。

## 允许

- 导出当前可检查的 draft、evidence、figure/table 与 review refs；
- 记录 package manifest、source refs、freshness 与 blocked context；
- 在正式 submission package 尚未授权时支持人工反馈；
- 把反馈路由回 reviewer revision / canonical paper repair owner。

## 禁止

- 授权 publication/submission；
- 清除 publishability/quality gate；
- 写 `publication_eval/latest.json` 或 controller decision；
- 把 inspection package 当 canonical paper/current package；
- 直接修改 submission package；
- 用 UI、zip 存在或 export success 声明 ready。

## Owner route

人工反馈必须回到 MAS owner chain：AI reviewer/auditor、publication gate、write/delivery owner 或 human gate。OPL 负责 action transport与 hosted display，不持有医学 verdict 或 artifact authority。

## Evidence boundary

Package materialized 只证明 inspection artifact 存在。Publication ready、submission ready、current package freshness 与 paper progress仍需要对应 owner receipt、quality verdict 和 canonical artifact refs。

## 相关入口

- [Product surfaces](./README.md)
- [Architecture](../architecture.md)
- [Runtime boundary](../runtime/contracts/runtime_boundary.md)
