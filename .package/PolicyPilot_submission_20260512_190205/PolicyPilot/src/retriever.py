from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, List, Tuple

from .models import CompanyProfile, Policy, PolicyClause


def tokenize(text: str) -> List[str]:
    """轻量中文/英文 token 化。无外部依赖，便于本地环境稳定运行。"""
    words = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fa5]", text.lower())
    tokens: List[str] = []
    tokens.extend(words)
    chinese_chars = [w for w in words if re.fullmatch(r"[\u4e00-\u9fa5]", w)]
    tokens.extend(["".join(chinese_chars[i : i + 2]) for i in range(max(0, len(chinese_chars) - 1))])
    tokens.extend(["".join(chinese_chars[i : i + 3]) for i in range(max(0, len(chinese_chars) - 2))])
    return [t for t in tokens if t.strip()]


def build_policy_clauses(policies: Iterable[Policy]) -> List[PolicyClause]:
    clauses: List[PolicyClause] = []
    for p in policies:
        clauses.append(PolicyClause(p.id, p.name, "subsidy", p.subsidy, weight=1.0))
        for req in p.requirements:
            clauses.append(PolicyClause(p.id, p.name, "requirement", req, weight=1.4))
        for mat in p.required_materials:
            clauses.append(PolicyClause(p.id, p.name, "material", mat, weight=1.1))
        for risk in p.risk_rules:
            clauses.append(PolicyClause(p.id, p.name, "risk", risk, weight=1.0))
        for kw in p.keywords:
            clauses.append(PolicyClause(p.id, p.name, "keyword", kw, weight=0.8))
    return clauses


def _tf(tokens: List[str]) -> Counter:
    return Counter(tokens)


def _idf(corpus_tokens: List[List[str]]) -> Counter:
    n = len(corpus_tokens)
    df: Counter = Counter()
    for toks in corpus_tokens:
        for t in set(toks):
            df[t] += 1
    return Counter({t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()})


def retrieve_relevant_clauses(query: str, policies: Iterable[Policy], top_k: int = 10) -> List[Tuple[PolicyClause, float]]:
    clauses = build_policy_clauses(policies)
    if not clauses:
        return []

    docs_tokens = [tokenize(c.text + " " + c.policy_name) for c in clauses]
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    idf = _idf(docs_tokens)
    q_tf = _tf(query_tokens)

    results: List[Tuple[PolicyClause, float]] = []
    for clause, toks in zip(clauses, docs_tokens):
        d_tf = _tf(toks)
        score = 0.0
        for t, q_count in q_tf.items():
            if t in d_tf:
                score += q_count * d_tf[t] * idf.get(t, 1.0)
        if score > 0:
            results.append((clause, round(score * clause.weight, 4)))

    return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]


def build_company_query(profile: CompanyProfile) -> str:
    parts = [
        profile.name,
        profile.region,
        profile.industry,
        " ".join(profile.keywords),
        profile.raw_text,
    ]
    return "\n".join([p for p in parts if p])
