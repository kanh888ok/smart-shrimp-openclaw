#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型对比模块
对比多个机器学习模型的性能
"""

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 机器学习模型
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_score, KFold, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# 导入项目配置
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
from config import DATA_DIR, REPORTS_DIR

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class ModelComparison:
    """模型对比类"""

    def __init__(self, df):
        """初始化"""
        self.df = df

        # 准备特征
        self.feature_cols = [col for col in df.columns if col not in [
            '日期', '预计产量 (kg)', '预警等级', '环境压力指数'
        ] and df[col].dtype in ['int64', 'float64']]

        self.X = df[self.feature_cols].fillna(df[self.feature_cols].median())
        self.y = df['预计产量 (kg)'].fillna(df['预计产量 (kg)'].median())

        # 定义模型
        self.models = {
            'Random Forest': RandomForestRegressor(
                n_estimators=100, max_depth=10, min_samples_split=5, random_state=42
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=100, max_depth=5, random_state=42
            ),
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=1.0),
            'Linear Regression': LinearRegression(),
        }

        self.results = {}
        self.best_model = None
        self.best_model_name = None

    def compare_models(self):
        """对比所有模型"""
        print("\n" + "=" * 70)
        print("模型对比分析")
        print("=" * 70)

        kf = KFold(n_splits=5, shuffle=True, random_state=42)

        for name, model in self.models.items():
            print(f"\n正在训练: {name}...")

            # 训练模型
            X_train, X_test, y_train, y_test = train_test_split(
                self.X, self.y, test_size=0.2, random_state=42
            )

            model.fit(X_train, y_train)

            # 预测
            y_pred = model.predict(X_test)

            # 计算指标
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))

            # 交叉验证
            cv_scores = cross_val_score(model, self.X, self.y, cv=kf, scoring='r2')

            # 存储结果
            self.results[name] = {
                'model': model,
                'r2': r2,
                'mae': mae,
                'rmse': rmse,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'y_test': y_test,
                'y_pred': y_pred
            }

            print(f"  R²: {r2:.3f}")
            print(f"  MAE: {mae:.2f} kg")
            print(f"  RMSE: {rmse:.2f} kg")
            print(f"  CV-R²: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

        # 选择最佳模型
        self.best_model_name = max(self.results, key=lambda x: self.results[x]['cv_mean'])
        self.best_model = self.results[self.best_model_name]['model']

        print(f"\n✅ 最佳模型: {self.best_model_name}")
        print(f"   交叉验证 R²: {self.results[self.best_model_name]['cv_mean']:.3f}")

    def plot_comparison(self, output_dir):
        """绘制对比图表"""
        print("\n正在生成对比图表...")

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('模型性能对比', fontsize=16, fontweight='bold')

        # 1. R² 得分对比
        ax1 = axes[0, 0]
        names = list(self.results.keys())
        r2_scores = [self.results[name]['r2'] for name in names]
        cv_scores = [self.results[name]['cv_mean'] for name in names]

        x = np.arange(len(names))
        width = 0.35

        ax1.bar(x - width/2, r2_scores, width, label='测试集 R²', color='steelblue')
        ax1.bar(x + width/2, cv_scores, width, label='交叉验证 R²', color='coral')
        ax1.set_xlabel('模型')
        ax1.set_ylabel('R² 得分')
        ax1.set_title('R² 得分对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # 2. MAE 对比
        ax2 = axes[0, 1]
        mae_scores = [self.results[name]['mae'] for name in names]

        bars = ax2.bar(names, mae_scores, color='lightgreen', edgecolor='black')
        ax2.set_xlabel('模型')
        ax2.set_ylabel('MAE (kg)')
        ax2.set_title('平均绝对误差对比 (越小越好)')
        ax2.set_xticklabels(names, rotation=45, ha='right')
        ax2.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)

        # 3. RMSE 对比
        ax3 = axes[1, 0]
        rmse_scores = [self.results[name]['rmse'] for name in names]

        bars = ax3.bar(names, rmse_scores, color='plum', edgecolor='black')
        ax3.set_xlabel('模型')
        ax3.set_ylabel('RMSE (kg)')
        ax3.set_title('均方根误差对比 (越小越好)')
        ax3.set_xticklabels(names, rotation=45, ha='right')
        ax3.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=9)

        # 4. 稳定性对比（CV标准差）
        ax4 = axes[1, 1]
        cv_stds = [self.results[name]['cv_std'] for name in names]

        bars = ax4.bar(names, cv_stds, color='lightskyblue', edgecolor='black')
        ax4.set_xlabel('模型')
        ax4.set_ylabel('标准差')
        ax4.set_title('模型稳定性对比 (越小越稳定)')
        ax4.set_xticklabels(names, rotation=45, ha='right')
        ax4.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom', fontsize=9)

        plt.tight_layout()

        # 保存
        output_path = output_dir / 'model_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✅ 已保存: {output_path.name}")

        return output_path

    def plot_radar_chart(self, output_dir):
        """绘制雷达图"""
        print("正在生成雷达图...")

        from math import pi

        # 准备数据
        categories = ['R² 得分', 'MAE(反向)', 'RMSE(反向)', '稳定性(反向)', '拟合度']

        # 归一化数据（0-1范围）
        def normalize(series, reverse=False):
            min_val = series.min()
            max_val = series.max()
            if reverse:
                return 1 - (series - min_val) / (max_val - min_val + 1e-10)
            return (series - min_val) / (max_val - min_val + 1e-10)

        r2_norm = normalize(pd.Series([self.results[name]['r2'] for name in self.results.keys()]))
        mae_norm = normalize(pd.Series([self.results[name]['mae'] for name in self.results.keys()]), reverse=True)
        rmse_norm = normalize(pd.Series([self.results[name]['rmse'] for name in self.results.keys()]), reverse=True)
        cv_norm = normalize(pd.Series([self.results[name]['cv_std'] for name in self.results.keys()]), reverse=True)

        # 计算综合得分
        overall = (r2_norm + mae_norm + rmse_norm + cv_norm) / 4

        # 选择TOP3模型
        top3_idx = overall.nlargest(3).index
        top3_names = [list(self.results.keys())[i] for i in top3_idx]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

        # 绘制雷达图
        angles = [n / len(categories) * 2 * pi for n in range(len(categories))]
        angles += angles[:1]

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for idx, name in enumerate(top3_names):
            values = [
                self.results[name]['r2'],
                1 / (self.results[name]['mae'] + 1),
                1 / (self.results[name]['rmse'] + 1),
                1 / (self.results[name]['cv_std'] + 1),
                self.results[name]['cv_mean']
            ]

            # 归一化到0-1
            max_val = max(values)
            values_norm = [v / max_val for v in values]
            values_norm += values_norm[:1]

            ax.plot(angles, values_norm, 'o-', linewidth=2, label=name, color=colors[idx])
            ax.fill(angles, values_norm, alpha=0.15, color=colors[idx])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('模型综合性能雷达图 (TOP 3)', fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.grid(True)

        plt.tight_layout()

        # 保存
        output_path = output_dir / 'model_radar_chart.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  ✅ 已保存: {output_path.name}")

        return output_path

    def generate_report(self):
        """生成对比报告"""
        print("\n正在生成对比报告...")

        report_path = REPORTS_DIR / 'model_comparison_report.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("模型对比分析报告\n")
            f.write("SmartShrimp Team\n")
            f.write("=" * 70 + "\n\n")

            f.write("一、模型列表\n")
            f.write("-" * 70 + "\n")
            for i, name in enumerate(self.results.keys(), 1):
                f.write(f"{i}. {name}\n")
            f.write("\n")

            f.write("二、性能对比\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'模型':<20s} {'R²':>8s} {'MAE':>10s} {'RMSE':>10s} {'CV-R²':>10s}\n")
            f.write("-" * 70 + "\n")

            for name in self.results.keys():
                res = self.results[name]
                f.write(f"{name:<20s} {res['r2']:8.3f} {res['mae']:10.2f} "
                       f"{res['rmse']:10.2f} {res['cv_mean']:10.3f}\n")

            f.write("\n")

            f.write("三、最佳模型\n")
            f.write("-" * 70 + "\n")
            f.write(f"模型名称: {self.best_model_name}\n")
            f.write(f"交叉验证 R²: {self.results[self.best_model_name]['cv_mean']:.3f} "
                   f"± {self.results[self.best_model_name]['cv_std']:.3f}\n")
            f.write(f"测试集 R²: {self.results[self.best_model_name]['r2']:.3f}\n")
            f.write(f"测试集 MAE: {self.results[self.best_model_name]['mae']:.2f} kg\n")
            f.write(f"测试集 RMSE: {self.results[self.best_model_name]['rmse']:.2f} kg\n")
            f.write("\n")

            f.write("四、建议\n")
            f.write("-" * 70 + "\n")
            f.write(f"推荐使用 {self.best_model_name} 作为产量预测模型。\n\n")

            if self.results[self.best_model_name]['cv_mean'] > 0.7:
                f.write("该模型性能优秀，可用于实际生产预测。\n")
            elif self.results[self.best_model_name]['cv_mean'] > 0.5:
                f.write("该模型性能良好，可作为参考工具使用。\n")
            else:
                f.write("该模型性能一般，建议增加更多特征或数据。\n")

            f.write("\n" + "=" * 70 + "\n")

        print(f"  ✅ 已保存: {report_path.name}")

        return report_path

    def save_best_model(self):
        """保存最佳模型"""
        model_path = Path(__file__).parent.parent / 'best_model.joblib'
        joblib.dump(self.best_model, model_path)
        print(f"  ✅ 最佳模型已保存: {model_path.name}")

        return model_path

def run_comparison():
    """运行完整的模型对比"""
    print("\n" + "=" * 70)
    print("模型对比分析系统")
    print("=" * 70)

    # 加载数据
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if not data_files:
        print("\n❌ 未找到数据文件")
        return

    print(f"\n使用数据文件: {data_files[0].name}")

    loader = ShrimpDataLoader(data_files[0])
    df = loader.load()

    # 特征工程
    fe = FeatureEngineer(df)
    df_enhanced = fe.run_all()

    # 模型对比
    comparison = ModelComparison(df_enhanced)
    comparison.compare_models()

    # 生成图表
    output_dir = REPORTS_DIR / 'model_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison.plot_comparison(output_dir)
    comparison.plot_radar_chart(output_dir)

    # 生成报告
    comparison.generate_report()
    comparison.save_best_model()

    print("\n" + "=" * 70)
    print("✅ 模型对比完成！")
    print("=" * 70)
    print(f"\n📁 输出文件：")
    print(f"  图表目录：{output_dir}")
    print(f"  对比报告：{REPORTS_DIR / 'model_comparison_report.txt'}")
    print(f"  最佳模型：{Path(__file__).parent.parent / 'best_model.joblib'}")
    print("=" * 70)

if __name__ == '__main__':
    run_comparison()
