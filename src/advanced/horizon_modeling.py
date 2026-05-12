#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Horizon分别建模模块
针对不同预测时间范围（短期/中期/长期）分别建模
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class HorizonModeler:
    """Horizon分别建模器"""

    def __init__(self, horizon_config=None):
        """
        Args:
            horizon_config: Horizon配置
                {
                    'short': {'days': 7, 'name': '短期预测'},
                    'medium': {'days': 30, 'name': '中期预测'},
                    'long': {'days': 90, 'name': '长期预测'}
                }
        """
        if horizon_config is None:
            # 默认配置
            self.horizon_config = {
                'short': {'days': 7, 'name': '短期预测 (1-7天)'},
                'medium': {'days': 30, 'name': '中期预测 (8-30天)'},
                'long': {'days': 90, 'name': '长期预测 (31-90天)'}
            }
        else:
            self.horizon_config = horizon_config

        self.models = {}
        self.feature_sets = {}
        self.trained = False

    def _prepare_horizon_features(self, X, horizon_type):
        """
        为特定horizon准备特征

        Args:
            X: 原始特征
            horizon_type: horizon类型 ('short', 'medium', 'long')

        Returns:
            DataFrame: 处理后的特征
        """
        # 复制特征
        X_horizon = X.copy()

        # 根据horizon类型添加特定特征
        if horizon_type == 'short':
            # 短期：高频特征，更关注最近的变化
            if '水温 (°C)' in X_horizon.columns:
                X_horizon['水温_lag1'] = X_horizon['水温 (°C)'].shift(1)
                X_horizon['水温_change'] = X_horizon['水温 (°C)'].diff()

            if '溶解氧 (mg/L)' in X_horizon.columns:
                X_horizon['溶解氧_lag1'] = X_horizon['溶解氧 (mg/L)'].shift(1)
                X_horizon['溶解氧_change'] = X_horizon['溶解氧 (mg/L)'].diff()

        elif horizon_type == 'medium':
            # 中期：趋势特征，关注周期性变化
            if '水温 (°C)' in X_horizon.columns:
                X_horizon['水温_rolling7_mean'] = X_horizon['水温 (°C)'].rolling(window=7).mean()
                X_horizon['水温_rolling7_std'] = X_horizon['水温 (°C)'].rolling(window=7).std()

            if '投喂量 (kg)' in X_horizon.columns:
                X_horizon['投喂量_rolling7_sum'] = X_horizon['投喂量 (kg)'].rolling(window=7).sum()

        elif horizon_type == 'long':
            # 长期：季节性特征，关注长期趋势
            if '水温 (°C)' in X_horizon.columns:
                X_horizon['水温_rolling30_mean'] = X_horizon['水温 (°C)'].rolling(window=30).mean()
                X_horizon['水温_rolling30_std'] = X_horizon['水温 (°C)'].rolling(window=30).std()

            if '日期' in X_horizon.columns:
                X_horizon['月份'] = pd.to_datetime(X_horizon['日期']).dt.month
                X_horizon['季度'] = pd.to_datetime(X_horizon['日期']).dt.quarter

        # 删除NaN值
        X_horizon = X_horizon.bfill().ffill()

        return X_horizon

    def _create_model_for_horizon(self, horizon_type):
        """
        为特定horizon创建模型

        Args:
            horizon_type: horizon类型

        Returns:
            model: 模型对象
        """
        if horizon_type == 'short':
            # 短期：更复杂的模型，捕捉快速变化
            return RandomForestRegressor(
                n_estimators=150,
                max_depth=15,
                min_samples_split=3,
                random_state=42
            )

        elif horizon_type == 'medium':
            # 中期：平衡复杂度
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )

        elif horizon_type == 'long':
            # 长期：更简单的模型，避免过拟合
            return Ridge(alpha=10.0)
        else:
            return RandomForestRegressor(n_estimators=100, random_state=42)

    def fit(self, X, y, verbose=True):
        """
        训练所有horizon的模型

        Args:
            X: 特征数据（包含'日期'列）
            y: 目标变量
            verbose: 是否显示详细信息
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Horizon分别建模训练")
            print(f"{'='*70}")

        # 确保有日期列
        if '日期' not in X.columns:
            raise ValueError("特征数据必须包含'日期'列")

        X_with_date = X.copy()
        X_with_date['日期'] = pd.to_datetime(X_with_date['日期'])
        X_with_date = X_with_date.sort_values('日期')

        for horizon_name, config in self.horizon_config.items():
            if verbose:
                print(f"\n训练 {config['name']}...")

            # 准备horizon特征
            X_horizon = self._prepare_horizon_features(X_with_date, horizon_name)

            # 移除非数值列
            feature_cols = [col for col in X_horizon.columns
                          if col not in ['日期'] and X_horizon[col].dtype in ['float64', 'int64', 'float32', 'int32']]

            self.feature_sets[horizon_name] = feature_cols

            X_features = X_horizon[feature_cols]

            # 确保没有NaN值
            X_features = X_features.fillna(0)

            # 创建并训练模型
            model = self._create_model_for_horizon(horizon_name)
            model.fit(X_features, y)

            self.models[horizon_name] = model

            if verbose:
                train_pred = model.predict(X_features)
                train_r2 = r2_score(y, train_pred)
                print(f"  训练集 R² = {train_r2:.4f}")
                print(f"  特征数量 = {len(feature_cols)}")

        self.trained = True

        if verbose:
            print(f"\n{'='*70}")
            print(f"训练完成！共 {len(self.models)} 个Horizon模型")
            print(f"{'='*70}")

        return self

    def predict(self, X, horizon_type='auto'):
        """
        预测

        Args:
            X: 特征数据
            horizon_type: Horizon类型 ('short', 'medium', 'long', 'auto')
                'auto' 表示自动选择最合适的horizon

        Returns:
            array: 预测结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        X_with_date = X.copy()

        if '日期' in X_with_date.columns:
            X_with_date['日期'] = pd.to_datetime(X_with_date['日期'])

        # 如果是auto，根据当前日期选择horizon
        if horizon_type == 'auto':
            # 简单策略：默认使用medium
            horizon_type = 'medium'

        # 准备特征
        X_horizon = self._prepare_horizon_features(X_with_date, horizon_type)
        feature_cols = self.feature_sets[horizon_type]
        X_features = X_horizon[feature_cols]

        # 确保没有NaN值
        X_features = X_features.fillna(0)

        # 预测
        model = self.models[horizon_type]
        predictions = model.predict(X_features)

        return predictions

    def predict_all_horizons(self, X):
        """
        使用所有horizon进行预测

        Args:
            X: 特征数据

        Returns:
            DataFrame: 包含所有horizon的预测结果
        """
        results = pd.DataFrame(index=X.index)

        for horizon_name, config in self.horizon_config.items():
            pred = self.predict(X, horizon_type=horizon_name)
            results[f'{horizon_name}_pred'] = pred

        return results

    def evaluate(self, X_test, y_test, verbose=True):
        """
        评估所有horizon模型

        Args:
            X_test: 测试特征
            y_test: 测试目标
            verbose: 是否显示详细信息

        Returns:
            dict: 评估结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        results = {}

        if verbose:
            print(f"\n{'='*70}")
            print(f"Horizon模型评估")
            print(f"{'='*70}")

        for horizon_name, config in self.horizon_config.items():
            y_pred = self.predict(X_test, horizon_type=horizon_name)

            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            results[horizon_name] = {
                'r2': r2,
                'mae': mae,
                'rmse': rmse,
                'config': config
            }

            if verbose:
                print(f"\n{config['name']}:")
                print(f"  R² = {r2:.4f}")
                print(f"  MAE = {mae:.2f} kg")
                print(f"  RMSE = {rmse:.2f} kg")

        if verbose:
            # 找出最佳horizon
            best_horizon = max(results.items(), key=lambda x: x[1]['r2'])
            print(f"\n{'='*70}")
            print(f"最佳Horizon: {best_horizon[1]['config']['name']}")
            print(f"R² = {best_horizon[1]['r2']:.4f}")
            print(f"{'='*70}")

        return results

    def get_best_horizon(self, X_test, y_test):
        """
        找出最佳horizon

        Args:
            X_test: 测试特征
            y_test: 测试目标

        Returns:
            tuple: (horizon_name, performance_metrics)
        """
        results = self.evaluate(X_test, y_test, verbose=False)

        best_horizon = max(results.items(), key=lambda x: x[1]['r2'])

        return best_horizon


def create_horizon_modeler(short_days=7, medium_days=30, long_days=90):
    """
    创建Horizon建模器的便捷函数

    Args:
        short_days: 短期天数
        medium_days: 中期天数
        long_days: 长期天数

    Returns:
        HorizonModeler: Horizon建模器对象
    """
    config = {
        'short': {'days': short_days, 'name': f'短期预测 (1-{short_days}天)'},
        'medium': {'days': medium_days, 'name': f'中期预测 ({short_days+1}-{medium_days}天)'},
        'long': {'days': long_days, 'name': f'长期预测 ({medium_days+1}-{long_days}天)'}
    }

    return HorizonModeler(horizon_config=config)
