#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型评估模块
提供完整的模型评估报告
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

def load_data_and_model():
    """加载数据和模型"""
    from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
    from config import DATA_DIR
    import joblib

    # 加载数据
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if not data_files:
        raise FileNotFoundError("未找到数据文件")

    loader = ShrimpDataLoader(data_files[0])
    df = loader.load()

    # 特征工程
    fe = FeatureEngineer(df)
    df_enhanced = fe.run_all()

    # 加载模型
    model_path = Path(__file__).parent.parent / 'random_forest_model.joblib'
    if model_path.exists():
        model = joblib.load(model_path)
    else:
        raise FileNotFoundError("未找到训练好的模型，请先运行完整分析")

    return df_enhanced, model

def cross_validation_evaluation(df, model):
    """交叉验证评估"""
    print("\n【交叉验证评估】")
    print("-" * 70)

    # 准备特征
    feature_cols = [col for col in df.columns if col not in [
        '日期', '预计产量 (kg)', '预警等级', '环境压力指数'
    ] and df[col].dtype in ['int64', 'float64']]

    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df['预计产量 (kg)'].fillna(df['预计产量 (kg)'].median())

    # 5折交叉验证
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # R² 分数
    r2_scores = cross_val_score(model, X, y, cv=kf, scoring='r2')
    print(f"R² 分数（5折交叉验证）:")
    print(f"  各折得分: {[f'{s:.3f}' for s in r2_scores]}")
    print(f"  平均值: {r2_scores.mean():.3f} ± {r2_scores.std():.3f}")

    # RMSE
    mse_scores = -cross_val_score(model, X, y, cv=kf, scoring='neg_mean_squared_error')
    rmse_scores = np.sqrt(mse_scores)
    print(f"\nRMSE（5折交叉验证）:")
    print(f"  各折得分: {[f'{s:.2f}' for s in rmse_scores]}")
    print(f"  平均值: {rmse_scores.mean():.2f} ± {rmse_scores.std():.2f} kg")

    # MAE
    mae_scores = -cross_val_score(model, X, y, cv=kf, scoring='neg_mean_absolute_error')
    print(f"\nMAE（5折交叉验证）:")
    print(f"  各折得分: {[f'{s:.2f}' for s in mae_scores]}")
    print(f"  平均值: {mae_scores.mean():.2f} ± {mae_scores.std():.2f} kg")

    return {
        'r2_mean': r2_scores.mean(),
        'r2_std': r2_scores.std(),
        'rmse_mean': rmse_scores.mean(),
        'rmse_std': rmse_scores.std(),
        'mae_mean': mae_scores.mean(),
        'mae_std': mae_scores.std(),
    }

def residual_analysis(df, model):
    """残差分析"""
    print("\n【残差分析】")
    print("-" * 70)

    # 准备特征
    feature_cols = [col for col in df.columns if col not in [
        '日期', '预计产量 (kg)', '预警等级', '环境压力指数'
    ] and df[col].dtype in ['int64', 'float64']]

    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df['预计产量 (kg)'].fillna(df['预计产量 (kg)'].median())

    # 预测
    y_pred = model.predict(X)
    residuals = y - y_pred

    print(f"残差统计:")
    print(f"  平均值: {residuals.mean():.2f} kg")
    print(f"  标准差: {residuals.std():.2f} kg")
    print(f"  最大正残差: {residuals.max():.2f} kg（低估）")
    print(f"  最大负残差: {residuals.min():.2f} kg（高估）")

    # 残差分布
    print(f"\n残差分布:")
    print(f"  在 ±10kg 内: {(np.abs(residuals) <= 10).sum()} / {len(residuals)} ({(np.abs(residuals) <= 10).sum() / len(residuals) * 100:.1f}%)")
    print(f"  在 ±20kg 内: {(np.abs(residuals) <= 20).sum()} / {len(residuals)} ({(np.abs(residuals) <= 20).sum() / len(residuals) * 100:.1f}%)")
    print(f"  在 ±50kg 内: {(np.abs(residuals) <= 50).sum()} / {len(residuals)} ({(np.abs(residuals) <= 50).sum() / len(residuals) * 100:.1f}%)")

    # 预测精度
    mape = np.mean(np.abs(residuals / y)) * 100
    print(f"\n预测精度:")
    print(f"  平均绝对百分比误差 (MAPE): {mape:.1f}%")

    return {
        'residual_mean': residuals.mean(),
        'residual_std': residuals.std(),
        'mape': mape,
        'within_10kg': (np.abs(residuals) <= 10).sum() / len(residuals),
        'within_20kg': (np.abs(residuals) <= 20).sum() / len(residuals),
    }

def feature_importance_analysis(df, model):
    """特征重要性分析"""
    print("\n【特征重要性分析】")
    print("-" * 70)

    # 准备特征
    feature_cols = [col for col in df.columns if col not in [
        '日期', '预计产量 (kg)', '预警等级', '环境压力指数'
    ] and df[col].dtype in ['int64', 'float64']]

    # 获取特征重要性
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    print("特征重要性排名:")
    for i, idx in enumerate(indices):
        if importances[idx] > 0.01:  # 只显示重要性 > 1% 的特征
            print(f"  {i+1}. {feature_cols[idx]:20s} : {importances[idx]:.3f} ({importances[idx]*100:.1f}%)")

    return {
        feature_cols[i]: importances[i]
        for i in range(len(feature_cols))
    }

def model_stability_test(df, model):
    """模型稳定性测试"""
    print("\n【模型稳定性测试】")
    print("-" * 70)

    from sklearn.model_selection import train_test_split

    feature_cols = [col for col in df.columns if col not in [
        '日期', '预计产量 (kg)', '预警等级', '环境压力指数'
    ] and df[col].dtype in ['int64', 'float64']]

    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df['预计产量 (kg)'].fillna(df['预计产量 (kg)'].median())

    # 多次随机分割测试
    r2_scores = []
    rmse_scores = []

    for i in range(10):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=i*42
        )

        from sklearn.ensemble import RandomForestRegressor
        model_temp = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        model_temp.fit(X_train, y_train)

        y_pred = model_temp.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        r2_scores.append(r2)
        rmse_scores.append(rmse)

    print(f"10次随机分割测试结果:")
    print(f"  R² 范围: {min(r2_scores):.3f} ~ {max(r2_scores):.3f}")
    print(f"  R² 平均: {np.mean(r2_scores):.3f} ± {np.std(r2_scores):.3f}")
    print(f"  RMSE 范围: {min(rmse_scores):.2f} ~ {max(rmse_scores):.2f} kg")
    print(f"  RMSE 平均: {np.mean(rmse_scores):.2f} ± {np.std(rmse_scores):.2f} kg")

    return {
        'r2_stability': np.std(r2_scores),
        'rmse_stability': np.std(rmse_scores),
    }

def save_evaluation_report(cv_results, residual_results, importance, stability):
    """保存评估报告"""
    from config import REPORTS_DIR

    report_path = REPORTS_DIR / 'model_evaluation.txt'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("模型评估报告\n")
        f.write("SmartShrimp Team\n")
        f.write("=" * 70 + "\n\n")

        f.write("1. 交叉验证结果\n")
        f.write("-" * 70 + "\n")
        f.write(f"R² 得分: {cv_results['r2_mean']:.3f} ± {cv_results['r2_std']:.3f}\n")
        f.write(f"RMSE: {cv_results['rmse_mean']:.2f} ± {cv_results['rmse_std']:.2f} kg\n")
        f.write(f"MAE: {cv_results['mae_mean']:.2f} ± {cv_results['mae_std']:.2f} kg\n\n")

        f.write("2. 残差分析结果\n")
        f.write("-" * 70 + "\n")
        f.write(f"残差平均值: {residual_results['residual_mean']:.2f} kg\n")
        f.write(f"残差标准差: {residual_results['residual_std']:.2f} kg\n")
        f.write(f"MAPE: {residual_results['mape']:.1f}%\n")
        f.write(f"±10kg 内准确率: {residual_results['within_10kg']*100:.1f}%\n")
        f.write(f"±20kg 内准确率: {residual_results['within_20kg']*100:.1f}%\n\n")

        f.write("3. 特征重要性 TOP 5\n")
        f.write("-" * 70 + "\n")
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feat, imp) in enumerate(sorted_importance[:5]):
            f.write(f"{i+1}. {feat}: {imp:.3f} ({imp*100:.1f}%)\n")
        f.write("\n")

        f.write("4. 模型稳定性\n")
        f.write("-" * 70 + "\n")
        f.write(f"R² 稳定性（标准差）: {stability['r2_stability']:.3f}\n")
        f.write(f"RMSE 稳定性（标准差）: {stability['rmse_stability']:.2f} kg\n\n")

        f.write("=" * 70 + "\n")
        f.write("评估结论\n")
        f.write("=" * 70 + "\n")

        # 生成结论
        if cv_results['r2_mean'] >= 0.7:
            conclusion = "模型拟合良好，可用于产量预测"
        elif cv_results['r2_mean'] >= 0.5:
            conclusion = "模型拟合尚可，可作为参考工具"
        else:
            conclusion = "模型拟合一般，建议增加更多特征或数据"

        f.write(f"{conclusion}\n\n")
        f.write(f"优势:\n")
        f.write(f"  - 交叉验证R²达到 {cv_results['r2_mean']:.3f}，模型稳定性良好\n")
        f.write(f"  - {residual_results['within_20kg']*100:.1f}% 的预测误差在±20kg内\n")
        f.write(f"  - R²标准差仅为 {stability['r2_stability']:.3f}，模型表现稳定\n\n")

        f.write(f"改进建议:\n")
        if cv_results['r2_mean'] < 0.7:
            f.write(f"  - 增加更多特征（如天气数据、水质历史数据）\n")
            f.write(f"  - 收集更多训练数据\n")
            f.write(f"  - 尝试其他模型（XGBoost、神经网络）\n")
        if residual_results['mape'] > 15:
            f.write(f"  - 优化高误差样本的特征提取\n")

    print(f"\n✅ 评估报告已保存：{report_path}")

def run_evaluation():
    """运行完整评估"""
    print("\n" + "=" * 70)
    print("模型评估系统")
    print("=" * 70)

    # 加载数据和模型
    df, model = load_data_and_model()

    # 运行各项评估
    cv_results = cross_validation_evaluation(df, model)
    residual_results = residual_analysis(df, model)
    importance = feature_importance_analysis(df, model)
    stability = model_stability_test(df, model)

    # 保存报告
    save_evaluation_report(cv_results, residual_results, importance, stability)

    print("\n" + "=" * 70)
    print("✅ 模型评估完成！")
    print("=" * 70)

if __name__ == '__main__':
    run_evaluation()
