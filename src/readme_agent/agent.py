import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # Load environment variables from .env file

TARGET_PROJECT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

# TARGET_PROJECT = (
#     r"C:\M\py workspace\readme-agent"  # <- only line you change per project
# )

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
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


list_files_tool = types.FunctionDeclaration(
    name="list_files",
    description="Lists all readable files in a project folder, returning their full paths. Use this first to see what files exist before reading any.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "folder_path": types.Schema(
                type=types.Type.STRING,
                description="The folder to scan.",
            )
        },
        required=["folder_path"],
    ),
)

read_file_tool = types.FunctionDeclaration(
    name="read_file",
    description="Reads and returns the text contents of one specific file, given its full path.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "path": types.Schema(
                type=types.Type.STRING,
                description="Full path to the file to read",
            )
        },
        required=["path"],
    ),
)


tools = types.Tool(function_declarations=[list_files_tool, read_file_tool])
config = types.GenerateContentConfig(tools=[tools])

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=f"List the files in {TARGET_PROJECT}",
    config=config,
)
assert response.candidates is not None
assert response.candidates[0].content is not None
assert response.candidates[0].content.parts is not None
print(response.candidates[0].content.parts[0].function_call)


def call_tool(name, args):
    if name == "list_files":
        return list_files(args["folder_path"])
    elif name == "read_file":
        return read_file(args["path"])
    return "Unknown tool"


call = response.candidates[0].content.parts[0].function_call
assert call is not None
result = call_tool(call.name, call.args)
print(result)

contents = [
    types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    f"Write a README.md for the project at {TARGET_PROJECT}. "
                    "Respond with ONLY the raw Markdown content of the README — no introductory sentences, "
                    "no explanations, no commentary before or after. Just the README content itself."
                )
            )
        ],
    )
]

while True:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=contents,
        config=config,
    )
    if not response.candidates:
        raise RuntimeError("The model returned no candidates.")

    candidate = response.candidates[0]
    if candidate.content is None or not candidate.content.parts:
        raise RuntimeError("The model returned no content parts.")

    part = candidate.content.parts[0]
    contents.append(candidate.content)

    if part.function_call:
        call = part.function_call
        if not call.name:
            raise RuntimeError("The function call has no name.")

        result = call_tool(call.name, call.args or {})
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": result},
                    )
                ],
            )
        )
    else:
        if part.text is None:
            raise RuntimeError("The model returned no README text.")

        with open(os.path.join(TARGET_PROJECT , "README.md"), "w", encoding="utf-8") as f:
            f.write(part.text)
        print("README.md written successfully.")
        break
if __name__ == "__main__":
    print(".")