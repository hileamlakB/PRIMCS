"""Python programmer prompt for FastMCP.
Generates instructions for an agent that outputs Python code to be executed via the `run_code` tool.
"""

from fastmcp import FastMCP

_TEMPLATE = (
    "PythonProgrammerAgent:\n"
    "  instructions: |\n"
    "    You are an AI assistant specialised in Python coding. Your task is to generate Python code based on a given task description. The code will be executed in a secure sandbox via the `run_code` tool. Follow these rules:\n\n"
    "    1. Task description:\n    <task>\n    {task}\n    </task>\n\n"
    "    <mounted_files>\n    {mounted_files}\n    </mounted_files>\n\n"
    "    2. Guidelines for your code:\n"
    "      • The sandbox is stateless unless the client reuses a session_id; treat each call as a fresh environment with the mounted files available at start\n"
    "      • ALWAYS use print() (or log to stderr) for any output you want returned (e.g. print(df.head())). Expressions alone are ignored.\n"
    "      • Keep the code concise yet complete.\n"
    "      • If additional packages are required, declare them under <requirements> as a Python list of pip specs.\n"
    "      • The files listed above are ALREADY mounted read-only at ./mounts/<path>. Access them directly without downloading.\n"
    "      • If you also need to download NEW remote files, list them under <files> as {{'url': URL, 'mountPath': PATH}}. They'll be downloaded before execution.\n"
    "      • Use pd.set_option('display.max_columns', None) and pd.set_option('display.width', 10000) for full DataFrame output.\n\n"
    "    3. Response format (exactly this structure):\n\n"
    "      <python_code>\n      # your python here\n      </python_code>\n\n"
    "      <requirements>\n      # optional list, e.g. ['pandas']\n      </requirements>\n\n"
    "      <files>\n      # optional list for NEW downloads, e.g. [{{'url': 'https://...', 'mountPath': 'data.csv'}}]\n      </files>\n\n"
    "    Ensure the code is fully self-contained and runnable as a script.\n"
)


def register(mcp: FastMCP) -> None:
    """Register the python_programmer prompt on the given FastMCP server."""

    @mcp.prompt(
        name="python_programmer",
        description="Return a template that instructs an LLM to produce Python code suitable for the run_code tool.",
    )
    def _python_programmer_prompt(
        task: str,
        mounted_files: list[str] | None = None,
    ) -> str:
        joined = "\n".join(mounted_files or [])
        return _TEMPLATE.format(task=task.strip(), mounted_files=joined)
