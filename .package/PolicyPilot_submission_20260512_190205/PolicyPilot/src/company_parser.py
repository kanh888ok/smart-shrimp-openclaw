from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from .models import CompanyProfile

REGIONS = [
    "杭州", "浙江", "上海", "北京", "深圳", "广州", "澳门", "香港", "成都", "苏州", "南京", "合肥", "武汉", "西安",
    "长沙", "青岛", "厦门", "重庆", "天津", "宁波", "无锡", "宁德", "济南", "保定", "惠州", "佛山",
    "珠海", "东莞", "潍坊", "嘉兴", "连云港", "贵阳", "全国"
]

INDUSTRIES = [
    "RPA", "机器人流程自动化", "人工智能", "大模型", "软件开发", "软件", "互联网", "云计算", "电商", "电子商务",
    "智慧物流", "本地生活", "机器人", "智能硬件", "AIoT", "边缘计算", "智能制造", "工业智能", "医疗", "教育",
    "政务", "城市治理", "文创", "旅游科技", "跨境电商", "信息技术", "金融科技", "新能源汽车", "动力电池",
    "通信设备", "消费电子", "安防", "工程机械", "家电", "网络安全", "企业软件", "服务器", "AI芯片",
    "智能驾驶", "半导体", "医疗器械", "医药", "新能源",
]

KEYWORDS = [
    "AI", "人工智能", "大模型", "RPA", "机器人流程自动化", "算力", "云计算", "电商", "电子商务", "智慧物流", "本地生活", "GPU", "RAG", "Agent", "客服", "机器人", "视觉", "语音",
    "硬件", "传感器", "边缘计算", "教育", "医疗", "政务", "城市", "旅游", "文创", "跨境",
    "软著", "专利", "知识产权", "试点", "Demo", "原型", "合同", "订单", "营收", "研发", "预算",
    "财务报表", "资产总额", "科技人员", "上市", "总部", "平台", "纳税", "园区", "部署", "客户案例", "商业计划书", "团队简历",
]

FINANCING_STAGES = ["未融资", "天使轮", "种子轮", "Pre-A", "A轮", "B轮", "C轮", "战略融资"]
NEGATIONS = ["暂无", "无", "没有", "尚未", "未准备", "未提供", "缺少", "不具备", "待补充"]
KNOWN_ENTERPRISE_PATH = Path(__file__).resolve().parents[1] / "data" / "known_enterprises.json"


def _load_known_enterprises() -> list[dict]:
    try:
        return json.loads(KNOWN_ENTERPRISE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


KNOWN_ENTERPRISES = _load_known_enterprises()


def _alias_matches_text(alias: str, text: str) -> bool:
    if not alias:
        return False
    text_lower = text.lower()
    alias_lower = alias.lower()
    idx = text_lower.find(alias_lower)
    while idx != -1:
        if len(alias) >= 3:
            return True
        tail = text[idx + len(alias): idx + len(alias) + 8]
        tail_markers = [
            "公司", "集团", "科技", "控股", "股份", "上市", "总部", "员工", "营收", "成立",
            "是一家", "主营", "平台", "汽车", "电器", "医疗", "快递", "找房", "出行", "网络", "智能",
        ]
        if any(marker in tail for marker in tail_markers):
            return True
        idx = text_lower.find(alias_lower, idx + len(alias_lower))
    return False


def _matched_known_enterprise(text: str) -> dict | None:
    for item in KNOWN_ENTERPRISES:
        if any(_alias_matches_text(alias, text) for alias in item.get("aliases", [])):
            return item
    return None


def _is_negated_around(text: str, keyword: str, window: int = 20) -> bool:
    idx = text.find(keyword)
    while idx != -1:
        start = max(0, idx - window)
        # 只看关键词前方的否定词，避免“已有软著，暂无专利”把软著误判为否定。
        ctx_before = text[start:idx]
        if not any(n in ctx_before for n in NEGATIONS):
            return False
        idx = text.find(keyword, idx + len(keyword))
    return keyword in text


def _contains_any(text: str, words: Iterable[str]) -> bool:
    low = text.lower()
    return any(w.lower() in low for w in words)


def _contains_positive_any(text: str, words: Iterable[str]) -> bool:
    for w in words:
        if w.lower() in text.lower() and not _is_negated_around(text, w):
            return True
    return False


def _first_region(text: str) -> str:
    for r in REGIONS:
        if r in text:
            return r
    known = _matched_known_enterprise(text)
    if known:
        return str(known.get("region", "未知"))
    return "未知"


def _first_industry(text: str) -> str:
    known = _matched_known_enterprise(text)
    if known:
        return str(known.get("industry", "未知"))

    own_business_patterns = [
        r"(?:主营|专注于|从事|聚焦|核心产品|业务方向是|项目方向是)([^。；;\n]{0,80})",
    ]
    for p in own_business_patterns:
        for m in re.finditer(p, text, flags=re.I):
            segment = m.group(1)
            if "机器人流程自动化" in segment or "RPA" in segment.upper():
                return "人工智能"
            for ind in INDUSTRIES:
                if ind in segment:
                    if ind in ["软件开发", "RPA", "机器人流程自动化"]:
                        return "人工智能" if "AI" in segment.upper() or "人工智能" in segment else ind
                    return ind

    for ind in INDUSTRIES:
        if ind in text:
            if ind in ["电商", "电子商务"] and re.search(r"(电商|电子商务)[、,，和与].{0,20}(金融|物流|客户|行业)", text):
                continue
            return ind
    if "ai" in text.lower():
        return "人工智能"
    return "未知"


def _extract_int(patterns: List[str], text: str) -> int:
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            return int(float(m.group(1)))
    return 0


def _extract_number_with_unit(patterns: List[str], text: str, unit_multipliers: dict[str, float]) -> float:
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            value = float(m.group(1))
            unit = m.group(2) if len(m.groups()) >= 2 else ""
            return value * unit_multipliers.get(unit, 1.0)
    return 0.0


def _extract_money_wan(patterns: List[str], text: str) -> float:
    return _extract_number_with_unit(
        patterns,
        text,
        {
            "万亿元": 100000000,
            "万亿": 100000000,
            "千亿元": 10000000,
            "千亿": 10000000,
            "百亿元": 1000000,
            "百亿": 1000000,
            "亿元": 10000,
            "亿": 10000,
            "万元": 1,
            "万": 1,
        },
    )


def _extract_float(patterns: List[str], text: str) -> float:
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            return float(m.group(1))
    return 0.0


def _extract_employees(text: str) -> int:
    unit_patterns = [
        r"(?:团队|员工|职工|职工总数|人员|雇员|团队规模|员工规模|员工人数)\s*(?:超|超过|约|近|逾|为|不超过|少于|低于)?\s*(\d+(?:\.\d+)?)\s*(万人|千人|百人|人)",
        r"(?:超|超过|约|近|逾)?\s*(\d+(?:\.\d+)?)\s*(万人|千人|百人|人)\s*(?:团队|员工|职工|人员|雇员)",
    ]
    unit_value = _extract_number_with_unit(unit_patterns, text, {"万人": 10000, "千人": 1000, "百人": 100, "人": 1})
    if unit_value:
        return int(unit_value)

    patterns = [
        r"团队\s*(\d{1,5})\s*[人名]",
        r"员工\s*(\d{1,5})\s*[人名]?",
        r"职工总数\s*(\d{1,5})\s*[人名]?",
        r"员工人数\s*(\d{1,5})\s*[人名]?",
        r"研发人员\s*(\d{1,5})\s*[人名]?",
        r"(\d{1,5})\s*[人名]\s*(?:团队|研发|员工)",
        r"团队规模(?:约|为)?\s*(\d{1,5})",
    ]
    return _extract_int(patterns, text)


def _extract_revenue_wan(text: str) -> float:
    unit_patterns = [
        r"(?:年?营收|年?收入|销售额|销售收入|营业收入|上一年度销售收入|上年销售收入)\s*(?:超|超过|约|近|逾|为|达到|不超过|低于|少于)?\s*(\d+(?:\.\d+)?)\s*(万亿元|万亿|千亿元|千亿|百亿元|百亿|亿元|亿|万元|万)",
        r"(?:超|超过|约|近|逾|达到|不超过|低于|少于)?\s*(\d+(?:\.\d+)?)\s*(万亿元|万亿|千亿元|千亿|百亿元|百亿|亿元|亿|万元|万)\s*(?:年?营收|年?收入|销售额|销售收入|营业收入)",
    ]
    unit_value = _extract_money_wan(unit_patterns, text)
    if unit_value:
        return unit_value

    patterns = [
        r"年?营收\s*(\d+(?:\.\d+)?)\s*万",
        r"收入\s*(\d+(?:\.\d+)?)\s*万",
        r"销售额\s*(\d+(?:\.\d+)?)\s*万",
        r"销售收入\s*(\d+(?:\.\d+)?)\s*万",
        r"营收\s*(\d+(?:\.\d+)?)\s*万元",
        r"营收约?\s*(\d+(?:\.\d+)?)\s*万",
    ]
    return _extract_float(patterns, text)


def _extract_asset_total_wan(text: str) -> float:
    unit_patterns = [
        r"(?:资产总额|总资产|资产规模)\s*(?:超|超过|约|近|逾|为|达到|不超过|低于|少于)?\s*(\d+(?:\.\d+)?)\s*(万亿元|万亿|千亿元|千亿|百亿元|百亿|亿元|亿|万元|万)",
        r"(?:超|超过|约|近|逾|达到|不超过|低于|少于)?\s*(\d+(?:\.\d+)?)\s*(万亿元|万亿|千亿元|千亿|百亿元|百亿|亿元|亿|万元|万)\s*(?:资产总额|总资产|资产规模)",
    ]
    return _extract_money_wan(unit_patterns, text)


def _extract_rd_ratio(text: str) -> float:
    patterns = [
        r"研发投入(?:占比|比例)?\s*(?:约|超|超过|近|为)?\s*(\d+(?:\.\d+)?)\s*%",
        r"研发费用(?:占比|比例)?\s*(?:约|超|超过|近|为)?\s*(\d+(?:\.\d+)?)\s*%",
        r"R&D\s*(?:ratio|占比)?\s*(?:约|超|超过|近|为)?\s*(\d+(?:\.\d+)?)\s*%",
    ]
    return _extract_float(patterns, text)


def _extract_rd_staff_ratio(text: str) -> float:
    patterns = [
        r"研发人员(?:占比|比例)?\s*(?:约|超|超过|近|为)?\s*(\d+(?:\.\d+)?)\s*%",
        r"研发团队(?:占比|比例)?\s*(?:约|超|超过|近|为)?\s*(\d+(?:\.\d+)?)\s*%",
    ]
    return _extract_float(patterns, text)


def _extract_tech_staff_ratio(text: str) -> float:
    patterns = [
        r"科技人员(?:占比|比例)?\s*(?:约|超|超过|近|为|不低于|达到)?\s*(\d+(?:\.\d+)?)\s*%",
        r"科技人员数占职工总数(?:比例|占比)?\s*(?:约|超|超过|近|为|不低于|达到)?\s*(\d+(?:\.\d+)?)\s*%",
    ]
    return _extract_float(patterns, text)


def _has_no_major_violation(text: str) -> bool:
    clean_patterns = [
        "无重大违法", "无严重失信", "未发生重大安全", "未发生重大质量", "未发生严重环境违法",
        "近三年无重大违法", "无失信记录", "信用记录良好",
    ]
    return _contains_any(text, clean_patterns)


def _has_negative_record(text: str) -> bool:
    risk_patterns = ["重大违法", "严重失信", "重大安全事故", "重大质量事故", "严重环境违法", "科研失信"]
    if _has_no_major_violation(text):
        return False
    return _contains_any(text, risk_patterns)


def _extract_founded_year(text: str) -> int:
    m = re.search(r"成立于\s*(20\d{2}|19\d{2})\s*年?", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(20\d{2}|19\d{2})\s*年\s*成立", text)
    if m:
        return int(m.group(1))
    m = re.search(r"成立\s*(\d{1,2})\s*年", text)
    if m:
        return datetime.now().year - int(m.group(1))
    return 0


def _extract_name(text: str) -> str:
    patterns = [
        r"企业名称[:：]\s*([^\n，,。]{2,40})",
        r"公司名称[:：]\s*([^\n，,。]{2,40})",
        r"([\u4e00-\u9fa5A-Za-z0-9]{2,40}(?:集团公司|控股有限公司|股份有限公司|有限公司|集团|科技公司|初创公司|工作室|团队))",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    known = _matched_known_enterprise(text)
    if known:
        aliases = known.get("aliases", [])
        if aliases:
            return str(aliases[0])
    return "示例企业"


def _extract_financing(text: str) -> str:
    for stage in FINANCING_STAGES:
        if stage in text:
            return stage
    return "未披露"


def _classify_company_scale(profile: CompanyProfile) -> str:
    if profile.employees > 500 or profile.annual_revenue_wan > 20000 or profile.asset_total_wan > 20000:
        return "大型企业"
    if profile.employees and profile.annual_revenue_wan and profile.asset_total_wan:
        return "中小企业候选"
    return "信息不足"


def _is_public_company(text: str) -> bool:
    known = _matched_known_enterprise(text)
    known_tags = known.get("tags", []) if known else []
    return "上市公司" in known_tags or _contains_any(text, ["上市公司", "A股上市", "港股上市", "美股上市", "上市企业", "股票代码", "证券代码"])


def _is_group_company(text: str, name: str) -> bool:
    known = _matched_known_enterprise(text)
    known_tags = known.get("tags", []) if known else []
    return "集团企业" in known_tags or "集团" in name or _contains_any(text, ["集团公司", "控股集团", "集团企业", "大型集团"])


def _is_platform_company(text: str) -> bool:
    known = _matched_known_enterprise(text)
    known_tags = known.get("tags", []) if known else []
    return "平台型企业" in known_tags or _contains_any(text, ["平台企业", "平台型企业", "互联网平台", "工业互联网平台", "生态平台", "开放平台"])


def parse_company_profile(text: str) -> CompanyProfile:
    normalized = text.replace("，", ",").replace("。", ".").replace("：", ":")
    negative_patent = _contains_any(text, ["暂无发明专利", "暂无专利", "无发明专利", "没有专利", "无专利"])

    profile = CompanyProfile(raw_text=text)
    profile.name = _extract_name(text)
    profile.region = _first_region(text)
    profile.industry = _first_industry(text)
    profile.founded_year = _extract_founded_year(normalized)
    profile.employees = _extract_employees(normalized)
    profile.annual_revenue_wan = _extract_revenue_wan(normalized)
    profile.asset_total_wan = _extract_asset_total_wan(normalized)
    profile.rd_ratio_percent = _extract_rd_ratio(normalized)
    profile.rd_staff_ratio_percent = _extract_rd_staff_ratio(normalized)
    profile.tech_staff_ratio_percent = _extract_tech_staff_ratio(normalized)
    profile.financing_stage = _extract_financing(text)
    profile.company_scale = _classify_company_scale(profile)
    profile.is_public_company = _is_public_company(text)
    profile.is_group_company = _is_group_company(text, profile.name)
    profile.is_platform_company = _is_platform_company(text)
    positive_ip = _contains_positive_any(text, ["知识产权", "专利", "软著", "软件著作权", "商标", "著作权"])
    profile.has_software_copyright = _contains_positive_any(text, ["软著", "软件著作权"])
    profile.has_patent = ("专利" in text) and not negative_patent and not _is_negated_around(text, "专利")
    profile.has_ip = positive_ip or profile.has_software_copyright or profile.has_patent
    profile.has_demo = _contains_positive_any(text, ["demo", "Demo", "原型", "试点", "部署", "上线", "客户案例", "演示系统"])
    profile.has_financial_report = _contains_positive_any(text, ["财务报表", "审计", "流水", "纳税", "财务数据"])
    profile.has_contract_or_proof = _contains_positive_any(text, ["合同", "订单", "合作证明", "算力使用证明", "平台使用证明", "客户证明"])
    profile.has_budget = _contains_positive_any(text, ["预算", "费用计划", "资金计划", "算力预算"])
    profile.has_team_resume = _contains_positive_any(text, ["团队简历", "成员简历", "核心团队", "创始人履历"])
    profile.has_local_scenario = _contains_positive_any(text, ["本地场景", "澳门落地", "杭州落地", "深圳落地", "园区试点", "高校试点"])
    profile.has_no_major_violation = _has_no_major_violation(text)
    profile.has_negative_record = _has_negative_record(text)
    profile.keywords = [k for k in KEYWORDS if k.lower() in text.lower() and not _is_negated_around(text, k)]
    return profile
