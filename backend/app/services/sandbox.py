import json
from typing import Any, List

import pandas as pd
from e2b_code_interpreter import Sandbox

from app.models.schemas import Artifact


def upload_dataset_to_sandbox(code_interpreter: Sandbox, filename: str, file_bytes: bytes) -> str:
    dataset_path = f"./{filename}"
    code_interpreter.files.write(dataset_path, file_bytes)
    return dataset_path


def execute_python(code_interpreter: Sandbox, code: str) -> List[Any]:
    result = code_interpreter.run_code(code)
    if result.error:
        raise RuntimeError(str(result.error))
    return result.results or []


def try_execute_python(code_interpreter: Sandbox, code: str) -> tuple[List[Any] | None, str | None]:
    result = code_interpreter.run_code(code)
    if result.error:
        return None, str(result.error)
    return (result.results or []), None


def _to_table_artifact(value: Any, title: str = "Table") -> Artifact:
    if isinstance(value, pd.Series):
        df_value = value.to_frame(name=value.name or "value")
    elif isinstance(value, pd.DataFrame):
        df_value = value
    else:
        return Artifact(type="text", title=title, text=str(value))

    limited_df = df_value.head(200)
    return Artifact(
        type="table",
        title=title,
        columns=[str(c) for c in limited_df.columns],
        rows=limited_df.to_dict(orient="records"),
    )


def normalize_results(results: List[Any]) -> List[Artifact]:
    artifacts: List[Artifact] = []
    for item in results:
        if hasattr(item, "json") and getattr(item, "json"):
            try:
                plotly_payload = json.loads(getattr(item, "json"))
                if isinstance(plotly_payload, dict):
                    artifacts.append(
                        Artifact(type="plotly", title="Interactive Visualization", plotly_json=plotly_payload)
                    )
                    continue
            except Exception:
                pass

        if hasattr(item, "png") and getattr(item, "png"):
            artifacts.append(
                Artifact(
                    type="image",
                    title="Generated Visualization",
                    image_base64=getattr(item, "png"),
                )
            )
            continue

        if isinstance(item, (pd.DataFrame, pd.Series)):
            artifacts.append(_to_table_artifact(item))
            continue

        if hasattr(item, "text") and getattr(item, "text"):
            artifacts.append(Artifact(type="text", title="Output", text=str(item.text)))
            continue

        artifacts.append(Artifact(type="text", title="Output", text=str(item)))

    if not artifacts:
        artifacts.append(Artifact(type="text", title="Output", text="No artifacts generated."))
    return artifacts
