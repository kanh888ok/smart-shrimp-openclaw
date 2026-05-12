from pathlib import Path
from datetime import date

from src.company_parser import parse_company_profile
from src.generator import build_application_draft, build_material_checklist, build_pitch
from src.matcher import rank_policies
from src.models import Policy
from src.policy_insights import city_policy_summaries, policy_countdown, validate_policy_library
from src.policy_loader import load_opc_policies, load_sample_policies

ROOT = Path(__file__).resolve().parents[1]


def test_company_parser_extracts_core_fields():
    text = "杭州某 AI 初创公司，团队 8 人，年营收 80 万元，研发投入占比 35%，已有 1 项软件著作权，产品完成 Demo。"
    profile = parse_company_profile(text)
    assert profile.region == "杭州"
    assert profile.employees == 8
    assert profile.annual_revenue_wan == 80
    assert profile.rd_ratio_percent == 35
    assert profile.has_ip is True
    assert profile.has_demo is True


def test_company_parser_handles_large_enterprise_units():
    text = (
        "阿里巴巴集团是一家全球领先的互联网科技企业，团队超20万人，"
        "主营核心电商、云计算、智慧物流与本地生活服务。"
        "公司成立于1999年，年营收超9000亿元，研发投入占比约6%，"
        "已有数万项国内外发明专利及软件著作权。"
    )
    profile = parse_company_profile(text)
    assert profile.name == "阿里巴巴集团"
    assert profile.region == "杭州"
    assert profile.industry == "互联网"
    assert profile.employees == 200000
    assert profile.annual_revenue_wan == 90000000
    assert profile.rd_ratio_percent == 6
    assert profile.company_scale == "大型企业"
    assert profile.is_group_company is True
    assert profile.has_ip is True


def test_company_parser_handles_large_platform_company_profile():
    text = (
        "腾讯控股有限公司是一家总部位于深圳的平台型互联网企业，业务覆盖社交、游戏、云计算和人工智能。"
        "公司为港股上市公司，员工人数约10万人，年营收超过6000亿元，总资产超过1.5万亿元，"
        "持续投入AI大模型和云基础设施研发，拥有大量专利。"
    )
    profile = parse_company_profile(text)
    assert profile.name == "腾讯控股有限公司"
    assert profile.region == "深圳"
    assert profile.industry == "互联网"
    assert profile.employees == 100000
    assert profile.annual_revenue_wan == 60000000
    assert profile.asset_total_wan == 150000000
    assert profile.company_scale == "大型企业"
    assert profile.is_public_company is True
    assert profile.is_platform_company is True
    assert profile.has_ip is True


def test_company_parser_uses_known_company_industry_when_description_is_broad():
    text = (
        "华为技术有限公司是全球领先的信息与通信基础设施企业，总部在深圳，员工约20万人，"
        "营业收入超过7000亿元，资产总额超过1万亿元，拥有大量通信、芯片和人工智能相关专利。"
    )
    profile = parse_company_profile(text)
    assert profile.name == "华为技术有限公司"
    assert profile.region == "深圳"
    assert profile.industry == "通信设备"
    assert profile.employees == 200000
    assert profile.annual_revenue_wan == 70000000
    assert profile.asset_total_wan == 100000000
    assert profile.company_scale == "大型企业"
    assert profile.has_ip is True


def test_known_enterprise_table_covers_representative_large_companies():
    cases = [
        ("商汤科技是一家人工智能公司，员工约6000人，营业收入超过30亿元，拥有大量算法专利。", "商汤", "上海", "人工智能"),
        ("宁德时代主营动力电池，员工超10万人，年营收超4000亿元，拥有大量专利。", "宁德时代", "宁德", "动力电池"),
        ("美的集团是一家家电与智能制造集团企业，员工超15万人，年营收超3000亿元。", "美的", "佛山", "家电"),
        ("顺丰控股提供智慧物流服务，员工超过15万人，年营收超过2500亿元。", "顺丰", "深圳", "智慧物流"),
        ("中芯国际是半导体制造企业，员工超过2万人，年营收超过600亿元。", "中芯国际", "上海", "半导体"),
    ]
    for text, name_part, region, industry in cases:
        profile = parse_company_profile(text)
        assert name_part in profile.name
        assert profile.region == region
        assert profile.industry == industry
        assert profile.company_scale == "大型企业"


def test_known_enterprise_short_aliases_require_company_context():
    profile = parse_company_profile("这是一个理想状态下的企业申报材料，团队20人，年营收200万元。")
    assert profile.name == "示例企业"
    assert profile.region == "未知"
    assert profile.industry != "新能源汽车"


def test_company_parser_prefers_own_business_over_customer_industries():
    text = (
        "杭州分叉智能科技有限公司（影刀RPA）是一家专注于机器人流程自动化及AI技术研发的高新技术企业，"
        "团队规模约400人。公司成立于2019年，近年来营收保持高速增长，研发人员占比超60%，"
        "拥有数十项软件著作权及核心发明专利。核心产品已在上万家电商、金融、物流等行业的企业客户中完成商业化落地部署。"
    )
    profile = parse_company_profile(text)
    assert profile.region == "杭州"
    assert profile.industry in ["人工智能", "RPA", "机器人流程自动化"]
    assert profile.industry != "电商"
    assert profile.employees == 400
    assert profile.annual_revenue_wan == 0
    assert profile.rd_staff_ratio_percent == 60
    assert profile.has_ip is True


def test_company_parser_extracts_complete_sme_profile():
    text = (
        "杭州星河智能软件有限公司注册在杭州，主营工业视觉检测软件，成立于2021年。"
        "职工总数86人，上一年度销售收入3200万元，资产总额1800万元，"
        "科技人员占比45%，研发费用占比12%，拥有3项软件著作权和1项发明专利。"
        "产品已在两家制造企业完成试点部署，已有客户合同和项目预算说明，近三年无重大违法失信记录。"
    )
    profile = parse_company_profile(text)
    assert profile.region == "杭州"
    assert profile.industry in ["软件", "人工智能", "智能制造", "工业智能"]
    assert profile.employees == 86
    assert profile.annual_revenue_wan == 3200
    assert profile.asset_total_wan == 1800
    assert profile.tech_staff_ratio_percent == 45
    assert profile.rd_ratio_percent == 12
    assert profile.has_ip is True
    assert profile.has_demo is True
    assert profile.has_contract_or_proof is True
    assert profile.has_budget is True
    assert profile.has_no_major_violation is True


def test_company_parser_keeps_missing_sme_fields_empty():
    text = (
        "苏州云启科技有限公司是一家AI客服软件企业，员工45人，已有软著和Demo，"
        "但暂未整理上一年度销售收入和资产总额证明。"
    )
    profile = parse_company_profile(text)
    assert profile.employees == 45
    assert profile.annual_revenue_wan == 0
    assert profile.asset_total_wan == 0
    assert profile.has_ip is True
    assert profile.has_demo is True


def test_sme_policy_flags_asset_size_and_credit_risk():
    policies = load_sample_policies(ROOT / "data" / "sample_policies.json")
    profile = parse_company_profile(
        "杭州某软件企业，员工120人，销售收入8000万元，资产总额3亿元，研发费用占比10%，已有软著，但存在严重失信记录。"
    )
    results = rank_policies(profile, policies)
    sme_result = next(r for r in results if "中小企业" in r.policy.name)
    assert sme_result.score <= 44
    assert any("企业规模超过中小企业" in r.item for r in sme_result.risk_flags)
    assert any("重大违法/失信" in r.item for r in sme_result.risk_flags)


def test_policy_matching_returns_ranked_results():
    policies = load_sample_policies(ROOT / "data" / "sample_policies.json")
    profile = parse_company_profile(
        "杭州 AI 初创公司，团队 8 人，主营大模型客服，年营收 80 万元，有软著和 Demo，准备申请算力补贴。"
    )
    results = rank_policies(profile, policies)
    assert len(results) >= 3
    assert results[0].score >= results[-1].score
    assert any("算力" in r.policy.name for r in results[:3])


def test_large_company_is_capped_for_sme_policy():
    policies = load_sample_policies(ROOT / "data" / "sample_policies.json")
    profile = parse_company_profile(
        "阿里巴巴集团是一家互联网科技企业，团队超20万人，年营收超9000亿元，已有专利和软件著作权。"
    )
    results = rank_policies(profile, policies)
    sme_result = next(r for r in results if "中小企业" in r.policy.name)
    assert sme_result.score <= 44
    assert any("企业规模超过中小企业" in r.item for r in sme_result.risk_flags)


def test_load_opc_reference_policies_when_available():
    path = ROOT / "reference_repos" / "opc-policy" / "data" / "policies.json"
    if not path.exists():
        return
    policies = load_opc_policies(path)
    assert len(policies) >= 50
    first = policies[0]
    assert first.name
    assert first.region
    assert first.category
    assert first.required_materials
    assert first.official_url or first.source
    assert any(p.application_window or p.application_method for p in policies)


def test_policy_insights_countdown_and_city_summary():
    policy = Policy(
        id="P1",
        name="深圳算力券",
        region="深圳",
        category="算力支持",
        target_industries=["人工智能"],
        subsidy="最高100万元",
        requirements=["注册地要求：深圳"],
        required_materials=["营业执照", "算力服务合同"],
        keywords=["算力"],
        risk_rules=[],
        issuer="深圳市相关部门",
        official_url="https://example.gov.cn/policy",
        amount_max_yuan=1000000,
        application_schedule={"type": "deadline", "deadline": "2026-05-20"},
        verified=True,
    )
    countdown = policy_countdown(policy, today=date(2026, 5, 12))
    assert countdown is not None
    assert countdown["days_left"] == 8
    assert countdown["status"] == "30天内截止"

    rows = city_policy_summaries([policy])
    assert rows[0]["区域"] == "深圳"
    assert rows[0]["政策数"] == 1
    assert rows[0]["最高金额(万元)"] == 100


def test_policy_library_validation_flags_missing_source():
    policy = Policy(
        id="P2",
        name="缺来源政策",
        region="杭州",
        category="财政补贴",
        target_industries=["软件"],
        subsidy="补贴",
        requirements=[],
        required_materials=[],
        keywords=[],
        risk_rules=[],
    )
    issues = validate_policy_library([policy])
    assert any(item["问题"] == "缺少官方来源链接" for item in issues)
    assert any(item["问题"] == "缺少申报条件" for item in issues)


def test_generators_produce_markdown():
    policies = load_sample_policies(ROOT / "data" / "sample_policies.json")
    profile = parse_company_profile(
        "杭州 AI 初创公司，团队 8 人，主营大模型客服，年营收 80 万元，有软著和 Demo，准备申请算力补贴。"
    )
    results = rank_policies(profile, policies)
    draft = build_application_draft(profile, results[0])
    checklist = build_material_checklist(results[0])
    pitch = build_pitch(profile, results[:3])
    assert "申报书初稿" in draft
    assert "材料清单" in checklist
    assert "PolicyPilot" in pitch
