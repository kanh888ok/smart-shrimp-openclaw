#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移学习模块
使用预训练的时间序列模型进行微调，提升预测性能
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 尝试导入transformers库
try:
    from transformers import TimeSeriesTransformerModel, TimeSeriesTransformerConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("提示: 未安装transformers库。安装命令: pip install transformers")

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class TimeSeriesPretrainedModel(nn.Module):
    """
    预训练时间序列Transformer模型

    基于Transformer架构的时间序列预测模型
    支持迁移学习：在大规模数据上预训练，在特定任务上微调
    """

    def __init__(self, input_dim: int = 8, d_model: int = 64, nhead: int = 4,
                 num_layers: int = 2, dropout: float = 0.1, seq_length: int = 7):
        """
        Args:
            input_dim: 输入特征维度
            d_model: Transformer隐藏层维度
            nhead: 多头注意力头数
            num_layers: Transformer层数
            dropout: Dropout率
            seq_length: 输入序列长度
        """
        super(TimeSeriesPretrainedModel, self).__init__()

        self.input_dim = input_dim
        self.d_model = d_model
        self.seq_length = seq_length

        # 输入嵌入层
        self.embedding = nn.Linear(input_dim, d_model)

        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # 输出层
        self.fc_out = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1)
        )

    def forward(self, x):
        """
        前向传播

        Args:
            x: 输入张量 (batch_size, seq_length, input_dim)

        Returns:
            预测值 (batch_size, 1)
        """
        # 嵌入
        x = self.embedding(x)  # (batch_size, seq_length, d_model)

        # 位置编码
        x = self.pos_encoder(x)

        # Transformer编码
        x = self.transformer_encoder(x)  # (batch_size, seq_length, d_model)

        # 全局平均池化
        x = x.mean(dim=1)  # (batch_size, d_model)

        # 输出
        out = self.fc_out(x)  # (batch_size, 1)

        return out


class PositionalEncoding(nn.Module):
    """
    位置编码模块
    为时间序列添加位置信息
    """

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 100):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # 创建位置编码矩阵
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() *
                             (-np.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x):
        """
        Args:
            x: (batch_size, seq_length, d_model)
        Returns:
            添加位置编码后的x
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransferLearningPredictor:
    """
    迁移学习预测器

    使用预训练模型并在对虾养殖数据上微调
    """

    def __init__(self, input_features: List[str], target_feature: str = '预计产量 (kg)',
                 seq_length: int = 7, d_model: int = 64, num_layers: int = 2):
        """
        Args:
            input_features: 输入特征列表
            target_feature: 目标特征
            seq_length: 输入序列长度
            d_model: 模型维度
            num_layers: Transformer层数
        """
        self.input_features = input_features
        self.target_feature = target_feature
        self.seq_length = seq_length
        self.input_dim = len(input_features)

        # 初始化模型
        self.model = TimeSeriesPretrainedModel(
            input_dim=self.input_dim,
            d_model=d_model,
            nhead=4,
            num_layers=num_layers,
            dropout=0.1,
            seq_length=seq_length
        )

        # 数据标准化
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()

        # 设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

        # 训练状态
        self.is_fitted = False
        self.is_finetuned = False

    def _prepare_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        准备时间序列数据

        Args:
            df: 数据框

        Returns:
            X: (n_samples, seq_length, n_features)
            y: (n_samples,)
        """
        # 确保所有特征都存在
        available_features = [f for f in self.input_features if f in df.columns]
        if len(available_features) < 3:
            raise ValueError(f"可用特征不足，至少需要3个，当前只有{len(available_features)}个")

        # 提取数据
        X_data = df[available_features].values
        y_data = df[self.target_feature].values if self.target_feature in df.columns else None

        # 创建序列
        X_sequences = []
        y_sequences = []

        for i in range(len(df) - self.seq_length):
            X_sequences.append(X_data[i:i + self.seq_length])
            if y_data is not None:
                y_sequences.append(y_data[i + self.seq_length])

        X = np.array(X_sequences)
        y = np.array(y_sequences) if y_sequences else None

        return X, y

    def pretrain(self, df: pd.DataFrame, epochs: int = 50, batch_size: int = 16,
                 learning_rate: float = 0.001, verbose: bool = True):
        """
        预训练模型（在大规模数据上）

        Args:
            df: 预训练数据
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率
            verbose: 是否显示详细信息
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"迁移学习 - 预训练阶段")
            print(f"{'='*70}")
            print(f"数据量: {len(df)} 条")
            print(f"序列长度: {self.seq_length}")
            print(f"特征维度: {self.input_dim}")
            print(f"设备: {self.device}")

        # 准备数据
        X, y = self._prepare_sequences(df)

        if y is None:
            raise ValueError("预训练数据必须包含目标变量")

        # 标准化
        X_scaled = self.scaler_X.fit_transform(X.reshape(-1, X.shape[-1]))
        X_scaled = X_scaled.reshape(X.shape)

        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

        # 转换为张量
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        y_tensor = torch.FloatTensor(y_scaled).to(self.device)

        # 创建数据加载器
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = torch.utils.data.DataLoader(
            dataset, batch_size=batch_size, shuffle=True
        )

        # 优化器和损失函数
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        # 训练
        self.model.train()
        losses = []

        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in dataloader:
                # 前向传播
                optimizer.zero_grad()
                predictions = self.model(batch_X).squeeze()

                # 计算损失
                loss = criterion(predictions, batch_y)

                # 反向传播
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)

            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")

        # 保存预训练权重
        self.pretrained_state = self.model.state_dict().copy()
        self.is_fitted = True

        if verbose:
            print(f"\n✅ 预训练完成!")
            print(f"   最终损失: {losses[-1]:.6f}")
            print(f"   改进: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")
            print(f"{'='*70}\n")

    def finetune(self, df: pd.DataFrame, epochs: int = 30, batch_size: int = 8,
                 learning_rate: float = 0.0001, verbose: bool = True):
        """
        微调模型（在特定任务上）

        Args:
            df: 微调数据
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率（通常比预训练小）
            verbose: 是否显示详细信息
        """
        if not self.is_fitted:
            raise RuntimeError("模型未预训练，请先调用pretrain()")

        if verbose:
            print(f"\n{'='*70}")
            print(f"迁移学习 - 微调阶段")
            print(f"{'='*70}")
            print(f"数据量: {len(df)} 条")
            print(f"学习率: {learning_rate}（比预训练小10倍）")
            print(f"设备: {self.device}")

        # 加载预训练权重
        self.model.load_state_dict(self.pretrained_state)

        # 准备数据
        X, y = self._prepare_sequences(df)

        if y is None:
            raise ValueError("微调数据必须包含目标变量")

        # 标准化
        X_scaled = self.scaler_X.transform(X.reshape(-1, X.shape[-1]))
        X_scaled = X_scaled.reshape(X.shape)

        y_scaled = self.scaler_y.transform(y.reshape(-1, 1)).flatten()

        # 转换为张量
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)
        y_tensor = torch.FloatTensor(y_scaled).to(self.device)

        # 创建数据加载器
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = torch.utils.data.DataLoader(
            dataset, batch_size=batch_size, shuffle=True
        )

        # 优化器和损失函数（使用更小的学习率）
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        # 微调（只训练最后几层）
        # 冻结前面的层
        for name, param in self.model.named_parameters():
            if 'transformer_encoder' in name:
                param.requires_grad = False

        # 训练
        self.model.train()
        losses = []

        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in dataloader:
                # 前向传播
                optimizer.zero_grad()
                predictions = self.model(batch_X).squeeze()

                # 计算损失
                loss = criterion(predictions, batch_y)

                # 反向传播
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)

            if verbose and (epoch + 1) % 5 == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")

        # 解冻所有层
        for param in self.model.parameters():
            param.requires_grad = True

        self.is_finetuned = True

        if verbose:
            print(f"\n✅ 微调完成!")
            print(f"   最终损失: {losses[-1]:.6f}")
            print(f"   改进: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")
            print(f"{'='*70}\n")

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        预测

        Args:
            df: 输入数据

        Returns:
            预测值
        """
        if not self.is_finetuned:
            raise RuntimeError("模型未微调，请先调用finetune()")

        # 准备数据
        X, _ = self._prepare_sequences(df)

        # 标准化
        X_scaled = self.scaler_X.transform(X.reshape(-1, X.shape[-1]))
        X_scaled = X_scaled.reshape(X.shape)

        # 转换为张量
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        # 预测
        self.model.eval()
        with torch.no_grad():
            predictions_scaled = self.model(X_tensor).squeeze().cpu().numpy()

        # 反标准化
        predictions = self.scaler_y.inverse_transform(predictions_scaled.reshape(-1, 1)).flatten()

        return predictions

    def evaluate(self, df: pd.DataFrame) -> Dict:
        """
        评估模型

        Args:
            df: 测试数据

        Returns:
            评估指标
        """
        # 准备数据
        X, y_true = self._prepare_sequences(df)

        if y_true is None:
            raise ValueError("测试数据必须包含目标变量")

        # 预测
        y_pred = self.predict(df)

        # 计算指标
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))

        results = {
            'r2': r2,
            'mae': mae,
            'rmse': rmse,
            'predictions': y_pred,
            'true_values': y_true
        }

        print(f"\n{'='*70}")
        print(f"模型评估结果")
        print(f"{'='*70}")
        print(f"R² 得分: {r2:.4f}")
        print(f"MAE: {mae:.2f} kg")
        print(f"RMSE: {rmse:.2f} kg")
        print(f"{'='*70}\n")

        return results

    def save_model(self, path: Union[str, Path]):
        """
        保存模型

        Args:
            path: 保存路径
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'input_features': self.input_features,
            'target_feature': self.target_feature,
            'seq_length': self.seq_length,
            'is_fitted': self.is_fitted,
            'is_finetuned': self.is_finetuned
        }

        torch.save(checkpoint, path)
        print(f"模型已保存到: {path}")

    def load_model(self, path: Union[str, Path]):
        """
        加载模型

        Args:
            path: 模型路径
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")

        checkpoint = torch.load(path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler_X = checkpoint['scaler_X']
        self.scaler_y = checkpoint['scaler_y']
        self.input_features = checkpoint['input_features']
        self.target_feature = checkpoint['target_feature']
        self.seq_length = checkpoint['seq_length']
        self.is_fitted = checkpoint['is_fitted']
        self.is_finetuned = checkpoint['is_finetuned']

        print(f"模型已从 {path} 加载")


def create_synthetic_pretrain_data(n_samples: int = 1000, noise: float = 0.1) -> pd.DataFrame:
    """
    创建合成预训练数据

    模拟大规模的养殖数据，用于预训练

    Args:
        n_samples: 样本数量
        noise: 噪声水平

    Returns:
        合成数据框
    """
    np.random.seed(42)

    # 生成时间序列
    t = np.linspace(0, 4 * np.pi, n_samples)

    # 生成特征（模拟养殖数据）
    data = {
        '水温 (°C)': 28 + 2 * np.sin(t) + np.random.normal(0, 0.5, n_samples),
        '盐度 (ppt)': 20 + np.random.normal(0, 2, n_samples),
        'pH 值': 8.0 + 0.3 * np.sin(t / 2) + np.random.normal(0, 0.1, n_samples),
        '溶解氧': 6 + np.sin(t) + np.random.normal(0, 0.5, n_samples),
        '氨氮': 0.5 + 0.2 * np.cos(t) + np.random.normal(0, 0.1, n_samples),
        '亚硝酸盐': 0.1 + np.random.normal(0, 0.05, n_samples),
        '投喂量': 3 + np.sin(t / 3) + np.random.normal(0, 0.3, n_samples),
        '虾体重 (g)': 10 + 0.5 * t + np.random.normal(0, 1, n_samples)
    }

    # 生成目标变量（产量）- 与特征相关
    # 基础产量
    base_yield = 100 + 10 * t

    # 各因素的影响
    temp_effect = (data['水温 (°C)'] - 28) * 2
    do_effect = (data['溶解氧'] - 6) * 5
    feed_effect = data['投喂量'] * 8

    # 总产量
    yield_kg = base_yield + temp_effect + do_effect + feed_effect
    yield_kg += np.random.normal(0, noise * 10, n_samples)  # 添加噪声

    data['预计产量'] = yield_kg

    df = pd.DataFrame(data)

    return df


# 便捷函数
def run_transfer_learning(df_train: pd.DataFrame, df_finetune: pd.DataFrame,
                         input_features: List[str], verbose: bool = True) -> TransferLearningPredictor:
    """
    运行完整的迁移学习流程

    Args:
        df_train: 预训练数据（可以是合成的大规模数据）
        df_finetune: 微调数据（真实的对虾养殖数据）
        input_features: 输入特征列表
        verbose: 是否显示详细信息

    Returns:
        训练好的模型
    """
    print(f"\n{'='*70}")
    print(f"迁移学习完整流程")
    print(f"{'='*70}")

    # 创建模型
    model = TransferLearningPredictor(
        input_features=input_features,
        target_feature='预计产量',
        seq_length=7,
        d_model=64,
        num_layers=2
    )

    # 阶段1: 预训练
    print(f"\n【阶段1/2】预训练")
    print(f"数据量: {len(df_train)} 条")
    model.pretrain(df_train, epochs=50, batch_size=32, learning_rate=0.001, verbose=verbose)

    # 阶段2: 微调
    print(f"\n【阶段2/2】微调")
    print(f"数据量: {len(df_finetune)} 条")
    model.finetune(df_finetune, epochs=30, batch_size=8, learning_rate=0.0001, verbose=verbose)

    # 评估
    print(f"\n【评估】")
    model.evaluate(df_finetune)

    return model


