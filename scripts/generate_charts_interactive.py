#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式图表生成脚本
可选择生成单个图表或所有图表
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import os
import platform
import subprocess

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")
import warnings
warnings.filterwarnings('ignore')

# 路径配置
base_dir = Path(__file__).parent.parent
data_dir = base_dir / 'data'
output_dir = base_dir / 'reports' / 'figures_interactive'
output_dir.mkdir(parents=True, exist_ok=True)

# 加载数据
data_files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.csv'))
if not data_files:
    print(f"错误：在 {data_dir} 目录下未找到数据文件")
    exit(1)

data_path = data_files[0]
df = pd.read_excel(data_path, engine='openpyxl') if data_path.suffix == '.xlsx' else pd.read_csv(data_path)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

def open_image(filepath):
    """打开图片文件"""
    try:
        if platform.system() == 'Windows':
            os.startfile(str(filepath))
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', str(filepath)])
        else:
            subprocess.Popen(['xdg-open', str(filepath)])
        return True
    except:
        return False

def plot_fcr():
    """FCR 趋势图"""
    if 'FCR' not in df.columns:
        print("  ⚠️ 数据中没有 FCR 列")
        return False

    print("  正在生成 FCR 趋势图...")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['FCR'], marker='o', linewidth=2, markersize=6)
    ax.axhline(y=1.5, color='green', linestyle='--', linewidth=2, label='优秀水平 (FCR<1.5)')
    ax.axhline(y=2.0, color='orange', linestyle='--', linewidth=2, label='警戒水平 (FCR>2.0)')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('FCR', fontsize=12)
    ax.set_title('FCR (饲料转化率) 趋势分析', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'fcr_trend.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 已保存：fcr_trend.png")
    open_image(filepath)
    return True

def plot_sgr():
    """SGR 趋势图"""
    if 'SGR' not in df.columns:
        print("  ⚠️ 数据中没有 SGR 列")
        return False

    print("  正在生成 SGR 趋势图...")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['SGR'], marker='s', linewidth=2, markersize=6, color='green')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('SGR (%/天)', fontsize=12)
    ax.set_title('SGR (特定生长率) 趋势分析', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'sgr_trend.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 已保存：sgr_trend.png")
    open_image(filepath)
    return True

def plot_environmental():
    """环境参数图"""
    print("  正在生成环境参数图...")

    env_cols = []
    for col in df.columns:
        if any(keyword in str(col).lower() for keyword in ['水温', '盐度', 'ph', '溶解氧', '氧']):
            if df[col].dtype in ['float64', 'int64']:
                env_cols.append(col)

    if len(env_cols) < 2:
        print("  ⚠️ 环境参数数据不足")
        return False

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, col in enumerate(env_cols[:4]):
        ax = axes[i]
        ax.plot(df.index, df[col], marker='o', linewidth=2)
        ax.set_title(str(col), fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    filepath = output_dir / 'environmental_params.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 已保存：environmental_params.png")
    open_image(filepath)
    return True

def plot_correlation():
    """相关性热力图"""
    print("  正在生成相关性热力图...")

    if len(numeric_cols) < 2:
        print("  ⚠️ 数值列不足")
        return False

    fig, ax = plt.subplots(figsize=(12, 10))
    corr_matrix = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                square=True, linewidths=0.5, ax=ax, cbar_kws={'shrink': 0.8})
    ax.set_title('变量相关性热力图', fontsize=16, fontweight='bold')
    plt.tight_layout()

    filepath = output_dir / 'correlation_heatmap.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 已保存：correlation_heatmap.png")
    open_image(filepath)
    return True

def plot_histograms():
    """分布直方图"""
    print("  正在生成分布直方图...")

    plot_cols = numeric_cols[:4]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    colors = ['skyblue', 'lightgreen', 'lightcoral', 'plum']

    for i, (col, color) in enumerate(zip(plot_cols, colors)):
        ax = axes[i]
        ax.hist(df[col].dropna(), bins=15, color=color, edgecolor='black', alpha=0.7)
        ax.axvline(df[col].mean(), color='red', linestyle='--', linewidth=2,
                  label=f'均值: {df[col].mean():.2f}')
        ax.set_xlabel(str(col), fontsize=12)
        ax.set_ylabel('频数', fontsize=12)
        ax.set_title(f'{col} 分布', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    filepath = output_dir / 'histograms.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✅ 已保存：histograms.png")
    open_image(filepath)
    return True

# 菜单
print("=" * 70)
print("图表生成菜单")
print("=" * 70)
print("1. FCR 趋势图")
print("2. SGR 趋势图")
print("3. 环境参数图")
print("4. 相关性热力图")
print("5. 分布直方图")
print("6. 生成所有图表")
print("0. 退出")
print("=" * 70)

choice = input("\n请选择要生成的图表 (0-6): ").strip()

if choice == '1':
    plot_fcr()
elif choice == '2':
    plot_sgr()
elif choice == '3':
    plot_environmental()
elif choice == '4':
    plot_correlation()
elif choice == '5':
    plot_histograms()
elif choice == '6':
    print("\n生成所有图表...")
    plot_fcr()
    plot_sgr()
    plot_environmental()
    plot_correlation()
    plot_histograms()
    print("\n✅ 所有图表生成完成！")
    print(f"保存位置：{output_dir}")
elif choice == '0':
    print("退出")
else:
    print("无效选择")
