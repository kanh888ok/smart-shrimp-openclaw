#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path

print("生成对虾养殖示例数据...")

# 设置随机种子
np.random.seed(42)

# 生成30天的数据
dates = pd.date_range(start='2026-02-15', periods=30, freq='D')
n = len(dates)

data = {
    '日期': dates,
    '水温 (°C)': np.random.normal(28, 2, n).clip(24, 32),
    '盐度': np.random.normal(25, 1.5, n).clip(20, 30),
    'pH 值': np.random.normal(8.0, 0.2, n).clip(7.5, 8.5),
    '溶解氧': np.random.normal(6.5, 0.8, n).clip(5.0, 8.0),
    '投喂量': np.linspace(50, 150, n) + np.random.normal(0, 8, n),
    '虾体重': np.linspace(5, 25, n) + np.random.normal(0, 1.5, n),
    '存活率': np.linspace(98, 92, n) + np.random.normal(0, 0.8, n),
    '摄食率': np.random.normal(85, 5, n).clip(70, 95),
    '成本': np.linspace(1000, 3000, n) + np.random.normal(0, 150, n),
    '预计产量': np.linspace(500, 1500, n) + np.random.normal(0, 80, n),
}

df = pd.DataFrame(data)

# 重命名列以匹配预期的格式
df = df.rename(columns={
    '盐度': '盐度 (ppt)',
    '溶解氧': '溶解氧 (mg/L)',
    '投喂量': '投喂量 (kg)',
    '虾体重': '虾体重 (g)',
    '存活率': '存活率 (%)',
    '摄食率': '摄食率 (%)',
    '成本': '成本 (元)',
    '预计产量': '预计产量 (kg)'
})

# 保存
data_dir = Path(__file__).parent / 'data'
data_dir.mkdir(exist_ok=True)

output_path = data_dir / 'shrimp_farming_sample.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"成功生成数据：{output_path}")
print(f"行数：{len(df)}, 列数：{len(df.columns)}")
print("\n列名：")
for col in df.columns:
    print(f"  - {col}")
