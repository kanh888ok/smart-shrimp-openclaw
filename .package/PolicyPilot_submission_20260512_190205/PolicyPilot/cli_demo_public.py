from __future__ import annotations

from pathlib import Path

from src.company_parser import parse_company_profile
from src.generator import build_application_draft, build_material_checklist, build_pitch, build_qna
from src.llm import LLMProvider
from src.matcher import rank_policies
from src.models import AnalysisReport
from src.policy_loader import load_sample_policies
from src.report import save_report
from src.utils import results_to_csv

BASE = Path(__file__).parent

COMPANY_TEXT = """
上海云核智能科技有限公司是一家人工智能初创企业，注册并经营在上海，团队 18 人。
公司主营面向金融和制造业的企业知识库智能体与大模型应用平台，成立于 2025 年，年营收 220 万元，研发投入占比 42%。
公司已有 2 项软件著作权，产品完成 Demo，并在上海本地园区企业完成试点部署。
企业已准备项目计划书、营业执照、真实性承诺书和模型 API 调用预算，但尚未准备完整财务报表、正式模型服务合同和语料采购合同。
目前希望申请上海算力券、模型券、语料券或科技型中小企业相关政策。
""".strip()


def main() -> None:
    out = BASE / "outputs_public"
    out.mkdir(parents=True, exist_ok=True)
    policies = load_sample_policies(BASE / "data" / "public_policies.json")
    profile = parse_company_profile(COMPANY_TEXT)
    results = rank_policies(profile, policies)
    top = results[0]

    llm = LLMProvider(use_openai=False)
    draft = build_application_draft(profile, top, llm=llm)
    checklist = build_material_checklist(top)
    pitch = build_pitch(profile, results[:3])
    qna = build_qna(profile, results[:3])
    report = AnalysisReport(profile, results, draft, checklist, pitch, qna, "公开来源政策库 demo：评估申报准备度而非官方通过率。")

    save_report(report, out)
    (out / "public_policy_results.csv").write_bytes(results_to_csv(results))

    print("PolicyPilot public-source demo completed.")
    print(f"Company: {profile.name} | Region: {profile.region} | Industry: {profile.industry}")
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.policy.name}: {r.score} | {r.level}")
    print(f"Outputs: {out}")


if __name__ == "__main__":
    main()
