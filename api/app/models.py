from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class AskRequest(BaseModel):
    query: str
    k: int = 30
    recent_only: bool = False
    from_session: Optional[int] = None
    to_session: Optional[int] = None


class Source(BaseModel):
    doc_title: str
    session_no: int | None
    heading: str | None
    path: str | None
    chunk_id: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    context: List[Dict[str, Any]]