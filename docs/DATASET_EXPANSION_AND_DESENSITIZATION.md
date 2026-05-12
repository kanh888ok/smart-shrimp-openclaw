# 数据集扩充与脱敏方案

## 1. 扩充目标

当前仓库已经包含公开政策库、公开来源目录和脱敏 outcome 样例。后续扩充的目标不是构造“官方审批通过率训练集”，而是构建更完整的公开来源申报准备度数据底座：

- 扩充政策文本与申报指南，用于政策匹配和材料清单生成。
- 扩充公开公示/公告派生 outcome，用于验证规则排序和产品解释。
- 保留来源 URL 与公示阶段，保证数据可追溯。
- 移除企业实名和敏感字段，避免把公开名单二次加工成可识别企业画像库。

## 2. 优先采集来源

新增候选源记录在：

```text
data/public_expansion_source_candidates.csv
```

优先级从高到低：

1. AI 算力券/人工智能券资格审核公示  
   与 PolicyPilot 的 AI 政策申报定位最贴合，可扩充算力券、模型券、语料券相关政策结果样例。

2. 科技型中小企业拟入库/入库公告  
   数量大、批次多、规则明确，适合校准“资格条件”和“材料准备度”的解释。

3. 专精特新中小企业公示/公告  
   可扩展到中小企业成长性、创新能力、细分领域能力等政策场景。

4. 各地政策申报指南  
   用于扩充 `public_policies.json`，不直接作为 outcome 样例。

## 3. 统一脱敏字段

公开页面或附件中即使存在企业名称，也不在提交版数据集中保留。统一生成不可逆 `case_id`。

建议保留字段：

```text
case_id
policy_id
region
year
batch
notice_stage
policy_family
outcome_label
source_url
features_available
features_removed
note
```

建议移除字段：

```text
company_name
unified_social_credit_code
legal_representative
contact_person
phone
email
address
contract_amount
financial_data
application_text
expert_score
review_comment
```

## 4. 标签体系

当前标签继续沿用：

```text
public_notice_candidate
public_notice_qualified
public_notice_final_included
public_notice_not_included_after_objection
```

含义：

- `public_notice_candidate`：进入拟公示名单，不等同于最终入库。
- `public_notice_qualified`：资格审核或项目审核公示通过，不等同于资金拨付。
- `public_notice_final_included`：公示期结束后公布入库或最终名单。
- `public_notice_not_included_after_objection`：从公告差额或异议核实中形成的聚合负样本，不保留企业身份。

## 5. 输出样例

```csv
case_id,policy_id,region,year,batch,notice_stage,policy_family,outcome_label,source_url,features_removed
SZ-TSME-2024-B02-0001,PUB-CN-TSME-2017,深圳,2024,第二批,final_notice,科技型中小企业,public_notice_final_included,https://www.sz.gov.cn/cn/xxgk/zfxxgj/tzgg/content/post_11505430.html,"company_name,credit_code,contact,address,application_materials"
```

## 6. 对外表述

推荐表述：

> 数据集基于官方公开政策文本、公开公示/公告名单和脱敏 outcome 样例构建，用于政策匹配、申报准备度评分、材料缺口识别和风险解释。数据不包含政府内部审批记录、企业完整申报书、财务报表、合同文本或专家评分。

避免表述：

> 数据集来自政府内部审批系统，可以训练官方通过率预测模型。

## 7. 扩充后的价值

完成扩充后，数据规模可以从当前 63 条脱敏 outcome 样例扩展到数千条公开公示派生样例。它能支撑：

- 更充分的政策类别覆盖。
- 更可信的数据来源说明。
- 更稳定的评分阈值校准。
- 更自然的产品演示，而不是只依赖少量手写样例。

