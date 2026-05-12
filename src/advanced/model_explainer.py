#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型可解释性模块
使用 SHAP 进行模型解释和可视化
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class ModelExplainer:
    """模型解释器"""

    def __init__(self, model, X, feature_names, output_dir=None):
        """
        Args:
            model: 训练好的模型
            X: 特征数据
            feature_names: 特征名称列表
            output_dir: 输出目录
        """
        self.model = model
        self.X = X
        self.feature_names = feature_names
        self.output_dir = output_dir

        self.explainer = None
        self.shap_values = None

    def calculate_shap(self):
        """计算 SHAP 值"""
        try:
            import shap

            print("\n[SHAP] 计算特征重要性...")

            # 创建解释器
            if hasattr(self.model, 'feature_importances_'):
                # 树模型使用 TreeExplainer
                self.explainer = shap.TreeExplainer(self.model)
                self.shap_values = self.explainer.shap_values(self.X)
            else:
                # 其他模型使用 KernelExplainer
                self.explainer = shap.KernelExplainer(
                    self.model.predict,
                    shap.kmeans(self.X, n_clusters=10)
                )
                self.shap_values = self.explainer.shap_values(self.X, nsamples=100)

            print("  [OK] SHAP 值计算完成")
            return True

        except ImportError:
            print("  [警告] SHAP 未安装，跳过")
            print("  安装命令: pip install shap")
            return False

    def plot_summary(self, save_path=None):
        """绘制 SHAP 摘要图"""
        if self.explainer is None:
            print("  [跳过] SHAP 值未计算")
            return

        try:
            import shap

            print("\n[SHAP] 生成摘要图...")

            plt.figure(figsize=(12, 8))

            # 摘要图
            shap.summary_plot(
                self.shap_values,
                self.X,
                feature_names=self.feature_names,
                plot_type="bar",
                show=False
            )

            plt.title('SHAP 特征重要性（均值绝对值）', fontsize=14, fontweight='bold')
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] 已保存: {save_path.name}")
            else:
                plt.show()

        except Exception as e:
            print(f"  [错误] 生成失败: {e}")

    def plot_dependence(self, feature_idx=0, save_path=None):
        """绘制依赖图"""
        if self.explainer is None:
            print("  [跳过] SHAP 值未计算")
            return

        try:
            import shap

            print(f"\n[SHAP] 生成依赖图（特征 {feature_idx}）...")

            shap.dependence_plot(
                self.shap_values,
                self.X,
                feature_idx,
                feature_names=self.feature_names,
                show=False
            )

            plt.title(f'SHAP 依赖图 - {self.feature_names[feature_idx]}', fontsize=14, fontweight='bold')
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] 已保存: {save_path.name}")
            else:
                plt.show()

        except Exception as e:
            print(f"  [错误] 生成失败: {e}")

    def plot_force(self, sample_idx=0, save_path=None):
        """绘制力图"""
        if self.explainer is None:
            print("  [跳过] SHAP 值未计算")
            return

        try:
            import shap

            print(f"\n[SHAP] 生成力图（样本 {sample_idx}）...")

            plt.figure(figsize=(14, 8))

            shap.force_plot(
                self.explainer.expected_value,
                self.shap_values[sample_idx],
                self.X[sample_idx],
                feature_names=self.feature_names,
                matplotlib=True,
                show=False
            )

            plt.title(f'SHAP 力图 - 样本 {sample_idx}', fontsize=14, fontweight='bold')
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"  [OK] 已保存: {save_path.name}")
            else:
                plt.show()

        except Exception as e:
            print(f"  [错误] 生成失败: {e}")

    def get_top_features(self, n=10):
        """获取最重要的特征"""
        if self.explainer is None:
            print("  [跳过] SHAP 值未计算")
            return None

        try:
            import shap

            # 计算平均绝对 SHAP 值
            mean_shap = np.abs(self.shap_values).mean(axis=0)

            # 创建 DataFrame
            importance_df = pd.DataFrame({
                '特征': self.feature_names,
                '重要性': mean_shap
            }).sort_values('重要性', ascending=False)

            return importance_df.head(n)

        except Exception as e:
            print(f"  [错误] 计算失败: {e}")
            return None

    def generate_report(self):
        """生成完整的解释报告"""
        print("\n" + "=" * 70)
        print("模型可解释性分析报告")
        print("=" * 70)

        # 计算 SHAP 值
        if not self.calculate_shap():
            return

        # 获取 Top 特征
        top_features = self.get_top_features(10)

        if top_features is not None:
            print("\n[特征重要性 Top 10]")
            for idx, row in top_features.iterrows():
                print(f"  {idx+1}. {row['特征']}: {row['重要性']:.4f}")

        # 生成图表
        if self.output_dir:
            from pathlib import Path

            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 摘要图
            self.plot_summary(output_path / 'shap_summary.png')

            # 依赖图（第一个特征）
            self.plot_dependence(0, output_path / 'shap_dependence.png')

            # 力图（第一个样本）
            self.plot_force(0, output_path / 'shap_force.png')

            print(f"\n[报告] 可解释性分析完成")
            print(f"  保存位置：{self.output_dir}")

        print("\n" + "=" * 70)


def explain_model(model, X, feature_names, output_dir=None):
    """
    解释模型

    Args:
        model: 训练好的模型
        X: 特征数据
        feature_names: 特征名称
        output_dir: 输出目录
    """
    explainer = ModelExplainer(model, X, feature_names, output_dir)
    explainer.generate_report()

    return explainer


if __name__ == '__main__':
    # 测试
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import DATA_DIR, REPORTS_DIR
    from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer, YieldPredictor

    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 训练模型
        predictor = YieldPredictor(df_enhanced)
        predictor.run_all()

        # 准备特征
        feature_cols = [col for col in df_enhanced.columns if col not in [
            '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
        ] and df_enhanced[col].dtype in ['float64', 'int64']]

        X = df_enhanced[feature_cols].fillna(df_enhanced[feature_cols].median())

        # 解释模型
        explain_model(
            predictor.model,
            X.values,
            feature_cols,
            REPORTS_DIR / 'shap_analysis'
        )
    else:
        print("未找到数据文件")
