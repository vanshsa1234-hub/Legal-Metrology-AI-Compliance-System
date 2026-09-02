"""
Legal Lens - Legal RAG API (Phase 7, stretch: docs/PRODUCTION_READINESS_PRD.md)
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.rag_service import resolve_ambiguity

router = APIRouter(prefix="/api/rag", tags=["Legal RAG"])


class RagQuery(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/resolve")
def resolve(query: RagQuery, db: Session = Depends(get_db)):
    """
    Retrieve the legal rules most relevant to an ambiguous compliance
    question, with an optional LLM-generated answer grounded strictly
    in those rules (only when ANTHROPIC_API_KEY is configured).
    """
    return resolve_ambiguity(db, query.question, top_k=query.top_k)
