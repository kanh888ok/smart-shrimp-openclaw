#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主循环控制器 - 实现 Agent 的完全自主运行

完整的自主循环：
定时感知 → 自动检测异常 → 自主决策 → 执行动作 → 记录日志 → 循环
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum

from .shrimp_farming_agent import ShrimpFarmingAgent

# 可选导入（需要requests）
try:
    from .device_controller import RealExecutionController
except ImportError:
    RealExecutionController = None

from .skill_manager import SkillManager, create_skill_manager


class LoopStatus(Enum):
    """循环状态"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class AutonomousLoop:
    """
    自主循环控制器

    实现完全自主的养殖管理循环
    """

    def __init__(
        self,
        data_path: str,
        check_interval: int = 300,  # 检查间隔（秒），默认 5 分钟
        config: Optional[Dict] = None
    ):
        """
        初始化自主循环

        Args:
            data_path: 数据文件路径
            check_interval: 检查间隔（秒）
            config: 配置字典
        """
        self.data_path = data_path
        self.check_interval = check_interval
        self.config = config or {}

        # 初始化组件
        self.agent = ShrimpFarmingAgent(data_path, config)
        self.executor = RealExecutionController(
            base_dir=".",
            simulation_mode=config.get('simulation_mode', True)
        )
        self.skill_manager = create_skill_manager()

        # 循环控制
        self.status = LoopStatus.STOPPED
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 统计信息
        self.total_cycles = 0
        self.total_alerts = 0
        self.total_actions = 0
        self.last_check_time: Optional[datetime] = None
        self.next_check_time: Optional[datetime] = None

        # 日志
        self.logger = logging.getLogger(__name__)
        self._setup_logger()

    def _setup_logger(self):
        """设置日志"""
        log_dir = Path("output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    log_dir / f"autonomous_loop_{datetime.now().strftime('%Y%m%d')}.log",
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )

    def start(self, max_cycles: Optional[int] = None):
        """
        启动自主循环

        Args:
            max_cycles: 最大循环次数（None 表示无限循环）
        """
        if self.status == LoopStatus.RUNNING:
            self.logger.warning("循环已在运行中")
            return

        self.status = LoopStatus.RUNNING
        self.stop_event.clear()

        self.logger.info("=" * 60)
        self.logger.info("🚀 自主循环启动")
        self.logger.info("=" * 60)
        self.logger.info(f"检查间隔: {self.check_interval} 秒")
        self.logger.info(f"最大循环: {max_cycles or '无限'}")
        self.logger.info("")

        # 启动循环线程
        self.thread = threading.Thread(
            target=self._run_loop,
            args=(max_cycles,),
            daemon=True
        )
        self.thread.start()

    def stop(self):
        """停止自主循环"""
        if self.status != LoopStatus.RUNNING:
            return

        self.logger.info("")
        self.logger.info("🛑 正在停止自主循环...")

        self.stop_event.set()
        self.status = LoopStatus.STOPPED

        if self.thread:
            self.thread.join(timeout=5)

        self.logger.info("✅ 自主循环已停止")
        self.logger.info("")

    def pause(self):
        """暂停循环"""
        if self.status == LoopStatus.RUNNING:
            self.status = LoopStatus.PAUSED
            self.logger.info("⏸️ 循环已暂停")

    def resume(self):
        """恢复循环"""
        if self.status == LoopStatus.PAUSED:
            self.status = LoopStatus.RUNNING
            self.logger.info("▶️ 循环已恢复")

    def _run_loop(self, max_cycles: Optional[int] = None):
        """运行循环（在独立线程中）"""
        cycle_count = 0

        try:
            while not self.stop_event.is_set():
                # 检查是否暂停
                if self.status == LoopStatus.PAUSED:
                    time.sleep(1)
                    continue

                # 检查最大循环次数
                if max_cycles and cycle_count >= max_cycles:
                    self.logger.info(f"达到最大循环次数: {max_cycles}")
                    break

                # 执行一个循环
                self._run_cycle()

                cycle_count += 1
                self.total_cycles = cycle_count

                # 计算下次检查时间
                self.last_check_time = datetime.now()
                self.next_check_time = self.last_check_time + timedelta(seconds=self.check_interval)

                # 等待下一次检查
                self._wait_for_next_check()

        except Exception as e:
            self.logger.error(f"循环运行出错: {e}", exc_info=True)
            self.status = LoopStatus.ERROR

    def _run_cycle(self):
        """运行一个完整的自主循环"""
        cycle_start = datetime.now()

        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(f"🔄 循环 #{self.total_cycles + 1} 开始")
        self.logger.info("=" * 60)

        # 步骤 1: 感知环境状态
        self.logger.info("🔍 步骤 1/5: 感知环境状态...")
        context = self._perceive_environment()
        self.logger.info(f"   当前状态: DO={context.get('do_level', 0):.2f}, pH={context.get('ph', 0):.2f}")

        # 步骤 2: 检测异常
        self.logger.info("")
        self.logger.info("🚨 步骤 2/5: 检测异常...")
        alerts = self._detect_anomalies(context)
        self.total_alerts += len(alerts)

        if alerts:
            self.logger.info(f"   发现 {len(alerts)} 个异常:")
            for alert in alerts:
                self.logger.info(f"   - [{alert.get('severity', 'INFO')}] {alert.get('message', '')}")
        else:
            self.logger.info("   ✅ 未发现异常")

        # 步骤 3: 自主决策
        self.logger.info("")
        self.logger.info("🧠 步骤 3/5: 自主决策...")
        decisions = self._make_decisions(context, alerts)
        self.logger.info(f"   生成 {len(decisions)} 个决策")

        # 步骤 4: 执行动作
        self.logger.info("")
        self.logger.info("⚡ 步骤 4/5: 执行动作...")

        executed_actions = 0
        for decision in decisions:
            try:
                result = self._execute_decision(decision)
                executed_actions += 1

                if result.get('success'):
                    self.logger.info(f"   ✅ {decision.get('description', 'N/A')}")
                else:
                    self.logger.warning(f"   ⚠️ {decision.get('description', 'N/A')}: {result.get('message', '')}")

            except Exception as e:
                self.logger.error(f"   ❌ 执行失败: {e}")

        self.total_actions += executed_actions

        # 步骤 5: 记录日志
        self.logger.info("")
        self.logger.info("📝 步骤 5/5: 记录日志...")
        self._log_cycle_result(context, alerts, decisions)

        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        self.logger.info("")
        self.logger.info(f"✅ 循环完成，耗时: {cycle_duration:.2f} 秒")
        self.logger.info(f"📊 统计: 总循环={self.total_cycles}, 总告警={self.total_alerts}, 总动作={self.total_actions}")

    def _perceive_environment(self) -> dict:
        """感知环境状态"""
        state = self.agent.current_state

        return {
            'do_level': state.get('DO', 0),
            'ph': state.get('pH', 0),
            'temperature': state.get('temperature', 0),
            'fcr': state.get('FCR', 0),
            'sgr': state.get('SGR', 0),
            'survival_rate': state.get('survival_rate', 0),
            'stress_level': state.get('stress_level', 0)
        }

    def _detect_anomalies(self, context: dict) -> list:
        """检测异常"""
        # 使用技能管理器检测
        result = self.skill_manager.execute_skill(
            'skill_water_monitoring',
            context
        )

        anomalies = []

        if result.triggered and result.success:
            alerts = result.data.get('alerts', [])
            for alert in alerts:
                anomalies.append({
                    'severity': alert['severity'],
                    'message': alert['message'],
                    'recommendation': alert['recommendation']
                })

        return anomalies

    def _make_decisions(self, context: dict, alerts: list) -> list:
        """自主决策"""
        decisions = []

        # 决策 1: 如果溶解氧低，启动增氧
        if context.get('do_level', 999) < 5.0:
            result = self.skill_manager.execute_skill(
                'skill_aeration_control',
                context
            )

            if result.triggered and result.success:
                command = result.data['aeration_command']
                decisions.append({
                    'action_type': 'aeration',
                    'description': f"启动增氧机 {command['duration_minutes']} 分钟",
                    'parameters': command,
                    'priority': command['priority']
                })

        # 决策 2: 如果有异常，调整投喂
        if len(alerts) > 0 or context.get('do_level', 999) < 5.0:
            result = self.skill_manager.execute_skill(
                'skill_feeding_optimization',
                {**context, 'low_do': context.get('do_level', 999) < 5.0}
            )

            if result.triggered and result.success:
                decisions.append({
                    'action_type': 'adjust_feeding',
                    'description': "调整投喂量",
                    'parameters': result.data,
                    'priority': 'medium'
                })

        return decisions

    def _execute_decision(self, decision: dict) -> dict:
        """执行决策"""
        action_type = decision['action_type']
        parameters = decision['parameters']

        # 使用执行控制器
        action = {
            'action_id': f"AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'action_type': action_type,
            'parameters': parameters
        }

        result = self.executor.execute_action(action)

        return result

    def _log_cycle_result(self, context: dict, alerts: list, decisions: list):
        """记录循环结果"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'cycle_number': self.total_cycles + 1,
            'context': context,
            'alerts': alerts,
            'decisions': decisions,
            'statistics': {
                'total_cycles': self.total_cycles + 1,
                'total_alerts': self.total_alerts,
                'total_actions': self.total_actions
            }
        }

        # 保存到文件
        log_dir = Path("output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"autonomous_loop_{datetime.now().strftime('%Y%m%d')}.jsonl"

        import json

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        # 每 10 个循环生成一次报告
        if (self.total_cycles + 1) % 10 == 0:
            self._generate_periodic_report()

    def _generate_periodic_report(self):
        """生成阶段性报告"""
        agent_state = self.agent.get_agent_status()

        report = self.executor.generate_and_send_report(agent_state)

        self.logger.info(f"   📄 阶段性报告已生成: {report['report_path']}")

    def _wait_for_next_check(self):
        """等待下一次检查"""
        if self.next_check_time:
            wait_seconds = (self.next_check_time - datetime.now()).total_seconds()

            if wait_seconds > 0:
                # 每分钟检查一次停止信号
                while wait_seconds > 0 and not self.stop_event.is_set():
                    sleep_time = min(60, wait_seconds)
                    time.sleep(sleep_time)
                    wait_seconds -= sleep_time

                    if self.status == LoopStatus.PAUSED:
                        break

    def get_status(self) -> dict:
        """获取循环状态"""
        return {
            'status': self.status.value,
            'total_cycles': self.total_cycles,
            'total_alerts': self.total_alerts,
            'total_actions': self.total_actions,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'next_check_time': self.next_check_time.isoformat() if self.next_check_time else None,
            'check_interval': self.check_interval
        }


def demo_autonomous_loop():
    """演示自主循环"""
    import sys
    from pathlib import Path

    # 添加项目路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from config import DATA_DIR
    import glob

    # 查找数据文件
    data_files = list(glob.glob(str(DATA_DIR / '*.xlsx'))) + \
                 list(glob.glob(str(DATA_DIR / '*.csv')))

    if not data_files:
        print("❌ 未找到数据文件")
        return

    print("🚀 智虾系统 - 自主循环演示")
    print("=" * 60)
    print()

    # 创建自主循环
    loop = AutonomousLoop(
        data_path=data_files[0],
        check_interval=10,  # 10 秒检查一次（演示用）
        config={'simulation_mode': True}
    )

    # 运行 3 个循环
    print("运行 3 个自主循环...")
    print()

    loop.start(max_cycles=3)

    # 等待完成
    while loop.thread.is_alive():
        time.sleep(1)

    print()
    print("=" * 60)
    print("📊 演示完成")
    print()

    status = loop.get_status()
    print(f"总循环: {status['total_cycles']}")
    print(f"总告警: {status['total_alerts']}")
    print(f"总动作: {status['total_actions']}")
    print()
    print("💡 实际使用中，循环会持续运行，自动:")
    print("  - 监控环境状态")
    print("  - 检测异常情况")
    print("  - 做出管理决策")
    print("  - 执行必要操作")
    print("  - 记录完整日志")


if __name__ == "__main__":
    demo_autonomous_loop()
