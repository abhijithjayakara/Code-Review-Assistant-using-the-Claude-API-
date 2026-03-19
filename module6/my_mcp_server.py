#!/usr/bin/env python3
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
            if line != line.rstrip() + "\n" and line.rstrip():
                issues.append(f"Line {i}: trailing whitespace")
            # Check for tabs
            if "\t" in line:
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
