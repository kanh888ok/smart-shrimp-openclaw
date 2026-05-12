# PolicyPilot：企业政策申报准备度诊断 AI Agent

PolicyPilot 是一个面向中小企业、园区和企业服务机构的政策申报前置初筛原型。系统基于公开政策文本、脱敏公示样例和可解释评分规则，帮助企业判断：

```text
能申报什么政策 → 为什么匹配 → 缺什么材料 → 风险在哪里 → 如何补齐 → 生成申报书初稿
```

核心定位：**不是直接预测官方审批结果，而是评估企业当前材料状态下的申报准备度。**

---

## 1. 核心功能

- 企业画像抽取：地区、行业、团队规模、营收、研发投入、知识产权、Demo/试点等。
- 政策库加载：支持公开来源政策库、模拟政策库和用户上传 PDF/TXT。
- 政策库洞察：支持城市对比、申报窗口倒计时、官方来源/核验状态统计和数据质量检查。
- 轻量 RAG 检索：从政策条款中检索匹配依据。
- 申报准备度评分：区域匹配、行业匹配、资格条件、材料完备度、证据强度、风险扣分。
- 材料缺口识别：判断营业执照、项目计划书、合同、预算、财务报表、知识产权等是否覆盖。
- 风险提示：输出高/中/低风险和补齐建议。
- 申报书初稿：生成项目背景、技术路线、创新点、商业价值、社会效益等。
- 报告导出：Markdown、JSON、CSV。

---

## 2. 快速运行

```bash
cd policypilot_ai_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

打开 Streamlit 页面后，选择默认的 **公开来源政策库（推荐）**，直接点击“开始分析”即可演示。

---

## 3. 命令行 Demo

公开来源政策库 Demo：

```bash
python cli_demo_public.py
```

模拟政策库 Demo：

```bash
python cli_demo.py
```

运行后会生成：

```text
outputs/analysis_report.md
outputs/analysis_report.json
outputs/application_draft.md
outputs/material_checklist.md
outputs/product_intro.md
outputs/faq.md
outputs/policy_results.csv
```

---

## 4. 数据口径

本项目包含两类数据。

### 公开来源数据

```text
data/public_policies.json
data/public_source_catalog.csv
data/public_outcome_cases_desensitized.csv
data/desensitization_rules.json
data/known_enterprises.json
reference_repos/opc-policy/data/policies.json
```

说明：公开政策文本和公开公示/公告来源是真实公开来源；脱敏 outcome 样例只保留 case_id、地区、政策 ID、主体类型和公示结果标签，不保留企业实名、统一社会信用代码、联系方式、合同金额、财务数据或申报书原文。`known_enterprises.json` 是知名企业基础画像兜底表，当前覆盖 98 个常见国内大厂及 162 个别名，用于避免地区、行业和企业类型被材料中的客户行业或泛化描述误判。`reference_repos/opc-policy` 为第三方 MIT 开源参考项目 [opcgate/opc-policy](https://github.com/siuserxiaowei/opc-policy)，系统可将其结构化政策库转换为本项目的 Policy 格式用于演示。

### 演示模拟数据

```text
data/sample_policies.json
data/sample_companies.json
data/labeled_eval_cases.csv
data/scoring_rubric.csv
```

说明：用于演示产品流程和规则校准思路，不代表政府内部审批数据。

详见：

```text
docs/DATA_AND_SCORING.md
docs/PUBLIC_DATASET_NOTES.md
docs/DATASET_EXPANSION_AND_DESENSITIZATION.md
docs/COMPANY_INPUT_GUIDE.md
DISCLAIMER.md
```

---

## 5. 评分逻辑

系统采用可解释规则基线：

```text
总分 = 区域匹配 + 行业匹配 + 资格条件 + 材料完备度 + 证据强度 - 风险扣分
```

分数解释：

| 分数 | 标签 | 含义 |
|---:|---|---|
| 80–100 | 强匹配：建议优先申报 | 区域、行业、资格、材料和证据较完整 |
| 65–79 | 中高匹配：补齐材料后申报 | 方向匹配，但材料或证据仍有缺口 |
| 45–64 | 弱匹配：需要进一步论证 | 有相关性，但不适合直接申报 |
| 0–44 | 暂不建议：匹配度较低 | 核心条件不满足或缺口明显 |

---

## 6. 项目结构

```text
policypilot_ai_agent/
├── app.py                         # Streamlit 前端
├── cli_demo.py                    # 模拟政策库命令行 Demo
├── cli_demo_public.py             # 公开来源政策库命令行 Demo
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── DISCLAIMER.md
├── GITHUB_READY.md
├── data/
│   ├── public_policies.json
│   ├── public_source_catalog.csv
│   ├── public_outcome_cases_desensitized.csv
│   ├── desensitization_rules.json
│   ├── known_enterprises.json
│   ├── sample_policies.json
│   ├── sample_companies.json
│   ├── scoring_rubric.csv
│   └── labeled_eval_cases.csv
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DEMO_SCRIPT.md
│   ├── DATA_AND_SCORING.md
│   ├── PUBLIC_DATASET_NOTES.md
│   ├── EVALUATION_RUBRIC.md
│   ├── RESUME_BULLET.md
│   └── ROADMAP.md
├── examples/
│   ├── generated_outputs/
│   └── public_generated_outputs/
├── src/
│   ├── company_parser.py
│   ├── generator.py
│   ├── llm.py
│   ├── matcher.py
│   ├── models.py
│   ├── policy_insights.py
│   ├── policy_loader.py
│   ├── report.py
│   ├── retriever.py
│   └── utils.py
└── tests/
    └── test_core.py
```

---

## 7. 使用 OpenAI API（可选）

默认使用本地规则和模板，不需要 API Key。若要启用大模型改写申报书：

```bash
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY
streamlit run app.py
```

环境变量：

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

`.env` 已被 `.gitignore` 排除，不能提交到公开仓库。

---

## 8. 测试

```bash
PYTHONPATH=. pytest -q
```

测试覆盖企业画像抽取、公开政策匹配、材料生成和大厂/中小企业边界识别。

---

## 9. 产品一句话

> PolicyPilot 面向中小企业、园区和企业服务机构，基于官方公开政策文本和企业画像，自动完成政策匹配、申报准备度评分、材料缺口识别、风险提示和申报书初稿生成，帮助企业在正式申报前判断“能不能报、缺什么、风险在哪、怎么补”。

---

## 10. 简历表述

> 构建 PolicyPilot 企业政策申报准备度诊断 AI Agent，支持公开政策文本加载、企业画像抽取、政策条款检索、五维规则评分、材料缺口识别、风险提示与申报书初稿生成。系统采用轻量 RAG 和可解释规则基线，支持 Streamlit 交互式前端、Markdown/JSON/CSV 报告导出，可用于政企数字化、园区企业服务和中小企业政策申报辅助场景。
