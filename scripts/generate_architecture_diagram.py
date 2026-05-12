"""
技术架构图生成器
Technical Architecture Diagram Generator

生成智虾系统的技术架构图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def create_architecture_diagram():
    """创建技术架构图"""

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # 颜色方案（蓝绿渐变）
    colors = {
        '感知层': '#E3F2FD',  # 浅蓝
        '数据层': '#BBDEFB',  # 蓝
        '分析层': '#64B5F6',  # 中蓝
        '决策层': '#2196F3',  # 深蓝
        '执行层': '#1976D2',  # 更深蓝
        '用户层': '#0D47A1',  # 最深蓝
        'OpenClaw': '#FF6B6B'  # 红色（突出）
    }

    # 标题
    ax.text(50, 98, '智虾系统技术架构图',
            ha='center', va='top', fontsize=24, fontweight='bold')

    # ========== 层次定义 ==========

    # 第1层：感知层（底部）
    layer1_y = 85
    sensors = [
        {'name': 'DO传感器', 'x': 15, 'desc': '溶解氧监测'},
        {'name': '温度传感器', 'x': 30, 'desc': '水温/气温'},
        {'name': 'pH传感器', 'x': 45, 'desc': '酸碱度'},
        {'name': '投喂传感器', 'x': 60, 'desc': '饲料消耗'},
        {'name': '摄像头', 'x': 75, 'desc': '视觉监测'}
    ]

    for sensor in sensors:
        # 传感器框
        box = FancyBboxPatch((sensor['x']-4, layer1_y-4), 8, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=colors['感知层'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(sensor['x'], layer1_y-1, sensor['name'],
                ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(sensor['x'], layer1_y-3.5, sensor['desc'],
                ha='center', va='center', fontsize=8, style='italic')

    # 层标签
    ax.text(5, layer1_y-1, '感知层\nPerception',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=colors['感知层'], edgecolor='black'))

    # 箭头：感知层 → 数据层
    for i in range(5):
        x = 15 + i*15
        arrow = FancyArrowPatch((x, layer1_y-4), (x, layer1_y-10),
                              arrowstyle='->', mutation_scale=20,
                              color='gray', linewidth=2)
        ax.add_patch(arrow)

    # 第2层：数据层
    layer2_y = 72
    data_components = [
        {'name': '实时数据流', 'x': 20, 'tech': 'MQTT/WebSocket'},
        {'name': '历史数据库', 'x': 40, 'tech': 'MySQL/TimescaleDB'},
        {'name': '数据预处理', 'x': 60, 'tech': 'Pandas/NumPy'},
        {'name': '特征工程', 'x': 80, 'tech': 'Feature Engineering'}
    ]

    for comp in data_components:
        box = FancyBboxPatch((comp['x']-5, layer2_y-4), 10, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=colors['数据层'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(comp['x'], layer2_y-1, comp['name'],
                ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(comp['x'], layer2_y-3.5, comp['tech'],
                ha='center', va='center', fontsize=8)

    ax.text(5, layer2_y-1, '数据层\nData',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=colors['数据层'], edgecolor='black'))

    # 箭头：数据层 → 分析层
    arrow = FancyArrowPatch((50, layer2_y-4), (50, layer2_y-10),
                          arrowstyle='->', mutation_scale=20,
                          color='gray', linewidth=3)
    ax.add_patch(arrow)

    # 第3层：分析层（机器学习）
    layer3_y = 59
    ml_models = [
        {'name': 'Random Forest', 'x': 15, 'r2': 'R²=0.44'},
        {'name': 'XGBoost', 'x': 30, 'r2': 'R²=0.52'},
        {'name': 'LSTM', 'x': 45, 'r2': '深度学习'},
        {'name': 'Prophet', 'x': 60, 'r2': '时序预测'},
        {'name': 'Stacking', 'x': 75, 'r2': '集成模型'}
    ]

    for model in ml_models:
        box = FancyBboxPatch((model['x']-5, layer3_y-4), 10, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=colors['分析层'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(model['x'], layer3_y-1, model['name'],
                ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(model['x'], layer3_y-3.5, model['r2'],
                ha='center', va='center', fontsize=8)

    ax.text(5, layer3_y-1, '分析层\nAnalysis',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=colors['分析层'], edgecolor='black'))

    # 箭头：分析层 → OpenClaw
    arrow = FancyArrowPatch((50, layer3_y-4), (50, layer3_y-10),
                          arrowstyle='->', mutation_scale=20,
                          color=colors['OpenClaw'], linewidth=4,
                          linestyle='--')
    ax.add_patch(arrow)

    # 第4层：OpenClaw决策层（核心）
    layer4_y = 45
    opencraw_box = FancyBboxPatch((20, layer4_y-8), 60, 10,
                                 boxstyle="round,pad=0.5",
                                 facecolor=colors['OpenClaw'],
                                 edgecolor='darkred', linewidth=3)
    ax.add_patch(opencraw_box)

    ax.text(50, layer4_y-2, 'OpenClaw AI 智能决策引擎',
            ha='center', va='center', fontsize=16, fontweight='bold', color='white')

    # OpenClaw能力
    capabilities = [
        {'name': '智能对话', 'x': 30},
        {'name': '数据分析', 'x': 40},
        {'name': '异常诊断', 'x': 50},
        {'name': '预测分析', 'x': 60},
        {'name': '决策建议', 'x': 70}
    ]

    for cap in capabilities:
        ax.text(cap['x'], layer4_y-5.5, cap['name'],
                ha='center', va='center', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 箭头：OpenClaw → 执行层
    arrow = FancyArrowPatch((50, layer4_y-8), (50, layer4_y-14),
                          arrowstyle='->', mutation_scale=20,
                          color='gray', linewidth=3)
    ax.add_patch(arrow)

    # 第5层：执行层
    layer5_y = 28
    actions = [
        {'name': '增氧控制', 'x': 20, 'desc': '自动开关增氧机'},
        {'name': '投喂控制', 'x': 35, 'desc': '精准投喂量'},
        {'name': '预警通知', 'x': 50, 'desc': '短信/APP推送'},
        {'name': '报告生成', 'x': 65, 'desc': '日报/周报'},
        {'name': '日志记录', 'x': 80, 'desc': '操作审计'}
    ]

    for action in actions:
        box = FancyBboxPatch((action['x']-5, layer5_y-4), 10, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=colors['执行层'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(action['x'], layer5_y-1, action['name'],
                ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(action['x'], layer5_y-3.5, action['desc'],
                ha='center', va='center', fontsize=8, color='white')

    ax.text(5, layer5_y-1, '执行层\nExecution',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=colors['执行层'], edgecolor='black'))

    # 箭头：执行层 → 用户层
    arrow = FancyArrowPatch((50, layer5_y-4), (50, layer5_y-10),
                          arrowstyle='->', mutation_scale=20,
                          color='gray', linewidth=2)
    ax.add_patch(arrow)

    # 第6层：用户层（顶部）
    layer6_y = 15
    user_interfaces = [
        {'name': 'Web界面', 'x': 25, 'tech': 'Streamlit'},
        {'name': '移动APP', 'x': 50, 'tech': 'Flutter'},
        {'name': 'API接口', 'x': 75, 'tech': 'REST API'}
    ]

    for ui in user_interfaces:
        box = FancyBboxPatch((ui['x']-6, layer6_y-4), 12, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=colors['用户层'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(ui['x'], layer6_y-1, ui['name'],
                ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(ui['x'], layer6_y-3.5, ui['tech'],
                ha='center', va='center', fontsize=8, color='white')

    ax.text(5, layer6_y-1, '用户层\nUser',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=colors['用户层'], edgecolor='black'))

    # 侧边：部署环境
    deploy_y = 45
    ax.text(92, deploy_y, '部署环境\nDeployment',
            ha='center', va='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#F5F5F5', edgecolor='black'))

    deploy_info = [
        '阿里云ECS',
        '2核4G',
        'Docker容器',
        '24/7运行'
    ]

    for i, info in enumerate(deploy_info):
        ax.text(92, deploy_y-4-i*3.5, info,
                ha='center', va='center', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray'))

    # 底部：数据流说明
    ax.text(50, 5, '数据流向: 感知 → 数据 → 分析 → OpenClaw决策 → 执行 → 用户',
            ha='center', va='center', fontsize=10, style='italic',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))

    # 保存图片
    output_path = 'reports/technical_architecture_diagram.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 技术架构图已保存: {output_path}")

    return fig


def create_data_flow_diagram():
    """创建数据流图"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 97, '智虾系统数据流图',
            ha='center', va='top', fontsize=20, fontweight='bold')

    # 数据流节点
    nodes = [
        {'name': '传感器采集', 'x': 10, 'y': 70, 'color': '#E3F2FD'},
        {'name': '数据清洗', 'x': 30, 'y': 70, 'color': '#BBDEFB'},
        {'name': '特征工程', 'x': 50, 'y': 70, 'color': '#64B5F6'},
        {'name': 'ML模型预测', 'x': 70, 'y': 70, 'color': '#2196F3'},
        {'name': 'OpenClaw分析', 'x': 90, 'y': 70, 'color': '#FF6B6B'},
        {'name': '决策建议', 'x': 90, 'y': 45, 'color': '#1976D2'},
        {'name': '执行控制', 'x': 70, 'y': 45, 'color': '#0D47A1'},
        {'name': '效果反馈', 'x': 50, 'y': 45, 'color': '#0D47A1'},
        {'name': '模型优化', 'x': 30, 'y': 45, 'color': '#0D47A1'},
        {'name': '用户界面', 'x': 10, 'y': 45, 'color': '#0D47A1'}
    ]

    # 绘制节点
    for node in nodes:
        box = FancyBboxPatch((node['x']-5, node['y']-4), 10, 6,
                             boxstyle="round,pad=0.3",
                             facecolor=node['color'],
                             edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(node['x'], node['y']-1, node['name'],
                ha='center', va='center', fontsize=9, fontweight='bold')

    # 绘制箭头（主流程）
    main_flow = [(10, 70), (30, 70), (50, 70), (70, 70), (90, 70)]
    for i in range(len(main_flow)-1):
        arrow = FancyArrowPatch(main_flow[i], main_flow[i+1],
                              arrowstyle='->', mutation_scale=15,
                              color='blue', linewidth=2)
        ax.add_patch(arrow)

    # 绘制箭头（决策执行）
    decision_flow = [(90, 66), (90, 49), (70, 45)]
    for i in range(len(decision_flow)-1):
        arrow = FancyArrowPatch(decision_flow[i], decision_flow[i+1],
                              arrowstyle='->', mutation_scale=15,
                              color='green', linewidth=2)
        ax.add_patch(arrow)

    # 绘制箭头（反馈循环）
    feedback_flow = [(70, 41), (50, 45), (30, 45), (10, 45)]
    for i in range(len(feedback_flow)-1):
        arrow = FancyArrowPatch(feedback_flow[i], feedback_flow[i+1],
                              arrowstyle='->', mutation_scale=15,
                              color='orange', linewidth=2)
        ax.add_patch(arrow)

    # 绘制箭头（优化循环）
    optimize_flow = [(30, 41), (30, 66)]
    arrow = FancyArrowPatch(optimize_flow[0], optimize_flow[1],
                          arrowstyle='->', mutation_scale=15,
                          color='purple', linewidth=2, linestyle='--')
    ax.add_patch(arrow)

    # 图例
    legend_elements = [
        plt.Line2D([0], [0], color='blue', linewidth=2, label='主数据流'),
        plt.Line2D([0], [0], color='green', linewidth=2, label='决策执行'),
        plt.Line2D([0], [0], color='orange', linewidth=2, label='反馈循环'),
        plt.Line2D([0], [0], color='purple', linewidth=2, linestyle='--', label='模型优化')
    ]
    ax.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=10)

    # 说明文字
    ax.text(50, 25, '数据流向说明:\n'
                    '蓝色: 传感器数据 → 清洗 → 特征 → 预测 → OpenClaw分析\n'
                    '绿色: OpenClaw建议 → 执行控制\n'
                    '橙色: 执行结果 → 反馈 → 用户界面\n'
                    '紫色: 反馈数据 → 模型优化（持续改进）',
            ha='center', va='center', fontsize=9,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))

    # 保存图片
    output_path = 'reports/data_flow_diagram.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ 数据流图已保存: {output_path}")

    return fig


def create_opencraw_interaction_diagram():
    """创建OpenClaw交互图"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    ax.text(50, 97, 'OpenClaw 30天对话交互图',
            ha='center', va='top', fontsize=20, fontweight='bold')

    # 中央：OpenClaw
    center_box = FancyBboxPatch((35, 40), 30, 20,
                               boxstyle="round,pad=0.5",
                               facecolor='#FF6B6B',
                               edgecolor='darkred', linewidth=3)
    ax.add_patch(center_box)
    ax.text(50, 55, 'OpenClaw', ha='center', va='center', fontsize=16, fontweight='bold', color='white')
    ax.text(50, 48, 'AI智能体', ha='center', va='center', fontsize=12, color='white')
    ax.text(50, 43, '对话驱动', ha='center', va='center', fontsize=10, color='white')

    # 6次关键对话
    conversations = [
        {'day': 'Day 5', 'topic': '数据分析', 'x': 50, 'y': 85, 'result': '识别3个问题'},
        {'day': 'Day 6', 'topic': '投喂策略', 'x': 85, 'y': 70, 'result': 'FCR降至1.9'},
        {'day': 'Day 25', 'topic': '异常处理', 'x': 85, 'y': 30, 'result': '存活率稳定'},
        {'day': 'Day 28', 'topic': '产量预测', 'x': 50, 'y': 15, 'result': '预测1550kg'},
        {'day': 'Day 30', 'topic': '综合决策', 'x': 15, 'y': 30, 'result': '15天方案'},
        {'day': 'Day 30', 'topic': '总结建议', 'x': 15, 'y': 70, 'result': '8/10分评分'}
    ]

    for conv in conversations:
        # 对话框
        box = FancyBboxPatch((conv['x']-8, conv['y']-5), 16, 8,
                             boxstyle="round,pad=0.3",
                             facecolor='#E3F2FD',
                             edgecolor='blue', linewidth=1.5)
        ax.add_patch(box)

        ax.text(conv['x'], conv['y']-1.5, conv['day'],
                ha='center', va='center', fontsize=10, fontweight='bold', color='blue')
        ax.text(conv['x'], conv['y']-3, conv['topic'],
                ha='center', va='center', fontsize=9)
        ax.text(conv['x'], conv['y']-4.5, conv['result'],
                ha='center', va='center', fontsize=8, style='italic')

        # 箭头：对话 → OpenClaw
        arrow = FancyArrowPatch((conv['x'], conv['y']-5),
                              (50 if conv['x'] < 50 else 50,
                               60 if conv['y'] > 50 else 40),
                              arrowstyle='->', mutation_scale=12,
                              color='gray', linewidth=1.5)
        ax.add_patch(arrow)

    # 统计信息
    stats_text = '30天实验统计:\n\n' \
                 '• 对话次数: 50+次\n' \
                 '• OpenClaw决策: 8次\n' \
                 '• 预测准确率: 96.8%\n' \
                 '• 建议准确率: 100%\n' \
                 '• 响应时间: <1秒'

    ax.text(50, 5, stats_text,
            ha='center', va='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', edgecolor='orange', linewidth=2))

    # 保存图片
    output_path = 'reports/opencraw_interaction_diagram.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ OpenClaw交互图已保存: {output_path}")

    return fig


def main():
    """主函数：生成所有架构图"""
    print("""
╔════════════════════════════════════════════════════════════╗
║          技术架构图生成器                                  ║
║     Technical Architecture Diagram Generator                ║
╚════════════════════════════════════════════════════════════╝
    """)

    # 生成3个架构图
    print("\n正在生成技术架构图...")
    create_architecture_diagram()

    print("\n正在生成数据流图...")
    create_data_flow_diagram()

    print("\n正在生成OpenClaw交互图...")
    create_opencraw_interaction_diagram()

    print("\n✅ 所有架构图生成完成！")
    print("\n生成的文件:")
    print("  1. reports/technical_architecture_diagram.png - 技术架构图")
    print("  2. reports/data_flow_diagram.png - 数据流图")
    print("  3. reports/opencraw_interaction_diagram.png - OpenClaw交互图")
    print("\n这些图片可以直接用于参赛文章和演示！")


if __name__ == "__main__":
    main()
