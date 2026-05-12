#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主循环 Agent - 实现真正的自主性

核心特性：
1. 持续监控（自主感知）
2. 自动决策（无需人工触发）
3. 循环执行（感知-决策-执行闭环）
4. 日志记录（完整的可追溯性）
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

from .shrimp_farming_agent import ShrimpFarmingAgent, Action, MonitoringAlert

# 可选导入（需要requests）
try:
    from .device_controller import RealExecutionController
except ImportError:
    RealExecutionController = None


class AutonomousAgent:
    """
    自主循环 Agent

    这是 OpenClaw 的核心：一个能够自主感知、决策、执行的 Agent
    """

    def __init__(
        self,
        data_path: str,
        check_interval: int = 60,  # 检查间隔（秒）
        max_continuous_running: int = 3600,  # 最大连续运行时间（秒）
        config: Optional[Dict] = None
    ):
        """
        初始化自主 Agent

        Args:
            data_path: 数据文件路径
            check_interval: 检查间隔（秒）
            max_continuous_running: 最大连续运行时间（秒）
            config: 配置字典
        """
        # 基础 Agent
        self.base_agent = ShrimpFarmingAgent(data_path, config)

        # 执行控制器
        self.execution_controller = RealExecutionController(
            base_dir=".",
            simulation_mode=config.get('simulation_mode', True) if config else True,
            config=config
        )

        # 自主循环配置
        self.check_interval = check_interval
        self.max_continuous_running = max_continuous_running

        # 运行状态
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.stop_time: Optional[datetime] = None
        self.cycle_count = 0

        # 统计
        self.total_cycles = 0
        self.total_alerts = 0
        self.total_actions = 0
        self.total_errors = 0

        # 日志
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('output/logs/autonomous_agent.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def start(self, max_cycles: Optional[int] = None) -> Dict:
        """
        启动自主循环

        Args:
            max_cycles: 最大循环次数（None 表示无限制）

        Returns:
            运行结果摘要
        """
        if self.is_running:
            self.logger.warning("Agent 已经在运行中")
            return {"status": "already_running"}

        self.is_running = True
        self.start_time = datetime.now()
        self.cycle_count = 0

        self.logger.info("=" * 60)
        self.logger.info("🤖 OpenClaw 自主 Agent 启动")
        self.logger.info("=" * 60)
        self.logger.info(f"检查间隔: {self.check_interval} 秒")
        self.logger.info(f"最大循环次数: {max_cycles or '无限制'}")
        self.logger.info(f"最大运行时间: {self.max_continuous_running} 秒")
        self.logger.info("")

        try:
            # 主循环
            while self.is_running:
                # 检查停止条件
                if max_cycles and self.cycle_count >= max_cycles:
                    self.logger.info(f"达到最大循环次数: {max_cycles}")
                    break

                if self.start_time and \
                   (datetime.now() - self.start_time).total_seconds() > self.max_continuous_running:
                    self.logger.info(f"达到最大运行时间: {self.max_continuous_running} 秒")
                    break

                # 执行一个循环
                self._run_cycle()

                # 等待下一次检查
                if self.is_running:
                    self.logger.info(f"⏰ 等待 {self.check_interval} 秒后进行下一次检查...")
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("\n收到停止信号，正在停止...")
        except Exception as e:
            self.logger.error(f"❌ 运行出错: {e}", exc_info=True)
            self.total_errors += 1
        finally:
            self.stop()

        return self._get_summary()

    def stop(self):
        """停止自主循环"""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_time = datetime.now()

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("🛑 OpenClaw 自主 Agent 停止")
        self.logger.info("=" * 60)

    def _run_cycle(self):
        """运行一个完整的感知-决策-执行循环"""
        self.cycle_count += 1
        cycle_start = datetime.now()

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(f"🔄 循环 #{self.cycle_count} 开始")
        self.logger.info("=" * 60)

        # 1. 感知（监控）
        self.logger.info("🔍 步骤 1/4: 感知环境状态...")
        alerts = self.base_agent.monitor()
        self.total_alerts += len(alerts)

        if alerts:
            self.logger.info(f"   发现 {len(alerts)} 个告警:")
            for alert in alerts:
                self.logger.info(f"   - [{alert.severity.upper()}] {alert.message}")

            # 处理告警（写入传感器数据，发送通知）
            for alert in alerts:
                self.execution_controller.process_alert(alert.__dict__)
        else:
            self.logger.info("   ✅ 当前状态良好，无告警")

        # 2. 决策
        self.logger.info("")
        self.logger.info("🧠 步骤 2/4: 自主决策...")
        actions = self.base_agent.decide(alerts)
        self.total_actions += len(actions)

        if actions:
            self.logger.info(f"   生成 {len(actions)} 个执行动作:")
            for action in actions:
                self.logger.info(f"   - {action.action_type}: {action.description} (优先级: {action.priority})")
        else:
            self.logger.info("   无需执行动作")

        # 3. 执行
        self.logger.info("")
        self.logger.info("⚡ 步骤 3/4: 执行动作...")

        for action in actions:
            self.logger.info(f"   执行: {action.description}")

            # 使用真实执行控制器
            result = self.execution_controller.execute_action(action.__dict__)

            if result.get('status') == 'success':
                self.logger.info(f"   ✅ {result.get('message', '执行成功')}")
            else:
                self.logger.error(f"   ❌ {result.get('message', '执行失败')}")
                self.total_errors += 1

        # 4. 记录和报告
        self.logger.info("")
        self.logger.info("📊 步骤 4/4: 记录和报告...")

        # 更新统计
        self.total_cycles += 1

        # 计算循环时间
        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        self.logger.info(f"   循环完成，耗时: {cycle_duration:.2f} 秒")

        # 每10个循环生成一次报告
        if self.cycle_count % 10 == 0:
            self.logger.info("")
            self.logger.info("📄 生成阶段性报告...")
            agent_state = self.base_agent.get_agent_status()
            agent_state['recent_actions'] = [a.__dict__ for a in actions]
            agent_state['recent_alerts'] = [a.__dict__ for a in alerts]

            report_result = self.execution_controller.generate_and_send_report(agent_state)
            self.logger.info(f"   报告已生成: {report_result['report_path']}")

        # 显示当前统计
        self.logger.info("")
        self.logger.info("📈 当前统计:")
        self.logger.info(f"   总循环: {self.total_cycles}")
        self.logger.info(f"   总告警: {self.total_alerts}")
        self.logger.info(f"   总动作: {self.total_actions}")
        self.logger.info(f"   总错误: {self.total_errors}")

    def _get_summary(self) -> Dict:
        """获取运行摘要"""
        duration = (self.stop_time - self.start_time).total_seconds() if self.start_time and self.stop_time else 0

        summary = {
            "status": "completed",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "duration_seconds": duration,
            "total_cycles": self.total_cycles,
            "total_alerts": self.total_alerts,
            "total_actions": self.total_actions,
            "total_errors": self.total_errors,
            "success_rate": (self.total_actions - self.total_errors) / self.total_actions if self.total_actions > 0 else 1.0,
            "avg_cycle_time": duration / self.total_cycles if self.total_cycles > 0 else 0
        }

        return summary

    def run_single_cycle(self) -> Dict:
        """
        运行单个循环（用于测试）

        Returns:
            循环结果
        """
        self.logger.info("🔄 运行单个循环...")

        cycle_start = datetime.now()

        # 1. 感知
        alerts = self.base_agent.monitor()

        # 2. 决策
        actions = self.base_agent.decide(alerts)

        # 3. 执行
        results = []
        for action in actions:
            result = self.execution_controller.execute_action(action.__dict__)
            results.append(result)

        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        return {
            "alerts_count": len(alerts),
            "actions_count": len(actions),
            "results": results,
            "cycle_time": cycle_duration
        }


def demo_autonomous_agent():
    """演示自主 Agent"""
    import sys
    from pathlib import Path

    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from config import DATA_DIR

    # 查找数据文件
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if not data_files:
        print("❌ 未找到数据文件")
        return

    print("🤖 OpenClaw 自主 Agent 演示")
    print("=" * 60)
    print()

    # 创建自主 Agent
    agent = AutonomousAgent(
        data_path=str(data_files[0]),
        check_interval=5,  # 5秒检查一次（演示用）
        max_continuous_running=60,  # 最多运行60秒
        config={'simulation_mode': True}
    )

    # 运行单个循环（演示）
    print("运行单个循环...")
    result = agent.run_single_cycle()

    print()
    print("✅ 循环完成")
    print(f"   告警数: {result['alerts_count']}")
    print(f"   动作数: {result['actions_count']}")
    print(f"   耗时: {result['cycle_time']:.2f} 秒")
    print()

    # 显示结果
    if result['results']:
        print("执行结果:")
        for r in result['results']:
            print(f"   - {r.get('message', 'N/A')}")

    print()
    print("💡 提示: 运行完整自主循环请使用:")
    print("   agent.start(max_cycles=10)")


if __name__ == "__main__":
    demo_autonomous_agent()
