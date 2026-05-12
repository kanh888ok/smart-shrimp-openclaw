from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import streamlit as st

from src.company_parser import parse_company_profile
from src.generator import build_application_draft, build_demo_explanation, build_material_checklist, build_pitch, build_qna
from src.llm import LLMProvider
from src.matcher import rank_policies
from src.models import AnalysisReport
from src.policy_insights import city_policy_summaries, policy_countdown, validate_policy_library
from src.policy_loader import load_opc_policies, load_sample_policies, load_uploaded_policies
from src.report import render_report_markdown
from src.utils import results_to_csv

BASE_DIR = Path(__file__).parent
DEFAULT_COMPANY_TEXT = """
杭州云策智能科技公司是一家 AI 初创公司，团队 8 人，主营大模型客服与企业知识库问答系统。
公司成立于 2024 年，年营收 80 万元，研发投入占比 35%，已有 1 项软件著作权，暂无发明专利。
产品已经完成 Demo，并在园区企业客服场景完成试点部署。
目前希望申请算力补贴、科技型中小企业认定和创新创业资金。
企业已准备项目计划书，但尚未准备算力合同、正式财务报表和预算说明。
""".strip()

COMPANY_INPUT_TEMPLATE = """
企业名称：
注册地区：
所属行业：
成立时间：
职工总数：
上一年度销售收入：
资产总额：
科技人员占比：
研发费用占比：
知识产权情况：如软著、专利、商标、技术成果
产品/项目简介：
当前进展：如 Demo、原型、上线、试点、部署情况
客户/合同/订单/合作证明：
已准备材料：如营业执照、项目计划书、财务报表、预算说明、真实性承诺书
缺失或尚未准备的材料：
是否存在重大违法/失信记录：
希望申请的政策方向：如算力补贴、科技型中小企业、专精特新、创新创业资金
""".strip()

INPUT_FIELD_GUIDE = [
    ("企业基础信息", "企业名称、注册地区、成立时间、职工总数/团队规模"),
    ("规模指标", "上一年度销售收入、资产总额"),
    ("经营与研发", "行业方向、科技人员占比、研发费用占比"),
    ("技术与成果", "知识产权、专利/软著、Demo、原型、上线或试点"),
    ("业务证据", "客户案例、合同、订单、合作证明、场景落地"),
    ("申报材料", "营业执照、项目计划书、预算、财务报表、真实性承诺"),
    ("政策意向", "希望申请的政策类型或补贴方向"),
]


def _policy_library_stats(policies) -> dict:
    regions = sorted({p.region for p in policies if p.region})
    official_count = sum(1 for p in policies if p.official_url or str(p.source).startswith("http"))
    verified_count = sum(1 for p in policies if p.verified)
    max_amount = max([p.amount_max_yuan for p in policies] or [0])
    category_counts = Counter(p.category or "未分类" for p in policies)
    region_counts = Counter(p.region or "未标注" for p in policies)
    return {
        "count": len(policies),
        "regions": regions,
        "official_count": official_count,
        "verified_count": verified_count,
        "max_amount": max_amount,
        "category_counts": category_counts,
        "region_counts": region_counts,
    }


def _match_result_stats(results) -> dict:
    return {
        "total": len(results),
        "strong": sum(1 for r in results if r.score >= 80),
        "mid": sum(1 for r in results if 65 <= r.score < 80),
        "weak": sum(1 for r in results if 45 <= r.score < 65),
        "not_recommended": sum(1 for r in results if r.score < 45),
        "actionable": sum(1 for r in results if r.score >= 45),
    }


def _sme_readiness(profile) -> tuple[str, str]:
    if profile.company_scale == "大型企业":
        return "大型企业", "基础画像可识别，但当前政策库主要覆盖中小科技企业；建议关注重大专项、总部经济、平台经济、算力中心或产业链牵引类政策。"
    missing = []
    if not profile.employees:
        missing.append("职工总数")
    if not profile.annual_revenue_wan:
        missing.append("销售收入")
    if not profile.asset_total_wan:
        missing.append("资产总额")

    if profile.has_negative_record:
        return "信用风险", "存在重大违法、失信或安全/质量/环保风险线索，需先人工核实。"
    if profile.employees > 500 or profile.annual_revenue_wan > 20000 or profile.asset_total_wan > 20000:
        return "规模超限", "职工、销售收入或资产总额超过科技型中小企业常见门槛。"
    if missing:
        return "信息不足", "缺少：" + "、".join(missing) + "。"
    return "中小企业候选", "职工、销售收入和资产总额均在常见门槛内，仍需结合科技人员、研发投入和知识产权复核。"


def _status_badge(status: str) -> str:
    if status == "已覆盖":
        return "✅ 已覆盖"
    if status == "需复核":
        return "🟡 需复核"
    return "🔴 待补充"


def main() -> None:
    st.set_page_config(page_title="PolicyPilot", page_icon="🧭", layout="wide")
    st.title("PolicyPilot 企业政策申报与材料生成 AI Agent")
    st.caption("企业画像抽取 → 政策条款检索 → 匹配评分 → 材料缺口 → 风险提示 → 申报书初稿")

    with st.sidebar:
        st.header("配置")
        use_openai = st.toggle("启用 OpenAI 改写申报书", value=bool(os.getenv("OPENAI_API_KEY")))
        st.caption("未配置 API Key 时，系统使用本地模板；匹配、风险和材料判断不依赖外部 API。")
        opc_policy_path = BASE_DIR / "reference_repos" / "opc-policy" / "data" / "policies.json"
        dataset_options = ["公开来源政策库（推荐）"]
        if opc_policy_path.exists():
            dataset_options.append("OPC 一人公司政策库（本地参考）")
        dataset_options.append("模拟演示政策库")
        dataset_choice = st.selectbox(
            "内置政策库",
            dataset_options,
            index=0,
            help="公开来源政策库来自政府公开政策/公示的结构化摘要；OPC 本地参考库来自 MIT 开源项目 opcgate/opc-policy，用于本地对照研究；模拟演示政策库仅用于展示。",
        )
        uploaded_policies = st.file_uploader(
            "上传政策 PDF/TXT（可选）",
            type=["pdf", "txt"],
            accept_multiple_files=True,
        )
        st.caption("公开来源政策库仍用于申报准备度初筛，不代表官方审批预测。")
        st.divider()
        st.markdown("**产品定位**")
        st.write("不是 AI 写文案，而是政策申报前置决策系统。")

    col_left, col_right = st.columns([1.05, 1])

    with col_left:
        st.subheader("1. 企业材料输入")
        with st.expander("填写格式与建议包含的信息", expanded=False):
            st.write("可以直接粘贴企业简介，也可以按下面字段填写。信息越完整，材料缺口和风险判断越准确。")
            for title, desc in INPUT_FIELD_GUIDE:
                st.markdown(f"- **{title}**：{desc}")
            st.info("不确定或没有准备的材料也可以写出来，例如“尚未准备财务报表”。系统会把它识别为待补充项。")

        if "company_text_input" not in st.session_state:
            st.session_state["company_text_input"] = DEFAULT_COMPANY_TEXT

        c_template, c_demo = st.columns(2)
        with c_template:
            if st.button("使用标准填写模板", use_container_width=True):
                st.session_state["company_text_input"] = COMPANY_INPUT_TEMPLATE
        with c_demo:
            if st.button("恢复示例企业", use_container_width=True):
                st.session_state["company_text_input"] = DEFAULT_COMPANY_TEXT

        company_text = st.text_area(
            "企业简介 / 项目材料",
            key="company_text_input",
            height=360,
            help="可粘贴营业执照信息、项目介绍、团队规模、营收、知识产权、Demo、合同等材料。",
        )
        st.caption("推荐格式：企业名称、地区、行业、团队、营收、研发投入、知识产权、Demo/试点、合同/订单、已备材料、缺失材料、政策意向。")
        run = st.button("开始分析", type="primary", use_container_width=True)

    if dataset_choice.startswith("OPC"):
        sample_policies = load_opc_policies(BASE_DIR / "reference_repos" / "opc-policy" / "data" / "policies.json")
        if not sample_policies:
            st.warning("未找到 OPC 参考政策库，请确认 reference_repos/opc-policy/data/policies.json 已下载。")
    else:
        dataset_file = "public_policies.json" if dataset_choice.startswith("公开来源") else "sample_policies.json"
        sample_policies = load_sample_policies(BASE_DIR / "data" / dataset_file)
    uploaded = load_uploaded_policies(uploaded_policies)
    policies = uploaded + sample_policies
    stats = _policy_library_stats(policies)
    with st.sidebar:
        st.divider()
        st.markdown("**当前政策库概览**")
        st.write(f"政策数量：{stats['count']} 条")
        st.write(f"覆盖区域：{len(stats['regions'])} 个")
        st.write(f"官方来源：{stats['official_count']} 条")
        if stats["verified_count"]:
            st.write(f"已核验：{stats['verified_count']} 条")
        if stats["max_amount"]:
            st.write(f"最高金额：{stats['max_amount'] / 10000:g} 万元")
        st.caption("这里是当前选中政策库的总量；点击“开始分析”后，会显示与当前企业相关的候选数量。")
        with st.expander("查看数量拆解", expanded=False):
            st.markdown("**按政策类别**")
            for name, count in stats["category_counts"].most_common(8):
                st.write(f"{name}：{count} 条")
            st.markdown("**按区域**")
            for name, count in stats["region_counts"].most_common(8):
                st.write(f"{name}：{count} 条")

    if run and not policies:
        st.error("当前没有可用政策库。请切换内置政策库，或上传政策 PDF/TXT。")
        st.stop()

    if run or "results" in st.session_state:
        if run:
            profile = parse_company_profile(company_text)
            results = rank_policies(profile, policies)
            st.session_state["profile"] = profile
            st.session_state["results"] = results
            st.session_state["company_text"] = company_text
        else:
            profile = st.session_state["profile"]
            results = st.session_state["results"]

        with col_right:
            st.subheader("2. 企业画像抽取")
            c1, c2, c3 = st.columns(3)
            c1.metric("地区", profile.region)
            c2.metric("行业", profile.industry)
            c3.metric("团队", f"{profile.employees or 0} 人")
            c4, c5, c6 = st.columns(3)
            c4.metric("年营收", f"{profile.annual_revenue_wan:g} 万" if profile.annual_revenue_wan else "待补充")
            c5.metric("资产总额", f"{profile.asset_total_wan:g} 万" if profile.asset_total_wan else "待补充")
            c6.metric("知识产权", "有" if profile.has_ip else "无")
            c7, c8, c9 = st.columns(3)
            c7.metric("研发费用占比", f"{profile.rd_ratio_percent:g}%" if profile.rd_ratio_percent else "待补充")
            staff_ratio = profile.tech_staff_ratio_percent or profile.rd_staff_ratio_percent
            c8.metric("科技/研发人员占比", f"{staff_ratio:g}%" if staff_ratio else "待补充")
            c9.metric("信用风险", "有线索" if profile.has_negative_record else ("无重大记录" if profile.has_no_major_violation else "待核实"))
            sme_status, sme_note = _sme_readiness(profile)
            if sme_status == "中小企业候选":
                st.success(f"企业规模识别：{sme_status}｜{sme_note}")
            elif sme_status == "信息不足":
                st.warning(f"企业规模识别：{sme_status}｜{sme_note}")
            elif sme_status == "大型企业":
                st.info(f"企业规模识别：{sme_status}｜{sme_note}")
            else:
                st.error(f"企业规模识别：{sme_status}｜{sme_note}")
            tags = []
            if profile.is_group_company:
                tags.append("集团企业")
            if profile.is_public_company:
                tags.append("上市公司")
            if profile.is_platform_company:
                tags.append("平台型企业")
            if tags:
                st.caption("企业属性：" + "、".join(tags))
            st.write("**识别关键词：**", "、".join(profile.keywords) if profile.keywords else "暂无")

        st.divider()
        st.subheader("3. 可申报政策排行")

        result_stats = _match_result_stats(results)
        st.info(
            f"本次共从 {result_stats['total']} 条政策中筛选，"
            f"其中 {result_stats['actionable']} 条具备进一步评估价值："
            f"强匹配 {result_stats['strong']} 条，中高匹配 {result_stats['mid']} 条，"
            f"弱匹配 {result_stats['weak']} 条，暂不建议 {result_stats['not_recommended']} 条。"
        )

        with st.expander("政策库洞察：城市对比与数据质量", expanded=False):
            city_rows = city_policy_summaries(policies)
            if city_rows:
                default_regions = [row["区域"] for row in city_rows[:4]]
                selected_regions = st.multiselect(
                    "选择区域对比",
                    [row["区域"] for row in city_rows],
                    default=default_regions,
                )
                compare_rows = [row for row in city_rows if row["区域"] in selected_regions]
                st.dataframe(compare_rows, use_container_width=True, hide_index=True)
            else:
                st.caption("当前政策库暂无可对比的区域数据。")

            issues = validate_policy_library(policies)
            high = sum(1 for item in issues if item["级别"] == "高")
            medium = sum(1 for item in issues if item["级别"] == "中")
            low = sum(1 for item in issues if item["级别"] == "低")
            st.caption(f"数据质量检查：高风险 {high} 项｜中风险 {medium} 项｜低风险 {low} 项")
            if issues:
                st.dataframe(issues[:20], use_container_width=True, hide_index=True)
                if len(issues) > 20:
                    st.caption(f"仅展示前 20 项，共 {len(issues)} 项。")

        top_cols = st.columns(3)
        for i, r in enumerate(results[:3]):
            with top_cols[i]:
                st.metric(r.policy.name, f"{r.score} 分", r.level)
                st.caption(f"{r.policy.category}｜{r.policy.region}")

        selected_name = st.selectbox("选择一个政策查看细节", [r.policy.name for r in results])
        selected = next(r for r in results if r.policy.name == selected_name)

        d1, d2 = st.columns([1, 1])
        with d1:
            st.markdown(f"### {selected.policy.name}")
            st.write(f"**匹配等级：** {selected.level}")
            st.progress(min(selected.score / 100, 1.0))
            st.write(f"**政策区域：** {selected.policy.region}")
            if selected.policy.issuer:
                st.write(f"**发文单位：** {selected.policy.issuer}")
            if selected.policy.level or selected.policy.status:
                st.write(f"**政策层级/状态：** {selected.policy.level or '未标注'}｜{selected.policy.status or '未标注'}")
            if selected.policy.application_window:
                st.write(f"**申报窗口：** {selected.policy.application_window}")
            countdown = policy_countdown(selected.policy)
            if countdown:
                if countdown["status"] in ["即将截止", "已过期"]:
                    st.warning(f"窗口状态：{countdown['status']}｜{countdown['label']}｜剩余 {countdown['days_left']} 天")
                elif countdown["status"] == "常态化":
                    st.info(f"窗口状态：{countdown['status']}｜{countdown['label']}")
                else:
                    st.info(f"窗口状态：{countdown['status']}｜{countdown['label']}｜剩余 {countdown['days_left']} 天")
            if selected.policy.amount_max_yuan:
                st.write(f"**最高金额：** {selected.policy.amount_max_yuan / 10000:g} 万元")
            st.write(f"**支持方向：** {', '.join(selected.policy.target_industries)}")
            st.write(f"**政策激励：** {selected.policy.subsidy}")
            if selected.policy.official_url:
                st.link_button("查看官方原文", selected.policy.official_url)
            if selected.policy.updated_at or selected.policy.verified:
                st.caption(f"数据更新：{selected.policy.updated_at or '未标注'}｜{'已核验' if selected.policy.verified else '需复核'}")

            st.markdown("#### 评分拆解")
            st.json(selected.score_breakdown.to_dict(), expanded=False)

            st.markdown("#### 命中理由")
            for item in selected.hit_reasons:
                st.success(item)

        with d2:
            st.markdown("#### 材料状态")
            for item in selected.material_items:
                if item.status == "已覆盖":
                    st.success(f"{_status_badge(item.status)}｜{item.name}｜{item.reason}")
                elif item.status == "需复核":
                    st.warning(f"{_status_badge(item.status)}｜{item.name}｜{item.reason}")
                else:
                    st.error(f"{_status_badge(item.status)}｜{item.name}｜{item.reason}")

            st.markdown("#### 风险提示")
            for item in selected.risk_flags:
                if item.level == "高":
                    st.error(f"【{item.level}】{item.item}｜{item.mitigation}")
                elif item.level == "中":
                    st.warning(f"【{item.level}】{item.item}｜{item.mitigation}")
                else:
                    st.info(f"【{item.level}】{item.item}｜{item.mitigation}")

        st.markdown("#### 引用依据")
        for c in selected.cited_clauses:
            st.code(c)

        st.markdown("#### 下一步动作")
        st.write("\n".join(f"- {x}" for x in selected.next_actions))

        st.divider()
        st.subheader("4. 一键生成申报材料")
        llm = LLMProvider(use_openai=use_openai)
        draft = build_application_draft(profile, selected, llm=llm)
        checklist = build_material_checklist(selected)
        pitch = build_pitch(profile, results[:3])
        qna = build_qna(profile, results[:3])
        explanation = build_demo_explanation(profile, results[:3])
        report = AnalysisReport(profile, results, draft, checklist, pitch, qna, explanation)
        full_report = render_report_markdown(report)

        tab1, tab2, tab3, tab4 = st.tabs(["申报书初稿", "材料清单", "60 秒产品介绍", "常见问题"])
        with tab1:
            st.markdown(draft)
            st.download_button("下载申报书初稿 Markdown", data=draft.encode("utf-8"), file_name="policypilot_application_draft.md", mime="text/markdown")
        with tab2:
            st.markdown(checklist)
            st.download_button("下载材料清单", data=checklist.encode("utf-8"), file_name="policypilot_material_checklist.md", mime="text/markdown")
        with tab3:
            st.markdown(pitch)
            st.download_button("下载产品介绍", data=pitch.encode("utf-8"), file_name="policypilot_intro.md", mime="text/markdown")
        with tab4:
            st.markdown(qna)
            st.download_button("下载常见问题", data=qna.encode("utf-8"), file_name="policypilot_faq.md", mime="text/markdown")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("下载完整分析报告 Markdown", data=full_report.encode("utf-8"), file_name="policypilot_analysis_report.md", mime="text/markdown", use_container_width=True)
        with c2:
            st.download_button("下载政策匹配结果 CSV", data=results_to_csv(results), file_name="policypilot_policy_results.csv", mime="text/csv", use_container_width=True)

    else:
        with col_right:
            st.subheader("演示输出预览")
            st.info("点击“开始分析”后，将输出企业画像、政策匹配排行、缺失材料、风险提示和申报书初稿。")
            st.markdown(
                """
**你要强调的核心：**

- 不是单纯生成申报书；
- 是判断“能不能申报、缺什么、风险在哪、怎么提高通过率”；
- 可服务园区、孵化器、政企服务机构、中小企业。
"""
            )


if __name__ == "__main__":
    main()
