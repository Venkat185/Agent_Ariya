import os
from io import BytesIO

import pandas as pd
from e2b_code_interpreter import Sandbox
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.models.schemas import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    AnalyzeResponse,
    ChatTurn,
    ColumnProfile,
    DatasetFullResponse,
    DatasetProfileResponse,
)
from app.services.llm import request_analysis, request_code_fix
from app.services.session_store import create_session, get_session
from app.services.sandbox import (
    normalize_results,
    try_execute_python,
    upload_dataset_to_sandbox,
)
from app.utils.parsing import strip_code_blocks


router = APIRouter(prefix="/api", tags=["analysis"])


def _read_uploaded_csv(file_bytes: bytes) -> pd.DataFrame:
    try:
        return pd.read_csv(BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc


def _safe_preview_rows(df: pd.DataFrame, limit: int = 5) -> list[dict]:
    preview = df.head(limit).copy()
    preview = preview.where(pd.notnull(preview), None)
    return preview.to_dict(orient="records")


def _df_info_string(df: pd.DataFrame) -> str:
    return (
        df.dtypes.reset_index().rename(columns={"index": "column", 0: "dtype"}).to_string(index=False)
    )


@router.post("/dataset/profile", response_model=DatasetProfileResponse)
async def profile_dataset(file: UploadFile = File(...)) -> DatasetProfileResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    df = _read_uploaded_csv(file_bytes)
    columns = []
    for column_name in df.columns:
        series = df[column_name]
        columns.append(
            ColumnProfile(
                name=str(column_name),
                dtype=str(series.dtype),
                null_count=int(series.isna().sum()),
                unique_count=int(series.nunique(dropna=True)),
            )
        )

    session = create_session(file.filename, file_bytes, _df_info_string(df))

    return DatasetProfileResponse(
        session_id=session.session_id,
        filename=file.filename,
        rows=int(len(df)),
        columns=int(len(df.columns)),
        file_size_bytes=int(len(file_bytes)),
        column_profiles=columns,
        preview_rows=_safe_preview_rows(df),
    )


@router.get("/dataset/full", response_model=DatasetFullResponse)
def get_full_dataset(
    session_id: str = Query(...),
    limit: int = Query(5000, ge=1, le=50000),
) -> DatasetFullResponse:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Re-upload your dataset.")

    df = _read_uploaded_csv(session.file_bytes)
    total_rows = int(len(df))
    sliced = df.head(limit).copy()
    sliced = sliced.where(pd.notnull(sliced), None)
    return DatasetFullResponse(
        session_id=session.session_id,
        filename=session.filename,
        columns=[str(c) for c in df.columns],
        rows=sliced.to_dict(orient="records"),
        total_rows=total_rows,
        returned_rows=int(len(sliced)),
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile | None = File(None),
    query: str = Form(...),
    session_id: str | None = Form(None),
) -> AnalyzeResponse:
    current_session = None
    active_file_bytes: bytes
    active_filename: str
    df_info: str

    e2b_api_key = os.getenv("E2B_API_KEY")
    if not e2b_api_key:
        raise HTTPException(status_code=500, detail="E2B_API_KEY is not set.")

    if file:
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Please upload a CSV file.")
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        df = _read_uploaded_csv(file_bytes)
        df_info = _df_info_string(df)
        current_session = create_session(file.filename, file_bytes, df_info)
        active_file_bytes = file_bytes
        active_filename = file.filename
    elif session_id:
        current_session = get_session(session_id)
        if not current_session:
            raise HTTPException(status_code=404, detail="Session not found. Re-upload your dataset.")
        active_file_bytes = current_session.file_bytes
        active_filename = current_session.filename
        df_info = current_session.df_info
    else:
        raise HTTPException(status_code=400, detail="Provide either a CSV file or a valid session_id.")

    try:
        with Sandbox(api_key=e2b_api_key) as sandbox:
            dataset_path = upload_dataset_to_sandbox(sandbox, active_filename, active_file_bytes)
            prior_turns = current_session.turns if current_session else []
            llm_response, python_code = request_analysis(query, dataset_path, df_info, prior_turns)
            if not python_code:
                summary_text = strip_code_blocks(llm_response) or "Model did not return executable code."
                if current_session:
                    current_session.turns.append(ChatTurn(role="user", content=query))
                    current_session.turns.append(ChatTurn(role="assistant", content=summary_text))
                    current_session.analyses.append(
                        AnalysisHistoryItem(query=query, summary=summary_text, code=None, artifacts=[])
                    )
                return AnalyzeResponse(
                    session_id=current_session.session_id if current_session else session_id or "",
                    query=query,
                    summary=summary_text,
                    code=None,
                    artifacts=[],
                )

            execution_results, error_text = try_execute_python(sandbox, python_code)
            if error_text is not None:
                llm_response, fixed_code = request_code_fix(
                    query, dataset_path, df_info, python_code, error_text
                )
                if fixed_code:
                    python_code = fixed_code
                    execution_results, error_text = try_execute_python(sandbox, python_code)
                if error_text is not None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Generated code failed even after auto-fix: {error_text}",
                    )

            artifacts = normalize_results(execution_results or [])
            summary_text = strip_code_blocks(llm_response)
            if current_session:
                current_session.turns.append(ChatTurn(role="user", content=query))
                current_session.turns.append(ChatTurn(role="assistant", content=summary_text))
                current_session.analyses.append(
                    AnalysisHistoryItem(query=query, summary=summary_text, code=python_code, artifacts=artifacts)
                )
            return AnalyzeResponse(
                session_id=current_session.session_id if current_session else session_id or "",
                query=query,
                summary=summary_text,
                code=python_code,
                artifacts=artifacts,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/analysis/history", response_model=AnalysisHistoryResponse)
def get_analysis_history(session_id: str = Query(...)) -> AnalysisHistoryResponse:
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return AnalysisHistoryResponse(
        session_id=session.session_id,
        filename=session.filename,
        turns=session.turns,
        analyses=session.analyses,
    )
