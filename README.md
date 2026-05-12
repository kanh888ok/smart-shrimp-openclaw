# SmartShrimp OpenClaw

**智虾系统** 是一个面向 OpenClaw 养虾挑战赛的智能养殖管理原型。系统用 Kaggle 虾体测量数据、行业成本参数和仿真养殖场景演示水质监控、投喂优化、增氧控制、疾病预警、产量预测、自动日志和成本收益分析。

> 公开仓库口径：这是研究/竞赛原型，不是生产级自动化养殖控制系统。项目中的决策验证主要来自仿真场景和样例数据；真实虾塘部署需要传感器校准、设备联调和现场安全策略。

## 功能

| 模块 | 内容 |
|---|---|
| 数据分析 | FCR、SGR、环境压力指数、异常检测、趋势分析 |
| 预测建模 | Random Forest、Gradient Boosting、模型对比、可解释性分析 |
| 智能决策 | 水质告警、投喂建议、增氧/换水建议、疾病风险提示 |
| 可视化 | Streamlit Web 界面、实时监控大屏、决策过程可视化 |
| 报告 | Word/Markdown/HTML 报告生成、投资收益测算 |
| OpenClaw 技能 | 8 个核心技能定义见 [SKILL.md](SKILL.md) |

## 快速开始

安装核心依赖：

```bash
pip install -r requirements.txt
```

运行 Web 界面：

```bash
streamlit run app.py
```

高级模型为可选功能。如果需要 LSTM、Transformer、SHAP、Optuna、Prophet 等功能，再安装：

```bash
pip install -r requirements-advanced.txt
```

启动实时监控大屏：

```bash
streamlit run dashboard.py
```

启动决策过程可视化：

```bash
streamlit run src/decision_visualizer.py --server.port 8502
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

服务启动后访问 `http://localhost:8501`。

## 项目结构

```text
.
├── app.py                         # Streamlit 主界面
├── dashboard.py                   # 实时监控大屏
├── run.py                         # 命令行入口
├── enhanced_demo.py               # 增强演示入口
├── start.py                       # 一键启动脚本
├── data/                          # 样例数据和数据处理脚本
├── src/
│   ├── agent/                     # OpenClaw 智能体与技能管理
│   ├── advanced/                  # 高级模型、融合、解释、强化学习模块
│   ├── professional_analyzer.py   # 核心分析流程
│   └── roi_calculator.py          # 成本收益测算
├── scripts/                       # 图表和样例数据生成脚本
├── reports/                       # 已保留的实验结果 JSON 和示例图表
├── docs/                          # 技术文档、竞赛文章公开版和资产
├── config/                        # 配置模板
└── docker/                        # Dockerfile 和 Compose 配置
```

## 数据与指标口径

项目采用三类数据：

1. **Kaggle 虾体测量数据**：324 条虾体重量、长度、体积等真实测量数据，用于生物学基准。
2. **行业成本数据**：来自公开论文资料整理，用于 ROI 和成本收益测算。
3. **仿真养殖场景数据**：基于真实数据基准和养殖学公式生成，用于测试 OpenClaw 决策流程。

公开版默认采用保守表述：产量预测和 ROI 结果按实验/仿真口径解释。`reports/*.json` 中保留了不同实验设置下的模型结果；不要把增强仿真场景中的高 R² 直接解释为真实生产泛化性能。详细说明见 [docs/DATA_AND_METRICS.md](docs/DATA_AND_METRICS.md)。

## 常用命令

```bash
# 静态检查：编译所有 Python 文件
python -m compileall .

# 生成四张报告图
python scripts/generate_4_charts.py

# 生成样例数据
python scripts/generate_sample_data.py

# 投资收益演示
python enhanced_demo.py
```

## 配置

复制配置模板：

```bash
cp .env.example .env
```

OpenClaw/大模型服务配置模板位于 `config/openclaw.example.json`。该文件只保留占位符，不包含真实密钥。

样例数据说明见 [data/README.md](data/README.md)，实验结果说明见 [reports/README.md](reports/README.md)。

## 文档

- [docs/README.md](docs/README.md)：文档索引
- [docs/DATA_AND_METRICS.md](docs/DATA_AND_METRICS.md)：数据来源和指标口径
- [docs/competition_article_public.md](docs/competition_article_public.md)：参赛文章公开版
- [docs/PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md)：公开发布整理说明
- [docs/DOCKER.md](docs/DOCKER.md)：Docker 部署说明
- [docs/ADVANCED_MODELS.md](docs/ADVANCED_MODELS.md)：高级模型说明

## License

当前公开包未擅自改成开源授权，默认保留全部权利。若要正式开源，可将 `LICENSE` 替换为 MIT、Apache-2.0 或其他许可证。
