# PolicyPilot 提交说明

## 项目定位

PolicyPilot 是面向企业服务机构、园区和中小企业的政策申报准备度诊断 AI Agent 原型。系统基于企业输入材料抽取企业画像，结合结构化政策库进行政策匹配、评分拆解、材料缺口识别、风险提示，并生成申报书初稿和分析报告。

## 核心能力

- 企业画像抽取：地区、行业、团队规模、营收、资产、研发、知识产权、Demo/试点、合同/预算等。
- 大厂和中小企业边界识别：内置知名企业基础画像兜底表，减少大厂行业和地区误判。
- 政策匹配评分：区域、行业、资格、材料、证据、风险扣分。
- 材料缺口与风险提示：识别待补充材料和高/中/低风险项。
- 政策库洞察：政策数量、区域覆盖、官方来源、核验状态、城市对比、申报窗口倒计时和数据质量检查。
- 文档生成：申报书初稿、材料清单、完整分析报告、CSV 匹配结果。

## 运行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

默认不需要 API Key；如需启用 OpenAI 改写申报书，可复制 `.env.example` 为 `.env` 并填写 `OPENAI_API_KEY`。

## 数据说明

- `data/public_policies.json`：公开来源政策摘要。
- `data/public_outcome_cases_desensitized.csv`：公开公示 outcome 脱敏样例。
- `data/known_enterprises.json`：知名企业基础画像兜底表。
- `data/sample_policies.json`：演示政策库。

项目不包含企业实名敏感材料、统一社会信用代码、联系方式、完整合同或完整财务报表原文。

## 测试说明

测试文件位于 `tests/test_core.py`。当前打包机器缺少实际 Python 运行时，因此本地未能重新执行 `pytest`。
