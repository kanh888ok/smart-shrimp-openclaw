#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超参数优化模块
使用 Optuna 进行自动超参数搜索
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
import warnings
warnings.filterwarnings('ignore')

# 导入 Optuna
try:
    import optuna
    from optuna.pruning import MedianPruner
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("警告: Optuna 未安装，跳过超参数优化")


class HyperparameterOptimizer:
    """超参数优化器"""

    def __init__(self, X_train, y_train, X_test=None, y_test=None, n_trials=50):
        """
        Args:
            X_train: 训练特征
            y_train: 训练标签
            X_test: 测试特征（可选）
            y_test: 测试标签（可选）
            n_trials: 优化试验次数
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test if X_test is not None else X_train
        self.y_test = y_test if y_test is not None else y_train
        self.n_trials = n_trials

        self.best_params = None
        self.best_score = None
        self.study = None

    def objective(self, trial):
        """Optuna 目标函数"""
        # 定义搜索空间
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 20),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            'max_features': trial.suggest_float('max_features', 0.3, 1.0)
        }

        # 创建模型
        model = RandomForestRegressor(
            random_state=42,
            **params
        )

        # 交叉验证
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=5,
            scoring='r2',
            n_jobs=-1
        )

        return scores.mean()

    def optimize(self):
        """执行优化"""
        if not OPTUNA_AVAILABLE:
            print("[警告] Optuna 未安装，使用默认参数")
            return {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'max_features': 1.0
            }

        print("\n[超参数优化] 开始自动优化...")

        # 创建研究
        self.study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_warmup_steps=10)
        )

        # 优化
        self.study.optimize(
            self.objective,
            n_trials=self.n_trials,
            show_progress_bar=False
        )

        self.best_params = self.study.best_params
        self.best_score = self.study.best_value

        print(f"\n[OK] 优化完成！")
        print(f"  最佳 R²: {self.best_score:.3f}")
        print(f"  最佳参数: {self.best_params}")

        return self.best_params

    def get_optimization_history(self):
        """获取优化历史"""
        if self.study is None:
            return None

        trials = self.study.trials_dataframe()

        return {
            'trial_number': trials['number'].tolist(),
            'r2_score': trials['value'].tolist(),
            'n_estimators': [t.params['n_estimators'] for t in self.study.trials],
            'max_depth': [t.params['max_depth'] for t in self.study.trials]
        }


class AutoML:
    """AutoML 自动机器学习"""

    def __init__(self, df):
        """
        Args:
            df: 数据 DataFrame
        """
        self.df = df
        self.best_model = None
        self.best_params = None

    def run_auto_ml(self):
        """运行 AutoML"""
        print("\n" + "=" * 70)
        print("AutoML 自动机器学习系统")
        print("=" * 70)

        # 准备数据
        feature_cols = [col for col in self.df.columns if col not in [
            '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
        ] and self.df[col].dtype in ['float64', 'int64']]

        X = self.df[feature_cols].fillna(self.df[feature_cols].median())
        y = self.df['预计产量 (kg)'].fillna(self.df['预计产量 (kg)'].median())

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print("\n[超参数优化] 自动搜索最优参数...")
        optimizer = HyperparameterOptimizer(X_train, y_train, X_test, y_test, n_trials=30)

        # 优化
        best_params = optimizer.optimize()

        # 使用最佳参数训练最终模型
        print("\n[最终训练] 使用最佳参数训练最终模型...")
        self.best_model = RandomForestRegressor(
            random_state=42,
            **best_params
        )
        self.best_model.fit(X_train, y_train)

        # 评估
        y_pred = self.best_model.predict(X_test)
        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        print(f"\n[最终模型性能]")
        print(f"  R² 得分: {r2:.3f}")
        print(f"  MAE: {mae:.2f} kg")
        print(f"  RMSE: {rmse:.2f} kg")

        # 特征重要性
        importances = self.best_model.feature_importances_

        feature_importance = pd.DataFrame({
            '特征': feature_cols,
            '重要性': importances
        }).sort_values('重要性', ascending=False)

        print(f"\n[特征重要性 TOP 5]")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"  {idx+1}. {row['特征']}: {row['重要性']:.3f}")

        self.best_params = best_params

        print("\n[OK] AutoML 完成！")

        return self.best_model, r2


def run_hyperparameter_tuning(df):
    """
    运行超参数优化

    Args:
        df: 数据 DataFrame

    Returns:
        model: 优化后的模型
        r2: R² 得分
    """
    automl = AutoML(df)
    model, r2 = automl.run_auto_ml()

    print(f"\n总结:")
    print(f"  优化后 R²: {r2:.3f}")

    return model, r2


if __name__ == '__main__':
    # 测试
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import DATA_DIR
    from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer

    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        run_hyperparameter_tuning(df_enhanced)
    else:
        print("未找到数据文件")
