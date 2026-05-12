# 数据与使用声明

PolicyPilot 是政策申报前置初筛原型，不是政府审批系统，也不直接预测官方最终审批结果。

## 数据口径

- `data/public_policies.json`：基于公开政策文本/通知整理的结构化摘要，用于 Demo 与规则检索。
- `data/public_source_catalog.csv`：公开来源目录，记录来源类型、用途和数据口径。
- `data/public_outcome_cases_desensitized.csv`：由公开公示/公告派生的脱敏 outcome 样例，仅保留 `case_id`、地区、政策 ID、主体类型和公示结果标签。
- `data/sample_policies.json`、`data/sample_companies.json`：模拟演示数据，不代表官方材料。

## 不包含的信息

本仓库不包含企业实名、统一社会信用代码、联系人、电话、地址、合同金额、财务报表、申报书原文、专家评分或政府内部审批记录。

## 正确表述

可以说：

> 系统基于公开政策文本和脱敏公示样例，评估企业当前材料状态下的申报准备度，输出匹配政策、材料缺口、风险提示和申报书初稿。

不要说：

> 系统使用政府内部审批数据训练，可以准确预测企业是否通过审批。
