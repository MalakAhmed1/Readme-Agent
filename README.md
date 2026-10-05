# README Agent

An AI-powered command-line tool that automatically inspects a Python project and generates (or updates) its `README.md` from the actual source code. It uses an LLM (via the Groq API) equipped with file-inspection tools, so the resulting README reflects the current state of the code rather than going stale.

## How It Works

When run, `README Agent`:

1. Targets a project directory (passed as an argument, or defaulting to the project's own root).
2. Sends the model a prompt telling it to inspect the project. The model uses two tools iteratively:
   - **`list_files`** – walks the folder tree and returns full paths of readable files (skipping VCS, virtual-environment, cache, and lock/image files).
   - **`read_file`** – returns the text content of a single file by full path.
3. Builds up the conversation, calling the tools as many times as the model requests, until it returns the README text.
4. Writes the result to `README.md` in the target project.

If a `README.md` already exists, the model is asked to **update** it — keeping what is still correct, rewording anything outdated, and adding anything missing. Otherwise it creates the README from scratch. In both cases the model is instructed to return **only the raw Markdown content**.

## Project Layout

```
readme-agent/
├── .python-version          # Pinned Python version (3.14)
├── pyproject.toml           # Project & build configuration
├── README.md
└── src/
    └── readme_agent/
        ├── __init__.py      # Re-exports main()
        └── agent.py         # CLI logic: tools, LLM loop, README writer
```

## Requirements

- **Python 3.14+**
- **Groq API key** – set the `GROQ_API_KEY` environment variable (a `.env` file is loaded automatically via `python-dotenv`).

Dependencies:

| Package | Purpose |
| --- | --- |
| `groq` | Client for the Groq LLM API (chat completions with tools) |
| `python-dotenv` | Loads environment variables from a `.env` file |
| `google-genai` | Declared dependency (the active client is currently Groq) |

## Installation

The project uses [`uv`](https://docs.astral.sh/uv/). From the project root:

```bash
# Install the package in editable mode with its dependencies
uv sync

# (optionally) create a .env file containing:
#   GROQ_API_KEY=your_key_here
```

## Usage

```bash
# Update/create the README for a specific project directory
readme-agent /path/to/project

# With no argument, it targets the readme-agent project's own root
readme-agent
```

The command prints debugging info (the full LLM response) as it runs, then writes `README.md` and prints a success message.

## Configuration

| Setting | Source | Default |
| --- | --- | --- |
| Target project | First CLI argument | The `readme-agent` project root |
| LLM model | Hardcoded in `agent.py` | `qwen/qwen3.8-27b` |
| Max tokens | Hardcoded in `agent.py` | `900` |
| API key | `GROQ_API_KEY` env var / `.env` | — |

## Notes & Caveats

- The model name (`qwen/qwen3.8-27b`) and token limit are currently **hardcoded** in `src/readme_agent/agent.py`; adjust them there if needed.
- A `DEBUG` line prints the entire LLM response on every API call.
- The package **entry point** is `readme_agent:main`, but `__init__.py` imports `main` from the `agent` submodule. Both resolve to the same `main()`, so it works as shipped — though wiring the script directly to `readme_agent.agent:main` would make that link