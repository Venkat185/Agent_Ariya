import os
from typing import List, Tuple

from openai import OpenAI

from app.models.schemas import ChatTurn
from app.utils.parsing import extract_python_code_block


def build_system_prompt(dataset_path: str, df_info: str) -> str:
    df_section = (
        f"The dataset has the following columns and dtypes:\n{df_info}\n" if df_info else ""
    )
    return f"""You are "Ariya", an expert Python data scientist and data visualisation specialist.
You help a non-technical user understand their dataset. Respond like a confident senior analyst:
clear, concise, business-oriented, never rambling.

A dataset is available at path '{dataset_path}'.
{df_section}

OUTPUT FORMAT (strict):
Your reply MUST consist of exactly two parts, in this order:

1. A single fenced ```python ... ``` code block that performs the analysis end-to-end.
2. A short markdown explanation using this template:

**Headline:** one-sentence answer to the user's question, in bold.

**Key findings**
- 3 to 5 tight bullets, each with a concrete number or insight.

**What this means**
- 1–2 short sentences of business interpretation.

Optional:
**Caveats** (only if relevant, 1 short bullet about data quality, missing values, etc.).

Hard rules on tone and content:
- Do NOT narrate that you are about to write code, do NOT say "let's analyse", "I will now", "here is the code", "I'll run the code", etc. Skip meta-commentary entirely.
- Do NOT repeat the user's question.
- Do NOT describe what a heatmap / scatter plot / correlation is. Assume the user already knows.
- Use plain English, no jargon unless necessary.
- Every claim must be grounded in the dataset, not generic.
- Numbers must be rounded sensibly (0–2 decimals) and use thousands separators when large.
- Use markdown properly: `**bold**`, `- bullets`, and short paragraphs only. No H1/H2 headings, no horizontal rules, no emojis.

Code rules:
- Always wrap the code in a single ```python ... ``` block.
- Use the exact path '{dataset_path}' when reading the CSV.
- Only reference columns that actually exist in the schema above. Never invent column names.
- Make visualisations polished: sensible figure size, clear title, axis labels, legend, readable colour palette (viridis / cividis / Set2 / or a single brand colour).
- Prefer a single focused chart over many redundant charts.
- Do not call `plt.show()`.

Robustness rules you MUST follow to avoid runtime errors:
- Before any numeric operation (mean, sum, corr, regression, scaling, heatmap, etc.) select only numeric columns, e.g. `numeric_df = df.select_dtypes(include='number')`.
- For correlations always use `df.corr(numeric_only=True)` or `numeric_df.corr()`. Never call `df.corr()` directly on a mixed-dtype DataFrame.
- Coerce numeric-looking string columns with `pd.to_numeric(series, errors='coerce')` before math.
- Drop or impute NaNs sensibly (`dropna()` or `.fillna(...)`) before plotting or aggregation.
- For groupby aggregations over numeric metrics, explicitly pick the numeric columns (e.g. `df.groupby('col')[['num1','num2']].mean()`).
- Never assume a column is numeric based on its name; check dtypes from the schema above.
- If the user asks something impossible with the available columns, explain briefly in the explanation and still produce the closest meaningful analysis instead of guessing columns."""


def _client_and_model() -> Tuple[OpenAI, str]:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=openai_api_key), model_name


def request_analysis(
    user_message: str,
    dataset_path: str,
    df_info: str,
    conversation: List[ChatTurn] | None = None,
) -> Tuple[str, str]:
    client, model_name = _client_and_model()
    messages = [{"role": "system", "content": build_system_prompt(dataset_path, df_info)}]
    if conversation:
        messages.extend({"role": turn.role, "content": turn.content} for turn in conversation)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=model_name, messages=messages)

    content = response.choices[0].message.content or ""
    python_code = extract_python_code_block(content)
    return content, python_code


def request_code_fix(
    user_message: str,
    dataset_path: str,
    df_info: str,
    failing_code: str,
    error_text: str,
) -> Tuple[str, str]:
    client, model_name = _client_and_model()
    fix_request = (
        "The previous Python code you generated raised an error while executing in the sandbox. "
        "Please fix the code and return a corrected, complete Python block that satisfies the "
        "original user request. Follow every rule from the system prompt, especially: use only "
        "numeric columns for numeric operations (select_dtypes(include='number')), use "
        "df.corr(numeric_only=True), coerce types with pd.to_numeric(..., errors='coerce'), and "
        "handle NaNs.\n\n"
        f"Original user request: {user_message}\n\n"
        f"Failing code:\n```python\n{failing_code}\n```\n\n"
        f"Error message:\n{error_text}\n\n"
        "Return only the corrected code block followed by a short plain-English explanation."
    )
    messages = [
        {"role": "system", "content": build_system_prompt(dataset_path, df_info)},
        {"role": "user", "content": fix_request},
    ]
    response = client.chat.completions.create(model=model_name, messages=messages)
    content = response.choices[0].message.content or ""
    python_code = extract_python_code_block(content)
    return content, python_code
