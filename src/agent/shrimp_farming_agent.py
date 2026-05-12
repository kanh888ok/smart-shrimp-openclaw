#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 对虾养殖 AI Agent
符合 OpenClaw 挑战赛的核心要求：AI Agent 动手执行能力

核心功能：
1. 智能监控 - 实时数据分析
2. 自主决策 - 基于预测结果做出决策
3. 执行建议 - 生成可执行的操作指令
4. 效果模拟 - 模拟执行后的预期效果
5. 决策解释 - SHAP 可解释性分析
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass, asdict

# 引入现有系统
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from professional_analyzer import ShrimpDataLoader, FeatureEngineer, YieldPredictor
from advanced.model_explainer import ModelExplainer
from advanced.multi_modal_fusion import MultiModalPredictor


@dataclass
class Action:
    """执行动作数据类"""
    action_id: str
    action_type: str
    description: str
    reason: str
    parameters: Dict
    priority: str  # high, medium, low
    expected_effect: Dict
    execution_time: Optional[datetime] = None
    status: str = "pending"  # pending, executing, completed, failed


@dataclass
class MonitoringAlert:
    """监控告警"""
    alert_id: str
    severity: str  # critical, warning, info
    category: str  # water_quality, feeding, disease, equipment
    message: str
    current_value: float
    threshold: float
    recommendation: str
    timestamp: datetime


class ShrimpFarmingAgent:
    """
    对虾养殖 AI Agent

    这是符合 OpenClaw 挑战赛要求的核心 Agent 类，
    实现了从数据分析到自主决策的完整闭环。
    """

    def __init__(self, data_path, config: Optional[Dict] = None):
        """
        初始化 Agent

        Args:
            data_path: 数据文件路径
            config: 配置字典
        """
        self.data_path = data_path
        self.config = config or self._default_config()

        # 加载数据和模型
        self.loader = ShrimpDataLoader(data_path)
        self.df = self.loader.load()
        self.fe = FeatureEngineer(self.df)
        self.df_enhanced = self.fe.run_all()
        self.predictor = YieldPredictor(self.df_enhanced)
        self.predictor.run_all()

        # Agent 状态
        self.current_state = self._analyze_current_state()
        self.action_history: List[Action] = []
        self.alert_history: List[MonitoringAlert] = []

        # 性能指标
        self.total_decisions = 0
        self.successful_actions = 0

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            # 阈值设置
            'thresholds': {
                'FCR_critical': 2.5,
                'FCR_warning': 2.0,
                'SGR_critical': 0.5,
                'DO_critical': 3.0,
                'DO_warning': 4.0,
                'pH_warning_low': 7.5,
                'pH_warning_high': 8.5,
                'temp_warning_high': 32,
                'temp_warning_low': 22,
            },
            # 执行策略
            'execution_strategy': 'conservative',  # conservative, balanced, aggressive
            'simulation_mode': True,  # 是否为模拟模式
        }

    def _analyze_current_state(self) -> Dict:
        """分析当前状态"""
        latest = self.df_enhanced.iloc[-1]

        state = {
            'date': latest.get('日期', datetime.now()),
            'FCR': latest.get('FCR', 0),
            'SGR': latest.get('SGR', 0),
            'DO': latest.get('溶解氧 (mg/L)', 0),
            'pH': latest.get('pH 值', 0),
            'temperature': latest.get('水温 (°C)', 0),
            'survival_rate': latest.get('存活率 (%)', 0),
            'biomass': latest.get('预计产量 (kg)', 0),
            'stress_level': latest.get('环境压力指数', 0),
            'alert_level': latest.get('预警等级', '正常'),
        }

        return state

    def monitor(self) -> List[MonitoringAlert]:
        """
        智能监控 - Agent 的"感知"能力

        Returns:
            告警列表
        """
        alerts = []
        state = self.current_state
        thresholds = self.config['thresholds']

        # 1. FCR 监控
        if state['FCR'] > thresholds['FCR_critical']:
            alerts.append(MonitoringAlert(
                alert_id=f"FCR_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="critical",
                category="feeding",
                message=f"FCR 过高 ({state['FCR']:.2f})，饲料转化效率低",
                current_value=state['FCR'],
                threshold=thresholds['FCR_critical'],
                recommendation="立即减少投喂量 15-20%",
                timestamp=datetime.now()
            ))
        elif state['FCR'] > thresholds['FCR_warning']:
            alerts.append(MonitoringAlert(
                alert_id=f"FCR_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="warning",
                category="feeding",
                message=f"FCR 偏高 ({state['FCR']:.2f})",
                current_value=state['FCR'],
                threshold=thresholds['FCR_warning'],
                recommendation="建议减少投喂量 10%",
                timestamp=datetime.now()
            ))

        # 2. 溶解氧监控
        if state['DO'] < thresholds['DO_critical']:
            alerts.append(MonitoringAlert(
                alert_id=f"DO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="critical",
                category="water_quality",
                message=f"溶解氧过低 ({state['DO']:.2f} mg/L)，虾可能缺氧",
                current_value=state['DO'],
                threshold=thresholds['DO_critical'],
                recommendation="立即启动增氧机，运行 30 分钟",
                timestamp=datetime.now()
            ))
        elif state['DO'] < thresholds['DO_warning']:
            alerts.append(MonitoringAlert(
                alert_id=f"DO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="warning",
                category="water_quality",
                message=f"溶解氧偏低 ({state['DO']:.2f} mg/L)",
                current_value=state['DO'],
                threshold=thresholds['DO_warning'],
                recommendation="建议启动增氧机 15 分钟",
                timestamp=datetime.now()
            ))

        # 3. pH 值监控
        if state['pH'] < thresholds['pH_warning_low'] or state['pH'] > thresholds['pH_warning_high']:
            alerts.append(MonitoringAlert(
                alert_id=f"pH_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="warning",
                category="water_quality",
                message=f"pH 值异常 ({state['pH']:.2f})",
                current_value=state['pH'],
                threshold=thresholds['pH_warning_high'],
                recommendation="检查水质，必要时换水",
                timestamp=datetime.now()
            ))

        # 4. 水温监控
        if state['temperature'] > thresholds['temp_warning_high']:
            alerts.append(MonitoringAlert(
                alert_id=f"TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="warning",
                category="water_quality",
                message=f"水温过高 ({state['temperature']:.1f}°C)",
                current_value=state['temperature'],
                threshold=thresholds['temp_warning_high'],
                recommendation="增加换水频率，降低水温",
                timestamp=datetime.now()
            ))

        # 5. 存活率监控
        if state['survival_rate'] < 70:
            alerts.append(MonitoringAlert(
                alert_id=f"SURVIVAL_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                severity="critical",
                category="disease",
                message=f"存活率低 ({state['survival_rate']:.1f}%)",
                current_value=state['survival_rate'],
                threshold=70,
                recommendation="检查疾病风险，考虑提前收虾",
                timestamp=datetime.now()
            ))

        self.alert_history.extend(alerts)
        return alerts

    def decide(self, alerts: Optional[List[MonitoringAlert]] = None) -> List[Action]:
        """
        自主决策 - Agent 的"大脑"

        基于监控告警和预测分析，自主决定需要执行的操作

        Args:
            alerts: 监控告警列表（如果为 None，则自动运行监控）

        Returns:
            建议执行的动作列表
        """
        if alerts is None:
            alerts = self.monitor()

        actions = []
        state = self.current_state

        # 基于告警生成动作
        for alert in alerts:
            if alert.category == "feeding" and alert.severity == "critical":
                actions.append(Action(
                    action_id=f"FEED_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    action_type="adjust_feeding",
                    description="减少投喂量",
                    reason=alert.message,
                    parameters={
                        "reduction_percent": 20,
                        "duration_days": 3,
                        "current_fcr": state['FCR']
                    },
                    priority="high",
                    expected_effect={
                        "FCR_reduction": 0.3,
                        "feed_saving_kg": 50,
                        "time_to_effect": "2-3天"
                    }
                ))

            elif alert.category == "water_quality" and "溶解氧" in alert.message:
                duration = 30 if alert.severity == "critical" else 15
                actions.append(Action(
                    action_id=f"AERATE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    action_type="aeration",
                    description="启动增氧机",
                    reason=alert.message,
                    parameters={
                        "duration_minutes": duration,
                        "target_do": 5.0,
                        "current_do": state['DO']
                    },
                    priority="high" if alert.severity == "critical" else "medium",
                    expected_effect={
                        "DO_increase": 1.5,
                        "stress_reduction": 30,
                        "time_to_effect": "30分钟"
                    }
                ))

            elif alert.category == "water_quality" and "pH" in alert.message:
                actions.append(Action(
                    action_id=f"WATER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    action_type="water_change",
                    description="换水调节 pH",
                    reason=alert.message,
                    parameters={
                        "change_percent": 30,
                        "target_ph": 8.0,
                        "current_ph": state['pH']
                    },
                    priority="medium",
                    expected_effect={
                        "pH_change": 0.5,
                        "stress_reduction": 20,
                        "time_to_effect": "6-12小时"
                    }
                ))

        # 基于预测结果生成预防性动作
        prediction = self.predict_next_week()

        if prediction['predicted_FCR'] > self.config['thresholds']['FCR_warning']:
            actions.append(Action(
                action_id=f"PREVENT_FEED_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type="adjust_feeding",
                description="预防性减少投喂",
                reason=f"预测未来 7 天 FCR 将升至 {prediction['predicted_FCR']:.2f}",
                parameters={
                    "reduction_percent": 10,
                    "duration_days": 7,
                    "preventive": True
                },
                priority="medium",
                expected_effect={
                    "FCR_reduction": 0.2,
                    "feed_saving_kg": 30,
                    "time_to_effect": "3-5天"
                }
            ))

        if prediction['predicted_DO'] < self.config['thresholds']['DO_warning']:
            actions.append(Action(
                action_id=f"PREVENT_AERATE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                action_type="aeration",
                description="预防性增氧",
                reason=f"预测未来 7 天溶解氧将降至 {prediction['predicted_DO']:.2f} mg/L",
                parameters={
                    "schedule": "periodic",
                    "duration_minutes": 15,
                    "frequency": "每天2次"
                },
                priority="medium",
                expected_effect={
                    "DO_maintenance": 5.0,
                    "stress_reduction": 25,
                    "time_to_effect": "持续"
                }
            ))

        # 按优先级排序
        actions.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']])

        self.action_history.extend(actions)
        self.total_decisions += len(actions)

        return actions

    def execute(self, action: Action) -> Dict:
        """
        执行动作 - Agent 的"手"

        在实际部署中，这里会调用真实的设备 API。
        当前为模拟模式，返回预期效果。

        Args:
            action: 要执行的动作

        Returns:
            执行结果
        """
        action.status = "executing"
        action.execution_time = datetime.now()

        if self.config['simulation_mode']:
            # 模拟执行
            result = self._simulate_execution(action)
            action.status = "completed"
            self.successful_actions += 1
        else:
            # 实际执行（连接真实设备）
            result = self._real_execution(action)

        return result

    def _simulate_execution(self, action: Action) -> Dict:
        """模拟执行效果"""
        import random

        # 模拟执行时间
        execution_time = random.uniform(1, 5)

        # 模拟效果（有一定波动）
        effect = action.expected_effect.copy()

        if action.action_type == "adjust_feeding":
            effect['actual_FCR_reduction'] = effect['FCR_reduction'] * random.uniform(0.8, 1.2)
            effect['actual_feed_saving'] = effect['feed_saving_kg'] * random.uniform(0.9, 1.1)

        elif action.action_type == "aeration":
            effect['actual_DO_increase'] = effect['DO_increase'] * random.uniform(0.9, 1.1)
            effect['actual_stress_reduction'] = effect['stress_reduction'] * random.uniform(0.85, 1.15)

        result = {
            "action_id": action.action_id,
            "status": "success",
            "execution_time": execution_time,
            "simulated_effect": effect,
            "timestamp": datetime.now().isoformat(),
            "message": f"成功执行 {action.description}（模拟模式）"
        }

        return result

    def _real_execution(self, action: Action) -> Dict:
        """实际执行（需要连接真实设备 API）"""
        # TODO: 连接阿里云 IoT 平台或设备 API
        result = {
            "action_id": action.action_id,
            "status": "pending",
            "message": "实际执行功能需要在阿里云部署时配置设备 API"
        }
        return result

    def predict_next_week(self, days: int = 7) -> Dict:
        """
        预测未来状态

        Args:
            days: 预测天数

        Returns:
            预测结果字典
        """
        # 使用多模态融合预测器（如果可用）
        try:
            from advanced.multi_modal_fusion import run_multimodal_fusion
            multimodal_predictor = run_multimodal_fusion(
                self.df_enhanced,
                fusion_strategy='early'
            )

            # 这里简化处理，实际应该使用时序预测
            latest_FCR = self.current_state['FCR']
            latest_DO = self.current_state['DO']

            # 基于趋势预测
            FCR_trend = np.polyfit(range(len(self.df_enhanced)),
                                   self.df_enhanced['FCR'].values, 1)[0]
            DO_trend = np.polyfit(range(len(self.df_enhanced)),
                                  self.df_enhanced['溶解氧 (mg/L)'].values, 1)[0]

            predicted_FCR = latest_FCR + FCR_trend * days
            predicted_DO = latest_DO + DO_trend * days

        except Exception as e:
            # 回退到简单预测
            latest_FCR = self.current_state['FCR']
            latest_DO = self.current_state['DO']
            predicted_FCR = latest_FCR * 1.05  # 假设 FCR 会上升 5%
            predicted_DO = latest_DO * 0.95  # 假设 DO 会下降 5%

        return {
            'predicted_FCR': predicted_FCR,
            'predicted_DO': predicted_DO,
            'confidence': 'medium',
            'prediction_horizon': f'{days} 天'
        }

    def explain_decision(self, action: Action) -> Dict:
        """
        解释决策 - Agent 的"可解释性"

        使用 SHAP 分析为什么做出这个决策

        Args:
            action: 要解释的动作

        Returns:
            解释结果
        """
        try:
            # 准备特征
            feature_cols = [col for col in self.df_enhanced.columns
                          if col not in ['日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因']
                          and self.df_enhanced[col].dtype in ['float64', 'int64']]

            X = self.df_enhanced[feature_cols].fillna(self.df_enhanced[feature_cols].median())

            # 使用 SHAP 解释
            from advanced.model_explainer import explain_model
            from config import REPORTS_DIR

            output_dir = REPORTS_DIR / 'shap_analysis'
            explainer = explain_model(
                self.predictor.model,
                X.values,
                feature_cols,
                output_dir
            )

            # 获取关键特征
            top_features = explainer.get_top_features(5)

            explanation = {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "decision_reason": action.reason,
                "key_factors": top_features.to_dict('records') if top_features is not None else [],
                "model_confidence": self.predictor.metrics.get('R²', 0),
                "explanation_method": "SHAP (SHapley Additive exPlanations)"
            }

            return explanation

        except Exception as e:
            return {
                "action_id": action.action_id,
                "error": f"解释生成失败: {str(e)}",
                "explanation_method": "规则-based"
            }

    def run_agent_loop(self, iterations: int = 1) -> Dict:
        """
        运行 Agent 完整循环：监控 → 决策 → 执行 → 解释

        这是 Agent 的核心工作流程

        Args:
            iterations: 迭代次数

        Returns:
            运行结果摘要
        """
        summary = {
            'iterations_run': 0,
            'alerts_generated': 0,
            'actions_taken': 0,
            'success_rate': 0,
            'details': []
        }

        for i in range(iterations):
            # 1. 监控
            alerts = self.monitor()

            # 2. 决策
            actions = self.decide(alerts)

            # 3. 执行和解释
            iteration_details = {
                'iteration': i + 1,
                'timestamp': datetime.now().isoformat(),
                'alerts': [asdict(alert) for alert in alerts],
                'actions': []
            }

            for action in actions:
                # 执行
                result = self.execute(action)

                # 解释
                explanation = self.explain_decision(action)

                iteration_details['actions'].append({
                    'action': asdict(action),
                    'result': result,
                    'explanation': explanation
                })

            summary['details'].append(iteration_details)
            summary['iterations_run'] += 1
            summary['alerts_generated'] += len(alerts)
            summary['actions_taken'] += len(actions)

        # 计算成功率
        if self.total_decisions > 0:
            summary['success_rate'] = self.successful_actions / self.total_decisions

        return summary

    def get_agent_status(self) -> Dict:
        """获取 Agent 状态"""
        return {
            'current_state': self.current_state,
            'total_decisions': self.total_decisions,
            'successful_actions': self.successful_actions,
            'success_rate': self.successful_actions / self.total_decisions if self.total_decisions > 0 else 0,
            'pending_actions': len([a for a in self.action_history if a.status == 'pending']),
            'active_alerts': len([a for a in self.alert_history if a.severity == 'critical']),
            'config': self.config
        }

    def export_report(self) -> str:
        """导出 Agent 运行报告"""
        status = self.get_agent_status()

        report = f"""
# OpenClaw 对虾养殖 AI Agent 运行报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 当前状态

- 日期: {status['current_state']['date']}
- FCR: {status['current_state']['FCR']:.2f}
- SGR: {status['current_state']['SGR']:.2f}%
- 溶解氧: {status['current_state']['DO']:.2f} mg/L
- pH 值: {status['current_state']['pH']:.2f}
- 水温: {status['current_state']['temperature']:.1f}°C
- 存活率: {status['current_state']['survival_rate']:.1f}%
- 环境压力指数: {status['current_state']['stress_level']:.2f}
- 预警等级: {status['current_state']['alert_level']}

## Agent 性能

- 总决策数: {status['total_decisions']}
- 成功执行: {status['successful_actions']}
- 成功率: {status['success_rate']:.1%}
- 待执行动作: {status['pending_actions']}
- 活跃告警: {status['active_alerts']}

## 最近告警

"""

        # 添加最近 5 个告警
        recent_alerts = self.alert_history[-5:]
        for alert in recent_alerts:
            report += f"- **{alert.severity.upper()}** [{alert.category}]: {alert.message}\n"
            report += f"  - 当前值: {alert.current_value}, 阈值: {alert.threshold}\n"
            report += f"  - 建议: {alert.recommendation}\n\n"

        # 添加最近动作
        report += "## 最近执行的动作\n\n"
        recent_actions = self.action_history[-5:]
        for action in recent_actions:
            report += f"- **{action.action_type}**: {action.description}\n"
            report += f"  - 原因: {action.reason}\n"
            report += f"  - 优先级: {action.priority}\n"
            report += f"  - 状态: {action.status}\n"
            report += f"  - 预期效果: {action.expected_effect}\n\n"

        return report


def run_agent_demo(data_path: str) -> ShrimpFarmingAgent:
    """
    运行 Agent 演示

    Args:
        data_path: 数据文件路径

    Returns:
        Agent 实例
    """
    print("=" * 60)
    print("🦞 OpenClaw 对虾养殖 AI Agent")
    print("=" * 60)
    print()

    # 创建 Agent
    print("📊 正在初始化 Agent...")
    agent = ShrimpFarmingAgent(data_path)
    print(f"✅ Agent 初始化完成")
    print()

    # 显示当前状态
    print("📈 当前养殖状态:")
    state = agent.current_state
    for key, value in state.items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.2f}")
        else:
            print(f"  - {key}: {value}")
    print()

    # 运行监控
    print("🔍 运行智能监控...")
    alerts = agent.monitor()
    print(f"✅ 发现 {len(alerts)} 个告警")
    if alerts:
        print()
        for alert in alerts:
            print(f"  [{alert.severity.upper()}] {alert.message}")
    print()

    # 运行决策
    print("🧠 运行自主决策...")
    actions = agent.decide(alerts)
    print(f"✅ 生成 {len(actions)} 个执行动作")
    if actions:
        print()
        for action in actions:
            print(f"  - {action.description} (优先级: {action.priority})")
    print()

    # 执行动作
    print("⚡ 执行动作...")
    for action in actions:
        result = agent.execute(action)
        print(f"  ✅ {action.description}: {result['message']}")
        if 'simulated_effect' in result:
            effect = result['simulated_effect']
            print(f"     预期效果: {effect}")
    print()

    # 显示性能
    status = agent.get_agent_status()
    print("📊 Agent 性能:")
    print(f"  - 总决策数: {status['total_decisions']}")
    print(f"  - 成功执行: {status['successful_actions']}")
    print(f"  - 成功率: {status['success_rate']:.1%}")
    print()

    # 生成报告
    print("📄 生成运行报告...")
    report = agent.export_report()
    report_path = Path("reports/agent_report.md")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ 报告已保存到: {report_path}")
    print()

    return agent


if __name__ == "__main__":
    # 运行演示
    from config import DATA_DIR

    # 查找数据文件
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        data_path = str(data_files[0])
        agent = run_agent_demo(data_path)
    else:
        print("❌ 未找到数据文件，请先在 data/ 目录下放置数据文件")
