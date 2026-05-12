"""
智虾系统 - 增强版演示启动器
Enhanced Demo Launcher
"""

import sys
import subprocess
import os

def print_banner():
    """打印横幅"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║                                                              ║
║           🦐 智虾系统 - 增强版演示启动器 🦐                  ║
║                                                              ║
║           Smart Shrimp Aquaculture Management System         ║
║                                                              ║
║                   SmartShrimp Team                  ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)


def show_menu():
    """显示菜单"""
    menu = """
请选择要启动的功能：

  1. 📊 ROI成本收益计算器
  2. 📺 实时监控大屏（Dashboard）
  3. 🤖 决策过程可视化
  4. 📄 生成投资分析报告
  5. 🚀 完整系统演示（全部启动）
  6. ℹ️ 系统信息
  0. 退出

"""
    choice = input("请输入选项 (0-6): ").strip()
    return choice


def launch_roi_calculator():
    """启动ROI计算器"""
    print("\n📊 启动ROI成本收益计算器...")
    print("=" * 60)

    try:
        # 导入ROI计算器
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from roi_calculator import ROICalculator

        calculator = ROICalculator()

        print("\n【高位池养殖投资分析】\n")
        report = calculator.generate_investment_report("高位池", area=10)
        print(report)

        print("\n【三种养殖模式对比】\n")
        comparison = calculator.compare_modes(area=10)
        print(comparison.to_markdown(index=False))

        print("\n【与传统方式对比】\n")
        traditional_comparison = calculator.compare_with_traditional(area=10)

        print("传统方式:")
        for key, value in traditional_comparison['传统方式'].items():
            print(f"  {key}: {value}")

        print("\n智能系统:")
        for key, value in traditional_comparison['智能系统'].items():
            print(f"  {key}: {value}")

        print("\n改进效果:")
        for key, value in traditional_comparison['改进效果'].items():
            print(f"  {key}: {value}")

        print("\n✅ ROI计算完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def launch_dashboard():
    """启动实时监控大屏"""
    print("\n📺 启动实时监控大屏...")
    print("=" * 60)
    print("正在启动Streamlit服务...")
    print("访问地址: http://localhost:8501")
    print("按 Ctrl+C 停止服务\n")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard.py",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ 监控大屏已关闭")


def launch_decision_visualizer():
    """启动决策可视化"""
    print("\n🤖 启动决策过程可视化...")
    print("=" * 60)
    print("正在启动Streamlit服务...")
    print("访问地址: http://localhost:8502")
    print("按 Ctrl+C 停止服务\n")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/decision_visualizer.py",
            "--server.port", "8502"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ 决策可视化已关闭")


def generate_report():
    """生成投资分析报告"""
    print("\n📄 生成投资分析报告...")
    print("=" * 60)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from roi_calculator import ROICalculator

        calculator = ROICalculator()

        # 生成三种模式的报告
        modes = ["土池", "高位池", "工厂化"]

        for mode in modes:
            filename = f"reports/{mode}_投资分析报告.md"
            os.makedirs("reports", exist_ok=True)

            report = calculator.generate_investment_report(mode, area=10)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)

            print(f"✅ 已生成: {filename}")

        print("\n✅ 所有报告生成完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")


def show_system_info():
    """显示系统信息"""
    info = """
╔════════════════════════════════════════════════════════════╗
║                    系统信息                                ║
╠════════════════════════════════════════════════════════════╣
║                                                              ║
║  项目名称: 智虾系统                                         ║
║  团队: SmartShrimp Team                            ║
║  版本: v2.0 (增强版)                                        ║
║                                                              ║
║  核心功能:                                                   ║
║  ✅ 8个核心技能                                             ║
║  ✅ ROI成本收益计算器（新增）                               ║
║  ✅ 实时监控大屏（新增）                                     ║
║  ✅ 决策过程可视化（新增）                                   ║
║                                                              ║
║  数据来源:                                                   ║
║  📊 Kaggle真实虾测量数据集                                  ║
║  📚 CNKI论文《我国南美白对虾养殖的经济效益分析》             ║
║  🤖 仿真养殖场景数据                                        ║
║                                                              ║
║  技术栈:                                                     ║
║  💻 Python 3.8+                                             ║
║  🤖 Streamlit (Web界面)                                     ║
║  📊 Pandas, NumPy (数据处理)                                ║
║  📈 Plotly (可视化)                                         ║
║                                                              ║
║  新增功能亮点:                                               ║
║  ⭐ 基于CNKI论文的权威成本数据                              ║
║  ⭐ 3年ROI预测模型                                          ║
║  ⭐ 与传统养殖方式对比分析                                  ║
║  ⭐ 实时监控大屏                                            ║
║  ⭐ OpenClaw决策过程可视化                                  ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝
"""
    print(info)


def launch_full_demo():
    """启动完整演示"""
    print("\n🚀 启动完整系统演示...")
    print("=" * 60)
    print("将依次启动以下功能：")
    print("  1. ROI成本收益计算器")
    print("  2. 实时监控大屏")
    print("  3. 决策过程可视化")
    print("\n按Enter继续，Ctrl+C取消...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n已取消")
        return

    # 先运行ROI计算器
    launch_roi_calculator()

    print("\n" + "=" * 60)
    input("按Enter启动监控大屏...")

    # 后台启动其他服务（这里简化处理）
    print("\n💡 提示：完整演示需要手动启动各个模块")
    print("  - 监控大屏: streamlit run dashboard.py")
    print("  - 决策可视化: streamlit run src/decision_visualizer.py")


def main():
    """主函数"""
    print_banner()

    while True:
        try:
            choice = show_menu()

            if choice == "1":
                launch_roi_calculator()
            elif choice == "2":
                launch_dashboard()
            elif choice == "3":
                launch_decision_visualizer()
            elif choice == "4":
                generate_report()
            elif choice == "5":
                launch_full_demo()
            elif choice == "6":
                show_system_info()
            elif choice == "0":
                print("\n👋 感谢使用智虾系统！")
                break
            else:
                print("\n❌ 无效选项，请重新选择")

            print("\n" + "=" * 60)
            input("按Enter返回主菜单...")

        except KeyboardInterrupt:
            print("\n\n👋 感谢使用智虾系统！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
