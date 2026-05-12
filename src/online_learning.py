"""
在线学习模块
Online Learning Module
让模型可以根据新数据持续更新，无需重新训练
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import json
from pathlib import Path


class OnlineLearningModel:
    """
    在线学习模型

    核心特性：
    1. 增量学习：新数据到来时更新模型
    2. 数据缓冲：累积一定量数据后重新训练
    3. 性能追踪：记录模型性能变化
    4. 版本管理：保存历史模型版本
    """

    def __init__(self, model_type='random_forest', retrain_threshold=10):
        """
        初始化在线学习模型

        Args:
            model_type: 模型类型
            retrain_threshold: 重新训练的数据量阈值
        """
        self.model_type = model_type
        self.retrain_threshold = retrain_threshold

        # 初始化模型
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        # 数据缓冲区
        self.data_buffer = []
        self.buffer_size = 0

        # 性能追踪
        self.performance_history = []
        self.model_versions = []
        self.current_version = 0

        # 初始训练标记
        self.is_trained = False

    def initial_train(self, X_train, y_train):
        """
        初始训练

        Args:
            X_train: 训练特征
            y_train: 训练标签
        """
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # 记录初始性能
        train_score = self.model.score(X_train, y_train)
        self._log_performance('initial_train', train_score, len(X_train))

        # 保存初始版本
        self._save_model_version('initial')

        print(f"✅ 初始训练完成 - R²: {train_score:.4f}")

    def add_new_data(self, X_new, y_new):
        """
        添加新数据到缓冲区

        Args:
            X_new: 新特征数据
            y_new: 新标签数据
        """
        # 添加到缓冲区
        if isinstance(X_new, pd.DataFrame):
            X_new = X_new.values
        if isinstance(y_new, pd.Series):
            y_new = y_new.values

        for i in range(len(X_new)):
            self.data_buffer.append({
                'X': X_new[i],
                'y': y_new[i],
                'timestamp': datetime.now().isoformat()
            })
            self.buffer_size += 1

        print(f"📊 已添加 {len(X_new)} 条新数据到缓冲区（总计：{self.buffer_size}）")

        # 检查是否需要重新训练
        if self.buffer_size >= self.retrain_threshold:
            self._retrain()

    def predict(self, X):
        """
        预测

        Args:
            X: 特征数据

        Returns:
            预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练，请先调用 initial_train()")

        return self.model.predict(X)

    def predict_with_confidence(self, X):
        """
        预测并给出置信度

        Args:
            X: 特征数据

        Returns:
            (预测值, 置信度)
        """
        predictions = self.predict(X)

        # 使用Random Forest的树方差作为置信度
        if hasattr(self.model, 'estimators_'):
            tree_preds = np.array([tree.predict(X) for tree in self.model.estimators_])
            std = np.std(tree_preds, axis=0)
            # 转换为置信度百分比（标准差越小，置信度越高）
            confidence = 1 / (1 + std)
        else:
            confidence = np.ones(len(X)) * 0.8  # 默认置信度

        return predictions, confidence

    def _retrain(self):
        """使用缓冲区数据重新训练"""
        if not self.is_trained:
            print("⚠️ 模型尚未初始训练，跳过重新训练")
            return

        # 准备训练数据
        X_buffer = np.array([item['X'] for item in self.data_buffer])
        y_buffer = np.array([item['y'] for item in self.data_buffer])

        # 获取旧训练集的性能
        old_score = self.performance_history[-1]['score'] if self.performance_history else 0

        # 重新训练（使用缓冲区数据）
        self.model.fit(X_buffer, y_buffer)

        # 评估新性能
        new_score = self.model.score(X_buffer, y_buffer)

        # 记录性能
        self._log_performance('retrain', new_score, len(X_buffer))

        # 保存新版本
        self._save_model_version(f'v{self.current_version}')

        # 清空缓冲区
        self.data_buffer = []
        self.buffer_size = 0

        print(f"🔄 重新训练完成 - R²: {old_score:.4f} → {new_score:.4f}")

    def _log_performance(self, action, score, data_size):
        """记录性能"""
        self.performance_history.append({
            'version': self.current_version,
            'action': action,
            'score': score,
            'data_size': data_size,
            'timestamp': datetime.now().isoformat()
        })

    def _save_model_version(self, version_name):
        """保存模型版本"""
        self.current_version += 1

        self.model_versions.append({
            'version': self.current_version,
            'name': version_name,
            'timestamp': datetime.now().isoformat()
        })

    def get_performance_report(self):
        """获取性能报告"""
        if not self.performance_history:
            return "暂无性能记录"

        report = "模型性能报告\n"
        report += "=" * 50 + "\n\n"

        for perf in self.performance_history:
            report += f"版本 {perf['version']} - {perf['action']}\n"
            report += f"  时间: {perf['timestamp']}\n"
            report += f"  R²得分: {perf['score']:.4f}\n"
            report += f"  数据量: {perf['data_size']}\n\n"

        return report

    def export_performance_data(self):
        """导出性能数据（用于可视化）"""
        return pd.DataFrame(self.performance_history)


# 使用示例
if __name__ == "__main__":
    # 模拟数据
    np.random.seed(42)

    # 初始训练数据
    X_train = np.random.rand(100, 5)  # 100条数据，5个特征
    y_train = X_train.sum(axis=1) + np.random.normal(0, 0.1, 100)

    # 创建在线学习模型
    model = OnlineLearningModel(retrain_threshold=10)

    # 初始训练
    model.initial_train(X_train, y_train)

    # 模拟新数据持续到来
    for day in range(1, 6):
        print(f"\n=== 第{day}天 ===")

        # 新数据
        X_new = np.random.rand(3, 5)  # 每天3条新数据
        y_new = X_new.sum(axis=1) + np.random.normal(0, 0.1, 3)

        # 添加新数据
        model.add_new_data(X_new, y_new)

        # 预测
        X_test = np.random.rand(1, 5)
        pred, conf = model.predict_with_confidence(X_test)
        print(f"预测值: {pred[0]:.4f}, 置信度: {conf[0]:.4f}")

    # 性能报告
    print("\n" + model.get_performance_report())
