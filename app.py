import os
import json
import re
import sys
import io
import contextlib
import warnings
from typing import Optional, List, Any, Tuple
from PIL import Image
import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from openai import OpenAI
from e2b_code_interpreter import Sandbox

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataViz AI Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0d0f14;
    --surface:   #141720;
    --surface2:  #1c2030;
    --border:    #252a3a;
    --accent:    #4ade80;
    --accent2:   #22d3ee;
    --warn:      #fb923c;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --radius:    12px;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

.block-container {
    padding: 2rem 3rem !important;
    max-width: 1400px !important;
}

.hero {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.hero-icon { font-size: 2.8rem; line-height: 1; }
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.4rem;
    color: var(--text);
    margin: 0;
    letter-spacing: -0.02em;
}
.hero-subtitle {
    font-size: 0.95rem;
    color: var(--muted);
    margin: 0;
    font-weight: 300;
}

section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1.2rem !important;
}
.sidebar-section {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}
.sidebar-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.6rem;
}

.stTextInput input, .stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(74,222,128,0.15) !important;
}
.stSelectbox > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #0d0f14 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.8rem !important;
    letter-spacing: 0.02em;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

[data-testid="stFileUploader"] {
    background: var(--surface2) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.7rem;
}

.response-box {
    background: var(--surface2);
    border-left: 3px solid var(--accent);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 1.2rem 1.4rem;
    font-size: 0.93rem;
    line-height: 1.7;
    color: var(--text);
}

.badge {
    display: inline-block;
    background: rgba(74,222,128,0.12);
    color: var(--accent);
    border: 1px solid rgba(74,222,128,0.25);
    border-radius: 20px;
    padding: 0.18rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}

.stSpinner > div { border-top-color: var(--accent) !important; }

.stAlert {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
}

.stCheckbox label {
    font-size: 0.88rem !important;
    color: var(--muted) !important;
}

hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

code {
    background: var(--surface2) !important;
    color: var(--accent2) !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 4px !important;
    padding: 0.1em 0.35em !important;
    font-size: 0.85em !important;
}
</style>
""", unsafe_allow_html=True)

# ── Regex for code extraction ──────────────────────────────────────────────────
pattern = re.compile(r"```python\n(.*?)\n```", re.DOTALL)

# ── Model options ──────────────────────────────────────────────────────────────
MODEL_OPTIONS = {
    "GPT-4o  —  Best for complex analysis":   "gpt-4o",
    "GPT-4o Mini  —  Fast & affordable":      "gpt-4o-mini",
    "GPT-4 Turbo  —  Balanced performance":   "gpt-4-turbo",
}

# ─────────────────────────────────────────────────────────────────────────────
# Core functions
# ─────────────────────────────────────────────────────────────────────────────

def code_interpret(e2b_code_interpreter: Sandbox, code: str) -> Optional[List[Any]]:
    with st.spinner("⚙️  Running code in secure E2B sandbox…"):
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec_result = e2b_code_interpreter.run_code(code)

        if exec_result.error:
            st.error(f"**Sandbox error:** {exec_result.error}")
            return None
        return exec_result.results


def match_code_blocks(llm_response: str) -> str:
    match = pattern.search(llm_response)
    return match.group(1) if match else ""


def chat_with_llm(
    e2b_code_interpreter: Sandbox,
    user_message: str,
    dataset_path: str,
    df_info: str = "",
) -> Tuple[Optional[List[Any]], str]:

    system_prompt = f"""You are an expert Python data scientist and data visualisation specialist.
A dataset is available at path '{dataset_path}'.
{f"The dataset has the following columns and dtypes:{chr(10)}{df_info}{chr(10)}" if df_info else ""}
Your task:
1. Analyse the dataset and answer the user's query.
2. Write clean Python code (using pandas, matplotlib, seaborn, or plotly) to produce the answer / visualisation.
3. Always wrap your code in a ```python ... ``` block.
4. Use the exact path '{dataset_path}' when reading the CSV.
5. IMPORTANT: Only reference column names that actually exist in the dataset (listed above). Never guess column names.
6. Make visualisations beautiful: use good colour palettes, clear labels, and titles.
7. After the code block, provide a concise plain-English explanation of the findings."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]

    with st.spinner("🤖  Consulting the AI model…"):
        client = OpenAI(api_key=st.session_state.openai_api_key)
        response = client.chat.completions.create(
            model=st.session_state.model_name,
            messages=messages,
        )

    response_message = response.choices[0].message
    python_code = match_code_blocks(response_message.content)

    if python_code:
        code_results = code_interpret(e2b_code_interpreter, python_code)
        return code_results, response_message.content
    else:
        st.warning("No Python code block found in the model's response.")
        return None, response_message.content


def upload_dataset(code_interpreter: Sandbox, uploaded_file) -> str:
    dataset_path = f"./{uploaded_file.name}"
    try:
        code_interpreter.files.write(dataset_path, uploaded_file)
        return dataset_path
    except Exception as error:
        st.error(f"File upload error: {error}")
        raise error


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Session state ──────────────────────────────────────────────────────────
    for key, default in [
        ("openai_api_key", ""),
        ("e2b_api_key",    ""),
        ("model_name",     "gpt-4o"),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Title ──────────────────────────────────────────────────────────────────
    st.title("📊 AI Data Visualization Agent")
    st.write("Upload your dataset and ask questions about it!")

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("API Keys and Model Configuration")

        st.session_state.openai_api_key = st.text_input(
            "OpenAI API Key", type="password", placeholder="sk-…"
        )
        st.info("💡 Get your key at platform.openai.com")
        st.markdown(
            '[Get OpenAI API Key](https://platform.openai.com/api-keys)',
            unsafe_allow_html=False,
        )

        st.session_state.e2b_api_key = st.text_input(
            "E2B API Key", type="password", placeholder="e2b_…"
        )
        st.markdown(
            '[Get E2B API Key](https://e2b.dev/docs/legacy/getting-started/api-key)',
            unsafe_allow_html=False,
        )

        st.markdown("---")
        selected_label = st.selectbox(
            "Select Model",
            options=list(MODEL_OPTIONS.keys()),
            index=0,
        )
        st.session_state.model_name = MODEL_OPTIONS[selected_label]

    # ── File upload ────────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rows",    f"{df.shape[0]:,}")
        c2.metric("Columns", df.shape[1])
        c3.metric("Size",    f"{uploaded_file.size / 1024:.1f} KB")

        st.write("Dataset:")
        show_full = st.checkbox("Show full dataset", value=False)
        st.dataframe(df if show_full else df.head(), use_container_width=True)

        # ── Query ──────────────────────────────────────────────────────────────
        query = st.text_area(
            "What would you like to know about your data?",
            value="Can you compare the average cost for two people between different categories?",
        )

        if st.button("Analyze", use_container_width=True):
            if not st.session_state.openai_api_key or not st.session_state.e2b_api_key:
                st.error("Please enter both API keys in the sidebar.")
            else:
                with Sandbox(api_key=st.session_state.e2b_api_key) as code_interpreter:
                    uploaded_file.seek(0)
                    dataset_path = upload_dataset(code_interpreter, uploaded_file)
                    df_info = df.dtypes.reset_index().rename(
                        columns={"index": "column", 0: "dtype"}
                    ).to_string(index=False)
                    code_results, llm_response = chat_with_llm(
                        code_interpreter, query, dataset_path, df_info
                    )

                # ── Results ────────────────────────────────────────────────────
                st.write("AI Response:")
                display_text = re.sub(r"```python.*?```", "", llm_response, flags=re.DOTALL).strip()
                st.markdown(
                    f'<div class="response-box">{display_text}</div>',
                    unsafe_allow_html=True,
                )

                if code_results:
                    for result in code_results:
                        if hasattr(result, "png") and result.png:
                            png_data = base64.b64decode(result.png)
                            image = Image.open(BytesIO(png_data))
                            st.image(image, caption="Generated Visualization", use_container_width=True)
                        elif hasattr(result, "figure"):
                            st.pyplot(result.figure)
                        elif hasattr(result, "show"):
                            st.plotly_chart(result, use_container_width=True)
                        elif isinstance(result, (pd.DataFrame, pd.Series)):
                            st.dataframe(result, use_container_width=True)
                        else:
                            st.write(result)
                else:
                    st.info("No visualisation was generated. Try rephrasing your question.")


if __name__ == "__main__":
    main()
