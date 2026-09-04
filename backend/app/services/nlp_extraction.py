"""
Legal Lens - NLP-Assisted Field Extraction (Phase 11: docs/PRODUCTION_READINESS_PRD.md)

spaCy's general-purpose NER (en_core_web_sm) is a real, trained model,
but it's trained on news/Wikipedia text, not packaging labels - tested
directly against real label text, it mistags phrases like "Classic
Potato Chips" as ORG and misses standalone brand names entirely. So
this is deliberately NOT used to replace the existing regex/positional
extraction (ocr_service.py), which handles structured fields
(MRP/dates/batch numbers) NER isn't suited for at all. Instead it's a
second, independent signal: when spaCy's ORG entities agree with the
regex-extracted manufacturer text, confidence goes up; when they
disagree, the field is flagged for review rather than silently
trusted - never a blind replacement of one guess with another.

Loaded lazily and best-effort: if spacy or its model isn't installed,
cross-checking is silently skipped and the regex-only result (today's
behavior) is returned unchanged - this is an enhancement, not a
dependency anything else relies on.
"""
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

_nlp = None
_nlp_unavailable = False


def _get_nlp():
    global _nlp, _nlp_unavailable
    if _nlp is not None or _nlp_unavailable:
        return _nlp
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"spaCy NER unavailable ({e}); manufacturer cross-check will be skipped.")
        _nlp_unavailable = True
    return _nlp


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def extract_org_entities(text: str) -> List[str]:
    """Real spaCy NER call - returns ORG-labeled spans found in text."""
    nlp = _get_nlp()
    if nlp is None or not text.strip():
        return []
    doc = nlp(text[:5000])  # bound input size, this is label text, not a document
    return [ent.text for ent in doc.ents if ent.label_ == "ORG"]


def cross_check_manufacturer(combined_text: str, heuristic_value: Optional[str], heuristic_confidence: float) -> Dict[str, Any]:
    """
    Compares the regex-extracted manufacturer string against spaCy's
    independently-detected ORG entities in the same text.

    Returns {confidence, agrees, org_entities} - confidence is the
    (possibly adjusted) value to use; callers decide what to do with
    `agrees`/`org_entities` (e.g. surface a review flag).
    """
    org_entities = extract_org_entities(combined_text)
    result = {"confidence": heuristic_confidence, "agrees": None, "org_entities": org_entities}

    if not heuristic_value or not org_entities:
        return result

    best_overlap = max(_text_similarity(heuristic_value, org) for org in org_entities)
    if best_overlap >= 0.6:
        result["agrees"] = True
        result["confidence"] = min(99.0, heuristic_confidence + 10.0)
    else:
        result["agrees"] = False
        # Don't silently keep high confidence when an independent
        # signal disagrees - nudge it down so this surfaces for review
        # rather than being trusted the same as an agreeing case.
        result["confidence"] = max(0.0, heuristic_confidence - 15.0)

    return result
