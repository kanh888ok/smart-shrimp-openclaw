from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date
from typing import Iterable

from .models import Policy


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    m = re.search(r"(20\d{2}|19\d{2})-(\d{2})-(\d{2})", str(value))
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _next_recurring_window(schedule: dict, today: date) -> tuple[date, date] | None:
    months = schedule.get("months") or list(range(1, 13))
    day_start = int(schedule.get("day_start") or 1)
    day_end = int(schedule.get("day_end") or 20)
    for year in range(today.year, today.year + 3):
        for month in sorted(int(m) for m in months):
            try:
                start = date(year, month, day_start)
                end = date(year, month, day_end)
            except ValueError:
                continue
            if end >= today:
                return start, end
    return None


def policy_countdown(policy: Policy, today: date | None = None) -> dict | None:
    today = today or date.today()
    schedule = policy.application_schedule or {}

    if schedule:
        schedule_type = schedule.get("type")
        if schedule_type == "deadline":
            end = _parse_iso(schedule.get("deadline"))
            label = f"截止 {schedule.get('deadline')}" if schedule.get("deadline") else policy.application_window
            return _countdown_payload(label, end, today)
        if schedule_type == "window":
            start = _parse_iso(schedule.get("start"))
            end = _parse_iso(schedule.get("end"))
            label = schedule.get("display") or f"{schedule.get('start', '')} 至 {schedule.get('end', '')}".strip(" 至")
            return _countdown_payload(label, end, today, start)
        if schedule_type == "recurring":
            window = _next_recurring_window(schedule, today)
            if window:
                start, end = window
                label = schedule.get("display") or f"{start.isoformat()} 至 {end.isoformat()}"
                return _countdown_payload(label, end, today, start)

    window_text = policy.application_window or ""
    range_match = re.search(r"(20\d{2}-\d{2}-\d{2})\s*(?:至|-|~)\s*(20\d{2}-\d{2}-\d{2})", window_text)
    if range_match:
        start = _parse_iso(range_match.group(1))
        end = _parse_iso(range_match.group(2))
        return _countdown_payload(window_text, end, today, start)

    end = _parse_iso(window_text or policy.expire_date)
    if end:
        return _countdown_payload(window_text or f"截止 {end.isoformat()}", end, today)

    if any(k in window_text for k in ["常态化", "滚动", "长期"]):
        return {"label": window_text, "status": "常态化", "days_left": None, "end_date": "", "start_date": ""}

    return None


def _countdown_payload(label: str, end: date | None, today: date, start: date | None = None) -> dict | None:
    if not end:
        return None
    days_left = (end - today).days
    if days_left < 0:
        status = "已过期"
    elif days_left <= 7:
        status = "即将截止"
    elif days_left <= 30:
        status = "30天内截止"
    else:
        status = "进行中"
    return {
        "label": label,
        "status": status,
        "days_left": days_left,
        "end_date": end.isoformat(),
        "start_date": start.isoformat() if start else "",
    }


def city_policy_summaries(policies: Iterable[Policy]) -> list[dict]:
    groups: dict[str, list[Policy]] = defaultdict(list)
    for policy in policies:
        region = policy.region or "未标注"
        if region != "全国":
            groups[region].append(policy)

    rows = []
    for region, items in groups.items():
        categories = Counter(p.category for p in items if p.category)
        countdowns = [policy_countdown(p) for p in items]
        active_windows = [c for c in countdowns if c and isinstance(c.get("days_left"), int) and c["days_left"] >= 0]
        nearest = min(active_windows, key=lambda c: c["days_left"]) if active_windows else None
        rows.append({
            "区域": region,
            "政策数": len(items),
            "官方来源": sum(1 for p in items if p.official_url or str(p.source).startswith("http")),
            "已核验": sum(1 for p in items if p.verified),
            "最高金额(万元)": round(max([p.amount_max_yuan for p in items] or [0]) / 10000, 2),
            "主要类别": "、".join([name for name, _ in categories.most_common(3)]),
            "最近窗口": nearest["label"] if nearest else "未标注",
            "剩余天数": nearest["days_left"] if nearest else "",
        })
    return sorted(rows, key=lambda row: (row["政策数"], row["最高金额(万元)"]), reverse=True)


def validate_policy_library(policies: Iterable[Policy]) -> list[dict]:
    issues: list[dict] = []
    for policy in policies:
        name = policy.name or policy.id or "未命名政策"
        if not policy.name:
            issues.append(_issue("高", name, "缺少政策名称", "补充政策名称。"))
        if not policy.region:
            issues.append(_issue("高", name, "缺少政策区域", "补充国家、省、市或区县。"))
        if not policy.requirements:
            issues.append(_issue("中", name, "缺少申报条件", "补充主体资格、注册地、行业、规模等要求。"))
        if not policy.required_materials:
            issues.append(_issue("中", name, "缺少材料清单", "补充营业执照、财务、项目计划书等材料要求。"))
        if not (policy.official_url or str(policy.source).startswith("http")):
            issues.append(_issue("中", name, "缺少官方来源链接", "补充政策原文或主管部门链接。"))
        if not policy.application_window and not policy.application_method:
            issues.append(_issue("低", name, "缺少申报窗口/方式", "补充截止时间、滚动申报说明或办理入口。"))
        if not policy.issuer:
            issues.append(_issue("低", name, "缺少发文单位", "补充主管部门或发文机关。"))
        if policy.status and policy.status not in ["active", "draft"]:
            issues.append(_issue("中", name, f"政策状态为 {policy.status}", "复核是否仍适合推荐。"))
    return issues


def _issue(level: str, policy_name: str, item: str, suggestion: str) -> dict:
    return {"级别": level, "政策": policy_name, "问题": item, "建议": suggestion}
