# 智虾系统 - 技能定义

**数据来源**: Kaggle真实数据 + 通义千问大模型生成
**养殖周期**: 90-120天
**说明**: 本系统覆盖对虾养殖的完整流程，使用真实数据和大模型技术。

---

## 技能列表

本系统包含 8 个核心技能，覆盖对虾养殖的完整流程（90-120天周期）。

### 养殖周期覆盖

```
完整周期：90-120天
│
├─ 放苗前（0-7天）              → skill_water_monitoring
├─ 放苗期（7-10天）             → skill_water_monitoring
├─ 日常管理（10天-收获）       → 6个核心技能
├─ 收获规划（收获前1-2周）     → skill_yield_prediction
├─ 收获执行                    → skill_auto_logging
└─ 周期总结                    → skill_cost_benefit_analysis

覆盖度：100%
```

---

## 技能 1: 水质监控与预警

**id**: `skill_water_monitoring`
**name**: 水质监控与预警
**description**: |
  实时监控虾塘水质参数（溶解氧、pH、水温、氨氮等），
  当参数超出安全范围时自动触发预警并生成处理建议

**triggers**:
  - 溶解氧 (DO) 低于 5.0 mg/L
  - pH 值超出 7.5-8.5 范围
  - 水温超过 32°C 或低于 22°C
  - 氨氮超过 0.5 mg/L

**actions**:
  - 发送预警通知（记录到日志）
  - 生成水质分析报告
  - 推荐调节措施（增氧、换水等）
  - 更新养殖状态仪表板

**expected_outcomes**:
  - 发现水质异常的时间 < 1 分钟
  - 生成预警报告
  - 提供明确的处理建议

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证

---

## 技能 2: 智能投喂优化

**id**: `skill_feeding_optimization`
**name**: 智能投喂优化
**description**: |
  基于当前养殖状态、水质条件、历史数据，
  自动计算最优投喂量并生成投喂计划

**triggers**:
  - 每日定时触发（默认 08:00 和 17:00）
  - FCR（饲料转化率）高于 2.0
  - 溶解氧低于 4.0 mg/L
  - 水温异常（< 24°C 或 > 30°C）

**actions**:
  - 计算当日最优投喂量
  - 生成投喂计划（时间、量、频率）
  - 调整投喂策略（减少/增加/暂停）
  - 生成投喂指令文件

**expected_outcomes**:
  - 投喂量优化建议
  - 投喂时间表
  - 预期 FCR 改善效果

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证

---

## 技能 3: 增氧自动控制

**id**: `skill_aeration_control`
**name**: 增氧自动控制
**description**: |
  当检测到溶解氧不足时，自动计算增氧机运行时长
  并生成增氧控制指令

**triggers**:
  - 溶解氧低于 5.0 mg/L（预警级）
  - 溶解氧低于 3.0 mg/L（严重级）
  - 水温超过 30°C（辅助增氧）

**actions**:
  - 计算所需增氧时长
  - 生成增氧控制指令
  - 预测增氧后溶解氧水平
  - 记录增氧操作日志

**expected_outcomes**:
  - 增氧时长计算结果
  - 增氧控制指令
  - 预期溶解氧恢复时间

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证

---

## 技能 4: 换水决策支持

**id**: `skill_water_change_advisor`
**name**: 换水决策支持
**description**: |
  当水质参数持续异常时，分析是否需要换水，
  并计算最优换水量和频率

**triggers**:
  - pH 值连续 2 天超出 7.5-8.5 范围
  - 氨氮持续超过 0.5 mg/L
  - 亚硝酸盐超过 0.1 mg/L
  - 透明度低于 20 cm

**actions**:
  - 分析水质趋势
  - 计算换水量（百分比）
  - 生成换水操作指南
  - 预测换水后效果

**expected_outcomes**:
  - 换水建议报告
  - 换水量计算结果
  - 换水操作步骤

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证

---

## 技能 5: 疾病风险预警

**id**: `skill_disease_risk_alert`
**name**: 疾病风险预警
**description**: |
  基于存活率变化、摄食量、活动状态等指标，
  预测疾病风险并提前预警

**triggers**:
  - 存活率连续 3 天下降 > 1%/天
  - 日摄食量下降 > 20%
  - FCR 突然升高 > 0.5
  - 发现异常行为（如浮头、游边）

**actions**:
  - 计算疾病风险等级
  - 生成疾病预警报告
  - 推荐预防措施
  - 建议是否需要提前收虾

**expected_outcomes**:
  - 疾病风险评估
  - 预警等级（低/中/高）
  - 预防措施建议

**验证状态**: ✅ 基础功能已完成，图像识别待开发

---

## 技能 6: 产量预测与规划

**id**: `skill_yield_prediction`
**name**: 产量预测与规划
**description**: |
  基于历史数据和当前养殖状态，预测最终产量，
  并生成收获规划建议

**triggers**:
  - 养殖周期过半（> 60 天）
  - 每周定时更新预测
  - 重大环境变化后

**actions**:
  - 运行产量预测模型
  - 生成产量预测报告
  - 计算预期收益
  - 推荐最佳收获时间

**expected_outcomes**:
  - 产量预测结果（kg）
  - 预测置信度
  - 收获时间建议
  - 收益预估

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证，R²=0.44

---

## 技能 7: 养殖日志自动生成

**id**: `skill_auto_logging`
**name**: 养殖日志自动生成
**description**: |
  自动汇总每日养殖数据、操作记录、预警信息，
  生成结构化的养殖日志

**triggers**:
  - 每日 23:00 定时触发
  - 重大操作完成后
  - 用户手动触发

**actions**:
  - 汇总当日传感器数据
  - 记录所有执行的操作
  - 整理预警和处理记录
  - 生成 Markdown 日志

**expected_outcomes**:
  - 日期报日志文件
  - 数据统计摘要
  - 操作记录清单
  - 问题处理记录

**验证状态**: ✅ 已在真实数据和大模型生成场景上验证

---

## 技能 8: 成本效益分析

**id**: `skill_cost_benefit_analysis`
**name**: 成本效益分析
**description**: |
  分析养殖过程中的成本构成（饲料、电费、人工等）
  和预期收益，提供效益优化建议

**triggers**:
  - 每月定时触发
  - 养殖周期结束时
  - 用户手动触发

**actions**:
  - 计算总成本投入
  - 预测最终收益
  - 分析成本结构
  - 生成效益分析报告

**expected_outcomes**:
  - 成本明细表
  - 收益预测
  - 投入产出比
  - 优化建议

**验证状态**: ✅ 已实现（基于行业数据）
**数据来源**: 《我国南美白对虾养殖的经济效益分析》王静，上海海洋大学（CNKI）

---

## 技能执行示例

### 单个技能调用

```python
from src.agent.skill_manager import SkillManager

# 初始化技能管理器
skill_manager = SkillManager()

# 调用水质监控技能
result = skill_manager.execute_skill(
    skill_id="skill_water_monitoring",
    context={
        "do_level": 3.5,
        "ph": 8.2,
        "temperature": 29
    }
)

# 结果包含：
# - alerts: 生成的预警
# - actions: 执行的动作
# - reports: 生成的报告
# - logs: 执行日志
```

### 批量技能调用

```python
# 每日定时调用所有相关技能
skills_to_run = [
    "skill_water_monitoring",
    "skill_feeding_optimization",
    "skill_yield_prediction"
]

for skill_id in skills_to_run:
    result = skill_manager.execute_skill(skill_id)
```

---

## 技能开发规范

### 新技能定义模板

```yaml
id: skill_your_skill_name
name: 你的技能名称
description: |
  技能的详细描述
  说明这个技能的作用和应用场景

triggers:
  - 触发条件 1
  - 触发条件 2

actions:
  - 动作 1
  - 动作 2

expected_outcomes:
  - 预期结果 1
  - 预期结果 2

verification: 验证状态
```

---

## 技能优先级

根据养殖场景的重要性，技能优先级如下：

| 优先级 | 技能 | 理由 |
|-------|------|------|
| 🔴 P0 | skill_water_monitoring | 水质是养殖的基础 |
| 🔴 P0 | skill_aeration_control | 溶氧不足会致命 |
| 🔴 P0 | skill_feeding_optimization | 直接影响成本和产量 |
| 🟠 P1 | skill_disease_risk_alert | 提前预警减少损失 |
| 🟠 P1 | skill_yield_prediction | 辅助决策 |
| 🟡 P2 | skill_water_change_advisor | 水质调节的辅助手段 |
| 🟢 P3 | skill_auto_logging | 记录和追溯 |
| 🟢 P3 | skill_cost_benefit_analysis | 经营分析 |

---

## 技能状态

| 技能 | 状态 | 验证方式 | 完成度 |
|-----|------|---------|--------|
| skill_water_monitoring | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 100% |
| skill_feeding_optimization | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 100% |
| skill_aeration_control | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 100% |
| skill_water_change_advisor | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 100% |
| skill_disease_risk_alert | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 80% |
| skill_yield_prediction | ✅ 已实现 | Kaggle真实数据，R²=0.44 | 100% |
| skill_auto_logging | ✅ 已实现 | Kaggle真实数据 + 大模型场景 | 100% |
| skill_cost_benefit_analysis | ✅ 已实现 | Kaggle真实数据 + 大模型场景 + CNKI行业数据 | 100% |

---

## 技能扩展计划

### 短期（1-2月）

- [ ] 完善 skill_disease_risk_alert（添加图像识别）
- [ ] 完善 skill_cost_benefit_analysis（细化成本项）

### 中期（3-6月）

- [ ] 新增 skill_multi_pond_management（多塘口管理）
- [ ] 新增 skill_equipment_maintenance（设备维护提醒）
- [ ] 新增 skill_market_price_analysis（市场价格分析）

### 长期（6-12月）

- [ ] 新增 skill_supply_chain_optimization（供应链优化）
- [ ] 新增 skill_disease_diagnosis（疾病诊断）
- [ ] 新增 skill_breeding_advisor（繁殖管理）

---

## 重要说明

### 系统状态

```
数据来源：  Kaggle真实数据 + 通义千问大模型生成
技术架构：  大模型 + ML预测模型
验证方式：  真实数据验证 + 场景测试
完成度：    核心功能100%
```

### 技术亮点

```
✅ 混合数据策略：
   - Kaggle真实数据保证准确性
   - 大模型生成数据扩展场景

✅ 大模型应用：
   - 智能数据生成
   - 智能决策分析
   - 自然语言交互
   - 自动报告生成

✅ 技术架构：
   - 通义千问（大模型）
   - Random Forest/XGBoost（ML预测）
   - 完整的自动化循环
```

---

**© 2026 SmartShrimp Team · 智虾系统**
