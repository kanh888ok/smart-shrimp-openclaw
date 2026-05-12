#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成可视化图表（Windows 版本 - 自动弹出）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os
import subprocess

# Windows 字体配置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sns.set_style("whitegrid")
sns.set_palette("husl")

# 路径配置
base_dir = Path(__file__).parent.parent
data_dir = base_dir / 'data'
output_dir = base_dir / 'reports' / 'figures_win'
output_dir.mkdir(parents=True, exist_ok=True)

# 查找数据文件
data_files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.csv'))
if not data_files:
    print(f"错误：在 {data_dir} 目录下未找到数据文件")
    exit(1)

data_path = data_files[0]
print(f"使用数据文件：{data_path.name}")

try:
    df = pd.read_excel(data_path, engine='openpyxl') if data_path.suffix == '.xlsx' else pd.read_csv(data_path)
    print(f"成功加载 {len(df)} 条记录")
except Exception as e:
    print(f"加载数据失败：{e}")
    exit(1)

print("\n开始生成图表...\n")

# 获取数值列
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

    filepath = output_dir / 'correlation_heatmap.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{filepath.name}")

    # 自动打开
    os.startfile(str(filepath))
    print(f"  已打开图片\n")
    import time
    time.sleep(1)  # 等待一秒让图片打开

# 2. 水温分布图
col = '水温'
print("[2/5] 水温分布图...")
fig, ax = plt.subplots(figsize=(10, 6))
data_col = None
for c in df.columns:
    if '水温' in str(c):
        data_col = c
        break

if data_col:
    ax.hist(df[data_col].dropna(), bins=15, color='skyblue', edgecolor='black', alpha=0.7)
    ax.axvline(df[data_col].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df[data_col].mean():.2f}')
    ax.set_xlabel('水温 (°C)', fontsize=12)
    ax.set_ylabel('频数', fontsize=12)
    ax.set_title('水温分布直方图', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'histogram_水温.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{filepath.name}")
    os.startfile(str(filepath))
    print(f"  已打开图片\n")
    time.sleep(1)

# 3. 盐度分布图
print("[3/5] 盐度分布图...")
fig, ax = plt.subplots(figsize=(10, 6))
data_col = None
for c in df.columns:
    if '盐度' in str(c):
        data_col = c
        break

if data_col:
    ax.hist(df[data_col].dropna(), bins=15, color='lightgreen', edgecolor='black', alpha=0.7)
    ax.axvline(df[data_col].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df[data_col].mean():.2f}')
    ax.set_xlabel('盐度', fontsize=12)
    ax.set_ylabel('频数', fontsize=12)
    ax.set_title('盐度分布直方图', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'histogram_盐度.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{filepath.name}")
    os.startfile(str(filepath))
    print(f"  已打开图片\n")
    time.sleep(1)

# 4. pH值分布图
print("[4/5] pH值分布图...")
fig, ax = plt.subplots(figsize=(10, 6))
data_col = None
for c in df.columns:
    if 'pH' in str(c) or 'PH' in str(c):
        data_col = c
        break

if data_col:
    ax.hist(df[data_col].dropna(), bins=15, color='lightcoral', edgecolor='black', alpha=0.7)
    ax.axvline(df[data_col].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df[data_col].mean():.2f}')
    ax.set_xlabel('pH值', fontsize=12)
    ax.set_ylabel('频数', fontsize=12)
    ax.set_title('pH值分布直方图', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'histogram_pH值.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{filepath.name}")
    os.startfile(str(filepath))
    print(f"  已打开图片\n")
    time.sleep(1)

# 5. 溶解氧分布图
print("[5/5] 溶解氧分布图...")
fig, ax = plt.subplots(figsize=(10, 6))
data_col = None
for c in df.columns:
    if '溶解氧' in str(c) or '氧' in str(c):
        data_col = c
        break

if data_col:
    ax.hist(df[data_col].dropna(), bins=15, color='plum', edgecolor='black', alpha=0.7)
    ax.axvline(df[data_col].mean(), color='red', linestyle='--', linewidth=2, label=f'均值: {df[data_col].mean():.2f}')
    ax.set_xlabel('溶解氧', fontsize=12)
    ax.set_ylabel('频数', fontsize=12)
    ax.set_title('溶解氧分布直方图', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    filepath = output_dir / 'histogram_溶解氧.png'
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存：{filepath.name}")
    os.startfile(str(filepath))
    print(f"  已打开图片\n")

print("=" * 70)
print("所有图表生成完成！")
print(f"保存位置：{output_dir}")
print("=" * 70)
