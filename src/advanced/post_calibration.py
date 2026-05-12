#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后处理校准模块
对模型预测结果进行校准，减少系统性偏差
"""

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class PredictionCalibrator:
    """预测校准器"""

    def __init__(self, method='isotonic'):
        """
        Args:
            method: 校准方法
                - 'isotonic': 等渗回归（保序回归）
                - 'linear': 线性回归校准
                - 'quantile': 分位数映射
                - 'scaling': 简单缩放
        """
        self.method = method
        self.calibrator = None
        self.calibrated = False

        # 存储统计信息
        self.bias = None
        self.scaling_factor = None

    def fit(self, y_true, y_pred):
        """
        拟合校准器

        Args:
            y_true: 真实值
            y_pred: 预测值

        Returns:
            self
        """
        # 计算系统性偏差
        self.bias = np.mean(y_true - y_pred)

        if self.method == 'isotonic':
            # 等渗回归：单调的回归函数
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(y_pred, y_true)

        elif self.method == 'linear':
            # 线性回归校准
            self.calibrator = LinearRegression()
            self.calibrator.fit(y_pred.reshape(-1, 1), y_true)

        elif self.method == 'quantile':
            # 分位数映射：将预测分布映射到真实分布
            self.calibrator = {}
            quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]

            for q in quantiles:
                true_q = np.quantile(y_true, q)
                pred_q = np.quantile(y_pred, q)
                self.calibrator[q] = (true_q, pred_q)

        elif self.method == 'scaling':
            # 简单缩放
            self.scaling_factor = np.mean(y_true) / np.mean(y_pred)

        else:
            raise ValueError(f"Unknown method: {self.method}")

        self.calibrated = True
        return self

    def calibrate(self, y_pred):
        """
        校准预测值

        Args:
            y_pred: 原始预测值

        Returns:
            array: 校准后的预测值
        """
        if not self.calibrated:
            raise RuntimeError("校准器未训练，请先调用 fit()")

        if self.method == 'isotonic':
            return self.calibrator.predict(y_pred)

        elif self.method == 'linear':
            return self.calibrator.predict(y_pred.reshape(-1, 1))

        elif self.method == 'quantile':
            # 分位数映射
            calibrated = y_pred.copy()

            # 对每个分位数区间进行校准
            quantiles = sorted(self.calibrator.keys())
            for i, q in enumerate(quantiles):
                true_q, pred_q = self.calibrator[q]

                if i == 0:
                    # 最小值校准
                    mask = y_pred <= pred_q
                    scale = true_q / pred_q if pred_q != 0 else 1
                    calibrated[mask] = y_pred[mask] * scale
                else:
                    prev_q = quantiles[i-1]
                    prev_true, prev_pred = self.calibrator[prev_q]

                    # 区间内校准
                    mask = (y_pred > prev_pred) & (y_pred <= pred_q)
                    if mask.sum() > 0:
                        # 线性插值
                        scale_low = prev_true / prev_pred if prev_pred != 0 else 1
                        scale_high = true_q / pred_q if pred_q != 0 else 1

                        # 在区间内插值
                        normalized = (y_pred[mask] - prev_pred) / (pred_q - prev_pred)
                        calibrated[mask] = y_pred[mask] * (scale_low * (1 - normalized) + scale_high * normalized)

            # 最大值校准
            max_q = quantiles[-1]
            max_true, max_pred = self.calibrator[max_q]
            mask = y_pred > max_pred
            scale = max_true / max_pred if max_pred != 0 else 1
            calibrated[mask] = y_pred[mask] * scale

            return calibrated

        elif self.method == 'scaling':
            return y_pred * self.scaling_factor

        else:
            return y_pred

    def evaluate_calibration(self, y_true, y_pred_original, verbose=True):
        """
        评估校准效果

        Args:
            y_true: 真实值
            y_pred_original: 原始预测值
            verbose: 是否显示详细信息

        Returns:
            dict: 校准前后指标对比
        """
        y_pred_calibrated = self.calibrate(y_pred_original)

        # 原始预测指标
        orig_r2 = r2_score(y_true, y_pred_original)
        orig_mae = mean_absolute_error(y_true, y_pred_original)
        orig_rmse = np.sqrt(mean_squared_error(y_true, y_pred_original))

        # 校准后指标
        cal_r2 = r2_score(y_true, y_pred_calibrated)
        cal_mae = mean_absolute_error(y_true, y_pred_calibrated)
        cal_rmse = np.sqrt(mean_squared_error(y_true, y_pred_calibrated))

        results = {
            'original': {'r2': orig_r2, 'mae': orig_mae, 'rmse': orig_rmse},
            'calibrated': {'r2': cal_r2, 'mae': cal_mae, 'rmse': cal_rmse},
            'improvement': {
                'r2': cal_r2 - orig_r2,
                'mae': orig_mae - cal_mae,
                'rmse': orig_rmse - cal_rmse
            }
        }

        if verbose:
            print(f"\n{'='*70}")
            print(f"校准效果评估 ({self.method})")
            print(f"{'='*70}")
            print(f"\n原始预测:")
            print(f"  R² = {orig_r2:.4f}")
            print(f"  MAE = {orig_mae:.2f} kg")
            print(f"  RMSE = {orig_rmse:.2f} kg")

            print(f"\n校准后:")
            print(f"  R² = {cal_r2:.4f}")
            print(f"  MAE = {cal_mae:.2f} kg")
            print(f"  RMSE = {cal_rmse:.2f} kg")

            print(f"\n提升:")
            print(f"  R² 提升 = {results['improvement']['r2']:+.4f}")
            print(f"  MAE 降低 = {results['improvement']['mae']:+.2f} kg")
            print(f"  RMSE 降低 = {results['improvement']['rmse']:+.2f} kg")

            # 系统性偏差分析
            orig_bias = np.mean(y_true - y_pred_original)
            cal_bias = np.mean(y_true - y_pred_calibrated)

            print(f"\n系统性偏差:")
            print(f"  原始偏差 = {orig_bias:+.2f} kg")
            print(f"  校准后偏差 = {cal_bias:+.2f} kg")
            print(f"  偏差减少 = {abs(orig_bias) - abs(cal_bias):.2f} kg")
            print(f"{'='*70}")

        return results


class EnsembleCalibrator:
    """集成校准器（结合多种校准方法）"""

    def __init__(self, methods=None):
        """
        Args:
            methods: 校准方法列表
        """
        if methods is None:
            methods = ['isotonic', 'linear', 'scaling']

        self.methods = methods
        self.calibrators = {}
        self.weights = {}
        self.fitted = False

    def fit(self, y_true, y_pred, validation_data=None):
        """
        拟合所有校准器并确定权重

        Args:
            y_true: 训练集真实值
            y_pred: 训练集预测值
            validation_data: 验证集数据 (y_val_true, y_val_pred)，用于确定权重

        Returns:
            self
        """
        # 训练每个校准器
        for method in self.methods:
            calibrator = PredictionCalibrator(method=method)
            calibrator.fit(y_true, y_pred)
            self.calibrators[method] = calibrator

        # 确定权重
        if validation_data is not None:
            y_val_true, y_val_pred = validation_data

            # 在验证集上评估每个方法
            performances = {}
            for method, calibrator in self.calibrators.items():
                y_cal = calibrator.calibrate(y_val_pred)
                mae = mean_absolute_error(y_val_true, y_cal)
                performances[method] = mae

            # 权重与性能成反比
            total_inv_perf = sum(1/p for p in performances.values())
            for method, perf in performances.items():
                self.weights[method] = (1/perf) / total_inv_perf
        else:
            # 均等权重
            self.weights = {method: 1/len(self.methods) for method in self.methods}

        self.fitted = True
        return self

    def calibrate(self, y_pred):
        """
        集成校准

        Args:
            y_pred: 原始预测值

        Returns:
            array: 校准后的预测值
        """
        if not self.fitted:
            raise RuntimeError("校准器未训练，请先调用 fit()")

        # 获取每个校准器的结果
        predictions = []
        for method in self.methods:
            cal_pred = self.calibrators[method].calibrate(y_pred)
            predictions.append(cal_pred)

        # 加权平均
        weighted_pred = np.average(predictions, axis=0, weights=[self.weights[m] for m in self.methods])

        return weighted_pred


def find_best_calibration(y_train_true, y_train_pred, y_val_true, y_val_pred, verbose=True):
    """
    找出最佳校准方法

    Args:
        y_train_true: 训练集真实值
        y_train_pred: 训练集预测值
        y_val_true: 验证集真实值
        y_val_pred: 验证集预测值
        verbose: 是否显示详细信息

    Returns:
        tuple: (best_method, best_calibrator)
    """
    methods = ['isotonic', 'linear', 'scaling']
    results = []

    if verbose:
        print(f"\n{'='*70}")
        print(f"寻找最佳校准方法")
        print(f"{'='*70}")

    for method in methods:
        calibrator = PredictionCalibrator(method=method)
        calibrator.fit(y_train_true, y_train_pred)

        y_cal = calibrator.calibrate(y_val_pred)
        mae = mean_absolute_error(y_val_true, y_cal)
        r2 = r2_score(y_val_true, y_cal)

        results.append((method, mae, r2, calibrator))

        if verbose:
            print(f"\n{method}:")
            print(f"  验证集 MAE = {mae:.2f} kg")
            print(f"  验证集 R² = {r2:.4f}")

    # 找出最佳方法（最小MAE）
    best_method, best_mae, best_r2, best_calibrator = min(results, key=lambda x: x[1])

    if verbose:
        print(f"\n{'='*70}")
        print(f"最佳校准方法: {best_method}")
        print(f"验证集 MAE = {best_mae:.2f} kg")
        print(f"验证集 R² = {best_r2:.4f}")
        print(f"{'='*70}")

    return best_method, best_calibrator


# 便捷函数
def calibrate_predictions(y_train_true, y_train_pred, y_test_pred, method='auto'):
    """
    校准预测的便捷函数

    Args:
        y_train_true: 训练集真实值
        y_train_pred: 训练集预测值
        y_test_pred: 测试集预测值
        method: 校准方法 ('auto', 'isotonic', 'linear', 'scaling')

    Returns:
        array: 校准后的测试集预测值
    """
    if method == 'auto':
        # 使用等渗回归作为默认方法
        method = 'isotonic'

    calibrator = PredictionCalibrator(method=method)
    calibrator.fit(y_train_true, y_train_pred)

    return calibrator.calibrate(y_test_pred)
