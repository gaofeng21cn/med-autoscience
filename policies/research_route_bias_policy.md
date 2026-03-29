# Research Route Bias Policy

默认 `research_route_bias_policy = "high_plasticity_medical"`。

这套 policy 用来把医学课题的路线选择前移到 `scout / idea / decision`，核心偏置是：

- 优先高可塑性的预测、分类、风险分层路线
- 优先能自然长出 calibration、clinical utility、subgroup、explainability 的路线
- 优先能接入公开数据做外部验证、队列扩展或机制/背景增强的路线
- 降权单一固定临床假设、阴性即整条线失效的路线

公开数据只能在能实质改变证据强度时引入，不能为了“堆工作量”而装饰性加入。
