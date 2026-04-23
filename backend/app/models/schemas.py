from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


ArtifactType = Literal["image", "table", "text", "plotly"]


class Artifact(BaseModel):
    type: ArtifactType
    title: Optional[str] = None
    image_base64: Optional[str] = None
    plotly_json: Optional[Dict[str, Any]] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    text: Optional[str] = None


class AnalyzeResponse(BaseModel):
    session_id: str
    query: str
    summary: str
    code: Optional[str] = None
    artifacts: List[Artifact]


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    unique_count: int


class DatasetProfileResponse(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: int
    file_size_bytes: int
    column_profiles: List[ColumnProfile]
    preview_rows: List[Dict[str, Any]]


class DatasetFullResponse(BaseModel):
    session_id: str
    filename: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    returned_rows: int


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnalysisHistoryItem(BaseModel):
    query: str
    summary: str
    code: Optional[str] = None
    artifacts: List[Artifact]


class AnalysisHistoryResponse(BaseModel):
    session_id: str
    filename: str
    turns: List[ChatTurn]
    analyses: List[AnalysisHistoryItem]
