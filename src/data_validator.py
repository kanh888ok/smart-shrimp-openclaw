#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证模块
检查上传的数据是否符合要求
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class DataValidator:
    """数据验证器"""

    # 必需的列
    REQUIRED_COLUMNS = [
        '日期',
        '水温 (°C)',
        '盐度 (ppt)',
        'pH 值',
        '溶解氧 (mg/L)',
        '投喂量 (kg)',
        '虾体重 (g)',
        '存活率 (%)',
        '摄食率 (%)',
        '成本 (元)',
        '预计产量 (kg)'
    ]

    # 数值范围
    VALUE_RANGES = {
        '水温 (°C)': (15, 40),
        '盐度 (ppt)': (0, 40),
        'pH 值': (6.0, 9.5),
        '溶解氧 (mg/L)': (0, 15),
        '投喂量 (kg)': (0, 500),
        '虾体重 (g)': (0, 50),
        '存活率 (%)': (0, 100),
        '摄食率 (%)': (0, 100),
        '成本 (元)': (0, 100000),
        '预计产量 (kg)': (0, 10000),
    }

    def __init__(self, df: pd.DataFrame):
        """初始化"""
        self.df = df
        self.errors = []
        self.warnings = []
        self.valid = True

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        执行所有验证

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        self._check_required_columns()
        self._check_data_types()
        self._check_value_ranges()
        self._check_missing_values()
        self._check_data_consistency()

        self.valid = len(self.errors) == 0

        return self.valid, self.errors, self.warnings

    def _check_required_columns(self):
        """检查必需的列"""
        missing_cols = set(self.REQUIRED_COLUMNS) - set(self.df.columns)

        if missing_cols:
            self.errors.append(
                f"缺少必需的列: {', '.join(missing_cols)}"
            )

        # 检查列名变体（可能的用户错误）
        for required in self.REQUIRED_COLUMNS:
            if required not in self.df.columns:
                # 尝试找到相似的列名
                similar = self._find_similar_columns(required)
                if similar:
                    self.warnings.append(
                        f"列 '{required}' 不存在，是否指的是: {', '.join(similar)}?"
                    )

    def _check_data_types(self):
        """检查数据类型"""
        numeric_cols = [
            '水温 (°C)', '盐度 (ppt)', 'pH 值', '溶解氧 (mg/L)',
            '投喂量 (kg)', '虾体重 (g)', '存活率 (%)', '摄食率 (%)',
            '成本 (元)', '预计产量 (kg)'
        ]

        for col in numeric_cols:
            if col in self.df.columns:
                if not pd.api.types.is_numeric_dtype(self.df[col]):
                    # 尝试转换
                    try:
                        pd.to_numeric(self.df[col], errors='raise')
                    except (ValueError, TypeError):
                        self.errors.append(
                            f"列 '{col}' 应为数值类型，但实际是: {self.df[col].dtype}"
                        )

    def _check_value_ranges(self):
        """检查数值范围"""
        for col, (min_val, max_val) in self.VALUE_RANGES.items():
            if col in self.df.columns:
                # 检查是否有超出范围的值
                out_of_range = self.df[
                    (self.df[col] < min_val) | (self.df[col] > max_val)
                ]

                if len(out_of_range) > 0:
                    count = len(out_of_range)
                    pct = count / len(self.df) * 100

                    if pct > 10:  # 超过10%的数据有问题
                        self.errors.append(
                            f"列 '{col}' 有 {count} ({pct:.1f}%) 个值超出合理范围 "
                            f"[{min_val}, {max_val}]"
                        )
                    else:
                        self.warnings.append(
                            f"列 '{col}' 有 {count} ({pct:.1f}%) 个值可能超出范围 "
                            f"[{min_val}, {max_val}]"
                        )

    def _check_missing_values(self):
        """检查缺失值"""
        for col in self.df.columns:
            missing_count = self.df[col].isnull().sum()
            missing_pct = missing_count / len(self.df) * 100

            if missing_pct > 50:
                self.errors.append(
                    f"列 '{col}' 缺失值过多: {missing_count} ({missing_pct:.1f}%)"
                )
            elif missing_pct > 0:
                self.warnings.append(
                    f"列 '{col}' 有 {missing_count} ({missing_pct:.1f}%) 个缺失值"
                )

    def _check_data_consistency(self):
        """检查数据一致性"""
        # 检查日期是否递增
        if '日期' in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df['日期']):
                if not self.df['日期'].is_monotonic_increasing:
                    self.warnings.append("日期列不是严格递增的")
            else:
                # 尝试转换为日期
                try:
                    pd.to_datetime(self.df['日期'])
                except (ValueError, TypeError):
                    self.errors.append("日期列格式不正确")

        # 检查存活率是否递减（通常存活率只降不升）
        if '存活率 (%)' in self.df.columns:
            if len(self.df) > 1:
                survival_rate = self.df['存活率 (%)'].dropna()
                if len(survival_rate) > 1:
                    # 允许小幅上升（可能有新增虾苗）
                    increases = (survival_rate.diff() > 5).sum()
                    if increases > len(survival_rate) * 0.2:
                        self.warnings.append(
                            f"存活率有 {increases} 次大幅上升，请确认数据是否正确"
                        )

    def _find_similar_columns(self, target: str) -> List[str]:
        """找到相似的列名"""
        similar = []
        for col in self.df.columns:
            # 简单的相似度检查
            if any(word in str(col) for word in target.split()):
                if col != target:
                    similar.append(col)
        return similar

    def get_validation_report(self) -> str:
        """获取验证报告"""
        report = []
        report.append("=" * 70)
        report.append("数据验证报告")
        report.append("=" * 70)

        if self.valid:
            report.append("\n✅ 数据验证通过！")
        else:
            report.append("\n❌ 数据验证失败！")

        if self.errors:
            report.append("\n错误（必须修复）：")
            for i, error in enumerate(self.errors, 1):
                report.append(f"  {i}. {error}")

        if self.warnings:
            report.append("\n警告（建议检查）：")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"  {i}. {warning}")

        report.append("\n" + "=" * 70)

        return "\n".join(report)


def validate_data_file(file_path) -> Tuple[bool, pd.DataFrame]:
    """
    验证数据文件

    Args:
        file_path: 数据文件路径

    Returns:
        (是否有效, 数据框)
    """
    # 读取数据
    try:
        if str(file_path).endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ 文件读取失败: {e}")
        return False, None

    # 验证数据
    validator = DataValidator(df)
    valid, errors, warnings = validator.validate()

    # 打印报告
    print(validator.get_validation_report())

    if not valid:
        print("\n请修复以上错误后重新上传！")
        return False, None

    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告，建议检查")

    return True, df


if __name__ == '__main__':
    # 测试
    from pathlib import Path
    from config import DATA_DIR

    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        print(f"验证文件: {data_files[0].name}\n")
        validate_data_file(data_files[0])
    else:
        print("未找到数据文件")
