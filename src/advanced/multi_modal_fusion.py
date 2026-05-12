#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态融合模块
融合传感器时序数据、图像特征、环境统计特征
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# 尝试导入深度学习框架
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import AutoModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SensorFeatureExtractor:
    """传感器时序特征提取器"""

    def __init__(self, window_size=7):
        """
        Args:
            window_size: 滑动窗口大小
        """
        self.window_size = window_size
        self.scaler = StandardScaler()

    def extract_time_series_features(self, df):
        """
        提取时序特征

        Args:
            df: 包含时序数据的DataFrame

        Returns:
            时序特征数组
        """
        features_list = []

        # 选择数值型传感器数据
        sensor_cols = [col for col in df.columns if col in [
            '水温 (°C)', '盐度 (ppt)', 'pH 值', '溶解氧 (mg/L)',
            '氨氮 (mg/L)', '亚硝酸盐 (mg/L)', '投喂量 (kg)'
        ] and df[col].dtype in ['float64', 'int64']]

        if not sensor_cols:
            # 如果没有传感器列，返回所有数值列
            sensor_cols = [col for col in df.columns
                          if df[col].dtype in ['float64', 'int64']]

        # 确保数据按日期排序
        if '日期' in df.columns:
            df = df.sort_values('日期')

        # 滑动窗口提取特征
        for i in range(self.window_size, len(df)):
            window_data = df[sensor_cols].iloc[i-self.window_size:i]

            # 统计特征
            features = {
                # 均值
                **{f'{col}_mean': window_data[col].mean() for col in sensor_cols},
                # 标准差
                **{f'{col}_std': window_data[col].std() for col in sensor_cols},
                # 最大值
                **{f'{col}_max': window_data[col].max() for col in sensor_cols},
                # 最小值
                **{f'{col}_min': window_data[col].min() for col in sensor_cols},
                # 趋势（线性回归斜率）
                **{f'{col}_trend': self._compute_trend(window_data[col].values)
                   for col in sensor_cols},
                # 变化率
                **{f'{col}_change_rate': (window_data[col].iloc[-1] - window_data[col].iloc[0]) / (window_data[col].iloc[0] + 1e-6)
                   for col in sensor_cols},
            }

            features_list.append(features)

        return pd.DataFrame(features_list)

    def _compute_trend(self, values):
        """计算线性趋势（斜率）"""
        if len(values) < 2:
            return 0

        x = np.arange(len(values))
        try:
            coef = np.polyfit(x, values, 1)[0]
            return coef
        except:
            return 0

    def extract_statistical_features(self, df):
        """
        提取统计特征

        Args:
            df: DataFrame

        Returns:
            统计特征DataFrame
        """
        features = {}

        # 选择数值列
        numeric_cols = [col for col in df.columns
                       if df[col].dtype in ['float64', 'int64']]

        # 全局统计特征
        for col in numeric_cols:
            features[f'{col}_global_mean'] = df[col].mean()
            features[f'{col}_global_std'] = df[col].std()
            features[f'{col}_global_max'] = df[col].max()
            features[f'{col}_global_min'] = df[col].min()
            features[f'{col}_global_median'] = df[col].median()

        # 相关性特征
        if '预计产量 (kg)' in df.columns and len(numeric_cols) > 1:
            target = df['预计产量 (kg)']
            for col in numeric_cols:
                if col != '预计产量 (kg)':
                    corr = df[col].corr(target)
                    features[f'{col}_corr_target'] = corr if not np.isnan(corr) else 0

        return pd.DataFrame([features])


class ImageFeatureExtractor:
    """图像特征提取器"""

    def __init__(self, method='statistical'):
        """
        Args:
            method: 特征提取方法
                - 'statistical': 统计特征（不需要深度学习）
                - 'cnn': CNN特征（需要torch）
                - 'pretrained': 预训练模型（需要transformers）
        """
        self.method = method
        self.model = None

        if method == 'pretrained' and TRANSFORMERS_AVAILABLE:
            print("  [提示] 使用预训练模型提取图像特征")
            # 这里可以加载预训练模型
        elif method == 'cnn' and TORCH_AVAILABLE:
            print("  [提示] 使用CNN提取图像特征")
            # 这里可以定义CNN模型

    def extract_features(self, image_data=None):
        """
        提取图像特征

        Args:
            image_data: 图像数据（可以是路径、数组等）

        Returns:
            图像特征向量
        """
        # 如果没有图像数据，返回模拟特征
        if image_data is None:
            # 返回随机特征（实际应用中应该从真实图像提取）
            return np.random.rand(128)  # 128维图像特征

        # 实际应用中的图像特征提取
        if self.method == 'statistical':
            return self._extract_statistical_features(image_data)
        elif self.method == 'cnn':
            return self._extract_cnn_features(image_data)
        elif self.method == 'pretrained':
            return self._extract_pretrained_features(image_data)

    def _extract_statistical_features(self, image_data):
        """提取统计特征"""
        # 这里应该是实际的图像处理代码
        # 示例：颜色直方图、纹理特征等
        return np.random.rand(64)

    def _extract_cnn_features(self, image_data):
        """使用CNN提取特征"""
        # 这里应该使用CNN模型
        return np.random.rand(256)

    def _extract_pretrained_features(self, image_data):
        """使用预训练模型提取特征"""
        # 这里应该使用预训练模型
        return np.random.rand(512)


class MultiModalDataLoader:
    """多模态数据加载器"""

    def __init__(self, df):
        """
        Args:
            df: 主数据DataFrame
        """
        self.df = df
        self.sensor_extractor = SensorFeatureExtractor(window_size=7)
        self.image_extractor = ImageFeatureExtractor(method='statistical')

    def load_multimodal_data(self, include_image=False):
        """
        加载多模态数据

        Args:
            include_image: 是否包含图像特征

        Returns:
            融合后的特征DataFrame
        """
        print("\n[多模态融合] 加载多模态数据...")

        # 1. 传感器时序特征
        print("  [1/3] 提取传感器时序特征...")
        sensor_features = self.sensor_extractor.extract_time_series_features(self.df)
        print(f"    提取了 {len(sensor_features)} 个时序样本，{len(sensor_features.columns)} 个特征")

        # 2. 统计特征
        print("  [2/3] 提取统计特征...")
        stat_features = self.sensor_extractor.extract_statistical_features(self.df)
        print(f"    提取了 {len(stat_features.columns)} 个统计特征")

        # 3. 图像特征（可选）
        image_features_list = []
        if include_image:
            print("  [3/3] 提取图像特征...")
            # 为每个样本提取图像特征
            for i in range(len(sensor_features)):
                img_feat = self.image_extractor.extract_features()
                image_features_list.append(img_feat)
            print(f"    提取了 {len(image_features_list[0])} 维图像特征")
        else:
            print("  [3/3] 跳过图像特征（未提供图像数据）")

        # 4. 融合特征
        print("\n[多模态融合] 融合多模态特征...")

        # 复制统计特征到每个时序样本
        stat_features_repeated = pd.concat([stat_features] * len(sensor_features), ignore_index=True)
        stat_features_repeated.index = sensor_features.index

        # 合并传感器特征和统计特征
        fused_features = pd.concat([sensor_features, stat_features_repeated], axis=1)

        # 添加图像特征（如果有的话）
        if include_image and image_features_list:
            image_features_df = pd.DataFrame(image_features_list,
                                             columns=[f'img_feat_{i}' for i in range(len(image_features_list[0]))])
            image_features_df.index = fused_features.index
            fused_features = pd.concat([fused_features, image_features_df], axis=1)

        print(f"  融合后特征维度: {fused_features.shape}")
        print(f"    - 时序特征: {len(sensor_features.columns)}")
        print(f"    - 统计特征: {len(stat_features.columns)}")
        if include_image:
            print(f"    - 图像特征: {len(image_features_list[0])}")

        return fused_features


class EarlyFusionModel:
    """早期融合模型"""

    def __init__(self, model_type='random_forest'):
        """
        Args:
            model_type: 模型类型
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()

    def train(self, X_train, y_train):
        """训练模型"""
        print(f"\n[早期融合] 训练 {self.model_type} 模型...")

        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)

        # 创建模型
        if self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # 训练
        self.model.fit(X_train_scaled, y_train)
        print("  [OK] 模型训练完成")

    def predict(self, X_test):
        """预测"""
        X_test_scaled = self.scaler.transform(X_test)
        return self.model.predict(X_test_scaled)

    def evaluate(self, X_test, y_test):
        """评估"""
        y_pred = self.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        return {
            'R²': r2,
            'MAE': mae,
            'RMSE': rmse
        }


class LateFusionModel:
    """晚期融合模型"""

    def __init__(self):
        """初始化晚期融合模型"""
        self.models = {}
        self.weights = {}

    def train(self, X_dict, y_train):
        """
        训练各模态的子模型

        Args:
            X_dict: 字典，键为模态名称，值为特征矩阵
            y_train: 标签
        """
        print("\n[晚期融合] 训练各模态子模型...")

        for modality, X in X_dict.items():
            print(f"  训练 {modality} 模型...")

            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            model.fit(X_scaled, y_train)

            # 保存模型和scaler
            self.models[modality] = {
                'model': model,
                'scaler': scaler
            }

            # 计算权重（基于训练集R²）
            y_pred = model.predict(X_scaled)
            r2 = r2_score(y_train, y_pred)
            self.weights[modality] = max(0, r2)

            print(f"    {modality} R²: {r2:.3f}")

        # 归一化权重
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for modality in self.weights:
                self.weights[modality] /= total_weight

        print(f"\n  融合权重: {self.weights}")

    def predict(self, X_dict):
        """
        预测

        Args:
            X_dict: 字典，键为模态名称，值为特征矩阵

        Returns:
            融合后的预测结果
        """
        predictions = []

        for modality, X in X_dict.items():
            if modality in self.models:
                scaler = self.models[modality]['scaler']
                model = self.models[modality]['model']

                X_scaled = scaler.transform(X)
                y_pred = model.predict(X_scaled)

                weight = self.weights.get(modality, 0)
                predictions.append(weight * y_pred)

        # 加权平均
        return np.sum(predictions, axis=0)

    def evaluate(self, X_dict, y_test):
        """评估"""
        y_pred = self.predict(X_dict)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        return {
            'R²': r2,
            'MAE': mae,
            'RMSE': rmse
        }


class HybridFusionModel:
    """混合融合模型（深度学习）"""

    def __init__(self, input_dims, hidden_dim=128):
        """
        Args:
            input_dims: 各模态的输入维度字典
            hidden_dim: 隐藏层维度
        """
        self.input_dims = input_dims
        self.hidden_dim = hidden_dim
        self.model = None

        if not TORCH_AVAILABLE:
            print("  [警告] PyTorch未安装，深度学习融合不可用")
            return

        # 创建神经网络模型
        self._build_model()

    def _build_model(self):
        """构建神经网络模型"""
        class FusionNet(nn.Module):
            def __init__(self, input_dims, hidden_dim):
                super(FusionNet, self).__init__()

                # 各模态的编码器
                self.encoders = nn.ModuleDict()
                for modality, dim in input_dims.items():
                    self.encoders[modality] = nn.Sequential(
                        nn.Linear(dim, hidden_dim),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(hidden_dim, hidden_dim // 2)
                    )

                # 融合层
                total_dim = len(input_dims) * (hidden_dim // 2)
                self.fusion = nn.Sequential(
                    nn.Linear(total_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(hidden_dim, hidden_dim // 2),
                    nn.ReLU(),
                    nn.Linear(hidden_dim // 2, 1)
                )

            def forward(self, x_dict):
                # 编码各模态
                encoded = []
                for modality, x in x_dict.items():
                    if modality in self.encoders:
                        enc = self.encoders[modality](x)
                        encoded.append(enc)

                # 拼接
                fused = torch.cat(encoded, dim=1)

                # 融合预测
                output = self.fusion(fused)
                return output

        self.model = FusionNet(self.input_dims, self.hidden_dim)

    def train(self, X_dict, y_train, epochs=50, batch_size=16, lr=0.001):
        """训练模型"""
        if not TORCH_AVAILABLE:
            print("  [错误] PyTorch未安装")
            return

        print(f"\n[混合融合] 训练神经网络融合模型...")

        # 转换为Tensor
        X_tensors = {}
        for modality, X in X_dict.items():
            X_tensors[modality] = torch.FloatTensor(X.values if hasattr(X, 'values') else X)

        y_tensor = torch.FloatTensor(y_train.values if hasattr(y_train, 'values') else y_train).reshape(-1, 1)

        # 优化器和损失函数
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        # 训练
        self.model.train()
        for epoch in range(epochs):
            # 简单批次训练（实际应该使用DataLoader）
            optimizer.zero_grad()
            outputs = self.model(X_tensors)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

            if (epoch + 1) % 10 == 0:
                print(f"  Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

        print("  [OK] 训练完成")

    def predict(self, X_dict):
        """预测"""
        if not TORCH_AVAILABLE:
            return None

        self.model.eval()

        # 转换为Tensor
        X_tensors = {}
        for modality, X in X_dict.items():
            X_tensors[modality] = torch.FloatTensor(X.values if hasattr(X, 'values') else X)

        with torch.no_grad():
            predictions = self.model(X_tensors)

        return predictions.numpy().flatten()

    def evaluate(self, X_dict, y_test):
        """评估"""
        y_pred = self.predict(X_dict)

        if y_pred is None:
            return None

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        return {
            'R²': r2,
            'MAE': mae,
            'RMSE': rmse
        }


class MultiModalPredictor:
    """多模态融合预测器（主类）"""

    def __init__(self, df, fusion_strategy='early'):
        """
        Args:
            df: 数据DataFrame
            fusion_strategy: 融合策略
                - 'early': 早期融合（特征级融合）
                - 'late': 晚期融合（决策级融合）
                - 'hybrid': 混合融合（深度学习）
        """
        self.df = df
        self.fusion_strategy = fusion_strategy
        self.data_loader = MultiModalDataLoader(df)
        self.model = None
        self.metrics = {}

    def prepare_data(self, include_image=False):
        """准备多模态数据"""
        print("\n" + "=" * 70)
        print("多模态融合预测系统")
        print("=" * 70)

        # 加载多模态数据
        self.fused_features = self.data_loader.load_multimodal_data(
            include_image=include_image
        )

        # 准备标签
        if '预计产量 (kg)' in self.df.columns:
            # 对齐标签（时序特征从第window_size个样本开始）
            target = self.df['预计产量 (kg)'].iloc[7:].values
            self.y = target
        else:
            raise ValueError("数据中缺少 '预计产量 (kg)' 列")

        print(f"\n[数据准备] 样本数: {len(self.fused_features)}, 标签数: {len(self.y)}")

        # 划分训练集和测试集
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.fused_features, self.y, test_size=0.2, random_state=42
        )

        print(f"  训练集: {len(self.X_train)} 样本")
        print(f"  测试集: {len(self.X_test)} 样本")

    def train_model(self, model_type='random_forest'):
        """训练模型"""
        if self.fusion_strategy == 'early':
            # 早期融合
            self.model = EarlyFusionModel(model_type=model_type)
            self.model.train(self.X_train, self.y_train)

        elif self.fusion_strategy == 'late':
            # 晚期融合
            # 将特征分组为不同模态
            X_dict = self._split_features_by_modality(self.X_train)

            self.model = LateFusionModel()
            self.model.train(X_dict, self.y_train)

        elif self.fusion_strategy == 'hybrid':
            # 混合融合
            X_dict = self._split_features_by_modality(self.X_train)
            input_dims = {k: v.shape[1] for k, v in X_dict.items()}

            self.model = HybridFusionModel(input_dims)
            self.model.train(X_dict, self.y_train)

    def _split_features_by_modality(self, X):
        """将特征按模态分组"""
        # 简化版：将特征分为时序和统计两组
        X_dict = {}

        # 时序特征（包含 _mean, _std, _max, _min, _trend, _change_rate）
        time_cols = [col for col in X.columns if any(suffix in col for suffix in
                     ['_mean', '_std', '_max', '_min', '_trend', '_change_rate'])]
        X_dict['time_series'] = X[time_cols]

        # 统计特征（包含 _global_ 或 _corr_）
        stat_cols = [col for col in X.columns if any(suffix in col for suffix in
                     ['_global_', '_corr_'])]
        if stat_cols:
            X_dict['statistical'] = X[stat_cols]
        else:
            # 如果没有专门的统计特征，使用部分时序特征
            X_dict['statistical'] = X[time_cols[:len(time_cols)//2]]

        return X_dict

    def evaluate_model(self):
        """评估模型"""
        if self.fusion_strategy == 'early':
            self.metrics = self.model.evaluate(self.X_test, self.y_test)

        elif self.fusion_strategy == 'late':
            X_dict = self._split_features_by_modality(self.X_test)
            self.metrics = self.model.evaluate(X_dict, self.y_test)

        elif self.fusion_strategy == 'hybrid':
            X_dict = self._split_features_by_modality(self.X_test)
            metrics = self.model.evaluate(X_dict, self.y_test)
            if metrics:
                self.metrics = metrics

        print(f"\n[模型性能]")
        print(f"  R² 得分: {self.metrics['R²']:.3f}")
        print(f"  MAE: {self.metrics['MAE']:.2f} kg")
        print(f"  RMSE: {self.metrics['RMSE']:.2f} kg")

        return self.metrics

    def get_feature_importance(self):
        """获取特征重要性（仅早期融合）"""
        if self.fusion_strategy == 'early' and hasattr(self.model.model, 'feature_importances_'):
            importances = pd.DataFrame({
                '特征': self.X_train.columns,
                '重要性': self.model.model.feature_importances_
            }).sort_values('重要性', ascending=False)

            return importances
        return None


def run_multimodal_fusion(df, fusion_strategy='early', model_type='random_forest'):
    """
    运行多模态融合

    Args:
        df: 数据DataFrame
        fusion_strategy: 融合策略 ('early', 'late', 'hybrid')
        model_type: 模型类型 ('random_forest', 'gradient_boosting')

    Returns:
        predictor: 训练好的预测器
    """
    predictor = MultiModalPredictor(df, fusion_strategy=fusion_strategy)

    # 准备数据
    predictor.prepare_data(include_image=False)  # 暂时不包含图像

    # 训练模型
    predictor.train_model(model_type=model_type)

    # 评估模型
    metrics = predictor.evaluate_model()

    # 特征重要性
    if fusion_strategy == 'early':
        importance = predictor.get_feature_importance()
        if importance is not None:
            print(f"\n[特征重要性 TOP 10]")
            for idx, row in importance.head(10).iterrows():
                print(f"  {idx+1}. {row['特征']}: {row['重要性']:.4f}")

    print("\n[OK] 多模态融合完成！")
    print("\n" + "=" * 70)

    return predictor


if __name__ == '__main__':
    # 测试
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from config import DATA_DIR
    from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer

    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        loader = ShrimpDataLoader(data_files[0])
        df = loader.load()

        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()

        # 运行多模态融合
        print("\n选择融合策略:")
        print("  1. 早期融合 (Early Fusion)")
        print("  2. 晚期融合 (Late Fusion)")
        print("  3. 混合融合 (Hybrid Fusion)")

        choice = input("\n请选择 (1-3): ").strip()

        strategy_map = {'1': 'early', '2': 'late', '3': 'hybrid'}
        strategy = strategy_map.get(choice, 'early')

        predictor = run_multimodal_fusion(df_enhanced, fusion_strategy=strategy)
    else:
        print("未找到数据文件")
