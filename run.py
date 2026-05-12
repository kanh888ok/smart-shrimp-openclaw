#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智虾系统 - 主入口
统一入口，整合所有功能
"""

import os
import sys
from pathlib import Path
import time

# 加载环境变量
from dotenv import load_dotenv
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def print_header():
    """打印标题"""
    print("\n" + "=" * 70)
    print(" " * 15 + "🦞 智虾系统")
    print(" " * 12 + "SmartShrimp Team")
    print("=" * 70)

def print_menu():
    """打印主菜单"""
    print("\n" + "=" * 70)
    print(" " * 15 + "智虾系统 - 主菜单")
    print(" " * 12 + "SmartShrimp Team")
    print("=" * 70)

    print("\n【核心功能 - 评委演示重点】\n")
    print("  1. 📊 完整分析演示（推荐）")
    print("     → 自动执行：数据加载→分析→预测→报告")
    print("     → 适用于：首次演示、完整功能展示\n")

    print("  2. 🌐 启动 Web 界面")
    print("     → 交互式可视化演示")
    print("     → 适用于：界面展示、交互操作\n")

    print("【进阶功能 - 技术展示】\n")
    print("  3. 🤖 模型评估与对比")
    print("     → 交叉验证 + 多模型性能对比\n")

    print("  4. 🧠 高级机器学习")
    print("     → 深度学习(LSTM/GRU/Transformer)")
    print("     → 时序模型(Prophet/ARIMA)")
    print("     → 模型融合、超参数优化、SHAP解释\n")

    print("【辅助功能】\n")
    print("  5. 📄 生成报告")
    print("     → Word/HTML/文档报告\n")

    print("  6. ℹ️  系统信息")
    print("     → 查看数据文件、模型状态、生成记录\n")

    print("  0. 退出")
    print("-" * 70)

def check_data():
    """检查数据文件是否存在"""
    from config import DATA_DIR
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    return len(data_files) > 0

def run_full_analysis():
    """运行完整分析"""
    print("\n" + "=" * 70)
    print("【完整分析】开始执行...")
    print("=" * 70)

    try:
        from src.professional_analyzer import main as pro_main
        pro_main()
        print("\n✅ 完整分析完成！")
        print(f"   报告位置：reports/analysis_report_pro.docx")
    except Exception as e:
        print(f"\n❌ 分析失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def generate_charts():
    """生成图表"""
    print("\n" + "=" * 70)
    print("【图表生成】")
    print("=" * 70)

    print("\n选择图表生成方式：")
    print("  1. 批量生成所有图表（不自动打开）")
    print("  2. 逐个生成并打开（Windows）")

    choice = input("\n请选择 (1-2): ").strip()

    if choice == '1':
        try:
            import scripts.generate_charts_final as gen
            print("\n正在生成图表...")
            gen.main() if hasattr(gen, 'main') else None
            print("\n✅ 图表已保存到：reports/figures_final/")
        except Exception as e:
            print(f"\n❌ 生成失败：{e}")

    elif choice == '2':
        try:
            import subprocess
            script_path = Path(__file__).parent / 'scripts' / 'generate_charts_windows.py'
            subprocess.run([sys.executable, str(script_path)])
        except Exception as e:
            print(f"\n❌ 生成失败：{e}")

    input("\n按回车键返回主菜单...")

def generate_word_report():
    """生成Word报告"""
    print("\n" + "=" * 70)
    print("【Word报告生成】")
    print("=" * 70)

    try:
        from src.professional_analyzer import generate_report_only
        generate_report_only()
        print("\n✅ Word报告已生成：reports/analysis_report_pro.docx")
    except Exception as e:
        print(f"\n❌ 生成失败：{e}")
        print("   提示：请先运行完整分析（选项1）")

    input("\n按回车键返回主菜单...")

def model_evaluation():
    """模型评估"""
    print("\n" + "=" * 70)
    print("【模型评估】")
    print("=" * 70)

    try:
        from src.model_evaluation import run_evaluation
        run_evaluation()
        print("\n✅ 模型评估完成！")
        print(f"   报告位置：reports/model_evaluation.txt")
    except Exception as e:
        print(f"\n❌ 评估失败：{e}")

    input("\n按回车键返回主菜单...")

def generate_sample_data():
    """生成示例数据"""
    print("\n" + "=" * 70)
    print("【示例数据生成】")
    print("=" * 70)

    try:
        from scripts import generate_sample_data
        generate_sample_data.main() if hasattr(generate_sample_data, 'main') else None
        print("\n✅ 示例数据已生成：data/shrimp_farming_sample.xlsx")
    except Exception as e:
        print(f"\n❌ 生成失败：{e}")

    input("\n按回车键返回主菜单...")

def show_system_info():
    """显示系统信息"""
    from config import DATA_DIR, REPORTS_DIR

    print("\n" + "=" * 70)
    print("【系统信息】")
    print("=" * 70)

    print("\n📂 数据文件：")
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        for f in data_files:
            size = f.stat().st_size / 1024  # KB
            print(f"  ✓ {f.name} ({size:.1f} KB)")
    else:
        print("  ⚠ 未找到数据文件")

    print("\n📊 已生成的报告：")
    report_files = list(REPORTS_DIR.glob('*.docx')) + list(REPORTS_DIR.glob('*.md'))
    if report_files:
        for f in report_files:
            mtime = f.stat().st_mtime
            import datetime
            time_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            print(f"  ✓ {f.name} ({time_str})")
    else:
        print("  ⚠ 未找到报告文件")

    print("\n📈 图表文件：")
    figures_dirs = [
        REPORTS_DIR / 'figures',
        REPORTS_DIR / 'figures_final',
        REPORTS_DIR / 'figures_test'
    ]
    chart_count = 0
    for d in figures_dirs:
        if d.exists():
            charts = list(d.glob('*.png'))
            chart_count += len(charts)

    if chart_count > 0:
        print(f"  ✓ 共 {chart_count} 个图表文件")
    else:
        print("  ⚠ 未找到图表文件")

    print("\n🤖 训练好的模型：")
    model_files = list(Path(__file__).parent.glob('*.pkl')) + list(Path(__file__).parent.glob('*.joblib'))
    if model_files:
        for f in model_files:
            print(f"  ✓ {f.name}")
    else:
        print("  ⚠ 未找到训练好的模型")

    print("\n" + "=" * 70)
    input("按回车键返回主菜单...")

def model_comparison():
    """模型对比"""
    print("\n" + "=" * 70)
    print("【模型对比】")
    print("=" * 70)

    try:
        from src.model_comparison import run_comparison
        run_comparison()
    except Exception as e:
        print(f"\n❌ 对比失败：{e}")

    input("\n按回车键返回主菜单...")

def start_dashboard():
    """启动 Web Dashboard"""
    print("\n" + "=" * 70)
    print("【Web Dashboard】")
    print("=" * 70)

    try:
        import subprocess
        print("\n正在启动 Streamlit Dashboard...")
        print("提示：Dashboard 将在浏览器中打开")
        print("      按 Ctrl+C 停止服务\n")

        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except Exception as e:
        print(f"\n❌ 启动失败：{e}")
        print("   请确保已安装 streamlit: pip install streamlit")

    input("\n按回车键返回主菜单...")

def generate_html_report():
    """生成 HTML 交互式报告"""
    print("\n" + "=" * 70)
    print("【HTML 交互式报告】")
    print("=" * 70)

    try:
        from src.html_report_generator import run_html_report_generation
        run_html_report_generation()

        # 自动打开
        report_path = Path(__file__).parent / 'reports' / 'interactive_report.html'
        if report_path.exists():
            print(f"\n正在打开报告...")
            os.startfile(str(report_path))
    except Exception as e:
        print(f"\n❌ 生成失败：{e}")

    input("\n按回车键返回主菜单...")

def advanced_ml_menu():
    """高级机器学习菜单"""
    while True:
        print("\n" + "=" * 70)
        print(" " * 20 + "高级机器学习")
        print("=" * 70)

        print("\n【深度学习】\n")
        print("  1. LSTM 神经网络")
        print("  2. GRU 神经网络")
        print("  3. Transformer 模型")

        print("\n【时序模型】\n")
        print("  4. Prophet 预测")
        print("  5. ARIMA 预测")

        print("\n【模型优化】\n")
        print("  6. 模型融合")
        print("  7. 超参数优化")
        print("  8. SHAP 模型解释")

        print("\n【高级技术】\n")
        print("  9. 多模态融合")
        print(" 10. 强化学习投喂优化")
        print(" 11. 迁移学习预测")

        print("\n  0. 返回主菜单")
        print("-" * 70)

        choice = input("\n请选择功能 (0-11): ").strip()

        if choice == '1':
            run_deep_learning_lstm()
        elif choice == '2':
            run_deep_learning_gru()
        elif choice == '3':
            run_deep_learning_transformer()
        elif choice == '4':
            run_time_series_prophet()
        elif choice == '5':
            run_time_series_arima()
        elif choice == '6':
            run_model_ensemble_advanced()
        elif choice == '7':
            run_hyperparameter_optimization()
        elif choice == '8':
            run_model_explanation()
        elif choice == '9':
            run_multimodal_fusion()
        elif choice == '10':
            run_reinforcement_learning()
        elif choice == '11':
            run_transfer_learning()
        elif choice == '0':
            break
        else:
            print("\n❌ 无效选择，请重新输入")
            time.sleep(1)

def report_menu():
    """报告生成菜单"""
    while True:
        print("\n" + "=" * 70)
        print(" " * 25 + "报告生成")
        print("=" * 70)

        print("\n【报告类型】\n")
        print("  1. Word 报告")
        print("  2. HTML 交互式报告")
        print("  3. 完整技术文档")
        print("  4. 生成示例数据")

        print("\n  0. 返回主菜单")
        print("-" * 70)

        choice = input("\n请选择报告类型 (0-4): ").strip()

        if choice == '1':
            generate_word_report()
        elif choice == '2':
            generate_html_report()
        elif choice == '3':
            generate_document_report()
        elif choice == '4':
            generate_sample_data()
        elif choice == '0':
            break
        else:
            print("\n❌ 无效选择，请重新输入")
            time.sleep(1)

def run_deep_learning_lstm():
    """运行 LSTM 深度学习预测"""
    print("\n" + "=" * 70)
    print("【深度学习 - LSTM】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.deep_learning_models import run_deep_learning_prediction

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行 LSTM
        run_deep_learning_prediction(df_enhanced, 'lstm')

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_deep_learning_gru():
    """运行 GRU 深度学习预测"""
    print("\n" + "=" * 70)
    print("【深度学习 - GRU】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.deep_learning_models import run_deep_learning_prediction

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行 GRU
        run_deep_learning_prediction(df_enhanced, 'gru')

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_deep_learning_transformer():
    """运行 Transformer 深度学习预测"""
    print("\n" + "=" * 70)
    print("【深度学习 - Transformer】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.deep_learning_models import run_deep_learning_prediction

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行 Transformer
        run_deep_learning_prediction(df_enhanced, 'transformer')

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_time_series_prophet():
    """运行 Prophet 时序预测"""
    print("\n" + "=" * 70)
    print("【时序模型 - Prophet】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.time_series_models import run_time_series_prediction

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        # 运行时序预测
        run_time_series_prediction(df)

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_time_series_arima():
    """运行 ARIMA 时序预测"""
    print("\n" + "=" * 70)
    print("【时序模型 - ARIMA】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.time_series_models import run_time_series_prediction

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        # 运行时序预测
        run_time_series_prediction(df)

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_model_ensemble_advanced():
    """运行模型融合"""
    print("\n" + "=" * 70)
    print("【模型融合】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.model_ensemble import run_model_ensemble

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行模型融合
        run_model_ensemble(df_enhanced)

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_hyperparameter_optimization():
    """运行超参数优化"""
    print("\n" + "=" * 70)
    print("【超参数优化】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.hyperparameter_tuning import run_hyperparameter_tuning

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行超参数优化
        run_hyperparameter_tuning(df_enhanced)

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_model_explanation():
    """运行模型解释"""
    print("\n" + "=" * 70)
    print("【模型解释】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer, YieldPredictor
        from src.advanced.model_explainer import explain_model
        from config import REPORTS_DIR

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 训练模型
        predictor = YieldPredictor(df_enhanced)
        predictor.run_all()

        # 准备特征
        feature_cols = [col for col in df_enhanced.columns if col not in [
            '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
        ] and df_enhanced[col].dtype in ['float64', 'int64']]

        X = df_enhanced[feature_cols].fillna(df_enhanced[feature_cols].median())

        # 解释模型
        explain_model(
            predictor.model,
            X.values,
            feature_cols,
            REPORTS_DIR / 'shap_analysis'
        )

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def run_multimodal_fusion():
    """运行多模态融合"""
    print("\n" + "=" * 70)
    print("【多模态融合】")
    print("=" * 70)

    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.multi_modal_fusion import run_multimodal_fusion

        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')

        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return

        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 选择融合策略
        print("\n选择融合策略:")
        print("  1. 早期融合 (Early Fusion) - 特征级融合")
        print("  2. 晚期融合 (Late Fusion) - 决策级融合")
        print("  3. 混合融合 (Hybrid Fusion) - 深度学习融合")

        choice = input("\n请选择 (1-3, 默认1): ").strip() or '1'

        strategy_map = {'1': 'early', '2': 'late', '3': 'hybrid'}
        strategy = strategy_map.get(choice, 'early')

        # 运行多模态融合
        predictor = run_multimodal_fusion(df_enhanced, fusion_strategy=strategy)

    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def generate_document_report():
    """生成文档报告"""
    print("\n" + "=" * 70)
    print("【文档报告生成】")
    print("=" * 70)

    try:
        from src.document_report_generator import generate_document_report

        print("\n选择报告格式:")
        print("  1. Word 文档")
        print("  2. Markdown 文档")
        print("  3. HTML 文档")
        print("  4. PDF 文档")

        choice = input("\n请选择 (1-4, 默认1): ").strip() or '1'

        format_map = {'1': 'word', '2': 'markdown', '3': 'html', '4': 'pdf'}
        report_format = format_map.get(choice, 'word')

        print(f"\n正在生成{report_format.upper()}报告...")
        generate_document_report(format=report_format)

        # 如果是Word或HTML，尝试打开
        if report_format in ['word', 'html']:
            from pathlib import Path
            from config import REPORTS_DIR

            if report_format == 'word':
                report_path = REPORTS_DIR / '完整技术报告.docx'
            else:
                report_path = REPORTS_DIR / '完整技术报告.html'

            if report_path.exists():
                print(f"\n正在打开报告...")
                os.startfile(str(report_path))

    except Exception as e:
        print(f"\n❌ 生成失败：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车键返回主菜单...")

def main():
    """主函数"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # 清屏
        print_header()

        # 检查数据
        if not check_data():
            print("\n⚠️  警告：data/ 目录下没有数据文件")
            print("   建议先选择选项 8 生成示例数据\n")

        print_menu()

        choice = input("\n请选择功能 (0-6): ").strip()

        if choice == '1':
            run_full_analysis()
        elif choice == '2':
            start_dashboard()
        elif choice == '3':
            model_evaluation()
            model_comparison()
        elif choice == '4':
            advanced_ml_menu()
        elif choice == '5':
            report_menu()
        elif choice == '6':
            show_system_info()
        elif choice == '0':
            print("\n感谢使用！再见！👋\n")
            break
        else:
            print("\n❌ 无效选择，请重新输入")
            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n❌ 程序出错：{e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")

def run_reinforcement_learning():
    """运行强化学习投喂优化"""
    print("\n" + "=" * 70)
    print("【强化学习投喂优化】")
    print("=" * 70)
    
    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.reinforcement_learning import optimize_feeding_strategy
        
        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')
        
        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return
        
        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()
        
        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()
        
        # 运行强化学习优化
        print("\n使用Q-Learning优化投喂策略...")
        optimizer = optimize_feeding_strategy(df_enhanced, n_episodes=500, verbose=True)
        
        # 测试推荐
        print("\n【策略推荐测试】")
        current_conditions = {
            '水温 (°C)': 28,
            '盐度': 20,
            'pH 值': 8.0,
            '溶解氧': 6,
            '氨氮': 0.5,
            '亚硝酸盐': 0.1,
            '投喂量': 3.5,
            '虾体重 (g)': 20,
            'FCR': 1.5,
            'SGR': 3.5
        }
        
        recommendation = optimizer.recommend_feed_strategy(current_conditions)
        print(f"\n推荐策略: {recommendation['recommended_adjustment']}")
        print(f"原因: {recommendation['reason']}")
        
    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键返回主菜单...")

def run_transfer_learning():
    """运行迁移学习预测"""
    print("\n" + "=" * 70)
    print("【迁移学习预测】")
    print("=" * 70)
    
    try:
        from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
        from src.advanced.transfer_learning import (
            create_synthetic_pretrain_data,
            run_transfer_learning
        )
        
        # 加载数据
        data_files = list(Path(__file__).parent / 'data').glob('*.xlsx')
        data_files += list(Path(__file__).parent / 'data').glob('*.csv')
        
        if not data_files:
            print("\n❌ 未找到数据文件")
            input("\n按回车键返回主菜单...")
            return
        
        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()
        
        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()
        
        # 创建合成预训练数据
        print("\n创建大规模预训练数据...")
        df_pretrain = create_synthetic_pretrain_data(n_samples=500, noise=0.1)
        print(f"预训练数据: {len(df_pretrain)} 条")
        
        # 定义特征
        input_features = [
            '水温 (°C)', '盐度', 'pH 值', '溶解氧',
            '氨氮', '亚硝酸盐', '投喂量', '虾体重 (g)'
        ]
        
        # 运行迁移学习
        print("\n运行迁移学习...")
        model = run_transfer_learning(
            df_train=df_pretrain,
            df_finetune=df_enhanced,
            input_features=input_features,
            verbose=True
        )
        
        # 保存模型
        from pathlib import Path
        models_dir = Path(__file__).parent / 'models'
        models_dir.mkdir(exist_ok=True)
        
        model_path = models_dir / 'transfer_learning_model.pth'
        model.save_model(model_path)
        
        print(f"\n✅ 模型已保存到: {model_path}")
        
    except Exception as e:
        print(f"\n❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键返回主菜单...")
