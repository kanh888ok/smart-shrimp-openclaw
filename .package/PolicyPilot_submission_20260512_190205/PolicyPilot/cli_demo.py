from __future__ import annotations

import json
from pathlib import Path

from src.company_parser import parse_company_profile
from src.generator import build_application_draft, build_demo_explanation, build_material_checklist, build_pitch, build_qna
from src.matcher import rank_policies
from src.models import AnalysisReport
from src.policy_loader import load_sample_policies
from src.report import save_report
from src.utils import results_to_csv

BASE_DIR = Path(__file__).parent


def main() -> None:
    policies = load_sample_policies(BASE_DIR / "data" / "sample_policies.json")
    companies = json.loads((BASE_DIR / "data" / "sample_companies.json").read_text(encoding="utf-8"))
    company_text = companies[0]["text"]

    profile = parse_company_profile(company_text)
    results = rank_policies(profile, policies)
    selected = results[0]

    draft = build_application_draft(profile, selected)
    checklist = build_material_checklist(selected)
    pitch = build_pitch(profile, results[:3])
    qna = build_qna(profile, results[:3])
    explanation = build_demo_explanation(profile, results[:3])
    report = AnalysisReport(profile, results, draft, checklist, pitch, qna, explanation)

    output_dir = BASE_DIR / "outputs"
    save_report(report, output_dir)
    (output_dir / "policy_results.csv").write_bytes(results_to_csv(results))

    print("PolicyPilot demo executed.")
    print(f"Company: {profile.name}")
    print("Top matches:")
    for idx, result in enumerate(results[:5], start=1):
        print(f"{idx}. {result.policy.name} | {result.score} | {result.level}")
    print(f"Outputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
