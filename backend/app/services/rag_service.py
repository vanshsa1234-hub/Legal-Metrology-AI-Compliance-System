"""
Legal Lens - Legal RAG (Phase 7, stretch: docs/PRODUCTION_READINESS_PRD.md)

Retrieval: TF-IDF cosine similarity over LegalRule text, computed on
the fly. At today's data scale (~30 rules) this is exact and
sub-millisecond - a persisted vector table or ANN index isn't earning
its complexity yet. Postgres + pgvector is available since Phase 5/7
(see the "enable pgvector" migration) as a straightforward upgrade
path if the rules corpus ever grows into the thousands.

Generation: if ANTHROPIC_API_KEY is set, the retrieved rule text
grounds a short, cited answer via the Anthropic API. Without a key,
the endpoint still returns the retrieved rules - never a fabricated
summary standing in for a real model call.
"""
import os
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from ..models import LegalRule


def _rule_corpus_text(rule: LegalRule) -> str:
    return " ".join(filter(None, [
        rule.rule_title, rule.legal_requirement, rule.description,
        rule.product_category, rule.applicable_regulation, rule.clause,
    ]))


def retrieve_relevant_rules(db: Session, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """TF-IDF cosine similarity retrieval over all legal rules."""
    rules = db.query(LegalRule).all()
    if not rules or not query.strip():
        return []

    corpus = [_rule_corpus_text(r) for r in rules]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus + [query])
    rule_vectors, query_vector = matrix[:-1], matrix[-1]

    scores = cosine_similarity(query_vector, rule_vectors)[0]
    ranked = sorted(zip(rules, scores), key=lambda pair: pair[1], reverse=True)

    return [
        {
            "rule_id": r.rule_id,
            "rule_title": r.rule_title,
            "legal_requirement": r.legal_requirement,
            "applicable_regulation": r.applicable_regulation,
            "clause": r.clause,
            "relevance_score": round(float(score), 4),
        }
        for r, score in ranked[:top_k] if score > 0
    ]


def resolve_ambiguity(db: Session, question: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Retrieve grounding rules for an ambiguous compliance question, and -
    only if ANTHROPIC_API_KEY is configured - use them to generate a
    short, cited answer. Always returns the retrieved evidence either way.
    """
    evidence = retrieve_relevant_rules(db, question, top_k=top_k)
    result = {"question": question, "retrieved_rules": evidence, "answer": None, "answer_source": None}

    if not evidence:
        result["answer_source"] = "no_relevant_rules"
        return result

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        result["answer_source"] = "retrieval_only"
        return result

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        rules_block = "\n".join(
            f"- [{r['rule_id']}] {r['rule_title']}: {r['legal_requirement']} "
            f"(Regulation: {r['applicable_regulation']}, Clause: {r.get('clause') or 'N/A'})"
            for r in evidence
        )
        prompt = (
            "You are assisting a Legal Metrology enforcement officer. "
            "Answer the question ONLY using the rules listed below, and "
            "cite rule IDs in brackets like [RULE-ID] for every claim. "
            "If the rules don't clearly answer the question, say so.\n\n"
            f"Rules:\n{rules_block}\n\nQuestion: {question}"
        )
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        result["answer"] = "".join(
            block.text for block in response.content if block.type == "text"
        )
        result["answer_source"] = "llm_grounded"
    except Exception as e:
        result["answer_source"] = "retrieval_only"
        result["llm_error"] = str(e)

    return result
