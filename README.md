# 📝 Readme Agent

An intelligent, autonomous CLI tool powered by Gemini 3.5 Flash that automatically analyzes your codebase and generates a comprehensive, production-ready `README.md` file.

By leveraging **Gemini Function Calling (Tool Use)**, the agent explores your project directory, lists source files, and reads their contents dynamically to craft accurate and contextual documentation.

---

## ✨ Features

- **Agentic Code Exploration**: Uses Gemini's native tool-calling capabilities to recursively list files and inspect code blocks.
- **Smart Filtering**: Built-in exclusion lists to automatically ignore binary files, lockfiles, virtual environments (`.venv`), git configurations (`.git`), caches, and environment files.
- **Powered by Gemini 3.5**: Leverages the official, ultra-fast `google-genai` SDK and `gemini-3.5-flash` model.
- **Flexible Target Directory**: Accepts any local folder path as a CLI argument to write a README for any project.
- **Single-Command Documentation**: Generates a professional, beautifully formatted README.md directly in your target folder in seconds.

---

## 🛠️ Tech Stack

- **Language**: Python >= 3.14 (or modern Python versions utilizing the `uv` build backend)
- **AI Framework**: `google-genai` SDK (Gemini API)
- **Environment Management**: `python-dotenv`
- **Build/Package Manager**: `uv` / `uv_build`

---

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have Python and `uv` installed. You will also need a **Gemini API Key**. Get yours from [Google AI Studio](https://aistudio.google.com/).

### 2. Installation

Clone this repository and navigate to its directory:

```bash
git clone https://github.com/MalakAhmed1/Readme-Agent.git
cd readme-agent
```

Install dependencies using `uv`:

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 📖 Usage

Run the agent by executing the script and passing the path of the target directory you want to generate documentation for:

```bash
uv run python src/readme_agent/agent.py "/path/to/target/project"
```

If no argument is passed, the agent will default to analyzing its own codebase:

```bash
uv run python src/readme_agent/agent.py
```

### 🔍 How It Works (Under the Hood)

1. **Tool Definition**: The script registers two Python functions as Gemini-executable tools:
   - `list_files(folder_path)`: Scans the target folder and returns paths of relevant readable files.
   - `read_file(path)`: Safely reads the text content of a requested file using UTF-8 encoding.
2. **Initialization**: The agent initializes a conversation session with the `gemini-3.5-flash` model and triggers an initial query to analyze the target directory structure.
3. **Agent Loop**:
   - The LLM determines which files are important and requests to inspect them via function/tool calls.
   - The script executes those tools locally and feeds the outputs back to the LLM.
   - This loop runs dynamically until the model has gathered all necessary details about the project's logic, architecture, and configuration.
4. **File Generation**: The LLM synthesizes the gathered details and generates the complete, raw Markdown content, which is then written directly to a new `README.md` at the root of your target project folder.

---

## ⚙️ Configuration & Customization

You can customize file and directory exclusion rules within the `list_files` function in `src/readme_agent/agent.py`:

```python
def list_files(folder_path: str):
    ignore = [".env", "uv.lock", ".gitignore"]
    ignore_exts = {".png", ".jpg", ".jpeg", ".lock"}
    ignore_dirs = {".venv", ".git", "__pycache__", ".pytest_cache"}
    # ...
```

Modify these lists to exclude or include specific assets or file extensions during codebase exploration.
