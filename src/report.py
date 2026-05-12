from __future__ import annotations

import json
from pathlib import Path

from .models import AnalysisReport, MatchResult


def render_match_markdown(match: MatchResult, index: int = 1) -> str:
    risks = "\n".join(f"- 【{r.level}】{r.item}：{r.mitigation}" for r in match.risk_flags) or "无"
    materials = "\n".join(f"- {m.name}：{m.status}（{m.reason}）" for m in match.material_items) or "无"
    return f"""
## {index}. {match.policy.name}

- 匹配分：{match.score}
- 匹配等级：{match.level}
- 区域：{match.policy.region}
- 类别：{match.policy.category}
- 激励：{match.policy.subsidy}
- 发文单位：{match.policy.issuer or '未标注'}
- 申报窗口：{match.policy.application_window or '未标注'}
- 官方来源：{match.policy.official_url or match.policy.source or '未标注'}

### 评分拆解
- 区域：{match.score_breakdown.region:.1f}
- 产业：{match.score_breakdown.industry:.1f}
- 资格：{match.score_breakdown.qualification:.1f}
- 材料：{match.score_breakdown.material:.1f}
- 证据：{match.score_breakdown.evidence:.1f}
- 扣分：{match.score_breakdown.penalty:.1f}

### 命中理由
{chr(10).join(f'- {x}' for x in match.hit_reasons) or '无'}

### 材料状态
{materials}

### 风险提示
{risks}

### 引用依据
{chr(10).join(f'- {x}' for x in match.cited_clauses) or '无'}

### 下一步动作
{chr(10).join(f'- {x}' for x in match.next_actions) or '无'}
""".strip()


def render_report_markdown(report: AnalysisReport) -> str:
    profile = report.company
    matches_md = "\n\n".join(render_match_markdown(m, i + 1) for i, m in enumerate(report.matches[:5]))
    return f"""
# PolicyPilot 企业政策申报分析报告

## 企业画像

- 企业名称：{profile.name}
- 地区：{profile.region}
- 行业：{profile.industry}
- 成立年份：{profile.founded_year or '待补充'}
- 团队规模：{profile.employees or '待补充'} 人
- 年营收：{profile.annual_revenue_wan or '待补充'} 万元
- 资产总额：{profile.asset_total_wan or '待补充'} 万元
- 研发投入占比：{profile.rd_ratio_percent or '待补充'}%
- 研发人员占比：{profile.rd_staff_ratio_percent or '待补充'}%
- 科技人员占比：{profile.tech_staff_ratio_percent or '待补充'}%
- 知识产权：{'有' if profile.has_ip else '无'}
- Demo/试点：{'有' if profile.has_demo else '无'}
- 关键词：{'、'.join(profile.keywords) if profile.keywords else '暂无'}

## 政策匹配排行

{matches_md}

---

{report.material_checklist}

---

{report.application_draft}

---

{report.pitch_script}

---

{report.qna}

---

## Demo 说明

{report.demo_explanation}
""".strip()


def save_report(report: AnalysisReport, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "analysis_report.md").write_text(render_report_markdown(report), encoding="utf-8")
    (output / "analysis_report.json").write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "application_draft.md").write_text(report.application_draft, encoding="utf-8")
    (output / "material_checklist.md").write_text(report.material_checklist, encoding="utf-8")
    (output / "product_intro.md").write_text(report.pitch_script, encoding="utf-8")
    (output / "faq.md").write_text(report.qna, encoding="utf-8")
