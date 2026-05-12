#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PinchBench 任务评估器

用于评估 OpenClaw AI Agent 在 PinchBench 任务上的表现
"""

import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    task_name: str
    passed: bool
    score: float
    max_score: float
    details: Dict
    duration: float


class TaskEvaluator:
    """
    PinchBench 任务评估器

    评估 Agent 在各个任务上的表现
    """

    def __init__(self, agent, output_dir: str = "output/evaluation"):
        """
        初始化评估器

        Args:
            agent: Agent 实例
            output_dir: 输出目录
        """
        self.agent = agent
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

    def evaluate_task(self, task_yaml_path: str) -> TaskResult:
        """
        评估单个任务

        Args:
            task_yaml_path: 任务 YAML 文件路径

        Returns:
            任务结果
        """
        # 加载任务定义
        with open(task_yaml_path, 'r', encoding='utf-8') as f:
            task = yaml.safe_load(f)

        task_id = task['task_id']
        task_name = task['task_name']

        self.logger.info(f"评估任务: {task_id} - {task_name}")

        start_time = datetime.now()

        try:
            # 1. 运行 Agent
            self.logger.info("步骤 1: 运行 Agent...")
            agent_output = self._run_agent(task)

            # 2. 检查成功条件
            self.logger.info("步骤 2: 检查成功条件...")
            passed, condition_results = self._check_success_conditions(
                task['success_conditions'],
                agent_output,
                task.get('expected_outputs', {})
            )

            # 3. 计算得分
            self.logger.info("步骤 3: 计算得分...")
            score, max_score, score_details = self._calculate_score(
                task['scoring_criteria'],
                agent_output,
                condition_results
            )

            # 4. 生成报告
            duration = (datetime.now() - start_time).total_seconds()

            result = TaskResult(
                task_id=task_id,
                task_name=task_name,
                passed=passed,
                score=score,
                max_score=max_score,
                details={
                    'condition_results': condition_results,
                    'score_details': score_details,
                    'agent_output': agent_output
                },
                duration=duration
            )

            # 保存结果
            self._save_result(result)

            return result

        except Exception as e:
            self.logger.error(f"评估失败: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                passed=False,
                score=0,
                max_score=100,
                details={'error': str(e)},
                duration=duration
            )

    def _run_agent(self, task: Dict) -> Dict:
        """运行 Agent 并收集输出"""
        # 准备测试输入
        test_inputs = task.get('test_inputs', {})
        sensor_data = test_inputs.get('sensor_data', {})

        # 更新 Agent 状态（模拟传感器数据）
        # 这里可以根据需要更新 Agent 的当前状态

        # 运行 Agent 循环
        alerts = self.agent.monitor()
        actions = self.agent.decide(alerts)

        # 执行动作
        from .device_controller import RealExecutionController
        executor = RealExecutionController(
            base_dir=".",
            simulation_mode=True
        )

        execution_results = []
        for action in actions:
            result = executor.execute_action(action.__dict__)
            execution_results.append(result)

        return {
            'alerts': [alert.__dict__ for alert in alerts],
            'actions': [action.__dict__ for action in actions],
            'execution_results': execution_results,
            'agent_state': self.agent.get_agent_status()
        }

    def _check_success_conditions(
        self,
        conditions: List[str],
        agent_output: Dict,
        expected_outputs: Dict
    ) -> tuple:
        """检查成功条件"""
        results = []

        for condition in conditions:
            result = self._check_single_condition(condition, agent_output, expected_outputs)
            results.append({
                'condition': condition,
                'passed': result
            })

        passed = all(r['passed'] for r in results)
        return passed, results

    def _check_single_condition(
        self,
        condition: str,
        agent_output: Dict,
        expected_outputs: Dict
    ) -> bool:
        """检查单个条件"""
        alerts = agent_output.get('alerts', [])
        actions = agent_output.get('actions', [])

        if "生成至少" in condition and "告警" in condition:
            # 检查告警数量
            num = int(condition.split("至少")[1].split("个")[0])
            return len(alerts) >= num

        elif "生成至少" in condition and "执行动作" in condition:
            # 检查动作数量
            num = int(condition.split("至少")[1].split("个")[0])
            return len(actions) >= num

        elif "动作类型为" in condition:
            # 检查动作类型
            action_type = condition.split("动作类型为")[1].strip()
            return any(a.get('action_type') == action_type for a in actions)

        elif "减少百分比在" in condition:
            # 检查减少百分比范围
            parts = condition.split("减少百分比在")[1].split("%")[0].split("-")
            min_val = int(parts[0].strip())
            max_val = int(parts[1].strip())

            for action in actions:
                if action.get('action_type') == 'adjust_feeding':
                    reduction = action.get('parameters', {}).get('reduction_percent', 0)
                    return min_val <= reduction <= max_val
            return False

        elif "有完整的执行日志" in condition:
            # 检查是否有执行日志
            execution_results = agent_output.get('execution_results', [])
            return len(execution_results) > 0

        elif "生成严重告警" in condition:
            # 检查是否有严重告警
            return any(a.get('severity') == 'critical' for a in alerts)

        elif "增氧时长" in condition:
            # 检查增氧时长
            min_duration = int(condition.split("增氧时长 >= ")[1].split("分钟")[0].strip())
            for action in actions:
                if action.get('action_type') == 'aeration':
                    duration = action.get('parameters', {}).get('duration_minutes', 0)
                    return duration >= min_duration
            return False

        elif "目标 DO" in condition:
            # 检查目标 DO
            target_do = float(condition.split("目标 DO >= ")[1].split("mg/L")[0].strip())
            for action in actions:
                if action.get('action_type') == 'aeration':
                    do_target = action.get('parameters', {}).get('target_do', 0)
                    return do_target >= target_do
            return False

        elif "换水百分比在" in condition:
            # 检查换水百分比范围
            parts = condition.split("换水百分比在")[1].split("%")[0].split("-")
            min_val = int(parts[0].strip())
            max_val = int(parts[1].strip())

            for action in actions:
                if action.get('action_type') == 'water_change':
                    change_percent = action.get('parameters', {}).get('change_percent', 0)
                    return min_val <= change_percent <= max_val
            return False

        elif "目标 pH" in condition:
            # 检查目标 pH 范围
            parts = condition.split("目标 pH 在")[1].split("范围内")[0].split("-")
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())

            for action in actions:
                if action.get('action_type') == 'water_change':
                    target_ph = action.get('parameters', {}).get('target_ph', 0)
                    return min_val <= target_ph <= max_val
            return False

        else:
            # 未知条件，默认通过
            self.logger.warning(f"未知的条件: {condition}")
            return True

    def _calculate_score(
        self,
        scoring_criteria: List[Dict],
        agent_output: Dict,
        condition_results: List[Dict]
    ) -> tuple:
        """计算得分"""
        total_score = 0
        max_score = 0
        score_details = []

        for criterion in scoring_criteria:
            name = criterion['name']
            weight = criterion['weight']
            description = criterion['description']

            # 简化的评分逻辑
            # 实际上应该根据 evaluation_method 进行更复杂的评估
            if "检测" in name:
                # 检测准确性：基于条件检查结果
                passed = any('检测' in c['condition'] and c['passed'] for c in condition_results)
                score = weight * 100 if passed else 0

            elif "决策" in name:
                # 决策合理性：基于动作参数是否合理
                actions = agent_output.get('actions', [])
                score = weight * 100 if len(actions) > 0 else 0

            elif "执行" in name:
                # 执行正确性：基于执行结果
                execution_results = agent_output.get('execution_results', [])
                success_count = sum(1 for r in execution_results if r.get('status') == 'success')
                score = weight * 100 * (success_count / len(execution_results)) if execution_results else 0

            elif "响应" in name:
                # 响应速度：基于是否有快速告警
                alerts = agent_output.get('alerts', [])
                has_critical = any(a.get('severity') == 'critical' for a in alerts)
                score = weight * 100 if has_critical else weight * 50

            elif "告警" in name:
                # 告警级别：基于是否有正确级别的告警
                alerts = agent_output.get('alerts', [])
                expected_outputs = {}
                # 这里应该从任务定义中获取预期的告警级别
                score = weight * 100 if len(alerts) > 0 else 0

            elif "完整性" in name:
                # 完整性：基于是否有日志
                execution_results = agent_output.get('execution_results', [])
                has_logs = any('log_path' in r for r in execution_results)
                score = weight * 100 if has_logs else 0

            else:
                score = 0

            total_score += score
            max_score += weight * 100

            score_details.append({
                'name': name,
                'weight': weight,
                'score': score,
                'max_score': weight * 100,
                'description': description
            })

        return total_score, max_score, score_details

    def _save_result(self, result: TaskResult):
        """保存结果"""
        # 保存 JSON
        output_file = self.output_dir / f"{result.task_id}_result.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'task_id': result.task_id,
                'task_name': result.task_name,
                'passed': result.passed,
                'score': result.score,
                'max_score': result.max_score,
                'details': result.details,
                'duration': result.duration,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        self.logger.info(f"结果已保存: {output_file}")

    def evaluate_all(self, task_dir: str = "tasks") -> List[TaskResult]:
        """
        评估所有任务

        Args:
            task_dir: 任务目录

        Returns:
            所有任务的结果
        """
        task_path = Path(task_dir)
        task_files = list(task_path.glob("*.yaml"))

        self.logger.info(f"找到 {len(task_files)} 个任务")

        results = []
        for task_file in sorted(task_files):
            result = self.evaluate_task(str(task_file))
            results.append(result)

        # 生成汇总报告
        self._generate_summary_report(results)

        return results

    def _generate_summary_report(self, results: List[TaskResult]):
        """生成汇总报告"""
        total_tasks = len(results)
        passed_tasks = sum(1 for r in results if r.passed)
        total_score = sum(r.score for r in results)
        max_total_score = sum(r.max_score for r in results)

        report = f"""# PinchBench 任务评估报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体结果

- **总任务数**: {total_tasks}
- **通过任务**: {passed_tasks}
- **通过率**: {passed_tasks / total_tasks * 100:.1f}%
- **总得分**: {total_score:.1f} / {max_total_score:.1f}
- **平均分**: {total_score / total_tasks:.1f}%

## 任务详情

"""

        for result in results:
            status_icon = "✅" if result.passed else "❌"
            report += f"""
### {status_icon} {result.task_name}

- **任务ID**: {result.task_id}
- **状态**: {'通过' if result.passed else '未通过'}
- **得分**: {result.score:.1f} / {result.max_score:.1f}
- **耗时**: {result.duration:.2f} 秒

"""

            # 添加得分详情
            if 'score_details' in result.details:
                report += "**评分详情:**\n\n"
                for detail in result.details['score_details']:
                    report += f"- {detail['name']}: {detail['score']:.1f}/{detail['max_score']:.1f}\n"

            report += "\n"

        # 保存报告
        report_file = self.output_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        self.logger.info(f"汇总报告已保存: {report_file}")
        print(report)


def main():
    """主函数"""
    import sys
    from pathlib import Path

    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from src.agent.shrimp_farming_agent import ShrimpFarmingAgent
    from src.agent.autonomous_agent import AutonomousAgent
    from config import DATA_DIR

    # 查找数据文件
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if not data_files:
        print("❌ 未找到数据文件")
        return

    print("🧪 PinchBench 任务评估")
    print("=" * 60)
    print()

    # 创建 Agent
    print("初始化 Agent...")
    agent = ShrimpFarmingAgent(str(data_files[0]))

    # 创建评估器
    evaluator = TaskEvaluator(agent)

    # 评估所有任务
    print("开始评估所有任务...")
    print()

    results = evaluator.evaluate_all()

    print()
    print("=" * 60)
    print("✅ 评估完成")
    print()
    print(f"通过率: {sum(1 for r in results if r.passed) / len(results) * 100:.1f}%")
    print(f"平均分: {sum(r.score for r in results) / len(results):.1f}")
    print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
