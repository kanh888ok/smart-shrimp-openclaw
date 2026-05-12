#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能管理器 - 管理和执行养虾技能

支持：
1. 技能注册和发现
2. 技能触发条件检查
3. 技能执行和结果返回
4. 技能组合调用
5. 技能执行日志
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class SkillResult:
    """技能执行结果"""
    skill_id: str
    skill_name: str
    success: bool
    triggered: bool
    message: str
    data: dict
    timestamp: str
    execution_time: float


class Skill:
    """技能基类"""

    def __init__(self, skill_id: str, config: dict = None):
        self.skill_id = skill_id
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def check_trigger(self, context: dict) -> bool:
        """检查触发条件"""
        raise NotImplementedError

    def execute(self, context: dict) -> dict:
        """执行技能"""
        raise NotImplementedError

    def get_expected_outcomes(self) -> list:
        """返回预期结果"""
        return []


class WaterMonitoringSkill(Skill):
    """水质监控技能"""

    def check_trigger(self, context: dict) -> bool:
        """检查是否需要触发"""
        do_level = context.get('do_level', 999)
        ph = context.get('ph', 8.0)
        temperature = context.get('temperature', 28)
        ammonia = context.get('ammonia', 0)

        # 检查各项指标
        triggers = []

        if do_level < 5.0:
            triggers.append(f"溶解氧偏低 ({do_level:.2f} mg/L)")

        if ph < 7.5 or ph > 8.5:
            triggers.append(f"pH 异常 ({ph:.2f})")

        if temperature < 22 or temperature > 32:
            triggers.append(f"水温异常 ({temperature:.1f}°C)")

        if ammonia > 0.5:
            triggers.append(f"氨氮超标 ({ammonia:.2f} mg/L)")

        return len(triggers) > 0

    def execute(self, context: dict) -> dict:
        """执行水质监控"""
        from ..professional_analyzer import ShrimpDataLoader, FeatureEngineer

        # 生成预警
        alerts = []
        do_level = context.get('do_level', 999)
        ph = context.get('ph', 8.0)
        temperature = context.get('temperature', 28)

        if do_level < 3.0:
            alerts.append({
                'severity': 'critical',
                'message': f'溶解氧严重过低 ({do_level:.2f} mg/L)',
                'recommendation': '立即启动增氧机'
            })
        elif do_level < 5.0:
            alerts.append({
                'severity': 'warning',
                'message': f'溶解氧偏低 ({do_level:.2f} mg/L)',
                'recommendation': '建议启动增氧机'
            })

        if ph < 7.5 or ph > 8.5:
            alerts.append({
                'severity': 'warning',
                'message': f'pH 异常 ({ph:.2f})',
                'recommendation': '检查并调节 pH'
            })

        return {
            'alerts': alerts,
            'current_status': {
                'do_level': do_level,
                'ph': ph,
                'temperature': temperature
            }
        }

    def get_expected_outcomes(self) -> list:
        return [
            '发现水质异常',
            '生成预警报告',
            '提供处理建议'
        ]


class FeedingOptimizationSkill(Skill):
    """投喂优化技能"""

    def check_trigger(self, context: dict) -> bool:
        """检查是否需要触发"""
        # 可以根据时间、FCR、溶解氧等触发
        trigger_reasons = []

        # 定时触发
        current_hour = datetime.now().hour
        if current_hour in [8, 17]:  # 早上8点和下午5点
            trigger_reasons.append('定时投喂时间')

        # FCR 触发
        if context.get('fcr', 0) > 2.0:
            trigger_reasons.append('FCR 过高')

        # 溶解氧触发
        if context.get('low_do', False):
            trigger_reasons.append('溶解氧偏低')

        return len(trigger_reasons) > 0

    def execute(self, context: dict) -> dict:
        """执行投喂优化"""
        # 计算投喂量
        base_feed = context.get('base_feed', 50)  # 基础投喂量 kg

        # 根据条件调整
        reduction_percent = 0

        if context.get('fcr', 0) > 2.0:
            reduction_percent += 15

        if context.get('low_do', False):
            reduction_percent += 10

        if context.get('temperature', 28) > 30:
            reduction_percent += 10

        # 计算最终投喂量
        adjusted_feed = base_feed * (1 - reduction_percent / 100)

        return {
            'base_feed': base_feed,
            'reduction_percent': reduction_percent,
            'adjusted_feed': adjusted_feed,
            'feeding_schedule': {
                'morning': adjusted_feed * 0.4,
                'evening': adjusted_feed * 0.6
            },
            'recommendations': [
                f'建议投喂量: {adjusted_feed:.1f} kg/天',
                f'较基础投喂减少 {reduction_percent}%',
                '早上投 40%，下午投 60%'
            ]
        }

    def get_expected_outcomes(self) -> list:
        return [
            '投喂量优化建议',
            '投喂时间表',
            '预期 FCR 改善'
        ]


class AerationControlSkill(Skill):
    """增氧控制技能"""

    def check_trigger(self, context: dict) -> bool:
        """检查是否需要触发"""
        do_level = context.get('do_level', 999)

        # 溶解氧低于阈值
        return do_level < 5.0

    def execute(self, context: dict) -> dict:
        """执行增氧控制"""
        do_level = context.get('do_level', 5.0)

        # 计算增氧时长
        if do_level < 3.0:
            # 严重缺氧
            duration = 60  # 60分钟
            priority = 'critical'
        elif do_level < 4.0:
            # 中度缺氧
            duration = 30
            priority = 'high'
        else:
            # 轻度缺氧
            duration = 15
            priority = 'medium'

        # 预测增氧后效果
        expected_do = min(do_level + 1.5, 8.0)  # 预计上升 1.5 mg/L

        return {
            'aeration_command': {
                'action': 'start_aerator',
                'duration_minutes': duration,
                'priority': priority,
                'target_do': expected_do
            },
            'expected_outcome': {
                'current_do': do_level,
                'expected_do': expected_do,
                'time_to_effect': f'{duration} 分钟'
            },
            'recommendations': [
                f'启动增氧机 {duration} 分钟',
                f'预计溶解氧升至 {expected_do:.2f} mg/L',
                f'优先级: {priority}'
            ]
        }

    def get_expected_outcomes(self) -> list:
        return [
            '增氧时长计算',
            '增氧控制指令',
            '预期溶解氧恢复时间'
        ]


class SkillManager:
    """
    技能管理器

    管理所有养虾技能的注册、触发、执行
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.skills: Dict[str, Skill] = {}
        self.logger = logging.getLogger(__name__)

        # 注册默认技能
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认技能"""
        self.register_skill(
            'skill_water_monitoring',
            WaterMonitoringSkill('skill_water_monitoring')
        )

        self.register_skill(
            'skill_feeding_optimization',
            FeedingOptimizationSkill('skill_feeding_optimization')
        )

        self.register_skill(
            'skill_aeration_control',
            AerationControlSkill('skill_aeration_control')
        )

    def register_skill(self, skill_id: str, skill: Skill):
        """注册技能"""
        self.skills[skill_id] = skill
        self.logger.info(f"技能已注册: {skill_id}")

    def check_skill_trigger(self, skill_id: str, context: dict) -> bool:
        """检查技能是否应该触发"""
        if skill_id not in self.skills:
            self.logger.warning(f"技能不存在: {skill_id}")
            return False

        skill = self.skills[skill_id]
        return skill.check_trigger(context)

    def execute_skill(
        self,
        skill_id: str,
        context: dict,
        force: bool = False
    ) -> SkillResult:
        """
        执行技能

        Args:
            skill_id: 技能 ID
            context: 执行上下文
            force: 是否强制执行（跳过触发检查）

        Returns:
            技能执行结果
        """
        start_time = datetime.now()

        if skill_id not in self.skills:
            return SkillResult(
                skill_id=skill_id,
                skill_name='Unknown',
                success=False,
                triggered=False,
                message=f'技能不存在: {skill_id}',
                data={},
                timestamp=start_time.isoformat(),
                execution_time=0
            )

        skill = self.skills[skill_id]

        # 检查触发条件
        triggered = False
        if not force:
            triggered = skill.check_trigger(context)
            if not triggered:
                return SkillResult(
                    skill_id=skill_id,
                    skill_name=skill_id,
                    success=True,
                    triggered=False,
                    message='触发条件未满足',
                    data={},
                    timestamp=start_time.isoformat(),
                    execution_time=0
                )
        else:
            triggered = True

        # 执行技能
        try:
            result_data = skill.execute(context)

            execution_time = (datetime.now() - start_time).total_seconds()

            return SkillResult(
                skill_id=skill_id,
                skill_name=skill_id,
                success=True,
                triggered=triggered,
                message='技能执行成功',
                data=result_data,
                timestamp=start_time.isoformat(),
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"技能执行失败: {e}")

            return SkillResult(
                skill_id=skill_id,
                skill_name=skill_id,
                success=False,
                triggered=triggered,
                message=f'执行失败: {str(e)}',
                data={},
                timestamp=start_time.isoformat(),
                execution_time=execution_time
            )

    def execute_skills_batch(
        self,
        skill_ids: List[str],
        context: dict
    ) -> List[SkillResult]:
        """批量执行技能"""
        results = []

        for skill_id in skill_ids:
            result = self.execute_skill(skill_id, context)
            results.append(result)

        return results

    def get_skill_info(self, skill_id: str) -> Optional[dict]:
        """获取技能信息"""
        if skill_id not in self.skills:
            return None

        skill = self.skills[skill_id]

        return {
            'skill_id': skill_id,
            'class': skill.__class__.__name__,
            'expected_outcomes': skill.get_expected_outcomes()
        }

    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())

    def save_execution_log(self, result: SkillResult, log_dir: str = "output/logs"):
        """保存执行日志"""
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        log_file = log_path / f"skill_execution_{datetime.now().strftime('%Y%m%d')}.jsonl"

        log_entry = {
            'skill_id': result.skill_id,
            'skill_name': result.skill_name,
            'success': result.success,
            'triggered': result.triggered,
            'message': result.message,
            'data': result.data,
            'timestamp': result.timestamp,
            'execution_time': result.execution_time
        }

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


# 便捷函数
def create_skill_manager() -> SkillManager:
    """创建技能管理器"""
    return SkillManager()


def demo_skills():
    """演示技能使用"""
    import sys
    from pathlib import Path

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("🔧 智虾系统 - 技能演示")
    print("=" * 60)
    print()

    # 创建技能管理器
    skill_manager = create_skill_manager()

    print("已注册的技能:")
    for skill_id in skill_manager.list_skills():
        info = skill_manager.get_skill_info(skill_id)
        print(f"  - {skill_id}")
        print(f"    类别: {info['class']}")
        print(f"    预期结果: {', '.join(info['expected_outcomes'])}")
    print()

    # 场景 1: 正常情况
    print("场景 1: 水质正常")
    print("-" * 60)
    context1 = {
        'do_level': 6.0,
        'ph': 8.0,
        'temperature': 28,
        'base_feed': 50
    }

    result1 = skill_manager.execute_skill(
        'skill_water_monitoring',
        context1
    )
    print(f"触发: {result1.triggered}")
    print(f"消息: {result1.message}")
    print()

    # 场景 2: 溶解氧过低
    print("场景 2: 溶解氧过低")
    print("-" * 60)
    context2 = {
        'do_level': 3.5,
        'ph': 8.0,
        'temperature': 28,
        'base_feed': 50
    }

    # 水质监控
    result2a = skill_manager.execute_skill(
        'skill_water_monitoring',
        context2
    )
    print(f"水质监控: {result2a.message}")
    if result2a.data.get('alerts'):
        for alert in result2a.data['alerts']:
            print(f"  - [{alert['severity']}] {alert['message']}")
            print(f"    建议: {alert['recommendation']}")

    # 增氧控制
    result2b = skill_manager.execute_skill(
        'skill_aeration_control',
        context2
    )
    print(f"增氧控制: {result2b.message}")
    if result2b.triggered:
        command = result2b.data['aeration_command']
        print(f"  - 启动增氧机 {command['duration_minutes']} 分钟")
        print(f"  - 预计溶解氧升至 {command['target_do']:.2f} mg/L")

    # 投喂优化
    result2c = skill_manager.execute_skill(
        'skill_feeding_optimization',
        {**context2, 'low_do': True}
    )
    print(f"投喂优化: {result2c.message}")
    if result2c.triggered:
        recs = result2c.data['recommendations']
        for rec in recs:
            print(f"  - {rec}")

    print()
    print("✅ 演示完成")


if __name__ == "__main__":
    demo_skills()
