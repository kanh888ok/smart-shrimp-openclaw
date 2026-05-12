#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 交互式报告生成器
使用 Plotly 生成交互式图表，导出为单个 HTML 文件
"""

import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 导入项目配置
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer, YieldPredictor
from config import DATA_DIR, REPORTS_DIR

class HTMLReportGenerator:
    """HTML 报告生成器"""

    def __init__(self, df, df_enhanced, predictor):
        """初始化"""
        self.df = df
        self.df_enhanced = df_enhanced
        self.predictor = predictor
        self.figures = {}

    def create_fcr_chart(self):
        """创建 FCR 趋势图"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=self.df_enhanced['日期'],
            y=self.df_enhanced['FCR'],
            mode='lines+markers',
            name='FCR',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=10),
            hovertemplate='<b>%{x}</b><br>FCR: %{y:.2f}<extra></extra>'
        ))

        # 添加参考线
        fig.add_hline(
            y=1.5,
            line_dash="dash",
            line_color="green",
            annotation_text="优秀水平 (FCR<1.5)",
            annotation_position="right"
        )

        fig.add_hline(
            y=2.0,
            line_dash="dash",
            line_color="orange",
            annotation_text="警戒水平 (FCR>2.0)",
            annotation_position="right"
        )

        fig.update_layout(
            title=dict(
                text='<b>FCR (饲料转化率) 趋势分析</b>',
                font=dict(size=20)
            ),
            xaxis_title='日期',
            yaxis_title='FCR',
            hovermode='x unified',
            template='plotly_white',
            height=500,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        return fig

    def create_sgr_chart(self):
        """创建 SGR 趋势图"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('日 SGR', '累积 SGR'),
            vertical_spacing=0.15
        )

        # 日 SGR
        fig.add_trace(
            go.Scatter(
                x=self.df_enhanced['日期'],
                y=self.df_enhanced['SGR'],
                mode='lines+markers',
                name='日 SGR',
                line=dict(color='#2ecc71', width=2),
                marker=dict(size=8),
                hovertemplate='日期: %{x}<br>SGR: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )

        # 累积 SGR
        if 'SGR_累积' in self.df_enhanced.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df_enhanced['日期'],
                    y=self.df_enhanced['SGR_累积'],
                    mode='lines+markers',
                    name='累积 SGR',
                    line=dict(color='#e74c3c', width=2),
                    marker=dict(size=8),
                    hovertemplate='日期: %{x}<br>累积 SGR: %{y:.2f}%<extra></extra>'
                ),
                row=2, col=1
            )

        fig.update_layout(
            title=dict(
                text='<b>SGR (特定生长率) 分析</b>',
                font=dict(size=20)
            ),
            template='plotly_white',
            height=700,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=True
        )

        return fig

    def create_environmental_chart(self):
        """创建环境参数图"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('水温 (°C)', '盐度 (ppt)', 'pH 值', '溶解氧 (mg/L)'),
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )

        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']

        for idx, (col, color) in enumerate([
            ('水温 (°C)', colors[0]),
            ('盐度 (ppt)', colors[1]),
            ('pH 值', colors[2]),
            ('溶解氧 (mg/L)', colors[3])
        ]):
            row = idx // 2 + 1
            col_pos = idx % 2 + 1

            fig.add_trace(
                go.Scatter(
                    x=self.df_enhanced['日期'],
                    y=self.df_enhanced[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                    fill='tozeroy' if col == '溶解氧 (mg/L)' else None,
                    hovertemplate=f'%{{x}}<br>{col}: %{{y:.2f}}<extra></extra>'
                ),
                row=row, col=col_pos
            )

        fig.update_layout(
            title=dict(
                text='<b>环境参数监测</b>',
                font=dict(size=20)
            ),
            template='plotly_white',
            height=700,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False
        )

        return fig

    def create_alert_timeline(self):
        """创建预警时间线"""
        if '预警等级' not in self.df_enhanced.columns:
            return None

        # 预警等级映射
        alert_order = {'红色预警': 4, '橙色预警': 3, '黄色预警': 2, '正常': 1}
        self.df_enhanced['预警等级_数值'] = self.df_enhanced['预警等级'].map(alert_order)

        fig = go.Figure()

        alert_colors = {
            '红色预警': 'red',
            '橙色预警': 'orange',
            '黄色预警': 'yellow',
            '正常': 'green'
        }

        for level in ['红色预警', '橙色预警', '黄色预警', '正常']:
            data = self.df_enhanced[self.df_enhanced['预警等级'] == level]
            if len(data) > 0:
                fig.add_trace(go.Scatter(
                    x=data['日期'],
                    y=data['预警等级_数值'],
                    mode='markers',
                    name=level,
                    marker=dict(
                        size=15,
                        color=alert_colors[level],
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate=f'%{{x}}<br>{level}<extra></extra>'
                ))

        fig.update_layout(
            title=dict(
                text='<b>环境预警时间线</b>',
                font=dict(size=20)
            ),
            xaxis_title='日期',
            yaxis_title='预警等级',
            template='plotly_white',
            height=500,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        # 自定义Y轴标签
        fig.update_yaxes(
            tickmode='array',
            tickvals=[1, 2, 3, 4],
            ticktext=['正常', '黄色', '橙色', '红色']
        )

        return fig

    def create_correlation_heatmap(self):
        """创建相关性热力图"""
        numeric_cols = self.df_enhanced.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['预警等级', '环境压力指数', '预警等级_数值']][:10]

        corr_matrix = self.df_enhanced[numeric_cols].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 11},
            colorbar=dict(
                title='相关系数',
                titleside='right',
                tickmode='array',
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['-1.0', '-0.5', '0.0', '0.5', '1.0']
            ),
            hovertemplate='变量1: %{x}<br>变量2: %{y}<br>相关系数: %{z:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='<b>变量相关性分析</b>',
                font=dict(size=20)
            ),
            template='plotly_white',
            height=700,
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis={'side': 'bottom'}
        )

        return fig

    def create_feature_importance(self):
        """创建特征重要性图"""
        if not self.predictor or not hasattr(self.predictor, 'feature_importance'):
            return None

        df_importance = self.predictor.feature_importance.head(10)

        fig = go.Figure(go.Bar(
            x=df_importance['重要性'],
            y=df_importance['特征'],
            orientation='h',
            marker=dict(
                color=df_importance['重要性'],
                colorscale='Blues',
                reversescale=True
            ),
            text=df_importance['重要性'].apply(lambda x: f'{x:.1%}'),
            textposition='outside',
            hovertemplate='%{y}<br>重要性: %{x:.3f}<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text='<b>产量预测特征重要性 (TOP 10)</b>',
                font=dict(size=20)
            ),
            xaxis_title='重要性',
            yaxis_title='特征',
            template='plotly_white',
            height=600,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        return fig

    def create_prediction_comparison(self):
        """创建预测vs实际图"""
        if not self.predictor:
            return None

        fig = go.Figure()

        # 预测值
        fig.add_trace(go.Scatter(
            x=self.predictor.y_test,
            y=self.predictor.y_pred,
            mode='markers',
            name='预测值',
            marker=dict(size=12, color='blue', opacity=0.6),
            hovertemplate='实际: %{x:.1f} kg<br>预测: %{y:.1f} kg<extra></extra>'
        ))

        # 完美预测线
        min_val = min(self.predictor.y_test.min(), self.predictor.y_pred.min())
        max_val = max(self.predictor.y_test.max(), self.predictor.y_pred.max())

        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='完美预测线',
            line=dict(color='red', dash='dash', width=2),
            hoverinfo='skip'
        ))

        fig.update_layout(
            title=dict(
                text='<b>产量预测：预测值 vs 实际值</b>',
                font=dict(size=20)
            ),
            xaxis_title='实际产量 (kg)',
            yaxis_title='预测产量 (kg)',
            template='plotly_white',
            height=500,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        return fig

    def create_kpi_cards(self):
        """创建 KPI 卡片"""
        # 计算关键指标
        fcr_avg = self.df_enhanced['FCR'].mean()
        fcr_min = self.df_enhanced['FCR'].min()
        fcr_max = self.df_enhanced['FCR'].max()

        sgr_avg = self.df_enhanced['SGR'].mean()
        survival_rate = self.df_enhanced['存活率 (%)'].iloc[-1] if len(self.df_enhanced) > 0 else 0

        # 预警统计
        if '预警等级' in self.df_enhanced.columns:
            alert_counts = self.df_enhanced['预警等级'].value_counts()
            red_alerts = alert_counts.get('红色预警', 0)
            normal_days = alert_counts.get('正常', 0)
        else:
            red_alerts = 0
            normal_days = len(self.df_enhanced)

        # 模型性能
        if self.predictor:
            r2_score = self.predictor.metrics.get('R²', 0)
            mae = self.predictor.metrics.get('MAE', 0)
        else:
            r2_score = 0
            mae = 0

        kpi_html = f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <!-- FCR 卡片 -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">平均 FCR (饲料转化率)</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{fcr_avg:.2f}</div>
                <div style="font-size: 12px; opacity: 0.8;">范围: {fcr_min:.2f} ~ {fcr_max:.2f}</div>
            </div>

            <!-- SGR 卡片 -->
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">平均 SGR (生长率)</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{sgr_avg:.2f}%</div>
                <div style="font-size: 12px; opacity: 0.8;">日均增长</div>
            </div>

            <!-- 存活率卡片 -->
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">当前存活率</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{survival_rate:.1f}%</div>
                <div style="font-size: 12px; opacity: 0.8;">养殖健康状况</div>
            </div>

            <!-- 模型性能卡片 -->
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">模型 R² 得分</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{r2_score:.3f}</div>
                <div style="font-size: 12px; opacity: 0.8;">MAE: {mae:.1f} kg</div>
            </div>

            <!-- 红色预警卡片 -->
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">红色预警天数</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{red_alerts}</div>
                <div style="font-size: 12px; opacity: 0.8;">需要特别注意</div>
            </div>

            <!-- 正常天数卡片 -->
            <div style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">正常天数</div>
                <div style="font-size: 36px; font-weight: bold; margin-bottom: 5px;">{normal_days}</div>
                <div style="font-size: 12px; opacity: 0.8;">环境稳定</div>
            </div>
        </div>
        """

        return kpi_html

    def generate_html_report(self, output_path):
        """生成完整的 HTML 报告"""
        print("\n正在生成交互式 HTML 报告...")

        # 生成所有图表
        print("  生成图表...")

        figures = {
            'fcr': self.create_fcr_chart(),
            'sgr': self.create_sgr_chart(),
            'environmental': self.create_environmental_chart(),
            'alert': self.create_alert_timeline(),
            'correlation': self.create_correlation_heatmap(),
            'feature_importance': self.create_feature_importance(),
            'prediction': self.create_prediction_comparison(),
        }

        # KPI 卡片
        kpi_html = self.create_kpi_cards()

        # 生成 HTML
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对虾养殖数据分析报告 - SmartShrimp Team</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 48px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header p {{
            font-size: 18px;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section-title {{
            font-size: 28px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .chart-container {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>🦞 对虾养殖数据分析报告</h1>
            <p>SmartShrimp Team · 2026年3月</p>
        </div>

        <!-- 内容 -->
        <div class="content">

            <!-- KPI 卡片 -->
            {kpi_html}

            <!-- FCR 趋势 -->
            <div class="section">
                <h2 class="section-title">📊 FCR (饲料转化率) 趋势分析</h2>
                <div class="chart-container" id="fcr-chart"></div>
            </div>

            <!-- SGR 分析 -->
            <div class="section">
                <h2 class="section-title">📈 SGR (特定生长率) 分析</h2>
                <div class="chart-container" id="sgr-chart"></div>
            </div>

            <!-- 环境参数 -->
            <div class="section">
                <h2 class="section-title">🌡️ 环境参数监测</h2>
                <div class="chart-container" id="environmental-chart"></div>
            </div>

            <!-- 预警时间线 -->
            <div class="section">
                <h2 class="section-title">🚨 环境预警时间线</h2>
                <div class="chart-container" id="alert-chart"></div>
            </div>

            <!-- 相关性分析 -->
            <div class="section">
                <h2 class="section-title">🔗 变量相关性分析</h2>
                <div class="chart-container" id="correlation-chart"></div>
            </div>

            <!-- 特征重要性 -->
            <div class="section">
                <h2 class="section-title">🎯 产量预测特征重要性</h2>
                <div class="chart-container" id="feature-chart"></div>
            </div>

            <!-- 预测对比 -->
            <div class="section">
                <h2 class="section-title">🤖 产量预测：预测值 vs 实际值</h2>
                <div class="chart-container" id="prediction-chart"></div>
            </div>

        </div>

        <!-- 页脚 -->
        <div class="footer">
            <p>© 2026 SmartShrimp Team · 用数据驱动对虾养殖智能化</p>
            <p style="margin-top: 10px; font-size: 14px;">报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // 渲染所有图表
        Plotly.newPlot('fcr-chart', {figures['fcr'].to_json(full_html=False)});
        Plotly.newPlot('sgr-chart', {figures['sgr'].to_json(full_html=False)});
        Plotly.newPlot('environmental-chart', {figures['environmental'].to_json(full_html=False)});
        """

        # 添加条件图表
        if figures['alert']:
            html_template += f"""Plotly.newPlot('alert-chart', {figures['alert'].to_json(full_html=False)});"""
        else:
            html_template += """document.getElementById('alert-chart').innerHTML = '<p style="text-align: center; color: #999;">暂无预警数据</p>';"""

        html_template += f"""
        Plotly.newPlot('correlation-chart', {figures['correlation'].to_json(full_html=False)});
        """

        if figures['feature_importance']:
            html_template += f"""Plotly.newPlot('feature-chart', {figures['feature_importance'].to_json(full_html=False)});"""
        else:
            html_template += """document.getElementById('feature-chart').innerHTML = '<p style="text-align: center; color: #999;">暂无模型数据</p>';"""

        if figures['prediction']:
            html_template += f"""Plotly.newPlot('prediction-chart', {figures['prediction'].to_json(full_html=False)});"""
        else:
            html_template += """document.getElementById('prediction-chart').innerHTML = '<p style="text-align: center; color: #999;">暂无预测数据</p>';"""

        html_template += """
    </script>
</body>
</html>
        """

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"  ✅ 已保存: {output_path.name}")

        return output_path

def run_html_report_generation():
    """运行 HTML 报告生成"""
    print("\n" + "=" * 70)
    print("HTML 交互式报告生成系统")
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

    # 训练模型
    predictor = YieldPredictor(df_enhanced)
    predictor.run_all()

    # 生成报告
    generator = HTMLReportGenerator(df, df_enhanced, predictor)

    output_path = REPORTS_DIR / 'interactive_report.html'
    generator.generate_html_report(output_path)

    print("\n" + "=" * 70)
    print("✅ HTML 报告生成完成！")
    print("=" * 70)
    print(f"\n📁 报告位置: {output_path}")
    print(f"\n💡 使用方法:")
    print(f"   1. 双击打开 HTML 文件")
    print(f"   2. 在浏览器中查看交互式图表")
    print(f"   3. 可以缩放、悬停查看详情")
    print("=" * 70)

if __name__ == '__main__':
    run_html_report_generation()
