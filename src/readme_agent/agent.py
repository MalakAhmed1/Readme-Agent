import json
import os
import sys

from dotenv import load_dotenv
from groq import Groq
from groq.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

load_dotenv()  # Load environment variables from .env file

TARGET_PROJECT = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)


client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)  # Initialize the GenAI client with the API key from environment variables


def list_files(folder_path: str):
    ignore = [".env", "uv.lock", ".gitignore"]
    ignore_exts = {".png", ".jpg", ".jpeg", ".lock"}
    ignore_dirs = {".venv", ".git", "__pycache__", ".pytest_cache"}
    filenames = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            ext = os.path.splitext(file)[1]
            if file not in ignore and ext not in ignore_exts:
                filenames.append(os.path.join(root, file))
    return filenames


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return "[Could not read this file]"


list_files_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "Lists all readable files in a project folder, returning their full paths. Use this first to see what files exist before reading any.",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "The folder to scan.",
                }
            },
            "required": ["folder_path"],
        },
    },
}

read_file_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Reads and returns the text contents of one specific file, given its full path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Full path to the file to read.",
                }
            },
            "required": ["path"],
        },
    },
}

tools: list[ChatCompletionToolParam] = [
    list_files_tool,
    read_file_tool,
]


def call_tool(name, args):
    if name == "list_files":
        return list_files(args["folder_path"])
    elif name == "read_file":
        return read_file(args["path"])
    return "Unknown tool"

def main():

    readme_path = os.path.join(TARGET_PROJECT, "README.md")
    if os.path.exists(readme_path):
        existing_readme = read_file(readme_path)
        prompt_text = (
            f"Here is the EXISTING README.md for the project at {TARGET_PROJECT}:\n\n"
            f"{existing_readme}\n\n"
            "Update this README so it accurately reflects the current state of the project's code. "
            "Keep whatever is still correct, fix or rewrite anything outdated, and add anything missing. "
            "Respond with ONLY the full, updated raw Markdown content — no commentary before or after."
        )
    else:
        prompt_text = (
            f"Write a README.md for the project at {TARGET_PROJECT}. "
            "Respond with ONLY the raw Markdown content of the README — no introductory sentences, "
            "no explanations, no commentary before or after. Just the README content itself."
        )

    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "user",
            "content": (
                f"First, inspect the project at {TARGET_PROJECT}. "
                "Use list_files to discover its files, then read the "
                "relevant files and generate the README."
                f"\n\n{prompt_text}"
            ),
        }
    ]

    while True:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=messages,
            tools=tools,
            max_tokens=900,
        )

        message = response.choices[0].message

        print("DEBUG - full response:", response)

        # Did the model ask to use a tool?
        if message.tool_calls:
            assistant_message: ChatCompletionAssistantMessageParam = {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }

            messages.append(assistant_message)

            for tool_call in message.tool_calls:
                function_name = tool_call.function.name

                function_args = json.loads(tool_call.function.arguments)

                result = call_tool(function_name, function_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )
        else:
            if not message.content:
                raise RuntimeError("The model returned no README text.")

            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(message.content)

            print("README.md written successfully.")
            break
if __name__ == "__main__":
    main()