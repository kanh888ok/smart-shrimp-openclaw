#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智虾系统 - Web Dashboard
基于 Streamlit 的交互式界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.professional_analyzer import ShrimpDataLoader, FeatureEngineer, YieldPredictor
from config import DATA_DIR, REPORTS_DIR

# 页面配置
st.set_page_config(
    page_title="对虾养殖分析系统",
    page_icon="🦞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1f77b4 0%, #17becf 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .danger-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 核心函数 ====================

@st.cache_data
def load_data(uploaded_file):
    """加载数据（缓存）"""
    try:
        loader = ShrimpDataLoader(uploaded_file)
        df = loader.load()

        # 数据验证
        from src.data_validator import DataValidator
        validator = DataValidator(df)
        valid, errors, warnings = validator.validate()

        if not valid:
            st.error("❌ 数据验证失败！")
            for error in errors:
                st.error(f"- {error}")
            st.error("\n请修复以上错误后重新上传数据文件")
            st.stop()

        if warnings:
            st.warning(f"⚠️ 发现 {len(warnings)} 个警告：")
            for warning in warnings[:3]:  # 只显示前3个
                st.warning(f"- {warning}")
            if len(warnings) > 3:
                st.info(f"...还有 {len(warnings)-3} 个警告")

        return df
    except Exception as e:
        st.error(f"数据加载失败：{e}")
        return None

@st.cache_data
def process_data(df):
    """特征工程（缓存）"""
    try:
        fe = FeatureEngineer(df)
        df_enhanced = fe.run_all()
        return df_enhanced
    except Exception as e:
        st.error(f"特征工程失败：{e}")
        return df

@st.cache_data
def train_model(df_enhanced):
    """训练模型（缓存）"""
    try:
        predictor = YieldPredictor(df_enhanced)
        predictor.run_all()
        return predictor
    except Exception as e:
        st.error(f"模型训练失败：{e}")
        return None

def create_metric_card(title, value, delta=None, suffix=""):
    """创建指标卡片"""
    delta_str = f"{delta}" if delta is not None else ""
    return f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #666;">{title}</div>
        <div style="font-size: 2rem; font-weight: bold; color: #1f77b4; margin: 0.5rem 0;">
            {value}{suffix}
        </div>
        {f'<div style="font-size: 0.8rem; color: {"green" if delta > 0 else "red"};">{delta_str}</div>' if delta else ''}
    </div>
    """

# ==================== 侧边栏 ====================

def sidebar():
    """侧边栏"""
    st.sidebar.title("🦞 控制面板")
    st.sidebar.markdown("---")

    # 数据上传
    st.sidebar.subheader("📂 数据上传")

    # 检查是否有本地数据
    data_files = list(DATA_DIR.glob('*.xlsx')) + list(DATA_DIR.glob('*.csv'))

    upload_option = st.sidebar.radio(
        "选择数据源",
        ["上传文件", "使用示例数据"]
    )

    if upload_option == "上传文件":
        uploaded_file = st.sidebar.file_uploader(
            "选择数据文件",
            type=['xlsx', 'csv'],
            help="支持 .xlsx 和 .csv 格式"
        )
        return uploaded_file
    else:
        if data_files:
            selected_file = st.sidebar.selectbox(
                "选择示例数据",
                options=data_files,
                format_func=lambda x: x.name
            )
            return selected_file
        else:
            st.sidebar.warning("未找到示例数据")
            return None

# ==================== 主页 ====================

def main_page(df, df_enhanced, predictor):
    """主页"""
    st.markdown('<h1 class="main-header">🦞 智虾系统</h1>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align: center; color: #666; margin-bottom: 2rem;">
        SmartShrimp Team · 2026年3月
    </div>
    """, unsafe_allow_html=True)

    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fcr_avg = df_enhanced['FCR'].mean()
        st.markdown(create_metric_card("平均 FCR", f"{fcr_avg:.2f}"), unsafe_allow_html=True)

    with col2:
        sgr_avg = df_enhanced['SGR'].mean()
        st.markdown(create_metric_card("平均 SGR", f"{sgr_avg:.2f}", "%"), unsafe_allow_html=True)

    with col3:
        do_avg = df_enhanced['溶解氧 (mg/L)'].mean()
        st.markdown(create_metric_card("平均溶解氧", f"{do_avg:.2f}", "mg/L"), unsafe_allow_html=True)

    with col4:
        survival_rate = df_enhanced['存活率 (%)'].iloc[-1] if len(df_enhanced) > 0 else 0
        st.markdown(create_metric_card("当前存活率", f"{survival_rate:.1f}", "%"), unsafe_allow_html=True)

    st.markdown("---")

    # 环境预警
    st.subheader("🚨 环境预警")

    if '预警等级' in df_enhanced.columns:
        alert_counts = df_enhanced['预警等级'].value_counts()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            red_count = alert_counts.get('红色预警', 0)
            st.markdown(f"""
            <div class="danger-box">
                <div style="font-size: 1.5rem; font-weight: bold;">{red_count}</div>
                <div>红色预警</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            orange_count = alert_counts.get('橙色预警', 0)
            st.markdown(f"""
            <div class="warning-box">
                <div style="font-size: 1.5rem; font-weight: bold;">{orange_count}</div>
                <div>橙色预警</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            yellow_count = alert_counts.get('黄色预警', 0)
            st.markdown(f"""
            <div style="background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem;">
                <div style="font-size: 1.5rem; font-weight: bold;">{yellow_count}</div>
                <div>黄色预警</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            normal_count = alert_counts.get('正常', 0)
            st.markdown(f"""
            <div class="success-box">
                <div style="font-size: 1.5rem; font-weight: bold;">{normal_count}</div>
                <div>正常</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 快速操作
    st.subheader("⚡ 快速分析")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 生成完整分析报告", use_container_width=True):
            st.info("请使用侧边栏导航到'报告生成'页面")

    with col2:
        if st.button("🔍 查看模型评估", use_container_width=True):
            st.info("请使用侧边栏导航到'模型评估'页面")

    with col3:
        if st.button("📈 查看详细图表", use_container_width=True):
            st.info("请使用侧边栏导航到'数据分析'页面")

# ==================== 数据分析页面 ====================

def data_analysis_page(df, df_enhanced):
    """数据分析页面"""
    st.title("📊 数据分析")

    # 标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "FCR 趋势", "SGR 分析", "环境参数", "相关性分析", "预警分析"
    ])

    with tab1:
        st.subheader("FCR (饲料转化率) 趋势分析")

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_enhanced['日期'],
                y=df_enhanced['FCR'],
                mode='lines+markers',
                name='FCR',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))

            fig.add_hline(y=1.5, line_dash="dash", line_color="green",
                         annotation_text="优秀水平 (FCR<1.5)")
            fig.add_hline(y=2.0, line_dash="dash", line_color="orange",
                         annotation_text="警戒水平 (FCR>2.0)")

            fig.update_layout(
                title="FCR 趋势图",
                xaxis_title="日期",
                yaxis_title="FCR",
                hovermode='x unified',
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.metric("平均 FCR", f"{df_enhanced['FCR'].mean():.2f}")
            st.metric("最小 FCR", f"{df_enhanced['FCR'].min():.2f}")
            st.metric("最大 FCR", f"{df_enhanced['FCR'].max():.2f}")
            st.metric("标准差", f"{df_enhanced['FCR'].std():.2f}")

    with tab2:
        st.subheader("SGR (特定生长率) 分析")

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('日 SGR', '累积 SGR'),
            vertical_spacing=0.15
        )

        fig.add_trace(
            go.Scatter(x=df_enhanced['日期'], y=df_enhanced['SGR'],
                      mode='lines+markers', name='日 SGR',
                      line=dict(color='#2ecc71', width=2)),
            row=1, col=1
        )

        if 'SGR_累积' in df_enhanced.columns:
            fig.add_trace(
                go.Scatter(x=df_enhanced['日期'], y=df_enhanced['SGR_累积'],
                          mode='lines+markers', name='累积 SGR',
                          line=dict(color='#e74c3c', width=2)),
                row=2, col=1
            )

        fig.update_layout(template='plotly_white', height=600)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("环境参数分析")

        param = st.selectbox(
            "选择参数",
            ['水温 (°C)', '盐度 (ppt)', 'pH 值', '溶解氧 (mg/L)']
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_enhanced['日期'],
            y=df_enhanced[param],
            mode='lines+markers',
            name=param,
            line=dict(width=2),
            marker=dict(size=6),
            fill='tozeroy' if param == '溶解氧 (mg/L)' else None
        ))

        fig.update_layout(
            title=f"{param} 趋势",
            xaxis_title="日期",
            yaxis_title=param,
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("相关性分析")

        numeric_cols = df_enhanced.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['预警等级', '环境压力指数']][:10]

        corr_matrix = df_enhanced[numeric_cols].corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="相关系数")
        ))

        fig.update_layout(
            title="变量相关性热力图",
            template='plotly_white',
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("环境预警分析")

        if '预警等级' in df_enhanced.columns:
            # 预警时间线
            alert_order = {'红色预警': 4, '橙色预警': 3, '黄色预警': 2, '正常': 1}
            df_enhanced['预警等级_数值'] = df_enhanced['预警等级'].map(alert_order)

            fig = go.Figure()

            for level, color in [
                ('红色预警', 'red'),
                ('橙色预警', 'orange'),
                ('黄色预警', 'yellow'),
                ('正常', 'green')
            ]:
                data = df_enhanced[df_enhanced['预警等级'] == level]
                if len(data) > 0:
                    fig.add_trace(go.Scatter(
                        x=data['日期'],
                        y=data['预警等级_数值'],
                        mode='markers',
                        name=level,
                        marker=dict(size=12, color=color, line=dict(width=2, color='white'))
                    ))

            fig.update_layout(
                title="环境预警时间线",
                xaxis_title="日期",
                yaxis_title="预警等级",
                template='plotly_white',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # 预警详情
            st.subheader("预警详情")

            for level in ['红色预警', '橙色预警', '黄色预警']:
                alerts = df_enhanced[df_enhanced['预警等级'] == level]
                if len(alerts) > 0:
                    with st.expander(f"{level} ({len(alerts)} 天)"):
                        for idx, row in alerts.iterrows():
                            date_str = row['日期'].strftime('%Y-%m-%d') if pd.notna(row.get('日期')) else f"第{idx+1}天"
                            reason = row.get('压力原因', '数据异常')
                            st.write(f"**{date_str}**: {reason}")

# ==================== 模型评估页面 ====================

def model_evaluation_page(df_enhanced, predictor):
    """模型评估页面"""
    st.title("🤖 模型评估")

    if not predictor or not predictor.model:
        st.warning("模型未训练，请先运行完整分析")
        return

    # 标签页
    tab1, tab2, tab3 = st.tabs(["模型性能", "特征重要性", "预测分析"])

    with tab1:
        st.subheader("模型性能指标")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("R² 得分", f"{predictor.metrics['R²']:.3f}")

        with col2:
            st.metric("MAE", f"{predictor.metrics['MAE']:.2f} kg")

        with col3:
            st.metric("RMSE", f"{predictor.metrics['RMSE']:.2f} kg")

        with col4:
            st.metric("训练样本数", f"{len(predictor.X)}")

        st.markdown("---")

        st.subheader("预测 vs 实际")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=predictor.y_test,
            y=predictor.y_pred,
            mode='markers',
            name='预测值',
            marker=dict(size=10, color='blue', opacity=0.6)
        ))

        fig.add_trace(go.Scatter(
            x=predictor.y_test,
            y=predictor.y_test,
            mode='lines',
            name='完美预测线',
            line=dict(color='red', dash='dash')
        ))

        fig.update_layout(
            title="预测值 vs 实际值",
            xaxis_title="实际产量 (kg)",
            yaxis_title="预测产量 (kg)",
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("特征重要性")

        if predictor.feature_importance is not None:
            fig = go.Figure(go.Bar(
                x=predictor.feature_importance['重要性'].head(10),
                y=predictor.feature_importance['特征'].head(10),
                orientation='h',
                marker=dict(color='steelblue')
            ))

            fig.update_layout(
                title="TOP 10 特征重要性",
                xaxis_title="重要性",
                yaxis_title="特征",
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)

            # 特征重要性表格
            st.subheader("特征重要性详情")
            st.dataframe(
                predictor.feature_importance.head(10),
                use_container_width=True,
                hide_index=True
            )

    with tab3:
        st.subheader("产量预测")

        st.info("💡 提示：可以调整下方参数，查看预测结果")

        col1, col2, col3 = st.columns(3)

        with col1:
            temp = st.slider("水温 (°C)", 20.0, 35.0, 28.0, 0.1)

        with col2:
            do = st.slider("溶解氧 (mg/L)", 3.0, 10.0, 6.5, 0.1)

        with col3:
            ph = st.slider("pH 值", 7.0, 9.0, 8.0, 0.1)

        if st.button("🔮 预测产量", use_container_width=True):
            st.success(f"预计产量：{1500:.0f} kg")
            st.info("（此为演示值，实际预测需要完整的特征数据）")

# ==================== 报告生成页面 ====================

def report_generation_page(df, df_enhanced, predictor):
    """报告生成页面"""
    st.title("📄 报告生成")

    st.info("💡 提示：生成报告需要先运行完整分析")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Word 报告")

        st.markdown("""
        **包含内容**：
        - 数据概览
        - FCR/SGR 分析
        - 环境预警
        - 模型预测结果
        - 决策建议
        """)

        if st.button("📝 生成 Word 报告", use_container_width=True):
            with st.spinner("正在生成 Word 报告..."):
                try:
                    from src.professional_analyzer import Visualizer, ReportGenerator

                    visualizer = Visualizer(df_enhanced, REPORTS_DIR / 'figures_dashboard')
                    visualizer.generate_all(predictor)

                    output_path = REPORTS_DIR / 'analysis_report_dashboard.docx'
                    report_gen = ReportGenerator(df_enhanced, predictor, visualizer, output_path)
                    report_gen.generate()

                    st.success(f"✅ 报告已生成：{output_path}")

                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label="⬇️ 下载报告",
                            data=f,
                            file_name='analysis_report.docx',
                            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        )
                except Exception as e:
                    st.error(f"生成失败：{e}")

    with col2:
        st.subheader("模型评估报告")

        st.markdown("""
        **包含内容**：
        - 交叉验证结果
        - 残差分析
        - 特征重要性
        - 稳定性测试
        """)

        if st.button("📊 生成评估报告", use_container_width=True):
            with st.spinner("正在生成评估报告..."):
                try:
                    from src.model_evaluation import run_evaluation
                    run_evaluation()

                    report_path = REPORTS_DIR / 'model_evaluation.txt'
                    if report_path.exists():
                        st.success(f"✅ 报告已生成：{report_path}")

                        with open(report_path, 'r', encoding='utf-8') as f:
                            st.text(f.read())
                except Exception as e:
                    st.error(f"生成失败：{e}")

# ==================== 高级模型页面 ====================

def advanced_models_page(df, df_enhanced):
    """高级模型页面"""
    st.title("🧠 高级机器学习模型")

    # 标签页
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "深度学习", "时序模型", "模型融合", "超参数优化", "模型解释", "模型对比", "多模态融合"
    ])

    with tab1:
        st.subheader("🧠 深度学习模型")

        st.info("💡 深度学习模型使用神经网络进行时序预测，能够捕捉复杂的非线性关系")

        model_type = st.selectbox(
            "选择模型类型",
            ["LSTM", "GRU", "Transformer"],
            help="LSTM: 长短期记忆网络\nGRU: 门控循环单元\nTransformer: 自注意力机制"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            epochs = st.slider("训练轮数", 10, 200, 50, 10)

        with col2:
            lr = st.slider("学习率", 0.0001, 0.01, 0.001, 0.0001, format="%.4f")

        with col3:
            batch_size = st.selectbox("批次大小", [8, 16, 32, 64], index=1)

        if st.button(f"🚀 训练 {model_type} 模型", use_container_width=True):
            try:
                from src.advanced.deep_learning_models import run_deep_learning_prediction

                with st.spinner(f"正在训练 {model_type} 模型，这可能需要几分钟..."):
                    predictor = run_deep_learning_prediction(df_enhanced, model_type.lower())

                    if predictor:
                        st.success(f"✅ {model_type} 模型训练完成！")

                        # 显示结果
                        metrics = predictor.get_metrics()

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("R² 得分", f"{metrics['R²']:.3f}")
                        with col2:
                            st.metric("MAE", f"{metrics['MAE']:.2f} kg")
                        with col3:
                            st.metric("RMSE", f"{metrics['RMSE']:.2f} kg")

                        # 预测可视化
                        if hasattr(predictor, 'y_true') and hasattr(predictor, 'y_pred'):
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=list(range(len(predictor.y_true))),
                                y=predictor.y_true,
                                mode='lines',
                                name='实际值',
                                line=dict(color='blue', width=2)
                            ))
                            fig.add_trace(go.Scatter(
                                x=list(range(len(predictor.y_pred))),
                                y=predictor.y_pred,
                                mode='lines',
                                name='预测值',
                                line=dict(color='red', width=2, dash='dash')
                            ))

                            fig.update_layout(
                                title=f"{model_type} 预测结果",
                                xaxis_title="样本",
                                yaxis_title="产量 (kg)",
                                template='plotly_white',
                                height=400
                            )

                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 训练失败：{e}")
                st.info("提示：请确保已安装 PyTorch (pip install torch)")

    with tab2:
        st.subheader("⏰ 时序预测模型")

        st.info("💡 时序模型专门用于基于历史数据预测未来趋势")

        ts_model = st.selectbox(
            "选择时序模型",
            ["Prophet", "ARIMA", "集成预测"],
            help="Prophet: Facebook 的时序预测工具\nARIMA: 自回归积分滑动平均\n集成预测: 结合多个模型"
        )

        periods = st.slider("预测天数", 1, 30, 7, 1)

        if st.button(f"🔮 运行 {ts_model} 预测", use_container_width=True):
            try:
                from src.advanced.time_series_models import run_time_series_prediction

                with st.spinner(f"正在运行 {ts_model} 预测..."):
                    ensemble = run_time_series_prediction(df)

                    if ensemble:
                        st.success(f"✅ {ts_model} 预测完成！")

                        # 获取预测结果
                        predictions = ensemble.predict_all(periods)

                        # 显示预测
                        if ts_model == "集成预测" or ts_model in predictions:
                            pred_data = predictions.get(ts_model, predictions.get('集成', None))

                            if pred_data is not None:
                                # 创建预测图
                                last_date = pd.to_datetime(df['日期'].iloc[-1])
                                forecast_dates = pd.date_range(
                                    start=last_date + pd.Timedelta(days=1),
                                    periods=periods,
                                    freq='D'
                                )

                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=pd.to_datetime(df['日期']),
                                    y=df['预计产量 (kg)'],
                                    mode='lines',
                                    name='历史数据',
                                    line=dict(color='blue', width=2)
                                ))
                                fig.add_trace(go.Scatter(
                                    x=forecast_dates,
                                    y=pred_data[:periods],
                                    mode='lines+markers',
                                    name='预测数据',
                                    line=dict(color='red', width=2, dash='dash')
                                ))

                                fig.update_layout(
                                    title=f"{ts_model} - 未来 {periods} 天产量预测",
                                    xaxis_title="日期",
                                    yaxis_title="产量 (kg)",
                                    template='plotly_white',
                                    height=400
                                )

                                st.plotly_chart(fig, use_container_width=True)

                        # 显示所有模型指标对比
                        metrics = ensemble.get_all_metrics()
                        if metrics:
                            st.subheader("模型性能对比")

                            metrics_df = pd.DataFrame(metrics).T
                            st.dataframe(metrics_df, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 预测失败：{e}")
                st.info("提示：请确保已安装 prophet 或 pmdarima (pip install prophet pmdarima)")

    with tab3:
        st.subheader("🔀 模型融合")

        st.info("💡 模型融合结合多个模型的预测结果，提高预测准确性和稳定性")

        st.markdown("""
        **融合策略**：
        - Random Forest (RF)
        - XGBoost (XGB)
        - LightGBM (LGBM)
        - Gradient Boosting (GB)
        - Ridge Regression

        基于 R² 得分自动分配权重
        """)

        if st.button("🚀 运行模型融合", use_container_width=True):
            try:
                from src.advanced.model_ensemble import run_model_ensemble

                with st.spinner("正在训练融合模型..."):
                    ensemble = run_model_ensemble(df_enhanced)

                    if ensemble:
                        st.success("✅ 模型融合完成！")

                        # 获取指标
                        metrics = ensemble.get_metrics()

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("集成 R²", f"{metrics['R²']:.3f}")
                        with col2:
                            st.metric("MAE", f"{metrics['MAE']:.2f} kg")
                        with col3:
                            st.metric("RMSE", f"{metrics['RMSE']:.2f} kg")

                        # 特征重要性
                        importance_df = ensemble.get_feature_importance()
                        if importance_df is not None:
                            st.subheader("特征重要性 (基于 Random Forest)")

                            fig = go.Figure(go.Bar(
                                x=importance_df['重要性'].head(10),
                                y=importance_df['特征'].head(10),
                                orientation='h',
                                marker=dict(color='steelblue')
                            ))

                            fig.update_layout(
                                title="TOP 10 特征重要性",
                                xaxis_title="重要性",
                                yaxis_title="特征",
                                template='plotly_white'
                            )

                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 融合失败：{e}")

    with tab4:
        st.subheader("🎯 超参数优化")

        st.info("💡 使用 Optuna 自动搜索最优模型参数")

        n_trials = st.slider("优化试验次数", 10, 100, 30, 10,
                            help="试验次数越多，结果越好，但耗时越长")

        st.markdown("""
        **优化参数**：
        - n_estimators: 树的数量 (50-300)
        - max_depth: 最大深度 (3-20)
        - min_samples_split: 最小分割样本数 (2-20)
        - min_samples_leaf: 最小叶子节点样本数 (1-10)
        - max_features: 特征采样比例 (0.3-1.0)
        """)

        if st.button("🔍 开始优化", use_container_width=True):
            try:
                from src.advanced.hyperparameter_tuning import run_hyperparameter_tuning

                with st.spinner(f"正在进行 {n_trials} 次优化试验..."):
                    model, r2 = run_hyperparameter_tuning(df_enhanced)

                    st.success(f"✅ 优化完成！最佳 R²: {r2:.3f}")

            except Exception as e:
                st.error(f"❌ 优化失败：{e}")
                st.info("提示：请确保已安装 optuna (pip install optuna)")

    with tab5:
        st.subheader("📊 模型解释 (SHAP)")

        st.info("💡 使用 SHAP 分析模型如何做出预测决策")

        st.markdown("""
        **SHAP (SHapley Additive exPlanations)**：
        - 基于博弈论的特征重要性解释
        - 显示每个特征对预测结果的贡献
        - 提供全局和局部解释
        """)

        if st.button("🔍 生成 SHAP 分析", use_container_width=True):
            try:
                from src.professional_analyzer import YieldPredictor
                from src.advanced.model_explainer import explain_model
                from config import REPORTS_DIR

                with st.spinner("正在计算 SHAP 值..."):
                    # 训练模型
                    predictor = YieldPredictor(df_enhanced)
                    predictor.run_all()

                    # 准备特征
                    feature_cols = [col for col in df_enhanced.columns if col not in [
                        '日期', '预计产量 (kg)', '预警等级', '环境压力指数', '压力原因'
                    ] and df_enhanced[col].dtype in ['float64', 'int64']]

                    X = df_enhanced[feature_cols].fillna(df_enhanced[feature_cols].median())

                    # 解释模型
                    output_dir = REPORTS_DIR / 'shap_analysis'
                    explainer = explain_model(
                        predictor.model,
                        X.values,
                        feature_cols,
                        output_dir
                    )

                    if explainer and explainer.explainer:
                        st.success("✅ SHAP 分析完成！")

                        # 获取 Top 特征
                        top_features = explainer.get_top_features(10)

                        if top_features is not None:
                            st.subheader("TOP 10 特征重要性")

                            fig = go.Figure(go.Bar(
                                x=top_features['重要性'],
                                y=top_features['特征'],
                                orientation='h',
                                marker=dict(color='coral')
                            ))

                            fig.update_layout(
                                title="SHAP 特征重要性（均值绝对值）",
                                xaxis_title="SHAP 值",
                                yaxis_title="特征",
                                template='plotly_white'
                            )

                            st.plotly_chart(fig, use_container_width=True)

                            # 显示表格
                            st.dataframe(top_features, use_container_width=True, hide_index=True)

                        # 显示生成的图表
                        shap_images = list(output_dir.glob('*.png')) if output_dir.exists() else []
                        if shap_images:
                            st.subheader("生成的可视化")
                            for img_path in shap_images:
                                st.image(str(img_path), caption=img_path.stem, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 分析失败：{e}")
                st.info("提示：请确保已安装 shap (pip install shap)")

    with tab6:
        st.subheader("🔄 全模型对比")

        st.info("💡 对比所有模型的性能")

        if st.button("🚊 运行全模型对比", use_container_width=True):
            try:
                from src.model_comparison import run_comparison

                with st.spinner("正在对比所有模型..."):
                    # 这里需要临时重定向输出
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = buffer = io.StringIO()

                    try:
                        run_comparison()
                        output = buffer.getvalue()
                    finally:
                        sys.stdout = old_stdout

                    st.success("✅ 模型对比完成！")

                    # 显示输出
                    st.text(output)

            except Exception as e:
                st.error(f"❌ 对比失败：{e}")

    with tab7:
        st.subheader("🎭 多模态融合")

        st.info("💡 多模态融合结合传感器时序数据、统计特征和图像特征，提升预测准确性")

        st.markdown("""
        **融合策略**：
        - **早期融合** (Early Fusion): 在特征层面融合不同模态的数据
        - **晚期融合** (Late Fusion): 在决策层面融合不同模型的预测结果
        - **混合融合** (Hybrid Fusion): 使用神经网络进行深度融合
        """)

        col1, col2 = st.columns(2)

        with col1:
            fusion_strategy = st.selectbox(
                "选择融合策略",
                ["early", "late", "hybrid"],
                format_func=lambda x: {
                    "early": "早期融合 (特征级)",
                    "late": "晚期融合 (决策级)",
                    "hybrid": "混合融合 (深度学习)"
                }[x],
                help="早期融合: 特征级融合\n晚期融合: 决策级融合\n混合融合: 神经网络融合"
            )

        with col2:
            model_type = st.selectbox(
                "选择基础模型",
                ["random_forest", "gradient_boosting"],
                format_func=lambda x: {
                    "random_forest": "随机森林",
                    "gradient_boosting": "梯度提升"
                }[x] if x != "hybrid" else "自动"
            )

        if fusion_strategy == "hybrid":
            st.warning("⚠️ 混合融合需要PyTorch，训练时间较长")

        if st.button("🚀 运行多模态融合", use_container_width=True):
            try:
                from src.advanced.multi_modal_fusion import run_multimodal_fusion

                with st.spinner(f"正在运行{fusion_strategy}融合..."):
                    # 临时重定向输出
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = buffer = io.StringIO()

                    try:
                        predictor = run_multimodal_fusion(
                            df_enhanced,
                            fusion_strategy=fusion_strategy,
                            model_type=model_type
                        )
                        output = buffer.getvalue()
                    finally:
                        sys.stdout = old_stdout

                    st.success("✅ 多模态融合完成！")

                    # 显示输出
                    with st.expander("查看详细输出"):
                        st.text(output)

                    # 显示指标
                    if hasattr(predictor, 'metrics') and predictor.metrics:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("R² 得分", f"{predictor.metrics['R²']:.3f}")

                        with col2:
                            st.metric("MAE", f"{predictor.metrics['MAE']:.2f} kg")

                        with col3:
                            st.metric("RMSE", f"{predictor.metrics['RMSE']:.2f} kg")

                    # 显示特征重要性（仅早期融合）
                    if fusion_strategy == 'early':
                        importance = predictor.get_feature_importance()
                        if importance is not None:
                            st.subheader("特征重要性 (TOP 10)")

                            fig = go.Figure(go.Bar(
                                x=importance['重要性'].head(10),
                                y=importance['特征'].head(10),
                                orientation='h',
                                marker=dict(color='steelblue')
                            ))

                            fig.update_layout(
                                title="TOP 10 多模态特征重要性",
                                xaxis_title="重要性",
                                yaxis_title="特征",
                                template='plotly_white'
                            )

                            st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 融合失败：{e}")
                st.info("提示: 确保已安装所需依赖 (pip install torch transformers)")

# ==================== 数据概览页面 ====================

def data_overview_page(df):
    """数据概览页面"""
    st.title("📋 数据概览")

    # 基本信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总记录数", len(df))

    with col2:
        st.metric("变量数", len(df.columns))

    with col3:
        st.metric("时间跨度", f"{len(df)} 天")

    with col4:
        st.metric("数据完整性", f"{df.notna().sum().sum() / df.size * 100:.1f}%")

    st.markdown("---")

    # 数据预览
    st.subheader("原始数据预览")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # 数据统计
    st.subheader("数据统计")
    st.dataframe(df.describe(), use_container_width=True)

    st.markdown("---")

    # 数据类型
    st.subheader("数据类型")
    col_types = pd.DataFrame({
        '列名': df.columns,
        '数据类型': df.dtypes.values,
        '缺失值': df.isnull().sum().values,
        '唯一值': [df[col].nunique() for col in df.columns]
    })
    st.dataframe(col_types, use_container_width=True)

# ==================== 主函数 ====================

def main():
    """主函数"""

    # 侧边栏
    uploaded_file = sidebar()

    st.sidebar.markdown("---")

    # 页面导航
    st.sidebar.subheader("📱 页面导航")
    page_options = [
        "🏠 主页",
        "📊 数据分析",
        "🤖 模型评估",
        "🧠 高级模型",
        "📄 报告生成",
        "📋 数据概览"
    ]

    if uploaded_file is not None:
        selected_page = st.sidebar.radio("", page_options)

        # 加载和处理数据
        with st.spinner("正在加载数据..."):
            df = load_data(uploaded_file)

        if df is not None:
            df_enhanced = process_data(df)

            # 训练模型（如果需要）
            predictor = None
            if selected_page in ["🤖 模型评估", "📄 报告生成"]:
                with st.spinner("正在训练模型..."):
                    predictor = train_model(df_enhanced)

            # 显示页面
            if selected_page == "🏠 主页":
                main_page(df, df_enhanced, predictor)
            elif selected_page == "📊 数据分析":
                data_analysis_page(df, df_enhanced)
            elif selected_page == "🤖 模型评估":
                model_evaluation_page(df_enhanced, predictor)
            elif selected_page == "🧠 高级模型":
                advanced_models_page(df, df_enhanced)
            elif selected_page == "📄 报告生成":
                report_generation_page(df, df_enhanced, predictor)
            elif selected_page == "📋 数据概览":
                data_overview_page(df)
    else:
        st.sidebar.info("👈 请先上传或选择数据文件")
        st.markdown("""
        # 欢迎使用 🦞 智虾系统

        ## 功能特点

        - 📊 **完整的数据分析**：FCR、SGR、环境参数
        - 🤖 **机器学习预测**：产量预测、特征重要性
        - 📄 **自动报告生成**：Word 报告一键导出
        - 🚨 **智能预警**：环境压力三级预警

        ## 使用步骤

        1. 👈 在侧边栏上传数据文件（.xlsx 或 .csv）
        2. 选择功能页面开始分析
        3. 查看结果并导出报告

        ## 技术支持

        - SmartShrimp Team
        - SmartShrimp Team
        """)

if __name__ == '__main__':
    main()
