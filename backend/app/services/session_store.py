from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List
from uuid import uuid4

from app.models.schemas import AnalysisHistoryItem, ChatTurn


@dataclass
class AnalysisSession:
    session_id: str
    filename: str
    file_bytes: bytes
    df_info: str
    turns: List[ChatTurn] = field(default_factory=list)
    analyses: List[AnalysisHistoryItem] = field(default_factory=list)


_sessions: Dict[str, AnalysisSession] = {}
_lock = Lock()


def create_session(filename: str, file_bytes: bytes, df_info: str) -> AnalysisSession:
    with _lock:
        session_id = str(uuid4())
        session = AnalysisSession(
            session_id=session_id,
            filename=filename,
            file_bytes=file_bytes,
            df_info=df_info,
        )
        _sessions[session_id] = session
        return session


def get_session(session_id: str) -> AnalysisSession | None:
    with _lock:
        return _sessions.get(session_id)

