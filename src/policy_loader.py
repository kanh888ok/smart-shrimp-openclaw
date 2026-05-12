from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from pypdf import PdfReader

from .models import Policy


OPC_CATEGORY_LABELS = {
    "subsidy": "财政补贴",
    "tax": "税费优惠",
    "space": "空间/工位支持",
    "talent": "人才政策",
    "computing": "算力支持",
    "scenario": "场景示范",
    "competition": "赛事/项目征集",
    "loan": "融资贷款",
    "registration": "注册便利",
    "comprehensive": "综合政策",
}


def _dedupe(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys([str(x).strip() for x in items if str(x).strip()]))


def load_sample_policies(path: str | Path = "data/sample_policies.json") -> List[Policy]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [Policy.from_dict(item) for item in data]


def _schedule_label(schedule) -> str:
    if not schedule:
        return ""
    if isinstance(schedule, str):
        return schedule
    if not isinstance(schedule, dict):
        return ""
    if schedule.get("display"):
        return str(schedule["display"])
    schedule_type = schedule.get("type")
    if schedule_type == "deadline" and schedule.get("deadline"):
        return f"截止 {schedule['deadline']}"
    if schedule_type == "window":
        start = schedule.get("start", "")
        end = schedule.get("end", "")
        return f"{start} 至 {end}".strip(" 至")
    if schedule_type == "recurring":
        months = "/".join(str(x) for x in schedule.get("months", []))
        start = schedule.get("day_start", "")
        end = schedule.get("day_end", "")
        return f"每年{months + '月' if months else ''}{start}-{end}日"
    return ""


def _requirements_from_opc(req: dict) -> List[str]:
    items: List[str] = []
    if req.get("registration_location"):
        items.append(f"注册地要求：{req['registration_location']}")
    if req.get("operation_location"):
        items.append(f"经营地要求：{req['operation_location']}")
    if req.get("company_age_max_years"):
        items.append(f"企业成立年限不超过{req['company_age_max_years']}年")
    if req.get("min_employees"):
        items.append(f"员工人数不少于{req['min_employees']}人")
    if req.get("max_employees"):
        items.append(f"员工人数不超过{req['max_employees']}人")
    if req.get("social_insurance_months"):
        items.append(f"社保缴纳不少于{req['social_insurance_months']}个月")
    if req.get("industries"):
        items.append("适用行业：" + "、".join(req["industries"]))
    if req.get("qualifications"):
        items.append("资质要求：" + "、".join(req["qualifications"]))
    if req.get("founder_identity"):
        items.append("创始人/法人身份要求：" + "、".join(req["founder_identity"]))
    items.extend(req.get("other", []) or [])
    return _dedupe(items or ["符合政策文件规定的注册地、产业方向和主体资格要求"])


def _materials_for_opc(category: str, requirements: List[str]) -> List[str]:
    materials = ["营业执照", "企业简介", "项目计划书", "真实性承诺书"]
    text = category + " ".join(requirements)
    if any(k in text for k in ["算力", "computing"]):
        materials.extend(["算力服务合同", "算力费用发票", "算力使用计划", "预算说明"])
    if any(k in text for k in ["补贴", "资金", "subsidy", "loan"]):
        materials.extend(["财务报表", "纳税证明", "预算说明"])
    if any(k in text for k in ["空间", "工位", "租金", "space"]):
        materials.extend(["租赁合同", "入驻证明"])
    if any(k in text for k in ["场景", "示范", "scenario"]):
        materials.extend(["场景合作证明", "部署截图", "试点报告"])
    if any(k in text for k in ["人才", "talent"]):
        materials.extend(["团队简历", "社保证明", "学历或人才证明"])
    if any(k in text for k in ["知识产权", "AI", "人工智能", "科技", "研发"]):
        materials.extend(["知识产权证明", "研发费用说明"])
    return _dedupe(materials)


def _policy_from_opc(item: dict) -> Policy:
    requirements_obj = item.get("requirements", {}) or {}
    application = item.get("application", {}) or {}
    links = item.get("links", {}) or {}
    benefits_obj = item.get("benefits", []) or []
    benefits = _dedupe([f"{b.get('item', '政策支持')}：{b.get('amount', '')}".strip("：") for b in benefits_obj])
    industries = _dedupe(requirements_obj.get("industries", []) or [])
    tags = _dedupe(item.get("tags", []) or [])
    category_raw = str(item.get("category", "comprehensive"))
    category = OPC_CATEGORY_LABELS.get(category_raw, category_raw)
    requirements = _requirements_from_opc(requirements_obj)
    official_url = str(links.get("official", "") or application.get("url", ""))
    region = str(item.get("district") or item.get("city") or item.get("province") or "全国")

    keywords = _dedupe(
        tags
        + industries
        + [item.get("city", ""), item.get("district", ""), category, item.get("name", "")]
        + [b.get("item", "") for b in benefits_obj]
    )
    risk_rules = [
        "OPC 参考政策库来自第三方 MIT 开源项目，正式使用前需回到官方链接复核。",
        "政策窗口、金额和申报方式可能随地方通知变化，需核对最新公告。",
    ]
    if not item.get("verified", False):
        risk_rules.append("该条政策未标记为已核验，建议优先人工确认来源。")
    if item.get("status") and item.get("status") != "active":
        risk_rules.append(f"政策状态为 {item.get('status')}，可能不在有效申报期。")
    if item.get("actual_cases"):
        risk_rules.append(str(item["actual_cases"]))

    return Policy(
        id=str(item.get("id", "")),
        name=str(item.get("name", "未命名政策")),
        region=region,
        category=category,
        target_industries=industries or tags or ["人工智能", "软件"],
        subsidy="；".join(benefits) if benefits else str(item.get("summary", "")),
        requirements=requirements,
        required_materials=_materials_for_opc(category_raw + category, requirements + tags),
        keywords=keywords,
        risk_rules=_dedupe(risk_rules),
        source=official_url or "opcgate/opc-policy MIT",
        level=str(item.get("level", "")),
        issuer=str(item.get("issuer", "")),
        status=str(item.get("status", "")),
        publish_date=str(item.get("publish_date", "")),
        effective_date=str(item.get("effective_date", "")),
        expire_date=str(item.get("expire_date", "")),
        application_window=str(application.get("next_window") or application.get("deadline") or _schedule_label(application.get("schedule", ""))),
        application_method=str(application.get("method", "")),
        application_url=str(application.get("url", "")),
        official_url=official_url,
        updated_at=str(item.get("updated_at", "")),
        verified=bool(item.get("verified", False)),
        amount_max_yuan=max([float(b.get("amount_max", 0) or 0) for b in benefits_obj] or [0.0]),
        benefits=benefits,
        application_schedule=dict(application.get("schedule", {}) or {}),
    )


def load_opc_policies(path: str | Path = "reference_repos/opc-policy/data/policies.json") -> List[Policy]:
    """加载 opcgate/opc-policy 的 MIT 结构化政策库，并转换为本项目 Policy。"""
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("policies", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    return [_policy_from_opc(item) for item in items]


def extract_text_from_pdf(file_obj) -> str:
    reader = PdfReader(file_obj)
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts).strip()


def read_text_file(file_obj) -> str:
    raw = file_obj.read()
    if isinstance(raw, bytes):
        for enc in ("utf-8", "gb18030", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore")
    return str(raw)


def parse_policy_text_to_policy(text: str, fallback_id: str, source: str = "uploaded_policy") -> Policy:
    """将上传政策文本粗略转成 Policy。正式系统可替换为 LLM 结构化抽取。"""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0][:80] if lines else "上传政策文件"

    region = "全国"
    for r in ["杭州", "浙江", "上海", "北京", "深圳", "广州", "澳门", "香港", "成都", "苏州", "南京", "合肥", "武汉", "西安"]:
        if r in text:
            region = r
            break

    target_industries = []
    for ind in ["人工智能", "大模型", "软件", "机器人", "智能硬件", "AIoT", "医疗", "教育", "政务", "文创", "旅游", "智能制造"]:
        if ind in text:
            target_industries.append(ind)
    if not target_industries:
        target_industries = ["人工智能", "软件"]

    required_materials = []
    for item in [
        "营业执照", "财务报表", "项目计划书", "商业计划书", "知识产权证明", "专利", "软著", "团队简历",
        "预算说明", "合同", "场景合作证明", "项目技术方案", "用户数据", "审计报告",
    ]:
        if item in text:
            required_materials.append(item)
    if not required_materials:
        required_materials = ["营业执照", "企业简介", "项目计划书", "财务报表"]

    keywords = []
    for k in ["算力", "补贴", "研发", "知识产权", "人工智能", "大模型", "场景", "示范", "创业", "硬件", "打样", "资质"]:
        if k in text:
            keywords.append(k)

    requirement_markers = ["条件", "要求", "符合", "应当", "需要", "申报主体", "支持对象", "申报范围"]
    requirements = [line for line in lines if any(k in line for k in requirement_markers)]
    if not requirements:
        requirements = ["符合政策文件规定的申报主体、产业方向和材料要求"]

    risk_rules = [
        "上传政策由规则解析生成，建议人工复核关键条款",
        "材料缺失或资格条件不明确会影响申报通过率",
    ]

    return Policy(
        id=fallback_id,
        name=title,
        region=region,
        category="上传政策",
        target_industries=target_industries,
        subsidy="以政策文件原文为准",
        requirements=requirements[:10],
        required_materials=list(dict.fromkeys(required_materials)),
        keywords=list(dict.fromkeys(keywords or target_industries)),
        risk_rules=risk_rules,
        source=source,
    )


def load_uploaded_policies(uploaded_files: Optional[Iterable]) -> List[Policy]:
    policies: List[Policy] = []
    if not uploaded_files:
        return policies

    for i, file in enumerate(uploaded_files, start=1):
        name = getattr(file, "name", f"uploaded_{i}")
        if name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file)
        else:
            text = read_text_file(file)
        if text.strip():
            policies.append(parse_policy_text_to_policy(text, fallback_id=f"UPLOAD-{i}", source=name))
    return policies
