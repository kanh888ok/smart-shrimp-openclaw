#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智虾系统 - 一键启动脚本

功能：
1. 启动自主循环
2. 启动 Web 界面
3. 查看系统状态
"""

import sys
import time
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def print_banner():
    """打印横幅"""
    print()
    print("=" * 70)
    print("🦞 智虾系统 - 智能养殖管理平台")
    print("=" * 70)
    print()
    print("SmartShrimp Team · 2026")
    print()


def start_autonomous_loop():
    """启动自主循环"""
    from src.agent.autonomous_loop import AutonomousLoop
    from config import DATA_DIR
    import glob

    print("🚀 启动自主循环...")
    print()

    # 查找数据文件
    data_files = list(glob.glob(str(DATA_DIR / '*.xlsx'))) + \
                 list(glob.glob(str(DATA_DIR / '*.csv')))

    if not data_files:
        print("❌ 未找到数据文件")
        print(f"   请在 {DATA_DIR} 目录下放置数据文件")
        return None

    print(f"✅ 找到数据文件: {data_files[0]}")
    print()

    # 创建自主循环
    loop = AutonomousLoop(
        data_path=data_files[0],
        check_interval=300,  # 5 分钟检查一次
        config={'simulation_mode': True}
    )

    # 启动循环
    print("📝 配置:")
    print(f"  - 检查间隔: {loop.check_interval} 秒 (5 分钟)")
    print(f"  - 模拟模式: {loop.config.get('simulation_mode', True)}")
    print()

    print("🔄 启动自主循环...")
    print("   系统将自动:")
    print("   1. 监控养殖状态")
    print("   2. 检测异常情况")
    print("   3. 做出管理决策")
    print("   4. 执行必要操作")
    print("   5. 记录完整日志")
    print()

    loop.start(max_cycles=None)  # 无限循环

    return loop


def start_web_dashboard():
    """启动 Web Dashboard"""
    print("🌐 启动 Web Dashboard...")
    print()

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=True
        )
    except KeyboardInterrupt:
        print("\n✅ Web Dashboard 已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def show_system_status():
    """显示系统状态"""
    from src.agent.autonomous_loop import AutonomousLoop
    from config import DATA_DIR
    import glob

    print("📊 系统状态")
    print("=" * 70)
    print()

    # 查找数据文件
    data_files = list(glob.glob(str(DATA_DIR / '*.xlsx'))) + \
                 list(glob.glob(str(DATA_DIR / '*.csv')))

    if not data_files:
        print("❌ 未找到数据文件")
        return

    # 创建循环实例（仅用于获取状态）
    loop = AutonomousLoop(data_files[0])

    # 读取最新日志
    log_path = Path("output/logs")
    if log_path.exists():
        log_files = list(log_path.glob("autonomous_loop_*.jsonl"))

        if log_files:
            import json

            latest_log = log_files[-1]

            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if lines:
                latest_entry = json.loads(lines[-1])

                print("最新循环:")
                print(f"  时间: {latest_entry.get('timestamp', 'N/A')}")
                print(f"  次数: {latest_entry.get('cycle_number', 0)}")
                print()

                context = latest_entry.get('context', {})
                print("当前状态:")
                print(f"  - 溶解氧: {context.get('do_level', 0):.2f} mg/L")
                print(f"  - pH: {context.get('ph', 0):.2f}")
                print(f"  - 水温: {context.get('temperature', 0):.1f}°C")
                print()

                alerts = latest_entry.get('alerts', [])
                print(f"异常数量: {len(alerts)}")
                if alerts:
                    for alert in alerts:
                        print(f"  - [{alert.get('severity', 'INFO')}] {alert.get('message', '')}")
                else:
                    print("  ✅ 无异常")
                print()

                decisions = latest_entry.get('decisions', [])
                print(f"决策数量: {len(decisions)}")
                if decisions:
                    for decision in decisions:
                        print(f"  - {decision.get('description', 'N/A')}")
                else:
                    print("  无需决策")
                print()

                stats = latest_entry.get('statistics', {})
                print("累计统计:")
                print(f"  - 总循环: {stats.get('total_cycles', 0)}")
                print(f"  - 总告警: {stats.get('total_alerts', 0)}")
                print(f"  - 总动作: {stats.get('total_actions', 0)}")
                print()

                return

    print("❌ 未找到日志记录")
    print("   系统可能尚未运行")


def main():
    """主函数"""
    print_banner()

    print("请选择功能:")
    print()
    print("  1. 启动自主循环 (推荐)")
    print("  2. 启动 Web Dashboard")
    print("  3. 查看系统状态")
    print("  4. 退出")
    print()

    choice = input("请输入选项 (1-4): ").strip()

    if choice == "1":
        loop = start_autonomous_loop()

        if loop:
            print()
            print("💡 提示:")
            print("  - 自主循环正在后台运行")
            print("  - 按 Ctrl+C 停止")
            print("  - 日志保存在 output/logs/")
            print()

            try:
                while loop.thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                print()
                print("🛑 正在停止...")
                loop.stop()

    elif choice == "2":
        start_web_dashboard()

    elif choice == "3":
        show_system_status()

    elif choice == "4":
        print("👋 再见！")
        return

    else:
        print("❌ 无效的选项")

    print()
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("👋 用户中断，再见！")
        sys.exit(0)
