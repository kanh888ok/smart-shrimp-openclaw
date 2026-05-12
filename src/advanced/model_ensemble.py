#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型融合模块
实现多种模型的集成预测
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
import joblib
import warnings
warnings.filterwarnings('ignore')


class ModelEnsemble:
    """模型融合器"""

    def __init__(self, df):
        """
        Args:
            df: 增强后的数据 DataFrame
        """
        self.df = df
        self.models = {}
        self.weights = {}
        self.trained = False

        # 准备数据
        self._prepare_data()

    def _prepare_data(self):
        """准备数据"""
        from sklearn.model_selection import train_test_split

        # 选择特征
        feature_cols = [col for col in self.df.columns if col not in [
            '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
        ] and self.df[col].dtype in ['float64', 'int64']]

        self.X = self.df[feature_cols].fillna(self.df[feature_cols].median())
        self.y = self.df['预计产量 (kg)'].fillna(self.df['预计产量 (kg)'].median())

        # 划分训练集和测试集
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )

        self.feature_cols = feature_cols

    def train_base_models(self):
        """训练基础模型"""
        print("\n[模型融合] 训练基础模型...")

        # 1. Random Forest
        print("  [1/5] 训练 Random Forest...")
        self.models['RF'] = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.models['RF'].fit(self.X_train, self.y_train)

        # 2. XGBoost
        print("  [2/5] 训练 XGBoost...")
        try:
            import xgboost as xgb
            self.models['XGB'] = xgb.XGBRegressor(
                n_estimators=100, max_depth=6, random_state=42, verbosity=0
            )
            self.models['XGB'].fit(self.X_train, self.y_train)
        except ImportError:
            print("    [跳过] XGBoost 未安装")

        # 3. LightGBM
        print("  [3/5] 训练 LightGBM...")
        try:
            import lightgbm as lgb
            self.models['LGBM'] = lgb.LGBMRegressor(
                n_estimators=100, max_depth=6, random_state=42, verbosity=-1
            )
            self.models['LGBM'].fit(self.X_train, self.y_train)
        except ImportError:
            print("    [跳过] LightGBM 未安装")

        # 4. Gradient Boosting
        print("  [4/5] 训练 Gradient Boosting...")
        self.models['GB'] = GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.models['GB'].fit(self.X_train, self.y_train)

        # 5. Ridge Regression
        print("  [5/5] 训练 Ridge Regression...")
        self.models['Ridge'] = Ridge(alpha=1.0)
        self.models['Ridge'].fit(self.X_train, self.y_train)

        # 验证模型
        self._validate_models()

        self.trained = True

    def _validate_models(self):
        """验证基础模型"""
        print("\n[模型验证] 计算模型权重...")

        from sklearn.metrics import r2_score

        # 计算每个模型的 R²
        r2_scores = {}

        for name, model in self.models.items():
            y_pred = model.predict(self.X_test)
            r2 = r2_score(self.y_test, y_pred)
            r2_scores[name] = r2
            print(f"  {name}: R² = {r2:.3f}")

        # 基于 R² 计算权重
        total_r2 = sum(max(0, r2) for r2 in r2_scores.values())

        if total_r2 > 0:
            for name in r2_scores:
                self.weights[name] = max(0, r2_scores[name]) / total_r2

            print("\n  [权重分配]")
            for name, weight in self.weights.items():
                print(f"    {name}: {weight:.2%}")

    def predict(self, X=None):
        """集成预测"""
        if not self.trained:
            print("[错误] 模型未训练")
            return None

        if X is None:
            X = self.X_test

        # 收集所有模型的预测
        predictions = []

        for name, model in self.models.items():
            y_pred = model.predict(X)
            predictions.append(y_pred)

        # 转换为 numpy array
        predictions = np.array(predictions)

        # 加权平均
        weighted_pred = np.zeros(len(predictions[0]))
        for i, (name, model) in enumerate(self.models.items()):
            weight = self.weights.get(name, 1.0 / len(self.models))
            weighted_pred += weight * predictions[i]

        return weighted_pred

    def get_metrics(self):
        """获取集成模型指标"""
        if not self.trained:
            return {}

        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

        y_pred_ensemble = self.predict()

        r2 = r2_score(self.y_test, y_pred_ensemble)
        mae = mean_absolute_error(self.y_test, y_pred_ensemble)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred_ensemble))

        return {
            'R²': r2,
            'MAE': mae,
            'RMSE': rmse
        }

    def get_feature_importance(self):
        """获取特征重要性（基于 Random Forest）"""
        if 'RF' in self.models:
            importances = self.models['RF'].feature_importances_

            return pd.DataFrame({
                '特征': self.feature_cols,
                '重要性': importances
            }).sort_values('重要性', ascending=False)

        return None


def run_model_ensemble(df):
    """
    运行模型融合

    Args:
        df: 数据 DataFrame

    Returns:
        ensemble: 训练好的集成模型
    """
    print("\n" + "=" * 70)
    print("模型融合系统")
    print("=" * 70)

    ensemble = ModelEnsemble(df)
    ensemble.train_base_models()

    # 获取指标
    metrics = ensemble.get_metrics()

    if metrics:
        print(f"\n[集成模型性能]")
        print(f"  R² 得分: {metrics['R²']:.3f}")
        print(f"  MAE: {metrics['MAE']:.2f} kg")
        print(f"  RMSE: {metrics['RMSE']:.2f} kg")

    # 特征重要性
    importance_df = ensemble.get_feature_importance()
    if importance_df is not None:
        print(f"\n[特征重要性 TOP 5]")
        for idx, row in importance_df.head(5).iterrows():
            print(f"  {idx+1}. {row['特征']}: {row['重要性']:.3f}")

    print("\n[OK] 模型融合完成！")

    return ensemble


def stacking_ensemble(df):
    """Stacking 集成"""
    print("\n[Stacking] 使用 Stacking 集成...")

    from sklearn.ensemble import StackingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import train_test_split

    # 准备数据
    feature_cols = [col for col in df.columns if col not in [
        '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
    ] and df[col].dtype in ['float64', 'int64']]

    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df['预计产量 (kg)'].fillna(df['预计产量 (kg)'].median())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 定义基础模型
    estimators = [
        ('rf', RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)),
        ('xgb', None),  # 如果有 xgboost
        ('gb', GradientBoostingRegressor(n_estimators=100, random_state=42))
    ]

    # 检查 xgboost 是否可用
    try:
        import xgboost as xgb
        estimators[1] = ('xgb', xgb.XGBRegressor(n_estimators=100, random_state=42))
    except ImportError:
        estimators[1] = ('xgb', None)

    # 移除 None
    estimators = [(name, est) for name, est in estimators if est is not None]

    # 创建 Stacking 模型
    stacking_model = StackingRegressor(
        estimators=estimators,
        final_estimator=Ridge(alpha=1.0),
        cv=5
    )

    # 训练
    print("  [训练] 训练 Stacking 模型...")
    stacking_model.fit(X_train, y_train)

    # 预测
    y_pred = stacking_model.predict(X_test)

    # 评估
    from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\n[Stacking 模型性能]")
    print(f"  R² 得分: {r2:.3f}")
    print(f"  MAE: {mae:.2f} kg")
    print(f"  RMSE: {rmse:.2f} kg")

    return stacking_model


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

        # 运行模型融合
        ensemble = run_model_ensemble(df_enhanced)
    else:
        print("未找到数据文件")
