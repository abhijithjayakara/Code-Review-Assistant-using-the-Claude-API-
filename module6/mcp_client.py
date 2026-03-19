import anthropic
import subprocess
import json
import os

client = anthropic.Anthropic()

# ============================================================
# WHAT MCP LOOKS LIKE FROM THE API SIDE
# The key difference from Tool Use:
# Tools come FROM the MCP server automatically — you don't define them
# ============================================================

print("=" * 55)
print("MODULE 6: MCP — Model Context Protocol")
print("=" * 55)

# ============================================================
# DEMO 1 — Understand MCP tool structure
# This shows what an MCP server's tools look like
# identical to Tool Use but defined by the SERVER not you
# ============================================================

print("\n--- DEMO 1: What MCP tools look like ---")

# Simulating what an MCP filesystem server exposes
# In real MCP these come automatically from the server
mcp_filesystem_tools = [
    {
        "name": "read_file",
        "description": "Read the complete contents of a file from the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating it if it doesn't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files matching a pattern in a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "pattern": {"type": "string"}
            },
            "required": ["path", "pattern"]
        }
    }
]

print(f"MCP server exposed {len(mcp_filesystem_tools)} tools:")
for t in mcp_filesystem_tools:
    print(f"  - {t['name']}: {t['description'][:55]}...")

# ============================================================
# DEMO 2 — Implement the MCP tool handlers
# These are your LOCAL implementations of the server tools
# ============================================================

print("\n--- DEMO 2: Tool handlers (your local MCP server) ---")

def handle_mcp_tool(tool_name, tool_input):
    """Route MCP tool calls to real implementations."""

    if tool_name == "read_file":
        path = tool_input["path"]
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content,
                "size_bytes": os.path.getsize(path),
                "lines": content.count("\n") + 1
            }
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "write_file":
        path = tool_input["path"]
        content = tool_input["content"]
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "list_directory":
        path = tool_input["path"]
        if not os.path.exists(path):
            return {"error": f"Directory not found: {path}"}
        try:
            items = []
            for item in os.listdir(path):
                full = os.path.join(path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(full) else "file",
                    "size": os.path.getsize(full) if os.path.isfile(full) else None
                })
            return {"path": path, "items": items, "count": len(items)}
        except Exception as e:
            return {"error": str(e)}

    elif tool_name == "search_files":
        import fnmatch
        path = tool_input["path"]
        pattern = tool_input["pattern"]
        matches = []
        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d != "node_modules"]
                for fname in files:
                    if fnmatch.fnmatch(fname, pattern):
                        matches.append(os.path.join(root, fname))
            return {"matches": matches, "count": len(matches)}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown tool: {tool_name}"}

print("Tool handlers ready: read_file, write_file, list_directory, search_files")

# ============================================================
# DEMO 3 — Full MCP conversation loop
# Claude uses filesystem tools to explore your project
# ============================================================

print("\n--- DEMO 3: Claude explores your project via MCP ---\n")

def run_mcp_conversation(user_message, max_turns=5):
    """
    Full MCP agentic loop.
    Claude can call tools multiple times before giving final answer.
    This is the core of any MCP-powered agent.
    """
    messages = [{"role": "user", "content": user_message}]
    turn = 0

    while turn < max_turns:
        turn += 1

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system="""You are a helpful coding assistant with filesystem access.
Use tools to explore and understand the codebase before answering.
Always read files before making claims about their content.""",
            tools=mcp_filesystem_tools,
            messages=messages
        )

        # If Claude is done — return final answer
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            return final_text

        # If Claude wants to use tools
        if response.stop_reason == "tool_use":
            # Add Claude's response to history
            messages.append({"role": "assistant", "content": response.content})

            # Process ALL tool calls Claude made in this turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [MCP] Claude calling: {block.name}({json.dumps(block.input)[:60]}...)")
                    result = handle_mcp_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            # Return all tool results to Claude
            messages.append({"role": "user", "content": tool_results})

    return "Max turns reached"

# Ask Claude to explore your real project
project_path = r"C:\Users\LENOVO\claude-mastery"

print("Question 1: Explore the project structure")
answer1 = run_mcp_conversation(
    f"List the directory at {project_path}, then tell me how many Python files exist and what modules are present."
)
print(f"Answer: {answer1}\n")

print("Question 2: Read and summarize a real file")
answer2 = run_mcp_conversation(
    f"Read the file {project_path}\\module4\\prompt_engineering.py and tell me which prompt engineering technique is most useful for production APIs and why."
)
print(f"Answer: {answer2}\n")

# ============================================================
# DEMO 4 — Claude WRITES a file via MCP
# ============================================================

print("--- DEMO 4: Claude writes a real file via MCP ---\n")

answer3 = run_mcp_conversation(
    f"""Read {project_path}\\code_reviewer.py to understand the pattern, 
then create a new file at {project_path}\\module6\\mcp_demo_output.txt 
that contains a summary of what MCP is and why it matters, written as 
if explaining to a manager. Keep it under 200 words."""
)
print(f"Answer: {answer3}")

# Verify the file was actually created
output_file = os.path.join(project_path, "module6", "mcp_demo_output.txt")
if os.path.exists(output_file):
    print(f"\n✅ File was actually created: {output_file}")
    with open(output_file) as f:
        print("--- File contents ---")
        print(f.read())
else:
    print("\n⚠️  File was not created")

# ============================================================
# DEMO 5 — Build your own MCP server (the real thing)
# ============================================================

print("\n--- DEMO 5: Your own MCP server structure ---")
print("Now we build a real MCP server that Claude Code can connect to.\n")

mcp_server_code = '''#!/usr/bin/env python3
"""
my_mcp_server.py — A real MCP server using the official SDK.
Claude Code connects to this and gets tools automatically.

Run with: python my_mcp_server.py
Then in Claude Code: /mcp add my-tools python my_mcp_server.py
"""

from mcp.server.fastmcp import FastMCP

# Create MCP server — give it a name
mcp = FastMCP("my-dev-tools")

@mcp.tool()
def get_code_stats(filepath: str) -> dict:
    """
    Get statistics about a code file.
    Returns line count, function count, and import count.
    """
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
        functions = len([l for l in lines if l.strip().startswith("def ")])
        imports = len([l for l in lines if l.strip().startswith("import") or l.strip().startswith("from")])
        
        return {
            "filepath": filepath,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_or_comment_lines": total_lines - code_lines,
            "function_count": functions,
            "import_count": imports
        }
    except FileNotFoundError:
        return {"error": f"File not found: {filepath}"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def check_python_style(filepath: str) -> dict:
    """
    Check a Python file for basic style issues.
    Returns a list of issues found.
    """
    issues = []
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line.rstrip()) > 100:
                issues.append(f"Line {i}: too long ({len(line.rstrip())} chars, max 100)")
            # Check for trailing whitespace
            if line != line.rstrip() + "\\n" and line.rstrip():
                issues.append(f"Line {i}: trailing whitespace")
            # Check for tabs
            if "\\t" in line:
                issues.append(f"Line {i}: tab character found, use spaces")
        
        return {
            "filepath": filepath,
            "issues_found": len(issues),
            "issues": issues[:10],  # first 10 only
            "clean": len(issues) == 0
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()  
def summarize_directory(dirpath: str) -> dict:
    """
    Summarize all Python files in a directory.
    Returns counts and file list.
    """
    import os
    import fnmatch
    
    py_files = []
    try:
        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if d not in ["node_modules", "__pycache__", ".git"]]
            for f in files:
                if fnmatch.fnmatch(f, "*.py"):
                    py_files.append(os.path.join(root, f))
        
        return {
            "directory": dirpath,
            "python_files": py_files,
            "total_python_files": len(py_files)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting MCP server: my-dev-tools")
    print("Tools available: get_code_stats, check_python_style, summarize_directory")
    mcp.run()
'''

# Write the MCP server file
server_path = os.path.join(project_path, "module6", "my_mcp_server.py")
with open(server_path, "w") as f:
    f.write(mcp_server_code)

print(f"✅ MCP server written to: {server_path}")
print("\nTo connect this to Claude Code:")
print("  1. Open Claude Code: claude")
print("  2. Type: /mcp")
print("  3. Add your server and it appears as tools automatically")