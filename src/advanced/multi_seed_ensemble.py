#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多种子集成模块
使用多个随机种子训练模型，提升预测稳定性
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# 尝试导入XGBoost和LightGBM
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False


class MultiSeedEnsemble:
    """多种子集成模型"""

    def __init__(self, base_model_type='random_forest', n_seeds=5, seeds=None):
        """
        Args:
            base_model_type: 基础模型类型
                - 'random_forest': RandomForestRegressor
                - 'xgboost': XGBRegressor
                - 'lightgbm': LGBMRegressor
                - 'gradient_boosting': GradientBoostingRegressor
                - 'ridge': Ridge
            n_seeds: 种子数量
            seeds: 自定义种子列表，如果为None则系统生成
        """
        self.base_model_type = base_model_type
        self.n_seeds = n_seeds

        if seeds is None:
            # 默认种子列表
            self.seeds = [42, 123, 456, 789, 2024][:n_seeds]
        else:
            self.seeds = seeds[:n_seeds]

        self.models = []
        self.trained = False
        self.feature_names = None

    def _create_model(self, seed):
        """创建指定类型的模型"""
        if self.base_model_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=seed
            )

        elif self.base_model_type == 'xgboost':
            if not XGB_AVAILABLE:
                raise ImportError("XGBoost未安装，请使用: pip install xgboost")
            return xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=seed,
                verbosity=0
            )

        elif self.base_model_type == 'lightgbm':
            if not LGB_AVAILABLE:
                raise ImportError("LightGBM未安装，请使用: pip install lightgbm")
            return lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=seed,
                verbosity=-1
            )

        elif self.base_model_type == 'gradient_boosting':
            return GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=seed
            )

        elif self.base_model_type == 'ridge':
            return Ridge(alpha=1.0, random_state=seed)

        else:
            raise ValueError(f"Unknown model type: {self.base_model_type}")

    def fit(self, X_train, y_train, verbose=True):
        """
        使用多个种子训练模型

        Args:
            X_train: 训练特征
            y_train: 训练目标
            verbose: 是否显示详细信息
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"多种子集成训练 ({self.base_model_type})")
            print(f"{'='*70}")
            print(f"种子数量: {self.n_seeds}")
            print(f"种子列表: {self.seeds}")
            print(f"训练样本: {len(X_train)}")
            print(f"特征数量: {len(X_train.columns)}")

        self.models = []
        self.feature_names = X_train.columns.tolist()

        # 训练每个种子对应的模型
        for i, seed in enumerate(self.seeds, 1):
            if verbose:
                print(f"\n[{i}/{self.n_seeds}] 训练模型 (seed={seed})...")

            model = self._create_model(seed)
            model.fit(X_train, y_train)
            self.models.append(model)

            if verbose:
                # 训练集评估
                train_pred = model.predict(X_train)
                train_r2 = r2_score(y_train, train_pred)
                print(f"  训练集 R² = {train_r2:.4f}")

        self.trained = True

        if verbose:
            print(f"\n{'='*70}")
            print(f"训练完成！共 {len(self.models)} 个模型")
            print(f"{'='*70}")

        return self

    def predict(self, X, method='mean'):
        """
        集成预测

        Args:
            X: 特征数据
            method: 集成方法
                - 'mean': 算术平均
                - 'median': 中位数
                - 'weighted': 加权平均（基于训练集R²）

        Returns:
            array: 预测结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        # 获取每个模型的预测
        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        predictions = np.array(predictions)

        # 集成
        if method == 'mean':
            return np.mean(predictions, axis=0)

        elif method == 'median':
            return np.median(predictions, axis=0)

        elif method == 'weighted':
            # 简单起见，使用等权重（实际可基于各模型性能计算权重）
            return np.mean(predictions, axis=0)

        else:
            raise ValueError(f"Unknown method: {method}")

    def predict_with_uncertainty(self, X):
        """
        带不确定性的预测（返回预测均值和标准差）

        Args:
            X: 特征数据

        Returns:
            tuple: (预测均值, 预测标准差)
        """
        predictions = []
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)

        predictions = np.array(predictions)

        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)

        return mean_pred, std_pred

    def evaluate(self, X_test, y_test, verbose=True):
        """
        评估集成模型

        Args:
            X_test: 测试特征
            y_test: 测试目标
            verbose: 是否显示详细信息

        Returns:
            dict: 评估结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        y_pred = self.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        results = {
            'r2': r2,
            'mae': mae,
            'rmse': rmse,
            'predictions': y_pred
        }

        if verbose:
            print(f"\n{'='*70}")
            print(f"多种子集成评估")
            print(f"{'='*70}")
            print(f"测试样本: {len(X_test)}")
            print(f"R² 得分 = {r2:.4f}")
            print(f"MAE = {mae:.2f} kg")
            print(f"RMSE = {rmse:.2f} kg")

            # 对比单模型
            print(f"\n单模型对比:")
            for i, model in enumerate(self.models):
                pred = model.predict(X_test)
                single_r2 = r2_score(y_test, pred)
                single_mae = mean_absolute_error(y_test, pred)
                print(f"  模型 {i+1} (seed={self.seeds[i]}): R²={single_r2:.4f}, MAE={single_mae:.2f} kg")

            # 集成提升
            single_r2s = [r2_score(y_test, model.predict(X_test)) for model in self.models]
            single_maes = [mean_absolute_error(y_test, model.predict(X_test)) for model in self.models]

            print(f"\n集成效果:")
            print(f"  平均 R² = {np.mean(single_r2s):.4f} → 集成 R² = {r2:.4f} (提升 {r2 - np.mean(single_r2s):.4f})")
            print(f"  平均 MAE = {np.mean(single_maes):.2f} kg → 集成 MAE = {mae:.2f} kg (降低 {np.mean(single_maes) - mae:.2f} kg)")
            print(f"{'='*70}")

        return results

    def get_feature_importance(self, method='mean'):
        """
        获取特征重要性

        Args:
            method: 'mean' 或 'median'

        Returns:
            DataFrame: 特征重要性
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        importances = []

        for model in self.models:
            if hasattr(model, 'feature_importances_'):
                importances.append(model.feature_importances_)
            else:
                # 对于没有feature_importances_的模型，返回空
                importances.append(np.zeros(len(self.feature_names)))

        importances = np.array(importances)

        if method == 'mean':
            mean_importance = np.mean(importances, axis=0)
            std_importance = np.std(importances, axis=0)
        else:
            mean_importance = np.median(importances, axis=0)
            std_importance = np.std(importances, axis=0)

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': mean_importance,
            'std': std_importance
        }).sort_values('importance', ascending=False)

        return importance_df


class HeterogeneousMultiSeedEnsemble:
    """异构多种子集成（不同模型类型 + 多种子）"""

    def __init__(self, model_types=None, n_seeds=3):
        """
        Args:
            model_types: 模型类型列表，如 ['random_forest', 'xgboost']
            n_seeds: 每种模型的种子数量
        """
        if model_types is None:
            model_types = ['random_forest', 'gradient_boosting', 'ridge']

        self.model_types = model_types
        self.n_seeds = n_seeds
        self.seeds = [42, 123, 456][:n_seeds]
        self.ensembles = {}
        self.trained = False

    def fit(self, X_train, y_train, verbose=True):
        """训练所有模型类型"""
        if verbose:
            print(f"\n{'='*70}")
            print(f"异构多种子集成训练")
            print(f"{'='*70}")
            print(f"模型类型: {self.model_types}")
            print(f"每种模型种子数: {self.n_seeds}")

        for model_type in self.model_types:
            if verbose:
                print(f"\n训练 {model_type}...")

            ensemble = MultiSeedEnsemble(
                base_model_type=model_type,
                n_seeds=self.n_seeds,
                seeds=self.seeds
            )
            ensemble.fit(X_train, y_train, verbose=False)
            self.ensembles[model_type] = ensemble

        self.trained = True

        if verbose:
            print(f"\n训练完成！共 {len(self.ensembles)} 种模型类型")

        return self

    def predict(self, X, weights=None):
        """
        集成预测（不同模型类型的加权平均）

        Args:
            X: 特征数据
            weights: 各模型类型的权重，None则使用等权重

        Returns:
            array: 预测结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用 fit()")

        predictions = []
        for model_type in self.model_types:
            pred = self.ensembles[model_type].predict(X)
            predictions.append(pred)

        predictions = np.array(predictions)

        if weights is None:
            weights = np.ones(len(self.model_types)) / len(self.model_types)

        return np.average(predictions, axis=0, weights=weights)


# 便捷函数
def create_multi_seed_ensemble(model_type='random_forest', n_seeds=5):
    """
    创建多种子集成模型的便捷函数

    Args:
        model_type: 模型类型
        n_seeds: 种子数量

    Returns:
        MultiSeedEnsemble: 集成模型对象
    """
    return MultiSeedEnsemble(
        base_model_type=model_type,
        n_seeds=n_seeds
    )
