"""
智虾系统 - 实时监控大屏
Real-time Monitoring Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# 页面配置
st.set_page_config(
    page_title="智虾系统 - 实时监控大屏",
    page_icon="🦐",
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
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-danger {
        background-color: #ffcccc;
        border-left: 5px solid #ff0000;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .alert-success {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<h1 class="main-header">🦐 智虾系统实时监控大屏</h1>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("⚙️ 控制面板")

    # 养殖模式选择
    farming_mode = st.selectbox(
        "养殖模式",
        ["土池", "高位池", "工厂化"],
        index=1
    )

    # 面积输入
    area = st.number_input("养殖面积（亩）", min_value=1, max_value=1000, value=10)

    # 模拟数据开关
    simulate_data = st.checkbox("使用模拟数据", value=True)

    # 刷新间隔
    refresh_interval = st.slider("刷新间隔（秒）", 1, 60, 5)

    st.divider()

    # 系统状态
    st.subheader("系统状态")
    st.markdown('<p class="status-running">● 系统运行中</p>', unsafe_allow_html=True)
    st.write(f"运行时间: {timedelta(days=30)}")
    st.write(f"数据更新: {datetime.now().strftime('%H:%M:%S')}")

# 生成模拟数据
def generate_realtime_data():
    """生成实时水质数据"""
    np.random.seed(int(datetime.now().timestamp()))

    # 基础数据
    data = {
        "timestamp": datetime.now(),
        "water_temp": round(28 + np.random.normal(0, 0.5), 1),
        "dissolved_oxygen": round(5.5 + np.random.normal(0, 0.5), 1),
        "ph": round(8.0 + np.random.normal(0, 0.2), 1),
        "ammonia": round(np.random.uniform(0.1, 0.3), 2),
        "salinity": round(15 + np.random.normal(0, 1), 1),
        "feeding_amount": round(85 + np.random.normal(0, 5), 1),
        "fcr": round(1.9 + np.random.normal(0, 0.1), 2),
        "survival_rate": round(92 + np.random.normal(0, 1), 1),
        "biomass": round(1550 + np.random.normal(0, 50), 0)
    }

    return data

# 判断状态
def get_status_indicator(value, threshold_min, threshold_max, name):
    """获取状态指示器"""
    if value < threshold_min or value > threshold_max:
        return "🔴", "alert-danger"
    elif value < threshold_min * 1.1 or value > threshold_max * 0.9:
        return "⚠️", "alert-warning"
    else:
        return "✅", "alert-success"

# 主界面
col1, col2, col3 = st.columns(3)

# 生成数据
if simulate_data:
    data = generate_realtime_data()
else:
    # 这里可以接入真实数据源
    data = generate_realtime_data()

# 关键指标卡片
with col1:
    st.markdown("""
    <div class="metric-card">
        <h2>🌡️ 水温</h2>
        <h1>{:.1f}°C</h1>
        <p>理想范围: 26-28°C</p>
    </div>
    """.format(data["water_temp"]), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h2>💧 溶解氧</h2>
        <h1>{:.1f} mg/L</h1>
        <p>理想范围: >5.0 mg/L</p>
    </div>
    """.format(data["dissolved_oxygen"]), unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h2>🧪 pH值</h2>
        <h1>{:.1f}</h1>
        <p>理想范围: 7.5-8.5</p>
    </div>
    """.format(data["ph"]), unsafe_allow_html=True)

st.divider()

# 第二行指标
col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        label="📊 生物量",
        value=f"{data['biomass']} kg",
        delta=f"+{np.random.uniform(10, 30):.1f} kg"
    )

with col5:
    st.metric(
        label="🍽️ 今日投喂",
        value=f"{data['feeding_amount']} kg",
        delta=f"{data['fcr']}"
    )

with col6:
    st.metric(
        label="💪 存活率",
        value=f"{data['survival_rate']}%",
        delta="稳定"
    )

st.divider()

# 主要内容区
tab1, tab2, tab3, tab4 = st.tabs(["📈 实时趋势", "⚠️ 预警中心", "🤖 OpenClaw决策", "📊 数据分析"])

# Tab 1: 实时趋势
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌡️ 水温24小时趋势")

        # 生成24小时数据
        hours = pd.date_range(end=datetime.now(), periods=24, freq="H")
        temps = [28 + 3 * np.sin(i/3) + np.random.normal(0, 0.3) for i in range(24)]

        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=hours,
            y=temps,
            mode='lines+markers',
            name='水温',
            line=dict(color='#FF6B6B', width=3)
        ))

        fig_temp.update_layout(
            title="水温变化曲线",
            xaxis_title="时间",
            yaxis_title="温度 (°C)",
            hovermode='x unified',
            height=300
        )

        st.plotly_chart(fig_temp, use_container_width=True)

    with col2:
        st.subheader("💧 溶解氧24小时趋势")

        do_levels = [5.5 + 1.5 * np.sin(i/4 + 1) + np.random.normal(0, 0.2) for i in range(24)]

        fig_do = go.Figure()
        fig_do.add_trace(go.Scatter(
            x=hours,
            y=do_levels,
            mode='lines+markers',
            name='溶解氧',
            line=dict(color='#4ECDC4', width=3),
            fill='tozeroy',
            fillcolor='rgba(78, 205, 196, 0.2)'
        ))

        # 添加警戒线
        fig_do.add_hline(y=5.0, line_dash="dash", line_color="red",
                        annotation_text="警戒线 5.0 mg/L")

        fig_do.update_layout(
            title="溶解氧变化曲线",
            xaxis_title="时间",
            yaxis_title="溶解氧 (mg/L)",
            hovermode='x unified',
            height=300
        )

        st.plotly_chart(fig_do, use_container_width=True)

    # FCR趋势
    st.subheader("📊 FCR变化趋势（最近30天）")

    days = pd.date_range(end=datetime.now(), periods=30, freq="D")
    fcr_trend = [2.2 - 0.3 * (i/30) + np.random.normal(0, 0.05) for i in range(30)]

    fig_fcr = go.Figure()
    fig_fcr.add_trace(go.Scatter(
        x=days,
        y=fcr_trend,
        mode='lines+markers',
        name='FCR',
        line=dict(color='#95E1D3', width=3)
    ))

    fig_fcr.add_hline(y=1.8, line_dash="dash", line_color="green",
                     annotation_text="目标值 1.8")

    fig_fcr.update_layout(
        title="饲料系数（FCR）优化趋势",
        xaxis_title="日期",
        yaxis_title="FCR",
        hovermode='x unified',
        height=250
    )

    st.plotly_chart(fig_fcr, use_container_width=True)

# Tab 2: 预警中心
with tab2:
    st.header("⚠️ 预警中心")

    # 模拟预警列表
    alerts = [
        {
            "level": "warning",
            "time": datetime.now() - timedelta(minutes=15),
            "message": "溶解氧偏低（4.8 mg/L），建议启动增氧机"
        },
        {
            "level": "info",
            "time": datetime.now() - timedelta(hours=2),
            "message": "水温正常（28.2°C），在理想范围内"
        },
        {
            "level": "success",
            "time": datetime.now() - timedelta(hours=6),
            "message": "FCR持续改善，当前1.88，接近目标值1.8"
        }
    ]

    for alert in alerts:
        if alert["level"] == "warning":
            st.markdown(f"""
            <div class="alert-box alert-danger">
                <strong>⚠️ 预警</strong> - {alert['message']}<br/>
                <small>{alert['time'].strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        elif alert["level"] == "info":
            st.markdown(f"""
            <div class="alert-box alert-warning">
                <strong>ℹ️ 提示</strong> - {alert['message']}<br/>
                <small>{alert['time'].strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-box alert-success">
                <strong>✅ 正常</strong> - {alert['message']}<br/>
                <small>{alert['time'].strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)

# Tab 3: OpenClaw决策
with tab3:
    st.header("🤖 OpenClaw决策过程")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("当前分析")

        st.info("""
        **📊 数据分析结果**

        - 溶解氧：4.8 mg/L（偏低）
        - 水温：28.2°C（正常）
        - FCR：1.88（改善中）
        - pH：8.1（正常）

        **🎯 判断：**
        当前主要风险是溶解氧偏低，建议立即增氧。
        """)

    with col2:
        st.subheader("决策建议")

        st.success("""
        **✅ OpenClaw建议：**

        1. **立即执行**（高优先级）
           - 启动增氧机30分钟
           - 预计DO提升至5.2 mg/L

        2. **今日调整**（中优先级）
           - 投喂量维持在85kg
           - 继续监控FCR变化

        3. **预防措施**（低优先级）
           - 凌晨2-6点预防性增氧
           - 每日检测水质2次
        """)

    st.divider()

    # 决策流程图
    st.subheader("🔄 决策流程")

    decision_flow = {
        "节点": ["数据采集", "AI分析", "风险评估", "生成建议", "执行动作", "效果验证"],
        "状态": ["✅", "✅", "✅", "✅", "⏳", "⏳"],
        "时间": ["00:00", "00:01", "00:02", "00:03", "待执行", "待验证"]
    }

    df_flow = pd.DataFrame(decision_flow)
    st.table(df_flow)

    # 决策依据
    st.subheader("📚 决策依据")

    with st.expander("查看详细推理过程"):
        st.markdown("""
        **第1步：数据采集**
        - 采集时间：2026-03-21 14:30:00
        - 数据来源：水质传感器 #1-3
        - 数据质量：✅ 良好

        **第2步：模式识别**
        - 溶解氧趋势：下降中
        - 过去3小时：5.2 → 4.9 → 4.8 mg/L
        - 预测1小时后：4.6 mg/L（低于警戒线）

        **第3步：风险评估**
        - 当前风险等级：🟡 中等
        - 主要风险：缺氧导致虾应激
        - 影响程度：可能影响摄食和生长

        **第4步：方案生成**
        - 方案A：立即增氧30分钟 → 推荐 ✅
        - 方案B：减少投喂20% → 备选
        - 方案C：换水10% → 成本较高

        **第5步：选择方案A**
        - 理由：见效快、成本低、风险小
        - 预期效果：DO提升至5.2 mg/L
        - 执行成本：约15元电费
        """)

# Tab 4: 数据分析
with tab4:
    st.header("📊 数据分析")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("成本结构分析")

        # 成本数据
        cost_data = {
            "成本项": ["饲料", "苗种", "人工", "地租", "其他"],
            "占比": [65, 12, 8, 5, 10],
            "金额（万元）": [7.8, 1.44, 0.96, 0.6, 1.2]
        }

        df_cost = pd.DataFrame(cost_data)

        fig_cost = px.pie(
            df_cost,
            values="占比",
            names="成本项",
            title="年度成本结构",
            color_discrete_sequence=px.colors.sequential.RdBu
        )

        st.plotly_chart(fig_cost, use_container_width=True)

    with col2:
        st.subheader("效益对比")

        comparison_data = {
            "指标": ["年产量", "年利润", "FCR", "存活率"],
            "传统方式": ["4000 kg", "4.0万元", "2.2", "65%"],
            "智能系统": ["4800 kg", "6.5万元", "1.88", "92%"],
            "提升": ["+20%", "+62.5%", "-14.5%", "+27%"]
        }

        df_comparison = pd.DataFrame(comparison_data)
        st.table(df_comparison)

    st.divider()

    # 投资回报
    st.subheader("💰 3年投资回报预测")

    roi_data = {
        "年份": ["第1年", "第2年", "第3年"],
        "初始投资": ["15万元", "0", "0"],
        "年度成本": ["12万元", "12万元", "12万元"],
        "年度收入": ["19.2万元", "19.2万元", "19.2万元"],
        "净利润": ["-7.8万元", "7.2万元", "7.2万元"],
        "累计利润": ["-7.8万元", "-0.6万元", "6.6万元"],
        "ROI": ["-52%", "-4%", "44%"]
    }

    df_roi = pd.DataFrame(roi_data)
    st.table(df_roi)

    st.info("""
    💡 **投资建议**：
    - 投资回收期：约1.1年
    - 3年累计ROI：44%
    - 推荐指数：⭐⭐⭐⭐
    """)

# 自动刷新
if st.button("🔄 立即刷新"):
    st.rerun()

time.sleep(refresh_interval)
st.rerun()
