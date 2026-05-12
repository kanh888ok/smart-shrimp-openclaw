#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时序预测模块
包含 Prophet、ARIMA 等时序模型
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


class ProphetPredictor:
    """Prophet 时序预测器"""

    def __init__(self, df):
        """
        Args:
            df: 数据 DataFrame，必须包含 '日期' 和 '预计产量 (kg)' 列
        """
        self.df = df.copy()
        self.model = None

    def prepare_data(self):
        """准备数据"""
        # Prophet 需要特定格式
        self.prophet_df = self.df[['日期', '预计产量 (kg)']].copy()
        self.prophet_df.columns = ['ds', 'y']

        # 确保日期格式正确
        if not pd.api.types.is_datetime64_any_dtype(self.prophet_df['ds']):
            self.prophet_df['ds'] = pd.to_datetime(self.prophet_df['ds'])

    def fit(self):
        """训练模型"""
        print("\n[Prophet] 训练时序预测模型...")
        try:
            from prophet import Prophet

            self.model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,  # 数据范围小于1周
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10
            )

            self.model.fit(self.prophet_df)
            print("  [OK] Prophet 模型训练完成")
            return True

        except ImportError:
            print("  [警告] Prophet 未安装，跳过此模型")
            print("  安装命令: pip install prophet")
            return False

    def predict(self, periods=7):
        """预测未来值"""
        if self.model is None:
            print("  [错误] 模型未训练")
            return None

        # 创建未来日期
        future = self.model.make_future_dataframe(periods=periods)
        forecast = self.model.predict(future)

        # 只返回预测的 future 部分
        forecast_future = forecast.tail(periods)

        return forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    def get_metrics(self, test_df=None):
        """获取评估指标"""
        if test_df is None:
            # 使用训练数据评估
            forecast = self.model.predict(self.model.make_future_dataframe(periods=0))

            # 计算指标
            y_true = self.prophet_df['y'].values
            y_pred = forecast['yhat'].values[:len(y_true)]

            from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

            r2 = r2_score(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))

            return {
                'R²': r2,
                'MAE': mae,
                'RMSE': rmse
            }
        return {}


class ARIMAPredictor:
    """ARIMA 时序预测器"""

    def __init__(self, df):
        """
        Args:
            df: 数据 DataFrame
        """
        self.df = df.copy()
        self.model = None

    def prepare_data(self, target_col='预计产量 (kg)'):
        """准备数据"""
        self.target_col = target_col
        self.data = self.df[target_col].values

        # 检查数据稳定性
        self.is_stationary = self._check_stationarity(self.data)

    def _check_stationarity(self, data):
        """检查数据是否平稳（简单版本）"""
        # 计算 rolling mean 和 std
        rolling_mean = pd.Series(data).rolling(window=7).mean()
        rolling_std = pd.Series(data).rolling(window=7).std()

        # 简单判断：如果 rolling mean 和 std 相对稳定，则认为平稳
        mean_change = rolling_mean.std() / rolling_mean.mean()
        std_change = rolling_std.std() / rolling_std.mean()

        return mean_change < 0.1 and std_change < 0.1

    def fit(self):
        """训练模型"""
        print("\n[ARIMA] 训练时序预测模型...")
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from pmdarima import auto_arima

            # 使用 auto_arima 自动选择最优参数
            print("  [提示] 使用 auto_arima 自动选择参数...")
            self.model = auto_arima(
                self.data,
                seasonal=False,  # 数据量小，不考虑季节性
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore'
            )

            print(f"  [OK] ARIMA{self.model.order} 模型训练完成")
            return True

        except ImportError:
            print("  [警告] pmdarima 或 statsmodels 未安装")
            print("  安装命令: pip install pmdarima statsmodels")
            return False

    def predict(self, periods=7):
        """预测未来值"""
        if self.model is None:
            print("  [错误] 模型未训练")
            return None

        # 预测
        forecast, conf_int = self.model.predict(n_periods=periods, return_conf_int=True)

        # 创建结果 DataFrame
        last_date = pd.to_datetime(self.df['日期'].iloc[-1])
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq='D')

        result_df = pd.DataFrame({
            '日期': forecast_dates,
            '预测值': forecast,
            '下界': conf_int[:, 0],
            '上界': conf_int[:, 1]
        })

        return result_df

    def get_metrics(self):
        """获取评估指标"""
        if self.model is None:
            return {}

        # 残差分析
        residuals = self.model.resid()

        from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

        # 预测训练数据
        predictions = self.model.predict_in_sample()

        y_true = self.data[1:]  # ARIMA 会损失第一个值
        y_pred = predictions[1:]

        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))

        return {
            'R²': r2,
            'MAE': mae,
            'RMSE': rmse,
            'AIC': self.model.aic(),
            'BIC': self.model.bic()
        }


class TimeSeriesEnsemble:
    """时序模型集成"""

    def __init__(self, df):
        """
        Args:
            df: 数据 DataFrame
        """
        self.df = df
        self.prophet_predictor = ProphetPredictor(df)
        self.arima_predictor = ARIMAPredictor(df)

    def fit_all(self):
        """训练所有模型"""
        print("\n" + "=" * 70)
        print("时序模型集成系统")
        print("=" * 70)

        # 训练 Prophet
        prophet_ok = self.prophet_predictor.prepare_data()
        if prophet_ok:
            prophet_ok = self.prophet_predictor.fit()

        # 训练 ARIMA
        arima_ok = self.arima_predictor.prepare_data()
        if arima_ok:
            arima_ok = self.arima_predictor.fit()

        return prophet_ok, arima_ok

    def predict_all(self, periods=7):
        """所有模型预测"""
        results = {}

        # Prophet 预测
        if self.prophet_predictor.model:
            prophet_pred = self.prophet_predictor.predict(periods)
            if prophet_pred is not None:
                results['Prophet'] = prophet_pred['yhat'].values

        # ARIMA 预测
        if self.arima_predictor.model:
            arima_pred = self.arima_predictor.predict(periods)
            if arima_pred is not None:
                results['ARIMA'] = arima_pred['预测值'].values

        # 简单平均集成
        if len(results) > 0:
            all_predictions = np.array(list(results.values()))
            ensemble_pred = np.mean(all_predictions, axis=0)

            # 添加集成结果
            results['集成'] = ensemble_pred

        return results

    def get_all_metrics(self):
        """获取所有模型的指标"""
        metrics = {}

        if self.prophet_predictor.model:
            metrics['Prophet'] = self.prophet_predictor.get_metrics()

        if self.arima_predictor.model:
            metrics['ARIMA'] = self.arima_predictor.get_metrics()

        return metrics

    def generate_report(self):
        """生成对比报告"""
        print("\n" + "=" * 70)
        print("时序模型对比报告")
        print("=" * 70)

        metrics = self.get_all_metrics()

        if not metrics:
            print("  [警告] 没有可用的模型指标")
            return

        # 打印对比
        print(f"\n{'模型':<15} {'R²':>10} {'MAE':>10} {'RMSE':>10}")
        print("-" * 50)

        for model_name, model_metrics in metrics.items():
            if 'R²' in model_metrics:
                print(f"{model_name:<15} {model_metrics['R²']:>10.3f} "
                      f"{model_metrics['MAE']:>10.2f} {model_metrics['RMSE']:>10.2f}")

        print("\n" + "=" * 70)


def run_time_series_prediction(df):
    """
    运行时序预测

    Args:
        df: 数据 DataFrame

    Returns:
        ensemble: 时序集成模型
    """
    ensemble = TimeSeriesEnsemble(df)
    prophet_ok, arima_ok = ensemble.fit_all()

    if prophet_ok or arima_ok:
        # 预测
        predictions = ensemble.predict_all(periods=7)

        # 生成报告
        ensemble.generate_report()

        return ensemble

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

        run_time_series_prediction(df)
    else:
        print("未找到数据文件")
