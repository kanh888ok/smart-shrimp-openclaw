from __future__ import annotations

from typing import List

from .llm import LLMProvider
from .models import CompanyProfile, MatchResult, RiskFlag


def _fmt_list(items: List[str], empty: str = "暂无") -> str:
    return "\n".join(f"- {x}" for x in items) if items else empty


def _fmt_risks(risks: List[RiskFlag]) -> str:
    if not risks:
        return "暂无明显风险"
    return "\n".join(f"- 【{r.level}】{r.item}：{r.mitigation}" for r in risks)


def build_application_draft(profile: CompanyProfile, match: MatchResult, llm: LLMProvider | None = None) -> str:
    """生成申报书初稿。可使用 LLM；无 API 时使用稳定模板。"""
    policy = match.policy
    prompt = f"""
请为企业生成一份政策申报书初稿，要求正式、具体、不要虚构事实。

企业材料：
{profile.raw_text}

政策名称：{policy.name}
政策方向：{policy.category}
政策要求：{policy.requirements}
材料缺口：{match.missing_items}
风险提示：{[r.item for r in match.risk_flags]}
引用依据：{match.cited_clauses}

输出结构：
1. 项目概述
2. 企业基础情况
3. 申报必要性
4. 技术路线
5. 创新点
6. 应用场景
7. 商业价值
8. 社会效益
9. 预算与实施计划
10. 待补充材料
""".strip()

    if llm and llm.use_openai:
        text = llm.generate(
            prompt,
            system="你是政企数字化和科技政策申报专家，擅长生成合规、清晰、可审核的中文申报材料。",
        )
        if text.strip():
            return text.strip()

    return _template_application_draft(profile, match)


def _template_application_draft(profile: CompanyProfile, match: MatchResult) -> str:
    policy = match.policy
    missing = "、".join(match.missing_items) if match.missing_items else "暂无明显缺失材料"
    keywords = "、".join(profile.keywords) if profile.keywords else "待补充"
    cited = _fmt_list(match.cited_clauses, "以政策原文为准")
    risks = _fmt_risks(match.risk_flags[:5])

    return f"""
# {policy.name} 申报书初稿

## 1. 项目概述
{profile.name}拟申报“{policy.name}”。企业当前业务方向为{profile.industry}，所在地为{profile.region}。本项目围绕企业现有技术能力和业务场景，申请政策支持以提升研发效率、产品化能力和场景落地能力。

## 2. 企业基础情况
企业材料显示，团队规模约为{profile.employees or '待补充'}人，成立年份为{profile.founded_year or '待补充'}，年营收约为{profile.annual_revenue_wan or '待补充'}万元，资产总额约为{profile.asset_total_wan or '待补充'}万元，研发投入占比为{profile.rd_ratio_percent or '待补充'}%，科技/研发人员占比为{profile.tech_staff_ratio_percent or profile.rd_staff_ratio_percent or '待补充'}%。企业已体现的关键词包括：{keywords}。

## 3. 申报必要性
企业所在的{profile.industry}方向对研发投入、算力资源、产品验证和场景合作依赖较强。通过政策申报，企业可降低研发与试点成本，补强技术成果证明和产业化材料，并加速从 Demo 到真实部署的转化。

## 4. 技术路线
项目建议采用“需求识别—数据与知识库建设—模型/算法服务—业务流程集成—效果评估—持续迭代”的技术路线。若涉及大模型或 AI Agent，应补充模型调用方式、数据来源、系统边界、人工复核机制、安全合规方案和性能评估指标。

## 5. 创新点
第一，项目将 AI 能力嵌入真实业务流程，而非停留在单点文案生成。第二，系统通过规则匹配、知识库检索和智能生成降低人工处理成本。第三，项目具备可复制性，可在同类企业、园区服务或行业场景中推广。

## 6. 应用场景
项目可服务于企业内部运营、客户服务、研发辅助、政策申报、销售支持等场景。后续应补充真实客户、试点单位、Demo 截图、部署证明或用户数据，以增强场景可信度。

## 7. 商业价值
项目可降低企业人工处理成本，提高材料准备、业务响应和管理决策效率。若完成产品化，可面向园区企业、中小企业服务机构、政企数字化服务商形成 SaaS 或项目制交付收入。

## 8. 社会效益
项目有助于提升中小企业对政策资源、数字化工具和 AI 技术的使用效率，降低创新创业门槛，并推动区域数字经济发展。

## 9. 预算与实施计划
建议将预算拆分为研发人力、模型与算力、数据处理、系统开发、测试部署和运营维护六类。实施计划可分为需求确认、MVP 开发、试点验证、材料完善和规模化推广五个阶段。

## 10. 政策依据摘录
{cited}

## 11. 风险与待补充材料
**主要风险：**
{risks}

**待补充材料：** {missing}
""".strip()


def build_material_checklist(match: MatchResult) -> str:
    rows = ["# 材料清单", "", "| 材料 | 状态 | 说明 |", "|---|---|---|"]
    for item in match.material_items:
        rows.append(f"| {item.name} | {item.status} | {item.reason} |")
    return "\n".join(rows)


def build_pitch(profile: CompanyProfile, top_matches: List[MatchResult]) -> str:
    top = top_matches[0] if top_matches else None
    policy_sentence = f"当前最高匹配政策为“{top.policy.name}”，匹配度 {top.score} 分。" if top else "系统可根据政策库自动排序候选政策。"
    return f"""
# PolicyPilot 60 秒产品介绍

**PolicyPilot** 是一套面向中小企业、园区和企业服务机构的政策申报准备度诊断 AI Agent。

中小企业普遍面临三个痛点：政策看不懂、资格判断难、材料准备慢。传统申报咨询依赖人工逐条查政策，成本高、周期长、风险不透明。

PolicyPilot 把这个流程做成一个 AI 决策辅助系统。企业只需输入简介或上传材料，系统即可抽取企业画像，检索政策条款，输出可申报政策排行、命中理由、缺失材料、风险提示和申报书初稿。{policy_sentence}

我们的核心价值不是简单替企业写材料，而是帮助企业判断：**能不能申报、缺什么材料、风险在哪里、怎样提高通过率**。

该系统可部署在园区企业服务中心、创业孵化器、政企服务机构和中小企业 SaaS 平台，帮助服务人员快速完成政策初筛，降低企业咨询成本，提高政策触达率和申报成功率。
""".strip()


def build_qna(profile: CompanyProfile, top_matches: List[MatchResult]) -> str:
    top = top_matches[0] if top_matches else None
    policy_name = top.policy.name if top else "候选政策"
    return f"""
# 常见问题

## Q1：这和普通 ChatGPT 写申报书有什么区别？
A：PolicyPilot 的核心不是写文案，而是结构化业务判断。系统先抽取企业画像，再按政策条件做匹配评分，输出材料缺口、风险等级和引用条款，最后才生成申报书初稿。

## Q2：如何降低大模型幻觉？
A：第一版采用规则评分与政策库检索作为主流程，生成内容只基于企业输入、政策条款和匹配结果。高风险结论用“需复核”表达，并要求人工确认。

## Q3：为什么这个项目有行业价值？
A：企业服务中心、园区、孵化器每天都要回答“我能申报什么政策”。PolicyPilot 能把初筛、材料清单、风险提示和初稿生成自动化，减少重复咨询和人工整理成本。

## Q4：现在最高匹配政策是什么？
A：当前演示企业最高匹配的是“{policy_name}”。系统给出匹配分、命中理由、缺失材料和下一步动作，便于企业马上补材料。

## Q5：后续怎么商业化？
A：可面向园区/政府企业服务部门做项目制交付，也可面向中小企业和财税咨询机构做 SaaS 订阅。后续接入真实政策库、企业材料 OCR、在线申报接口和园区后台。
""".strip()


def build_demo_explanation(profile: CompanyProfile, results: List[MatchResult]) -> str:
    top = results[0] if results else None
    return f"""
本次 Demo 使用企业“{profile.name}”作为样例。系统识别其地区为 {profile.region}、行业为 {profile.industry}、团队规模为 {profile.employees or '待补充'} 人，并按政策库进行排序。

最优候选政策为“{top.policy.name if top else '无'}”，匹配度为 {top.score if top else 0} 分。输出内容包括：企业画像、政策排行、评分拆解、命中理由、缺失材料、风险提示、申报书初稿、材料清单和产品介绍。

演示时重点强调：PolicyPilot 是政策申报前置决策系统，不是单纯文案生成器。
""".strip()
