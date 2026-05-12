#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间序列交叉验证模块
提供适合时间序列的验证策略，避免数据泄露
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class TemporalValidator:
    """时间序列验证器"""

    def __init__(self, method='time_series_split', n_splits=5, test_size=1):
        """
        Args:
            method: 验证方法
                - 'time_series_split': sklearn的TimeSeriesSplit
                - 'walk_forward': 滚动前向验证
                - 'expanding_window': 扩展窗口验证
            n_splits: 分割数量
            test_size: 测试集大小（仅用于walk_forward）
        """
        self.method = method
        self.n_splits = n_splits
        self.test_size = test_size
        self.results = []

    def split(self, X, y=None):
        """
        生成训练/测试分割索引

        Args:
            X: 特征数据
            y: 目标变量（可选）

        Yields:
            (train_idx, test_idx): 训练集和测试集索引
        """
        n_samples = len(X)

        if self.method == 'time_series_split':
            # 使用sklearn的TimeSeriesSplit
            tscv = TimeSeriesSplit(n_splits=self.n_splits)
            for train_idx, test_idx in tscv.split(X):
                yield train_idx, test_idx

        elif self.method == 'walk_forward':
            # 滚动前向验证
            # 使用固定大小的训练窗口和测试窗口
            min_train_size = n_samples // (self.n_splits + 1)

            for i in range(self.n_splits):
                train_start = 0
                train_end = min_train_size + i * self.test_size
                test_start = train_end
                test_end = min(test_start + self.test_size, n_samples)

                if test_end >= n_samples:
                    break

                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)

                yield train_idx, test_idx

        elif self.method == 'expanding_window':
            # 扩展窗口验证
            # 训练集逐步扩大，测试集大小固定
            min_train_size = n_samples // (self.n_splits + 1)

            for i in range(self.n_splits):
                train_start = 0
                train_end = min_train_size + i * self.test_size
                test_start = train_end
                test_end = min(test_start + self.test_size, n_samples)

                if test_end >= n_samples:
                    break

                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)

                yield train_idx, test_idx

        else:
            raise ValueError(f"Unknown method: {self.method}")

    def validate(self, model, X, y, verbose=True):
        """
        执行时间序列交叉验证

        Args:
            model: 模型对象（需实现fit和predict）
            X: 特征数据
            y: 目标变量
            verbose: 是否打印详细信息

        Returns:
            dict: 验证结果统计
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"时间序列交叉验证 ({self.method})")
            print(f"{'='*70}")
            print(f"数据量: {len(X)} 样本")
            print(f"分割数: {self.n_splits}")
            print(f"方法: {self.method}")

        # 存储每折的结果
        fold_results = []

        for fold_idx, (train_idx, test_idx) in enumerate(self.split(X, y), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # 训练模型
            model.fit(X_train, y_train)

            # 预测
            y_pred = model.predict(X_test)

            # 计算指标
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            fold_results.append({
                'fold': fold_idx,
                'train_size': len(train_idx),
                'test_size': len(test_idx),
                'r2': r2,
                'mae': mae,
                'rmse': rmse
            })

            if verbose:
                print(f"\n折 {fold_idx}:")
                print(f"  训练集: {len(train_idx)} 样本 (索引 {train_idx[0]}-{train_idx[-1]})")
                print(f"  测试集: {len(test_idx)} 样本 (索引 {test_idx[0]}-{test_idx[-1]})")
                print(f"  R² = {r2:.4f}")
                print(f"  MAE = {mae:.2f} kg")
                print(f"  RMSE = {rmse:.2f} kg")

        # 汇总统计
        r2_scores = [f['r2'] for f in fold_results]
        mae_scores = [f['mae'] for f in fold_results]
        rmse_scores = [f['rmse'] for f in fold_results]

        summary = {
            'method': self.method,
            'n_splits': len(fold_results),
            'r2_mean': np.mean(r2_scores),
            'r2_std': np.std(r2_scores),
            'mae_mean': np.mean(mae_scores),
            'mae_std': np.std(mae_scores),
            'rmse_mean': np.mean(rmse_scores),
            'rmse_std': np.std(rmse_scores),
            'fold_results': fold_results
        }

        if verbose:
            print(f"\n{'='*70}")
            print(f"汇总统计")
            print(f"{'='*70}")
            print(f"R² 得分: {summary['r2_mean']:.4f} ± {summary['r2_std']:.4f}")
            print(f"MAE: {summary['mae_mean']:.2f} ± {summary['mae_std']:.2f} kg")
            print(f"RMSE: {summary['rmse_mean']:.2f} ± {summary['rmse_std']:.2f} kg")
            print(f"{'='*70}")

        self.results = summary
        return summary

    def get_fold_predictions(self, model, X, y):
        """
        获取每折的预测结果

        Args:
            model: 模型对象
            X: 特征数据
            y: 目标变量

        Returns:
            DataFrame: 包含每折的预测结果
        """
        predictions = []

        for fold_idx, (train_idx, test_idx) in enumerate(self.split(X, y), 1):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            fold_pred = pd.DataFrame({
                'fold': fold_idx,
                'actual': y_test.values,
                'predicted': y_pred,
                'residual': y_test.values - y_pred
            })

            predictions.append(fold_pred)

        return pd.concat(predictions, ignore_index=True)


def compare_validation_methods(model, X, y, n_splits=5):
    """
    比较不同验证方法的结果

    Args:
        model: 模型对象
        X: 特征数据
        y: 目标变量
        n_splits: 分割数量

    Returns:
        DataFrame: 各方法的结果比较
    """
    methods = ['time_series_split', 'walk_forward', 'expanding_window']
    results = []

    print(f"\n{'='*70}")
    print(f"时间序列验证方法对比")
    print(f"{'='*70}")

    for method in methods:
        print(f"\n测试方法: {method}")

        validator = TemporalValidator(method=method, n_splits=n_splits)
        summary = validator.validate(model, X, y, verbose=False)

        results.append({
            '方法': method,
            'R²均值': f"{summary['r2_mean']:.4f}",
            'R²标准差': f"{summary['r2_std']:.4f}",
            'MAE均值': f"{summary['mae_mean']:.2f}",
            'RMSE均值': f"{summary['rmse_mean']:.2f}"
        })

        print(f"  R² = {summary['r2_mean']:.4f} ± {summary['r2_std']:.4f}")
        print(f"  MAE = {summary['mae_mean']:.2f} ± {summary['mae_std']:.2f} kg")

    results_df = pd.DataFrame(results)

    print(f"\n{'='*70}")
    print(f"对比结果")
    print(f"{'='*70}")
    print(results_df.to_string(index=False))
    print(f"{'='*70}")

    return results_df


# 便捷函数
def temporal_cross_validation(model, X, y, n_splits=5, method='time_series_split'):
    """
    时间序列交叉验证的便捷函数

    Args:
        model: 模型对象
        X: 特征数据
        y: 目标变量
        n_splits: 分割数量
        method: 验证方法

    Returns:
        dict: 验证结果
    """
    validator = TemporalValidator(method=method, n_splits=n_splits)
    return validator.validate(model, X, y, verbose=True)
