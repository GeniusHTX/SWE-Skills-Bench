# Task: Add Prometheus Backend SLO Configuration Support

## Background
   在 slo-generator 项目中增强 Prometheus 后端集成，新增 availability SLO 配置的计算逻辑。
   需要在 `slo_generator/` Python 包中新增或修改模块以支持基于 Prometheus 的 availability SLI 计算。

## Files to Create/Modify
   - `slo_generator/backends/prometheus_availability.py` (新建，Prometheus availability SLI 计算模块)
   - `slo_generator/utils/slo_config_validator.py` (新建，SLO 配置验证工具)
   - `tests/test_slo_implementation.py` (新建，单元测试)

## Requirements
   
   ### Prometheus Availability 模块 (slo_generator/backends/prometheus_availability.py)
   - 实现 `PrometheusAvailabilitySLI` 类
   - 支持通过 PromQL 查询计算 error rate：`sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`
   - 支持配置 SLO 目标值 (如 0.999 即 99.9%)
   - 支持配置滚动窗口 (如 28 天)
   - 提供 `compute_sli()` 方法返回 SLI 值
   - 提供 `evaluate_slo()` 方法判断是否达标

   ### SLO 配置验证器 (slo_generator/utils/slo_config_validator.py)
   - 实现 `validate_slo_config(config: dict) -> bool` 函数
   - 验证必填字段: service_name, slo_name, backend.type, goal, window
   - 验证 backend.type 为支持的类型 (如 "prometheus")
   - 验证 goal 在 (0, 1) 范围内
   - 配置不合法时抛出 ValueError 并提供描述性错误信息

   ### 单元测试 (tests/test_slo_implementation.py)
   - 测试 PrometheusAvailabilitySLI 类初始化
   - 测试 SLO 配置验证：合法配置通过、非法配置抛出 ValueError
   - 测试 evaluate_slo() 在 SLI 高于/低于目标时的返回值

## Acceptance Criteria
   - `python -m py_compile slo_generator/backends/prometheus_availability.py` 成功
   - `python -m py_compile slo_generator/utils/slo_config_validator.py` 成功
   - `python -m pytest tests/test_slo_implementation.py -v --tb=short` 全部通过
