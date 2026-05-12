#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成4张核心分析图表
1. FCR 趋势图
2. SGR 趋势图
3. 环境压力预警图
4. 相关性热力图
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer, Visualizer
from config import DATA_DIR, REPORTS_DIR

def main():
    """生成4张核心图表"""

    print("=" * 70)
    print("生成4张核心分析图表")
    print("=" * 70)

    # 查找数据文件
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if not data_files:
        print(f"\n错误：在 {DATA_DIR} 目录下未找到数据文件")
        return

    data_path = data_files[0]
    print(f"\n使用数据文件：{data_path.name}")

    # 加载数据
    print("\n[1/6] 加载数据...")
    loader = ShrimpDataLoader(data_path)
    df = loader.load()
    print(f"  [OK] 加载 {len(df)} 条记录")

    # 特征工程
    print("\n[2/6] 特征工程...")
    fe = FeatureEngineer(df)
    df_enhanced = fe.run_all()
    print(f"  [OK] 特征工程完成")

    # 创建输出目录
    output_dir = REPORTS_DIR / 'figures_4charts'
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建可视化器
    visualizer = Visualizer(df_enhanced, str(output_dir))

    # 生成4张核心图表
    print("\n[3/6] 开始生成图表...")

    print("\n[4/6] [1/4] FCR 趋势图...")
    if visualizer.plot_fcr_trend():
        print("  [OK] 已生成")

    print("\n[5/6] [2/4] SGR 趋势图...")
    if visualizer.plot_sgr_trend():
        print("  [OK] 已生成")

    print("\n[6/6] [3/4] 环境压力预警图...")
    if visualizer.plot_environmental_stress():
        print("  [OK] 已生成")

    print("\n[+] [4/4] 相关性热力图...")
    if visualizer.plot_correlation_heatmap():
        print("  [OK] 已生成")

    print("\n" + "=" * 70)
    print("[OK] 4张核心图表生成完成！")
    print("=" * 70)
    print(f"\n保存位置：{output_dir}")
    print("\n生成的图表：")
    print("  1. fcr_trend.png - FCR 趋势分析")
    print("  2. sgr_trend.png - SGR 生长率趋势")
    print("  3. environmental_stress.png - 环境压力预警")
    print("  4. correlation_heatmap_enhanced.png - 变量相关性")
    print("=" * 70)

if __name__ == '__main__':
    main()
