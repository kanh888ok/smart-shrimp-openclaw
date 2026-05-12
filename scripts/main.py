#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 对虾比赛 - 主程序入口

功能：
1. 读取养殖数据
2. 自动分析
3. 生成可视化
4. 输出报告
5. 钉钉推送

Author: SmartShrimp contributors
Version: 1.0.0
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_analyzer import ShrimpDataAnalyzer, analyze_shrimp_data
from src.visualizer import ShrimpVisualizer, visualize_shrimp_data


def create_sample_data() -> pd.DataFrame:
    """创建示例对虾养殖数据"""

    # 生成 30 天的养殖数据
    dates = pd.date_range(start='2026-02-15', periods=30, freq='D')
    n = len(dates)

    data = {
        '日期': dates,
        '水温 (°C)': np.random.normal(28, 2, n).clip(24, 32),
        '盐度 (ppt)': np.random.normal(25, 1.5, n).clip(20, 30),
        'pH 值': np.random.normal(8.0, 0.2, n).clip(7.5, 8.5),
        '溶解氧 (mg/L)': np.random.normal(6.5, 0.8, n).clip(5.0, 8.0),
        '投喂量 (kg)': np.linspace(50, 150, n) + np.random.normal(0, 10, n),
        '虾体重 (g)': np.linspace(5, 25, n) + np.random.normal(0, 2, n),
        '存活率 (%)': np.linspace(98, 92, n) + np.random.normal(0, 1, n),
        '摄食率 (%)': np.random.normal(85, 5, n).clip(70, 95),
        '成本 (元)': np.linspace(1000, 3000, n) + np.random.normal(0, 200, n),
        '预计产量 (kg)': np.linspace(500, 1500, n) + np.random.normal(0, 100, n)
    }

    df = pd.DataFrame(data)
    return df


def main():
    """主函数"""
    print("=" * 60)
    print("🦐 OpenClaw 对虾养殖数据分析系统")
    print("=" * 60)
    print(f"Author: SmartShrimp contributors")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: 1.0.0")
    print("=" * 60)
    
    # 创建输出目录
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)
    
    # 检查是否有数据文件
    data_dir = project_root / 'data'
    data_files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.csv'))
    
    if data_files:
        # 使用现有数据文件
        data_file = data_files[0]
        print(f"\n📂 发现数据文件：{data_file.name}")
        
        analyzer = ShrimpDataAnalyzer(str(data_file))
    else:
        # 创建示例数据
        print("\n⚠️ 未找到数据文件，生成示例数据...")
        df = create_sample_data()
        
        # 保存示例数据
        sample_file = data_dir / 'shrimp_farming_sample.xlsx'
        data_dir.mkdir(exist_ok=True)
        df.to_excel(sample_file, index=False)
        print(f"✅ 示例数据已保存：{sample_file}")
        
        analyzer = ShrimpDataAnalyzer(str(sample_file))
    
    # 运行完整分析
    print("\n" + "=" * 60)
    print("🔍 开始数据分析...")
    print("=" * 60)
    
    analysis_result = analyzer.run_full_analysis(str(reports_dir))
    
    # 生成可视化
    print("\n" + "=" * 60)
    print("📊 开始生成可视化图表...")
    print("=" * 60)
    
    visualizer = ShrimpVisualizer(analyzer.df, str(reports_dir / 'figures'))
    charts_result = visualizer.generate_all_charts()
    
    # 生成最终报告
    print("\n" + "=" * 60)
    print("📝 生成最终报告...")
    print("=" * 60)
    
    from src.report_generator import generate_full_report
    report_result = generate_full_report(analyzer, visualizer, str(reports_dir))
    
    # 输出摘要
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)
    print(f"\n📊 数据概况:")
    print(f"   - 数据行数：{analysis_result['rows']}")
    print(f"   - 数据列数：{analysis_result['columns']}")
    
    print(f"\n💡 关键洞察:")
    for i, insight in enumerate(analysis_result['insights'], 1):
        print(f"   {i}. {insight}")
    
    print(f"\n📈 生成图表：{charts_result['charts_count']} 个")
    print(f"\n📄 报告路径:")
    print(f"   - 分析摘要：{analysis_result['report_path']}")
    print(f"   - 完整报告：{report_result.get('word_report', 'N/A')}")
    print(f"   - PDF 报告：{report_result.get('pdf_report', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("🎯 下一步:")
    print("   1. 查看 reports/ 目录下的报告")
    print("   2. 查看 reports/figures/ 目录下的图表")
    print("   3. 配置钉钉推送（可选）")
    print("=" * 60)
    
    return {
        'status': 'success',
        'analysis': analysis_result,
        'charts': charts_result,
        'report': report_result
    }


if __name__ == '__main__':
    result = main()
    
    # 如果是在生产环境，可以发送钉钉通知
    if result['status'] == 'success':
        print("\n✅ 系统运行成功！")
        sys.exit(0)
    else:
        print("\n❌ 系统运行失败！")
        sys.exit(1)
