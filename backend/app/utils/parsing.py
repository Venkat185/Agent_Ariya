import re


PYTHON_CODE_BLOCK_PATTERN = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


def extract_python_code_block(content: str) -> str:
    match = PYTHON_CODE_BLOCK_PATTERN.search(content)
    return match.group(1) if match else ""


def strip_code_blocks(content: str) -> str:
    return re.sub(r"```python.*?```", "", content, flags=re.DOTALL).strip()
