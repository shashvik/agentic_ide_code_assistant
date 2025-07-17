import csv
import os,subprocess
from google.adk.agents import Agent,SequentialAgent,ParallelAgent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import tempfile
import shutil # For removing temporary directories
from google.auth.transport.requests import AuthorizedSession
from google.auth import default
import io
import json
from typing import Optional, List, Dict, Union, Literal
from google.adk.tools.agent_tool import AgentTool



from datetime import datetime
# os already imported
from google.adk.tools import google_search
# from google.adk.tools.agent_tool import AgentTool # Already imported above

# Load environment variables (e.g., API keys)
load_dotenv()

# --- Sandboxing Setup ---
SANDBOX_DIR = os.path.abspath("agentic_coder")

def _get_sandboxed_path(path: str) -> str:
    """
    Ensures that the provided path is safely contained within the SANDBOX_DIR.
    Prevents directory traversal attacks.
    """
    # Create the sandbox directory if it doesn't exist
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    
    # Normalize the requested path to resolve any '..' components
    normalized_path = os.path.normpath(os.path.join(SANDBOX_DIR, path))
    
    # Check if the normalized path is within the sandbox directory
    if os.path.commonprefix([normalized_path, SANDBOX_DIR]) != SANDBOX_DIR:
        raise ValueError(f"Path '{path}' is outside the allowed sandbox directory.")
        
    return normalized_path

# --- Tool Definitions ---

# Tool for creating directories
def create_directory(path: str) -> str:
    """
    Creates a new directory at the specified path within the sandbox.
    """
    try:
        sandboxed_path = _get_sandboxed_path(path)
        os.makedirs(sandboxed_path, exist_ok=True)
        return f"Directory '{sandboxed_path}' created successfully."
    except Exception as e:
        return f"Error creating directory '{path}': {e}"

# Tool for creating and writing to files
def create_and_write_file(path: str, content: str) -> str:
    """
    Creates a new file or overwrites an existing one at the specified path with the given content within the sandbox.
    """
    try:
        sandboxed_path = _get_sandboxed_path(path)
        with open(sandboxed_path, 'w') as f:
            f.write(content)
        return f"File '{sandboxed_path}' created/written successfully."
    except Exception as e:
        return f"Error creating/writing file '{path}': {e}"

# Tool for listing directory contents
def list_directory_contents(path: str) -> List[str]:
    """
    Lists the contents (files and directories) of a specified directory within the sandbox.
    """
    try:
        sandboxed_path = _get_sandboxed_path(path)
        return os.listdir(sandboxed_path)
    except FileNotFoundError:
        return [f"Error: Directory '{path}' not found."]
    except Exception as e:
        return [f"Error listing directory '{path}': {e}"]

def _build_file_tree(root_dir, relative_root=''):
    tree = []
    for item in sorted(os.listdir(root_dir)):
        full_path = os.path.join(root_dir, item)
        relative_path = os.path.join(relative_root, item)
        node = {
            "id": relative_path, 
            "name": item,
        }
        if os.path.isdir(full_path):
            node["type"] = "folder"
            node["children"] = _build_file_tree(full_path, relative_path)
        else:
            node["type"] = "file"
            ext = item.split('.')[-1]
            lang_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'html': 'html', 'css': 'css'}
            if ext in lang_map:
                node['language'] = lang_map[ext]

        tree.append(node)
    return tree

def list_directory_contents_recursive(path: str) -> Union[List[Dict], Dict]:
    """
    Recursively lists the contents of a specified directory within the sandbox.
    """
    try:
        sandboxed_path = _get_sandboxed_path(path)
        if not os.path.isdir(sandboxed_path):
            return {"error": f"Path '{path}' is not a directory."}
        return _build_file_tree(sandboxed_path)
    except Exception as e:
        return {"error": str(e)}


# Tool for executing shell commands (use with caution!)
def execute_shell_command(command: str) -> str:
    """
    Executes a shell command within the sandbox directory and returns its output.
    Use with extreme caution as this can execute arbitrary commands.
    """
    try:
        # Ensure the sandbox directory exists before running the command
        os.makedirs(SANDBOX_DIR, exist_ok=True)
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True, 
            cwd=SANDBOX_DIR  # Execute the command in the sandboxed directory
        )
        return f"Command executed successfully in '{SANDBOX_DIR}'. Output:\n{result.stdout}\nErrors:\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return f"Command failed with exit code {e.returncode}. Output:\n{e.stdout}\nErrors:\n{e.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

# NEW TOOLS for code manipulation
def read_file_content(path: str) -> str:
    """
    Reads the entire content of a file at the specified path within the sandbox and returns it as a string.
    """
    try:
        sandboxed_path = _get_sandboxed_path(path)
        with open(sandboxed_path, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except Exception as e:
        return f"Error reading file '{path}': {e}"

def replace_lines_in_file(file_path: str, start_line: int, end_line: int, new_lines_content: str) -> str:
    """
    Replaces a range of lines (inclusive, 1-based indexing) in a file with new content within the sandbox.
    The `new_lines_content` should be a string representing the new lines, with
    newlines to separate them if multiple lines are intended.
    """
    try:
        sandboxed_path = _get_sandboxed_path(file_path)
        with open(sandboxed_path, 'r') as f:
            lines = f.readlines() # Read all lines including their newlines

        # Adjust for 0-based indexing
        start_idx = start_line - 1
        end_idx = end_line - 1

        # Basic validation for line range
        if not (0 <= start_idx < len(lines) and 0 <= end_idx < len(lines) and start_idx <= end_idx):
            return f"Error: Line range [{start_line}, {end_line}] is invalid for file '{sandboxed_path}' (total lines: {len(lines)})."

        # Prepare new content lines, ensuring they also have newlines
        new_content_as_list = new_lines_content.splitlines(keepends=True)

        # Construct the new list of lines
        updated_lines = lines[:start_idx] + new_content_as_list + lines[end_idx + 1:]

        with open(sandboxed_path, 'w') as f:
            f.writelines(updated_lines)

        return f"Lines {start_line} to {end_line} in '{sandboxed_path}' replaced successfully."
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error replacing lines in file '{file_path}': {e}"


# --- Agent Definitions ---

# NEW AGENT: Documentation Search Agent
documentation_search_agent = Agent(
    name="documentation_search_agent",
    description="An expert in performing Google searches to find answers to user questions from reliable documentation.",
    instruction=f"""
    You are a highly skilled information retrieval agent. Your core function is to answer user questions by leveraging the `Google Search` tool to find information from authoritative documentation.

    When a user asks a question:
    1.  **Formulate precise search queries** using keywords from the user's question, prioritizing terms that would lead to official documentation (e.g., "GCP IAM roles documentation", "Kubernetes networking best practices guide", "AWS S3 bucket policy syntax").
    2.  **Execute the `Google Search` tool** with your formulated query.
    3.  **Carefully analyze the search results.** Prioritize results from official documentation, reputable cloud provider guides, well-known industry standards, or trusted technical blogs. Disregard less reliable sources like forums or outdated tutorials if official documentation is available.
    4.  **Synthesize a concise and accurate answer** based *only* on the information found in the documentation.
    5.  **Cite your sources** by providing the URLs of the documents from which you extracted the answer. If multiple sources were used, list them all.
    6.  If you cannot find a definitive answer or sufficient documentation, clearly state that the information could not be found with the available tools and suggest alternative approaches if possible.

    Input to this agent will be a string representing the user's question.
    Your output should be a clear, well-structured answer with cited sources.
    """,
    tools=[google_search]
)

# Define a Pydantic model for the expected output of the CodePlannerAgent
class CodePlan(BaseModel):
    project_name: str = Field(..., description="The suggested name for the project.")
    file_structure: Dict[str, Union[str, Dict]] = Field(..., description="A nested dictionary representing the desired file and folder structure. Keys are names, values are either file content (string) or another dictionary for subdirectories.")
    technologies: List[str] = Field(..., description="List of technologies/languages to be used.")
    main_task: str = Field(..., description="A concise description of the primary task the generated code should accomplish.")
    steps: List[str] = Field(..., description="A high-level plan of steps to accomplish the main task.")

# Sub-agent for planning the code structure and content
code_planner_agent = Agent(
    name='CodePlannerAgent',
    description="An agent that plans the file structure, content, and overall strategy for a coding project based on a user prompt.",
    instruction=f"""
    You are an expert software architect and planner. Your task is to analyze the user's request and
    generate a detailed plan for the coding project. This plan should include:
    1.  **Project Name**: A concise and relevant name for the project.
    2.  **File Structure**: A nested dictionary representing the desired file and folder structure.
        -   For files, the value should be the complete code content (as a string).
        -   For folders, the value should be another nested dictionary.
        -   Example: {{'my_project': {{'src': {{'main.py': 'print("Hello, World!")'}}, 'README.md': '# My Project'}}}}
    3.  **Technologies**: A list of programming languages, frameworks, and libraries that will be used.
    4.  **Main Task**: A single, concise sentence describing the primary goal of the generated code.
    5.  **Steps**: A high-level, ordered list of steps to achieve the main task.

    Be as detailed as possible in the file content, providing functional and runnable code where appropriate.
    Consider best practices for project organization.

    ---
    Constraint: Your output **MUST** conform to the `CodePlan` Pydantic model.
    """,
    tools=[AgentTool(agent=documentation_search_agent)] # Allow planning agent to search for information if needed
)

# Sub-agent for executing the file system operations
file_system_executor_agent = Agent(
    name='FileSystemExecutorAgent',
    description="An agent that creates directories and files based on a structured plan.",
    instruction=f"""
    You are a meticulous file system manager. Your task is to execute the file and folder
    creation based on the provided `CodePlan` from the `CodePlannerAgent`.
    You must use the `create_directory` and `create_and_write_file` tools to
    build the project structure.
    Always start by creating the root project directory.
    Recursively create directories and files as specified in the plan.
    Ensure all files have their content written correctly.

    ---
    Constraint: You must only use the provided file system tools. Do not attempt to
    write code or modify existing files directly unless instructed via the plan's content.
    """,
    tools=[create_directory, create_and_write_file, list_directory_contents], # List contents for debugging/verification
)

# NEW AGENT: CodeRefactorAgent
code_refactor_agent = Agent(
    name='CodeRefactorAgent',
    description="An agent specialized in analyzing, searching, and fixing specific parts of existing code files.",
    instruction=f"""
    You are a meticulous code refactorer and bug fixer. Your primary goal is to address specific
    issues or refactoring requests within existing code files.

    ---
    Workflow:
    1.  **Receive Instruction**: Understand the user's request, which will specify a file path
        and a description of what needs to be found/fixed/refactored.
    2.  **Read File Content**: Use the `read_file_content` tool to get the current content
        of the specified file.
    3.  **Analyze and Identify**: Based on the instruction and the file content, meticulously
        identify the exact lines or sections of code that need modification. This requires
        careful code comprehension. Determine the `start_line`, `end_line` (1-based, inclusive),
        and the `new_lines_content`. The `new_lines_content` should be a single string with
        newlines where appropriate (e.g., if replacing multiple lines or inserting new ones).
        If only one line is changed, `start_line` and `end_line` will be the same.
    4.  **Formulate Replacement**: Construct the `new_lines_content` that will replace the
        identified section. Ensure the new content is syntactically correct and addresses the
        user's request precisely.
    5.  **Apply Fix**: Use the `replace_lines_in_file` tool with the identified line range
        and the new content.
    6.  **Report Outcome**: Inform the user whether the fix was applied successfully or if there
        were any issues, explaining the changes made.

    ---
    Constraint: You must only use the `read_file_content` and `replace_lines_in_file` tools
    for modifying files. Do not create new files unless absolutely necessary for a refactor
    that requires splitting files (which is generally outside the scope of "fixing lines" and requires explicit user instruction).
    Always aim for minimal and precise changes.
    """,
    tools=[read_file_content, replace_lines_in_file, AgentTool(agent=documentation_search_agent)]
)

# Root Agent orchestrating the process
root_agent = Agent(
    model='gemini-2.5-pro',
    name='root_coding_agent',
    description="An advanced coding agent that can generate entire coding projects, including files, folders, and code content, and now also capable of searching and fixing specific parts of existing code.",
    instruction=f"""
    You are the primary orchestrator for building and maintaining coding projects.
    Your main goal is to take a user's prompt, understand the requirements,
    and then delegate to specialized sub-agents to plan, execute, or modify the project.

    ---
    Workflow:
    1.  **Understand the Prompt**: Carefully analyze the user's request.
        -   If the request is to **create a new project or significant new files**, delegate to the `CodePlannerAgent` followed by `FileSystemExecutorAgent`.
        -   If the request is to **find, modify, or fix specific parts of existing code** within a file, delegate to the `CodeRefactorAgent`.
        -   If the request is for **general documentation or information retrieval**, delegate to the `documentation_search_agent`.
    2.  **Plan the Project (if creating)**: Invoke the `CodePlannerAgent` to generate a detailed `CodePlan`.
    3.  **Execute File System Operations (if creating)**: Use the `FileSystemExecutorAgent` to create the planned directories and files.
    4.  **Refactor/Fix Code (if modifying)**: Invoke the `CodeRefactorAgent` with the file path and modification instructions.
    5.  **Verify and Report**: Optionally, use `list_directory_contents` or `read_file_content` to verify the changes and report success or any issues.
    6.  **Provide Instructions/Next Steps**: Inform the user about the actions taken and how they can proceed.
    """,
    global_instruction=(
        """
        You are a highly capable AI assistant specializing in code generation and project setup.
        Always aim to provide functional and well-structured code.
        If the user's prompt is unclear, ask clarifying questions.
        Be polite, helpful, and thorough in your responses.
        When creating files, ensure the content is syntactically correct for the specified language.
        When modifying files, ensure the changes are precise and maintain code integrity.
        """
    ),
    sub_agents=[code_planner_agent,file_system_executor_agent, code_refactor_agent],
    tools=[list_directory_contents, read_file_content,AgentTool(agent=documentation_search_agent)] # Root agent can also use these for overview or verification
)