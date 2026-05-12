#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件（根目录适配器）
重定向到 config/config.py
"""

import sys
from pathlib import Path

# 确保 config 目录在路径中
config_dir = Path(__file__).parent / 'config'
if str(config_dir) not in sys.path:
    sys.path.insert(0, str(config_dir))

# 导入实际的配置模块
import importlib.util
spec = importlib.util.spec_from_file_location("config_module", config_dir / "config.py")
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# 重新导出所有内容
for name in dir(config_module):
    if not name.startswith('_'):
        globals()[name] = getattr(config_module, name)

# 为了兼容性，确保所有内容都可用
__all__ = [
    'PROJECT_ROOT',
    'DATA_DIR',
    'REPORTS_DIR',
    'FIGURES_DIR',
    'get_chinese_font_config',
    'ANALYSIS_CONFIG',
    'ML_CONFIG',
    'VIZ_CONFIG',
    'REPORT_CONFIG',
]
