#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度学习预测模块
包含 LSTM、GRU 等时序预测模型
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# 设置设备
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class TimeSeriesDataset(Dataset):
    """时序数据集"""

    def __init__(self, data, seq_len=7):
        """
        Args:
            data: DataFrame 或 numpy array
            seq_len: 序列长度
        """
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)


class LSTMModel(nn.Module):
    """LSTM 时序预测模型"""

    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        """
        Args:
            input_size: 输入特征数
            hidden_size: LSTM 隐藏层大小
            num_layers: LSTM 层数
            dropout: Dropout 比例
        """
        super(LSTMModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM 层
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # 全连接层
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, (h_n, c_n) = self.lstm(x)

        # 取最后一个时间步的输出
        last_out = lstm_out[:, -1, :]

        # 全连接层
        output = self.fc(last_out)
        return output


class GRUModel(nn.Module):
    """GRU 时序预测模型"""

    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        """
        Args:
            input_size: 输入特征数
            hidden_size: GRU 隐藏层大小
            num_layers: GRU 层数
            dropout: Dropout 比例
        """
        super(GRUModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # GRU 层
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )

        # 全连接层
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        gru_out, h_n = self.gru(x)

        # 取最后一个时间步的输出
        last_out = gru_out[:, -1, :]

        # 全连接层
        output = self.fc(last_out)
        return output


class TransformerModel(nn.Module):
    """Transformer 时序预测模型"""

    def __init__(self, input_size, num_heads=4, num_layers=2, dropout=0.2):
        """
        Args:
            input_size: 输入特征数
            num_heads: 多头注意力头数
            num_layers: Transformer 层数
            dropout: Dropout 比例
        """
        super(TransformerModel, self).__init__()

        # 输入嵌入
        self.input_embedding = nn.Linear(input_size, 64)

        # Positional encoding
        self.pos_encoder = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )

        # Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64,
            nhead=num_heads,
            dim_feedforward=256,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # 全连接层
        self.fc = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)

        # 输入嵌入
        x = self.input_embedding(x)

        # 位置编码
        x = self.pos_encoder(x)

        # Transformer 编码
        x = x.permute(1, 0, 2)  # (seq_len, batch, d_model)
        transformer_out = self.transformer_encoder(x)
        transformer_out = transformer_out.permute(1, 0, 2)  # (batch, seq_len, d_model)

        # 取最后一个时间步
        last_out = transformer_out[:, -1, :]

        # 全连接层
        output = self.fc(last_out)
        return output


class DeepLearningPredictor:
    """深度学习预测器"""

    def __init__(self, df, model_type='lstm'):
        """
        Args:
            df: 数据 DataFrame
            model_type: 模型类型 ('lstm', 'gru', 'transformer')
        """
        self.df = df
        self.model_type = model_type
        self.scaler = MinMaxScaler()
        self.device = DEVICE

        # 准备数据
        self._prepare_data()

        # 创建模型
        self._create_model()

    def _prepare_data(self):
        """准备数据"""
        # 选择特征列
        feature_cols = [col for col in self.df.columns if col not in [
            '日期', '预警等级', '压力原因', '环境压力指数'
        ] and self.df[col].dtype in ['float64', 'int64']]

        # 归一化
        data_scaled = self.scaler.fit_transform(self.df[feature_cols])

        # 创建数据集
        self.dataset = TimeSeriesDataset(data_scaled, seq_len=7)

        # 数据加载器
        self.dataloader = DataLoader(
            self.dataset,
            batch_size=16,
            shuffle=False
        )

        self.feature_cols = feature_cols
        self.input_size = len(feature_cols)

    def _create_model(self):
        """创建模型"""
        if self.model_type == 'lstm':
            self.model = LSTMModel(self.input_size).to(self.device)
        elif self.model_type == 'gru':
            self.model = GRUModel(self.input_size).to(self.device)
        elif self.model_type == 'transformer':
            self.model = TransformerModel(self.input_size).to(self.device)
        else:
            raise ValueError(f"未知模型类型: {self.model_type}")

    def train(self, epochs=100, lr=0.001):
        """训练模型"""
        print(f"\n[{self.model_type.upper()}] 开始训练深度学习模型...")
        print(f"  设备: {self.device}")
        print(f"  参数: epochs={epochs}, lr={lr}")

        # 优化器和损失函数
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()

        # 训练
        self.model.train()
        losses = []

        for epoch in range(epochs):
            epoch_loss = 0
            for x_batch, y_batch in self.dataloader:
                x_batch = x_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                # 前向传播
                optimizer.zero_grad()
                outputs = self.model(x_batch)
                loss = criterion(outputs.squeeze(), y_batch.squeeze())

                # 反向传播
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(self.dataloader)
            losses.append(avg_loss)

            if (epoch + 1) % 20 == 0:
                print(f"  Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

        print(f"  [OK] 训练完成")

        return losses

    def predict(self):
        """预测"""
        self.model.eval()

        predictions = []
        actuals = []

        with torch.no_grad():
            for x_batch, y_batch in self.dataloader:
                x_batch = x_batch.to(self.device)

                outputs = self.model(x_batch)
                predictions.extend(outputs.squeeze().cpu().numpy())
                actuals.extend(y_batch.squeeze().cpu().numpy())

        # 反归一化
        predictions = np.array(predictions).reshape(-1, 1)
        actuals = np.array(actuals).reshape(-1, 1)

        # 反向变换（只对目标变量）
        predictions_full = np.zeros((len(predictions), len(self.feature_cols)))
        actuals_full = np.zeros((len(actuals), len(self.feature_cols)))

        # 假设最后一列是目标变量
        predictions_full[:, -1] = predictions[:, 0]
        actuals_full[:, -1] = actuals[:, 0]

        predictions_inv = self.scaler.inverse_transform(predictions_full)
        actuals_inv = self.scaler.inverse_transform(actuals_full)

        self.y_pred = predictions_inv[:, -1]
        self.y_true = actuals_inv[:, -1]

        # 计算指标
        self.r2 = r2_score(self.y_true, self.y_pred)
        self.mae = mean_absolute_error(self.y_true, self.y_pred)
        self.rmse = np.sqrt(mean_squared_error(self.y_true, self.y_pred))

        return self.y_pred

    def get_metrics(self):
        """获取评估指标"""
        return {
            'R²': self.r2,
            'MAE': self.mae,
            'RMSE': self.rmse
        }

    def save_model(self, path):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'model_type': self.model_type,
            'input_size': self.input_size,
            'feature_cols': self.feature_cols
        }, path)

    def load_model(self, path):
        """加载模型"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.model_type = checkpoint['model_type']
        self.input_size = checkpoint['input_size']
        self.feature_cols = checkpoint['feature_cols']


def run_deep_learning_prediction(df, model_type='lstm'):
    """
    运行深度学习预测

    Args:
        df: 数据 DataFrame
        model_type: 模型类型 ('lstm', 'gru', 'transformer')

    Returns:
        predictor: 训练好的预测器
    """
    print(f"\n{'='*70}")
    print(f"深度学习预测系统 - {model_type.upper()}")
    print(f"{'='*70}")

    try:
        predictor = DeepLearningPredictor(df, model_type)
        predictor.train(epochs=50)

        print(f"\n[预测] 开始预测...")
        y_pred = predictor.predict()

        metrics = predictor.get_metrics()

        print(f"\n[评估指标]")
        print(f"  R² 得分: {metrics['R²']:.3f}")
        print(f"  MAE: {metrics['MAE']:.2f} kg")
        print(f"  RMSE: {metrics['RMSE']:.2f} kg")

        print(f"\n[OK] {model_type.upper()} 模型训练完成！")

        return predictor

    except Exception as e:
        print(f"\n[错误] 深度学习模型训练失败: {e}")
        print("  提示: 可能需要安装 PyTorch")
        return None


if __name__ == '__main__':
    # 测试
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import DATA_DIR

    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))
    if data_files:
        import pandas as pd
        df = pd.read_excel(data_files[0])

        # 测试 LSTM
        run_deep_learning_prediction(df, 'lstm')
    else:
        print("未找到数据文件")
