from __future__ import annotations

import csv
import io
from typing import Iterable

from .models import MatchResult


def results_to_csv(results: Iterable[MatchResult]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["政策名称", "匹配分", "等级", "政策类别", "区域", "发文单位", "申报窗口", "最高金额", "官方来源", "命中理由", "缺失材料", "风险提示"])
    for r in results:
        writer.writerow([
            r.policy.name,
            r.score,
            r.level,
            r.policy.category,
            r.policy.region,
            r.policy.issuer,
            r.policy.application_window,
            r.policy.amount_max_yuan,
            r.policy.official_url or r.policy.source,
            "；".join(r.hit_reasons),
            "；".join(r.missing_items),
            "；".join([f"【{x.level}】{x.item}" for x in r.risk_flags]),
        ])
    return output.getvalue().encode("utf-8-sig")
