# 高级机器学习模块使用指南

本文档详细介绍对虾养殖数据分析系统中新增的高级机器学习功能。

## 📚 目录

1. [深度学习模型](#深度学习模型)
2. [时序预测模型](#时序预测模型)
3. [模型融合](#模型融合)
4. [超参数优化](#超参数优化)
5. [模型解释](#模型解释)
6. [安装依赖](#安装依赖)
7. [使用示例](#使用示例)

---

## 🧠 深度学习模型

### 概述

深度学习模型使用神经网络进行时序预测，能够捕捉复杂的非线性关系和时间依赖性。

### 支持的模型

#### 1. LSTM (长短期记忆网络)

- **特点**: 能够学习长期依赖关系
- **适用场景**: 时序数据中有长期趋势
- **架构**: 2层LSTM + Dropout + 全连接层
- **默认参数**:
  - hidden_size: 64
  - num_layers: 2
  - dropout: 0.2
  - batch_size: 16
  - epochs: 50

#### 2. GRU (门控循环单元)

- **特点**: 比LSTM更轻量，训练更快
- **适用场景**: 需要快速训练的场景
- **架构**: 2层GRU + Dropout + 全连接层
- **默认参数**: 同LSTM

#### 3. Transformer

- **特点**: 使用自注意力机制
- **适用场景**: 复杂的时序模式
- **架构**: Input Embedding + Positional Encoding + Transformer Encoder
- **默认参数**:
  - num_heads: 4
  - num_layers: 2
  - dropout: 0.2

### 使用方法

#### Python API

```python
from src.deep_learning_models import run_deep_learning_prediction

# 使用 LSTM
predictor = run_deep_learning_prediction(df, 'lstm')

# 使用 GRU
predictor = run_deep_learning_prediction(df, 'gru')

# 使用 Transformer
predictor = run_deep_learning_prediction(df, 'transformer')
```

#### 命令行

```bash
python run.py
# 选择选项 10-12
```

#### Streamlit Dashboard

导航到 "🧠 高级模型" → "深度学习" 标签页

### 输出结果

- **评估指标**: R²、MAE、RMSE
- **预测可视化**: 预测值 vs 实际值对比图
- **模型保存**: 可保存训练好的模型（.pt文件）

---

## ⏰ 时序预测模型

### 概述

时序模型专门用于基于历史数据预测未来趋势，考虑时间序列的特殊性质。

### 支持的模型

#### 1. Prophet (Facebook)

- **特点**: 自动处理季节性、趋势和节假日
- **适用场景**: 有明显季节性或趋势的数据
- **参数**:
  - yearly_seasonality: True
  - weekly_seasonality: False
  - daily_seasonality: False
  - changepoint_prior_scale: 0.05

#### 2. ARIMA (自回归积分滑动平均)

- **特点**: 经典的时序预测方法
- **适用场景**: 平稳或差分后平稳的时序数据
- **参数**: 自动选择最优参数（p, d, q）

#### 3. 时序集成

- **特点**: 结合Prophet和ARIMA的优势
- **策略**: 简单平均集成

### 使用方法

#### Python API

```python
from src.time_series_models import run_time_series_prediction

# 运行时序预测（包含Prophet和ARIMA）
ensemble = run_time_series_prediction(df)

# 预测未来7天
predictions = ensemble.predict_all(periods=7)

# 获取所有模型的指标
metrics = ensemble.get_all_metrics()
```

#### 命令行

```bash
python run.py
# 选择选项 13-14
```

#### Streamlit Dashboard

导航到 "🧠 高级模型" → "时序模型" 标签页

### 输出结果

- **预测结果**: 未来N天的预测值和置信区间
- **模型对比**: Prophet vs ARIMA性能对比
- **可视化**: 历史数据 + 预测趋势图

---

## 🔀 模型融合

### 概述

模型融合结合多个基学习器的预测结果，通过加权平均提高预测准确性和稳定性。

### 融合的模型

1. **Random Forest (RF)**: 随机森林
2. **XGBoost (XGB)**: 极端梯度提升
3. **LightGBM (LGBM)**: 轻量级梯度提升
4. **Gradient Boosting (GB)**: 梯度提升
5. **Ridge Regression**: 岭回归

### 融合策略

- **权重计算**: 基于各模型在测试集上的R²得分
- **预测方法**: 加权平均

$$
\text{Prediction} = \sum_{i=1}^{n} w_i \cdot \hat{y}_i
$$

其中 $w_i$ 是第 $i$ 个模型的权重，$\hat{y}_i$ 是其预测值。

### 使用方法

#### Python API

```python
from src.model_ensemble import run_model_ensemble

# 运行模型融合
ensemble = run_model_ensemble(df)

# 获取集成预测
y_pred = ensemble.predict()

# 获取评估指标
metrics = ensemble.get_metrics()
print(f"R²: {metrics['R²']:.3f}")
print(f"MAE: {metrics['MAE']:.2f}")
print(f"RMSE: {metrics['RMSE']:.2f}")

# 获取特征重要性
importance_df = ensemble.get_feature_importance()
```

#### 命令行

```bash
python run.py
# 选择选项 15
```

#### Streamlit Dashboard

导航到 "🧠 高级模型" → "模型融合" 标签页

### 输出结果

- **各模型性能**: RF、XGB、LGBM、GB、Ridge的R²得分
- **权重分配**: 各模型在集成中的权重
- **集成性能**: 最终集成模型的R²、MAE、RMSE
- **特征重要性**: 基于Random Forest的特征重要性排名

---

## 🎯 超参数优化

### 概述

使用Optuna自动搜索最优模型参数，提高模型性能。

### 优化的参数

| 参数 | 搜索范围 | 说明 |
|------|----------|------|
| n_estimators | 50-300 | 树的数量 |
| max_depth | 3-20 | 最大深度 |
| min_samples_split | 2-20 | 最小分割样本数 |
| min_samples_leaf | 1-10 | 最小叶子节点样本数 |
| max_features | 0.3-1.0 | 特征采样比例 |

### 优化算法

- **采样器**: TPESampler (Tree-structured Parzen Estimator)
- **剪枝器**: MedianPruner (提前终止表现差的试验)
- **优化目标**: 最大化5折交叉验证的R²得分

### 使用方法

#### Python API

```python
from src.hyperparameter_tuning import run_hyperparameter_tuning

# 运行超参数优化
model, r2 = run_hyperparameter_tuning(df)

print(f"优化后 R²: {r2:.3f}")
```

#### 命令行

```bash
python run.py
# 选择选项 16
```

#### Streamlit Dashboard

导航到 "🧠 高级模型" → "超参数优化" 标签页

### 输出结果

- **最佳参数**: 最优的超参数组合
- **最佳得分**: 优化后的R²得分
- **优化历史**: 每次试验的得分变化

---

## 📊 模型解释 (SHAP)

### 概述

使用SHAP (SHapley Additive exPlanations) 分析模型如何做出预测决策，提供可解释性。

### SHAP 方法

- **TreeExplainer**: 用于树模型（Random Forest、XGBoost等）
- **KernelExplainer**: 用于非树模型

### 可视化类型

1. **摘要图 (Summary Plot)**: 显示所有特征的重要性
2. **依赖图 (Dependence Plot)**: 显示单个特征的影响
3. **力图 (Force Plot)**: 显示单个样本的预测解释

### 使用方法

#### Python API

```python
from src.model_explainer import explain_model

# 解释模型
explainer = explain_model(
    model=predictor.model,
    X=X.values,
    feature_names=feature_cols,
    output_dir='reports/shap_analysis'
)

# 获取Top特征
top_features = explainer.get_top_features(n=10)
```

#### 命令行

```bash
python run.py
# 选择选项 17
```

#### Streamlit Dashboard

导航到 "🧠 高级模型" → "模型解释" 标签页

### 输出结果

- **特征重要性排名**: SHAP值排序的特征列表
- **可视化图表**:
  - `shap_summary.png`: 特征重要性摘要图
  - `shap_dependence.png`: 特征依赖图
  - `shap_force.png`: 预测力图

---

## 📦 安装依赖

### 基础依赖

```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

### 深度学习

```bash
pip install torch>=2.0.0 torchvision>=0.15.0
```

### 时序模型

```bash
# Prophet
pip install prophet>=1.1.0

# ARIMA
pip install pmdarima statsmodels>=0.14.0
```

### 模型融合

```bash
pip install xgboost lightgbm
```

### 超参数优化

```bash
pip install optuna>=3.0.0
```

### 模型解释

```bash
pip install shap>=0.42.0
```

### 一键安装所有依赖

```bash
pip install -r config/requirements.txt
```

---

## 💡 使用示例

### 示例1: 完整的深度学习流程

```python
import pandas as pd
from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer
from src.deep_learning_models import run_deep_learning_prediction

# 1. 加载数据
loader = ShrimpDataLoader('data/shrimp_data.xlsx')
df = loader.load()

# 2. 特征工程
fe = FeatureEngineer(df)
df_enhanced = fe.run_all()

# 3. 训练LSTM模型
predictor = run_deep_learning_prediction(df_enhanced, 'lstm')

# 4. 获取预测和指标
metrics = predictor.get_metrics()
print(f"R²: {metrics['R²']:.3f}")
```

### 示例2: 模型融合对比

```python
from src.model_ensemble import run_model_ensemble
from src.hyperparameter_tuning import run_hyperparameter_tuning

# 模型融合
ensemble = run_model_ensemble(df_enhanced)
print(f"融合模型 R²: {ensemble.get_metrics()['R²']:.3f}")

# 超参数优化
model, r2 = run_hyperparameter_tuning(df_enhanced)
print(f"优化模型 R²: {r2:.3f}")
```

### 示例3: 时序预测

```python
from src.time_series_models import run_time_series_prediction

# 运行时序预测
ensemble = run_time_series_prediction(df)

# 预测未来7天
predictions = ensemble.predict_all(periods=7)
print("未来7天预测:")
print(predictions['集成'])
```

### 示例4: 模型解释

```python
from src.model_explainer import explain_model
from src.professional_analyzer import YieldPredictor

# 训练模型
predictor = YieldPredictor(df_enhanced)
predictor.run_all()

# 解释模型
explainer = explain_model(
    predictor.model,
    X.values,
    feature_cols,
    'reports/shap_analysis'
)

# 查看Top特征
top_features = explainer.get_top_features(10)
print(top_features)
```

---

## 🎯 最佳实践

### 1. 选择合适的模型

- **数据量小** (< 100): 使用传统机器学习或Prophet
- **数据量中等** (100-1000): 使用XGBoost、LightGBM
- **数据量大** (> 1000): 使用深度学习模型

### 2. 模型组合策略

- **提高稳定性**: 使用模型融合
- **提高准确性**: 使用超参数优化
- **理解模型**: 使用SHAP解释

### 3. 调试技巧

- 从小规模数据开始测试
- 监控训练/验证损失
- 检查特征重要性是否合理
- 可视化预测结果

### 4. 性能优化

- 使用GPU加速深度学习训练
- 并行运行多个模型
- 缓存预处理结果
- 使用更小的batch size

---

## 📖 参考资料

### 深度学习

- [PyTorch 官方文档](https://pytorch.org/docs/)
- [LSTM 论文](https://www.bioinf.jku.at/publications/older/2604.pdf)
- [Transformer 论文](https://arxiv.org/abs/1706.03762)

### 时序模型

- [Prophet 文档](https://facebook.github.io/prophet/)
- [ARIMA 教程](https://otexts.com/fpp2/arima.html)

### 模型解释

- [SHAP 文档](https://shap.readthedocs.io/)
- [SHAP 论文](https://arxiv.org/abs/1705.07874)

### 超参数优化

- [Optuna 文档](https://optuna.readthedocs.io/)
- [TPE 算法](https://papers.nips.cc/paper/2011/file/86e8f7ab32cfd12577bc2619bc635690-Paper.pdf)

---

## ❓ 常见问题

### Q1: GPU不可用怎么办？

A: LSTM/GRU/Transformer会自动使用CPU，只是训练会慢一些。

### Q2: Prophet安装失败？

A: Windows上可能需要安装C++编译工具，或使用conda安装：
```bash
conda install -c conda-forge prophet
```

### Q3: 内存不足？

A: 减小batch_size或使用更少的训练数据。

### Q4: 如何保存训练好的模型？

A: 深度学习模型使用`predictor.save_model(path)`，其他模型使用joblib。

---

**SmartShrimp Team · 2026年3月**
