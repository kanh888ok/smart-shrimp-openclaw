from __future__ import annotations

from typing import List, Tuple

from .models import CompanyProfile, MaterialItem, MatchResult, Policy, RiskFlag, ScoreBreakdown
from .retriever import build_company_query, retrieve_relevant_clauses

NEGATIONS = ["暂无", "无", "没有", "尚未", "未准备", "未提供", "缺少", "不具备", "待补充"]
PROVINCE_CITIES = {
    "广东": ["广州", "深圳", "东莞", "佛山", "珠海", "惠州", "中山", "梅州"],
    "浙江": ["杭州", "宁波", "温州", "嘉兴"],
    "江苏": ["南京", "苏州", "无锡", "常州", "南通", "徐州", "扬州", "盐城", "连云港", "宿迁"],
    "山东": ["济南", "青岛", "潍坊"],
    "四川": ["成都"],
    "湖北": ["武汉"],
    "重庆": ["重庆"],
    "北京": ["北京"],
    "上海": ["上海"],
    "天津": ["天津"],
    "安徽": ["合肥"],
    "陕西": ["西安"],
    "湖南": ["长沙"],
    "福建": ["厦门", "福州"],
    "河南": ["郑州"],
    "云南": ["昆明"],
    "海南": ["海口"],
    "河北": ["石家庄", "保定"],
    "贵州": ["贵阳"],
}


def _positive_contains(text: str, keyword: str, window: int = 20) -> bool:
    idx = text.find(keyword)
    while idx != -1:
        ctx_before = text[max(0, idx - window):idx]
        if not any(n in ctx_before for n in NEGATIONS):
            return True
        idx = text.find(keyword, idx + len(keyword))
    return False


def _dedupe(items: List[str], limit: int | None = None) -> List[str]:
    result = list(dict.fromkeys([x for x in items if x]))
    return result[:limit] if limit else result


def _region_score(company_region: str, policy_region: str) -> Tuple[float, str | None, RiskFlag | None]:
    normalized_policy = policy_region.replace("省", "").replace("市", "")
    if policy_region == "全国":
        return 22.0, "政策区域为全国，区域条件基本满足", None
    if company_region == policy_region:
        return 25.0, f"企业所在地为{company_region}，与政策区域匹配", None
    if policy_region in company_region or company_region in policy_region:
        return 20.0, f"企业区域 {company_region} 与政策区域 {policy_region} 存在包含关系", None
    if company_region in PROVINCE_CITIES.get(normalized_policy, []):
        return 23.0, f"{company_region}属于{policy_region}范围内，区域条件基本匹配", None
    if company_region == "未知":
        return 6.0, None, RiskFlag("高", "企业注册地未知", "补充营业执照或统一社会信用代码信息，明确注册地。")
    return 0.0, None, RiskFlag("高", f"企业所在地为{company_region}，与政策区域{policy_region}不匹配", "确认是否存在分公司、项目落地地或联合申报主体。")


def _industry_score(profile: CompanyProfile, policy: Policy) -> Tuple[float, List[str]]:
    reasons = []
    score = 0.0
    text = profile.raw_text.lower()

    for ind in policy.target_industries:
        if ind.lower() in text or ind == profile.industry:
            score += 7.0
            reasons.append(f"企业业务涉及{ind}，命中政策支持产业。")

    for kw in policy.keywords:
        if _positive_contains(profile.raw_text, kw) or kw.lower() in profile.industry.lower():
            score += 2.0
            reasons.append(f"企业材料命中政策关键词：{kw}。")

    return min(score, 25.0), _dedupe(reasons, 6)


def _qualification_score(profile: CompanyProfile, policy: Policy) -> Tuple[float, List[str], List[str], List[RiskFlag]]:
    score = 0.0
    reasons: List[str] = []
    missing: List[str] = []
    risks: List[RiskFlag] = []

    if profile.employees > 0:
        score += 4.0
        reasons.append(f"已识别团队规模：{profile.employees}人。")
    else:
        missing.append("团队人数说明")
        risks.append(RiskFlag("中", "团队规模未知", "补充核心团队人数、研发人员比例和成员分工。"))

    if profile.annual_revenue_wan > 0:
        score += 4.0
        reasons.append(f"已识别年营收：{profile.annual_revenue_wan:g}万元。")
    else:
        missing.append("营收或财务数据")
        risks.append(RiskFlag("中", "财务数据缺失", "补充财务报表、纳税证明、银行流水或收入说明。"))

    if _is_sme_policy(policy):
        if profile.asset_total_wan > 0:
            score += 2.0
            reasons.append(f"已识别资产总额：{profile.asset_total_wan:g}万元。")
        else:
            missing.append("资产总额证明")

    if profile.rd_ratio_percent > 0:
        score += 3.0
        reasons.append(f"已识别研发投入占比：{profile.rd_ratio_percent:g}%。")
    elif profile.tech_staff_ratio_percent > 0:
        score += 2.0
        reasons.append(f"已识别科技人员占比：{profile.tech_staff_ratio_percent:g}%，但仍建议补充研发费用占比。")
        missing.append("研发费用占比或研发费用说明")
    elif profile.rd_staff_ratio_percent > 0:
        score += 2.0
        reasons.append(f"已识别研发人员占比：{profile.rd_staff_ratio_percent:g}%，但仍建议补充研发费用占比。")
        missing.append("研发费用占比或研发费用说明")
    elif any(k in policy.name + policy.category + "".join(policy.keywords) for k in ["科技", "研发", "中小企业"]):
        missing.append("研发投入占比或研发费用说明")
        risks.append(RiskFlag("中", "研发投入缺少量化指标", "补充研发费用、研发人员、研发项目和技术成果说明。"))

    if profile.has_negative_record:
        risks.append(RiskFlag("高", "存在重大违法/失信风险线索", "核实近三年安全、质量、环保和科研诚信记录；如存在限制情形，应暂缓申报。"))
    elif _is_sme_policy(policy) and profile.has_no_major_violation:
        reasons.append("已提及无重大违法或严重失信记录。")

    if profile.has_ip:
        score += 5.0
        reasons.append("具备知识产权或技术成果线索。")
    else:
        missing.append("知识产权证明：专利、软著、商标或技术成果说明")
        risks.append(RiskFlag("高", "缺少知识产权证明", "优先补充软著、专利、模型/系统技术说明或第三方检测报告。"))

    if profile.has_demo:
        score += 4.0
        reasons.append("具备 Demo、原型、试点或部署线索。")
    else:
        missing.append("Demo、原型、部署截图或试点证明")
        risks.append(RiskFlag("中", "缺少可验证 Demo 或试点证明", "补充演示系统链接、部署截图、试点报告或用户反馈。"))

    if profile.has_budget:
        score += 2.0
        reasons.append("已提及预算、费用计划或算力预算。")
    elif any(k in policy.name + policy.category for k in ["算力", "补贴", "资金"]):
        missing.append("预算说明或费用计划")
        risks.append(RiskFlag("中", "预算依据不足", "拆分算力、研发人力、数据处理、测试部署和运维费用。"))

    if profile.has_contract_or_proof:
        score += 3.0
        reasons.append("已提及合同、订单、客户或合作证明。")
    elif any(k in policy.name + policy.category for k in ["算力", "场景", "示范"]):
        missing.append("合同、算力使用证明或场景合作证明")
        risks.append(RiskFlag("高", "缺少合同/合作证明", "补充客户合同、试点协议、算力平台订单或场景方确认函。"))

    return min(score, 20.0), reasons, missing, risks


def _material_items(profile: CompanyProfile, policy: Policy) -> List[MaterialItem]:
    text = profile.raw_text
    items: List[MaterialItem] = []
    for item in policy.required_materials:
        status = "待补充"
        reason = "企业材料中未识别到该项。"
        if _positive_contains(text, item):
            status = "已覆盖"
            reason = "企业输入文本中直接出现该材料。"
        elif "知识产权" in item or item in ["专利", "软著", "知识产权或技术成果证明", "知识产权证明"]:
            if profile.has_ip:
                status = "已覆盖"
                reason = "企业已提及专利、软著或知识产权。"
        elif "财务" in item or "纳税" in item:
            if profile.has_financial_report:
                status = "已覆盖"
                reason = "企业已提及财务报表、审计、流水或纳税材料。"
        elif "Demo" in item or "原型" in item or "部署" in item:
            if profile.has_demo:
                status = "已覆盖"
                reason = "企业已提及 Demo、原型、上线、部署或试点。"
        elif "合同" in item or "合作证明" in item or "使用证明" in item or "订单" in item:
            if profile.has_contract_or_proof:
                status = "已覆盖"
                reason = "企业已提及合同、订单、客户或合作证明。"
        elif "预算" in item:
            if profile.has_budget:
                status = "已覆盖"
                reason = "企业已提及预算或费用计划。"
        elif "团队" in item:
            if profile.has_team_resume or profile.employees > 0:
                status = "需复核"
                reason = "企业已提及团队规模，但仍需正式简历或成员证明。"
        elif item in ["企业简介", "项目介绍", "产品或服务介绍", "应用场景说明"]:
            status = "需复核"
            reason = "已有企业介绍文本，但需整理成正式附件。"

        items.append(MaterialItem(item, status, reason))
    return items


def _evidence_score(profile: CompanyProfile, material_items: List[MaterialItem]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []
    if profile.has_demo:
        score += 4.0
        reasons.append("具备演示或试点线索，项目可验证性较好。")
    if profile.has_contract_or_proof:
        score += 4.0
        reasons.append("具备合同/订单/合作证明线索，商业真实性较强。")
    if profile.has_financial_report:
        score += 3.0
        reasons.append("具备财务材料线索，便于审核收入与费用。")
    if profile.has_local_scenario:
        score += 3.0
        reasons.append("具备本地落地或园区试点线索，符合场景导向政策。")
    covered = sum(1 for m in material_items if m.status == "已覆盖")
    if covered >= 3:
        score += 4.0
        reasons.append("多项关键材料已覆盖，申报准备度较高。")
    elif covered >= 1:
        score += 2.0
        reasons.append("部分关键材料已覆盖，但仍需补充正式附件。")
    return min(score, 15.0), reasons


def _level(score: float) -> str:
    if score >= 80:
        return "强匹配：建议优先申报"
    if score >= 65:
        return "中高匹配：补齐材料后申报"
    if score >= 45:
        return "弱匹配：需要进一步论证"
    return "暂不建议：匹配度较低"


def _is_sme_policy(policy: Policy) -> bool:
    text = policy.name + policy.category + "".join(policy.requirements) + "".join(policy.keywords)
    return "中小企业" in text or "小微企业" in text


def _sme_size_risk(profile: CompanyProfile, policy: Policy) -> RiskFlag | None:
    if not _is_sme_policy(policy):
        return None
    if profile.employees > 500 or profile.annual_revenue_wan > 20000 or profile.asset_total_wan > 20000:
        return RiskFlag(
            "高",
            "企业规模超过中小企业类政策常见门槛",
            "科技型中小企业常见门槛为职工不超过500人、年销售收入不超过2亿元、资产总额不超过2亿元；建议改为匹配重点企业、重大专项或产业链牵引类政策。",
        )
    return None


def _next_actions(policy: Policy, missing_items: List[str], risks: List[RiskFlag]) -> List[str]:
    actions = [
        "补充企业基础信息、营业执照、团队成员和财务数据。",
        "围绕政策评分点重写项目技术路线、创新点和应用场景。",
        "用量化指标说明项目经济价值、社会价值和产业带动效果。",
    ]
    if missing_items:
        actions.insert(0, "优先补齐缺失材料：" + "、".join(missing_items[:5]) + "。")
    if any("算力" in x for x in [policy.name, policy.category] + policy.keywords):
        actions.insert(0, "整理模型训练/推理任务、GPU 预算、算力平台报价和使用计划。")
    if any(k in policy.name + policy.category for k in ["场景", "示范"]):
        actions.insert(0, "补充真实试点单位、部署截图、用户数据和数据合规说明。")
    if any(r.level == "高" for r in risks):
        actions.insert(0, "先处理高风险项，避免进入正式申报后被退回。")
    return _dedupe(actions, 6)


def match_policy(profile: CompanyProfile, policy: Policy) -> MatchResult:
    hit_reasons: List[str] = []
    missing_items: List[str] = []
    risks: List[RiskFlag] = []

    region_score, region_reason, region_risk = _region_score(profile.region, policy.region)
    if region_reason:
        hit_reasons.append(region_reason)
    if region_risk:
        risks.append(region_risk)

    industry_score, industry_reasons = _industry_score(profile, policy)
    hit_reasons.extend(industry_reasons)

    qualification_score, q_reasons, q_missing, q_risks = _qualification_score(profile, policy)
    hit_reasons.extend(q_reasons)
    missing_items.extend(q_missing)
    risks.extend(q_risks)
    sme_risk = _sme_size_risk(profile, policy)
    if sme_risk:
        risks.append(sme_risk)

    material_items = _material_items(profile, policy)
    for m in material_items:
        if m.status == "待补充":
            missing_items.append(m.name)
    covered_count = sum(1 for m in material_items if m.status == "已覆盖")
    review_count = sum(1 for m in material_items if m.status == "需复核")
    material_score = min(15.0, covered_count * 2.8 + review_count * 1.2)

    evidence_score, evidence_reasons = _evidence_score(profile, material_items)
    hit_reasons.extend(evidence_reasons)

    penalty = min(len(set(missing_items)) * 0.7 + sum(2.0 for r in risks if r.level == "高"), 12.0)
    breakdown = ScoreBreakdown(region_score, industry_score, qualification_score, material_score, evidence_score, penalty)
    total = round(breakdown.total, 1)
    if sme_risk:
        total = min(total, 44.0)

    # 加入政策原始风险规则，作为低/中风险复核项。
    for rr in policy.risk_rules:
        if len(risks) < 8:
            risks.append(RiskFlag("低", rr, "按政策原文逐条复核，并准备对应证明材料。"))

    query = build_company_query(profile)
    cited_pairs = retrieve_relevant_clauses(query, [policy], top_k=6)
    cited = [f"【{c.clause_type}】{c.text}" for c, _ in cited_pairs]
    if not cited:
        cited = policy.requirements[:3]

    unique_missing = _dedupe(missing_items, 12)
    unique_risks: List[RiskFlag] = []
    seen = set()
    for r in risks:
        key = (r.level, r.item)
        if key not in seen:
            seen.add(key)
            unique_risks.append(r)
        if len(unique_risks) >= 8:
            break

    return MatchResult(
        policy=policy,
        score=total,
        level=_level(total),
        score_breakdown=breakdown,
        hit_reasons=_dedupe(hit_reasons, 10),
        material_items=material_items,
        missing_items=unique_missing,
        risk_flags=unique_risks,
        cited_clauses=_dedupe(cited, 8),
        next_actions=_next_actions(policy, unique_missing, unique_risks),
    )


def rank_policies(profile: CompanyProfile, policies: List[Policy]) -> List[MatchResult]:
    results = [match_policy(profile, policy) for policy in policies]
    return sorted(results, key=lambda x: x.score, reverse=True)
