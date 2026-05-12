#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成可视化图表
"""

import pandas as pd
import numpy as np
import matplotlib
import os
import subprocess
import platform
import warnings
# 强制使用非交互式后端（避免PyCharm字体问题）
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置中文字体（必须在导入pyplot后）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# 设置Seaborn字体
sns.set_style("whitegrid")
sns.set_palette("husl")

# 禁用警告
import warnings
warnings.filterwarnings('ignore')

# 路径配置
base_dir = Path(__file__).parent.parent
data_dir = base_dir / 'data'
output_dir = base_dir / 'reports' / 'figures_final'
output_dir.mkdir(parents=True, exist_ok=True)

# 加载数据
data_files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.csv'))
if not data_files:
    print(f"错误：在 {data_dir} 目录下未找到数据文件")
    exit(1)

data_path = data_files[0]
print(f"使用数据文件：{data_path.name}")

df = pd.read_excel(data_path, engine='openpyxl') if data_path.suffix == '.xlsx' else pd.read_csv(data_path)
print(f"成功加载 {len(df)} 条记录")

print("\n开始生成图表...\n")

# 获取数值列（自动检测）
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# 1. 相关性热力图
if len(numeric_cols) >= 2:
    print("[1/5] 相关性热力图...")
    fig, ax = plt.subplots(figsize=(12, 10))
    corr_matrix = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
                square=True, linewidths=0.5, ax=ax, cbar_kws={'shrink': 0.8})
    ax.set_title('变量相关性热力图', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK\n")

# 2-5. 为每个数值列生成直方图
plot_count = 2
for i, col in enumerate(numeric_cols[:4]):  # 最多4个直方图
    print(f"[{plot_count}/5] {col} 分布图...")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df[col].dropna(), bins=15, color='skyblue', edgecolor='black', alpha=0.7)
    ax.axvline(df[col].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df[col].mean():.2f}')
    ax.set_xlabel(str(col), fontsize=12)
    ax.set_ylabel('频数', fontsize=12)
    ax.set_title(f'{col} 分布', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    # 安全的文件名
    safe_name = str(col).replace(' ', '_').replace('(', '').replace(')', '').replace('°', '').replace('/', '_')
    plt.savefig(output_dir / f'histogram_{safe_name}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  OK\n")
    plot_count += 1

print("=" * 70)
print(f"图表生成完成！")
print(f"保存位置：{output_dir}")
print(f"\n生成的文件：")
chart_files = list(output_dir.glob('*.png'))
for i, f in enumerate(chart_files, 1):
    print(f"{i}. {f.name}")
print("=" * 70)

print(f"\n提示：")
print(f"  - 图表保存在：{output_dir}")
print(f"  - 共生成 {len(chart_files)} 个图表")
print(f"  - 可以在文件管理器中逐个打开查看")

