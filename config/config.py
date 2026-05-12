#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目配置文件
跨平台路径和设置配置
"""

import platform
from pathlib import Path

# 项目根目录（config/config.py 的上一级是项目根目录）
PROJECT_ROOT = Path(__file__).parent.parent

# 目录配置
DATA_DIR = PROJECT_ROOT / 'data'
REPORTS_DIR = PROJECT_ROOT / 'reports'
FIGURES_DIR = REPORTS_DIR / 'figures'

# 创建必要的目录
for dir_path in [DATA_DIR, REPORTS_DIR, FIGURES_DIR]:
    dir_path.mkdir(exist_ok=True)

# 字体配置（跨平台）
def get_chinese_font_config():
    """获取中文字体配置"""
    system = platform.system()

    if system == 'Windows':
        return {
            'font_path': 'C:\\Windows\\Fonts\\msyh.ttc',
            'font_names': ['Microsoft YaHei', 'SimHei'],
            'fallback': 'DejaVu Sans'
        }
    elif system == 'Darwin':  # macOS
        return {
            'font_path': '/System/Library/Fonts/PingFang.ttc',
            'font_names': ['PingFang SC', 'Heiti TC'],
            'fallback': 'DejaVu Sans'
        }
    else:  # Linux
        return {
            'font_path': '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
            'font_names': ['WenQuanYi Micro Hei', 'SimHei'],
            'fallback': 'DejaVu Sans'
        }

# 分析参数配置
ANALYSIS_CONFIG = {
    'fcr_threshold': 1.5,          # FCR 优秀水平
    'sgr_threshold': 3.0,          # SGR 优秀水平 (%/天)
    'dissolved_oxygen_min': 5.0,   # 溶解氧最低值 (mg/L)
    'ph_change_threshold': 0.3,    # pH 变化阈值
    'temp_min': 24.0,              # 水温最低值 (°C)
    'temp_max': 32.0,              # 水温最高值 (°C)
    'lag_days': 3,                 # 滞后天数
}

# 机器学习配置
ML_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'n_estimators': 100,
    'max_depth': 10,
}

# 可视化配置
VIZ_CONFIG = {
    'dpi': 300,
    'figure_format': 'png',
    'color_palette': 'husl',
}

# 报告配置
REPORT_CONFIG = {
    'author': 'SmartShrimp contributors',
    'version': '2.0',
    'language': 'zh-CN',
}
