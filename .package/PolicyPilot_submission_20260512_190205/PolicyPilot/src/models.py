from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal

RiskLevel = Literal["高", "中", "低"]
MaterialStatus = Literal["已覆盖", "待补充", "需复核"]


@dataclass
class Policy:
    """政策主数据。MVP 用 JSON 政策库，也支持上传 PDF/TXT 后粗解析。"""

    id: str
    name: str
    region: str
    category: str
    target_industries: List[str]
    subsidy: str
    requirements: List[str]
    required_materials: List[str]
    keywords: List[str]
    risk_rules: List[str]
    source: str = "sample_policy_library"
    level: str = ""
    issuer: str = ""
    status: str = ""
    publish_date: str = ""
    effective_date: str = ""
    expire_date: str = ""
    application_window: str = ""
    application_method: str = ""
    application_url: str = ""
    official_url: str = ""
    updated_at: str = ""
    verified: bool = False
    amount_max_yuan: float = 0.0
    benefits: List[str] = field(default_factory=list)
    application_schedule: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Policy":
        return Policy(
            id=str(data.get("id", "")),
            name=str(data.get("name", "未命名政策")),
            region=str(data.get("region", "全国")),
            category=str(data.get("category", "其他")),
            target_industries=list(data.get("target_industries", [])),
            subsidy=str(data.get("subsidy", "")),
            requirements=list(data.get("requirements", [])),
            required_materials=list(data.get("required_materials", [])),
            keywords=list(data.get("keywords", [])),
            risk_rules=list(data.get("risk_rules", [])),
            source=str(data.get("source", "sample_policy_library")),
            level=str(data.get("level", "")),
            issuer=str(data.get("issuer", "")),
            status=str(data.get("status", "")),
            publish_date=str(data.get("publish_date", "")),
            effective_date=str(data.get("effective_date", "")),
            expire_date=str(data.get("expire_date", "")),
            application_window=str(data.get("application_window", "")),
            application_method=str(data.get("application_method", "")),
            application_url=str(data.get("application_url", "")),
            official_url=str(data.get("official_url", "")),
            updated_at=str(data.get("updated_at", "")),
            verified=bool(data.get("verified", False)),
            amount_max_yuan=float(data.get("amount_max_yuan", 0.0) or 0.0),
            benefits=list(data.get("benefits", [])),
            application_schedule=dict(data.get("application_schedule", {}) or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CompanyProfile:
    """企业画像。先从自然语言简介中抽取；后续可以接营业执照、财报、软著等真实材料。"""

    raw_text: str
    name: str = "未命名企业"
    region: str = "未知"
    industry: str = "未知"
    founded_year: int = 0
    employees: int = 0
    annual_revenue_wan: float = 0.0
    asset_total_wan: float = 0.0
    rd_ratio_percent: float = 0.0
    rd_staff_ratio_percent: float = 0.0
    tech_staff_ratio_percent: float = 0.0
    financing_stage: str = "未披露"
    company_scale: str = "未知"
    is_public_company: bool = False
    is_group_company: bool = False
    is_platform_company: bool = False
    has_ip: bool = False
    has_patent: bool = False
    has_software_copyright: bool = False
    has_demo: bool = False
    has_financial_report: bool = False
    has_contract_or_proof: bool = False
    has_budget: bool = False
    has_team_resume: bool = False
    has_local_scenario: bool = False
    has_no_major_violation: bool = False
    has_negative_record: bool = False
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyClause:
    policy_id: str
    policy_name: str
    clause_type: Literal["requirement", "material", "risk", "subsidy", "keyword"]
    text: str
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MaterialItem:
    name: str
    status: MaterialStatus
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskFlag:
    level: RiskLevel
    item: str
    mitigation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreBreakdown:
    region: float
    industry: float
    qualification: float
    material: float
    evidence: float
    penalty: float

    @property
    def total(self) -> float:
        return max(0.0, min(100.0, self.region + self.industry + self.qualification + self.material + self.evidence - self.penalty))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["total"] = round(self.total, 1)
        return d


@dataclass
class MatchResult:
    policy: Policy
    score: float
    level: str
    score_breakdown: ScoreBreakdown
    hit_reasons: List[str]
    material_items: List[MaterialItem]
    missing_items: List[str]
    risk_flags: List[RiskFlag]
    cited_clauses: List[str]
    next_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy": self.policy.to_dict(),
            "score": self.score,
            "level": self.level,
            "score_breakdown": self.score_breakdown.to_dict(),
            "hit_reasons": self.hit_reasons,
            "material_items": [m.to_dict() for m in self.material_items],
            "missing_items": self.missing_items,
            "risk_flags": [r.to_dict() for r in self.risk_flags],
            "cited_clauses": self.cited_clauses,
            "next_actions": self.next_actions,
        }


@dataclass
class AnalysisReport:
    company: CompanyProfile
    matches: List[MatchResult]
    application_draft: str
    material_checklist: str
    pitch_script: str
    qna: str
    demo_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company.to_dict(),
            "matches": [m.to_dict() for m in self.matches],
            "application_draft": self.application_draft,
            "material_checklist": self.material_checklist,
            "pitch_script": self.pitch_script,
            "qna": self.qna,
            "demo_explanation": self.demo_explanation,
        }
