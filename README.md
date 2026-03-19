# Claude API Mastery — Developer Learning Repo

> A hands-on course for learning the Anthropic Claude API from scratch.  
> Every module has working code in both **Python** and **JavaScript**.  
> Built and tested on Windows. Works on Mac/Linux with minor path changes.

---

## What You Will Learn

| Module | Topic | Key Skills |
|--------|-------|------------|
| Module 1 | API Fundamentals | API keys, first call, models, tokens, pricing |
| Module 2 | Core Features | System prompts, multi-turn memory, streaming |
| Module 3 | Tool Use | Function calling, multi-tool routing, code execution |
| Module 4 | Prompt Engineering | 6 techniques — XML tags, few-shot, chain-of-thought, output control |
| Module 5 | Claude Code | Terminal agent, autonomous file editing, slash commands |
| Module 6 | MCP Protocol | Model Context Protocol, custom MCP servers |
| Module 7 | Advanced API | Batch API, prompt caching, rate limits, error handling |
| Module 8 | Final Project | Production-grade Code Review Assistant CLI tool |

---

## Prerequisites

- Python 3.10+ installed
- Node.js 18+ and npm installed
- An Anthropic API key — get one at https://console.anthropic.com
- Git Bash installed (required for Claude Code on Windows)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/claude-mastery.git
cd claude-mastery
```

### 2. Set your API key

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-YOUR-KEY-HERE", "User")
```
Close and reopen PowerShell, then verify:
```powershell
echo $env:ANTHROPIC_API_KEY
```

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-YOUR-KEY-HERE"
```
Add that line to your `~/.bashrc` or `~/.zshrc` to make it permanent.

### 3. Install Python SDK (once, globally)

```bash
pip install anthropic mcp
```

### 4. Install JS SDK per module

Each module folder has its own `package.json`. Run inside each module folder:

```bash
npm install
```

---

## Running Each Module

### Module 1 — First API Call

```bash
cd module1
python first_call.py
node first_call.mjs
```

**What it does:** Makes your first Claude API call, prints the response and token usage metadata.

---

### Module 2 — Core Features

```bash
cd module2
python system_prompt.py       # system prompts + personas
python multi_turn.py          # multi-turn conversation with memory
python streaming.py           # real-time streaming output

node system_prompt.mjs
node multi_turn.mjs
node streaming.mjs
```

**What it does:** Shows how to give Claude a role, maintain conversation history, and stream responses word by word.

---

### Module 3 — Tool Use

```bash
cd module3
python tool_use.py            # weather tool, code executor, multi-tool routing
node tool_use.mjs
```

**What it does:** Claude calls your functions autonomously. Covers single tool, real Python code execution, and routing between multiple tools.

---

### Module 4 — Prompt Engineering

```bash
cd module4
python prompt_engineering.py  # all 6 techniques + production pattern
node prompt_engineering.mjs
```

**What it does:** Demonstrates vague vs explicit prompts, XML tags, few-shot examples, chain-of-thought, output format control, and positive framing. Ends with a production-ready combined pattern.

---

### Module 5 — Claude Code

Install Claude Code globally (once):
```bash
npm install -g @anthropic-ai/claude-code
```

**Windows only** — set Git Bash path:
```powershell
[System.Environment]::SetEnvironmentVariable("CLAUDE_CODE_GIT_BASH_PATH", "C:\Program Files\Git\bin\bash.exe", "User")
```

Launch from any project folder:
```bash
claude
```

Useful commands inside Claude Code:
```
/init          # create CLAUDE.md project memory file
/mcp           # view connected MCP servers
/help          # all available commands
/exit          # exit
```

---

### Module 6 — MCP Protocol

```bash
cd module6
npm install
python mcp_client.py          # MCP filesystem tools demo
node mcp_client.mjs
```

**Connect your custom MCP server to Claude Code:**
```bash
claude mcp add my_mcp_server python "FULL_PATH/module6/my_mcp_server.py"
```

Then inside Claude Code:
```
use get_code_stats on module4/prompt_engineering.py
```

---

### Module 7 — Advanced API

```bash
cd module7
npm install
python advanced_api.py        # caching + batch API + error handling
node advanced_api.mjs
```

**What it does:**
- Prompt caching — 90% cheaper on repeated system prompts
- Batch API — submit 1000s of requests at 50% discount, results in under 24 hours
- Production error handling — exponential backoff, retry logic, token counting

---

### Module 8 — Final Project (Code Review Assistant)

```bash
cd module8

# Review a single file (with streaming)
python reviewer.py ../module3/tool_use.py

# Review a file + chat about it interactively
python reviewer.py ../module4/prompt_engineering.py --chat

# Batch review an entire folder (all files at once)
python reviewer.py --folder ../
```

**What it does:** A complete CLI tool that combines all modules — streaming reviews, multi-turn chat, batch processing, prompt caching, cost tracking, and production error handling.

---

## Project Structure

```
claude-mastery/
├── module1/
│   ├── first_call.py
│   └── first_call.mjs
├── module2/
│   ├── system_prompt.py / .mjs
│   ├── multi_turn.py / .mjs
│   └── streaming.py / .mjs
├── module3/
│   └── tool_use.py / .mjs
├── module4/
│   └── prompt_engineering.py / .mjs
├── module5/                        # Claude Code — no scripts, run `claude` in terminal
├── module6/
│   ├── mcp_client.py / .mjs
│   └── my_mcp_server.py            # custom MCP server
├── module7/
│   └── advanced_api.py / .mjs
├── module8/
│   └── reviewer.py                 # final production tool
├── hello.py                        # created by Claude Code (Module 5 demo)
├── buggy.py                        # created + fixed by Claude Code (Module 5 demo)
├── code_reviewer.py                # 145-line tool written by Claude Code
├── CLAUDE.md                       # Claude Code project memory
└── README.md
```

---

## API Patterns Reference

These four patterns appear throughout every module. Learn them once, use them everywhere.

### Pattern 1 — Basic call

```python
import anthropic
client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from environment

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.content[0].text)
```

### Pattern 2 — Multi-turn conversation

```python
history = []

def chat(user_message):
    history.append({"role": "user", "content": user_message})
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=history          # send full history every time
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply
```

### Pattern 3 — Tool use loop

```python
response = client.messages.create(model=..., tools=tools, messages=messages)

if response.stop_reason == "tool_use":
    tool_block = next(b for b in response.content if b.type == "tool_use")
    result = your_function(**tool_block.input)       # YOU run the function
    # send result back to Claude
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_block.id, "content": json.dumps(result)}
    ]})
```

### Pattern 4 — Streaming

```python
with client.messages.stream(model=..., messages=messages) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)   # prints each word as it arrives
    final = stream.get_final_message()    # metadata available after stream ends
```

---

## Models Quick Reference

| Model | Best for | Input price |
|-------|----------|-------------|
| `claude-haiku-4-5-20251001` | Fast, cheap, high volume | $0.80 / M tokens |
| `claude-sonnet-4-6` | Everything — use this by default | $3.00 / M tokens |
| `claude-opus-4-6` | Complex reasoning, hardest tasks | $15.00 / M tokens |

For all learning and most production use cases: **use `claude-sonnet-4-6`**.

---

## Cost Guide

A typical API call (500 input + 200 output tokens) costs approximately **₹0.13**.  
Running all 8 modules end to end costs approximately **₹100–150** total.

To avoid surprise charges, set a monthly spending limit at:  
https://console.anthropic.com → Billing → Limits

---

## Troubleshooting

**`npm` not found on Windows:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**`ANTHROPIC_API_KEY` not found:**  
Make sure you opened a new terminal after setting the environment variable.

**`ERR_MODULE_NOT_FOUND` for `@anthropic-ai/sdk`:**  
You need to run `npm install` inside the module folder first.

**Claude Code requires Git Bash:**  
Install from https://git-scm.com/downloads/win and set the path variable (see Module 5 setup above).

**Batch API `custom_id` error:**  
IDs must match `^[a-zA-Z0-9_-]{1,64}$` — no file paths or special characters.

---

## Resources

- Anthropic API Docs: https://docs.claude.com
- API Console + Keys: https://console.anthropic.com
- Claude Code Docs: https://docs.claude.com/en/docs/claude-code/overview
- Prompt Engineering Guide: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- MCP Documentation: https://code.claude.com/docs/en/mcp

---

## Author

Built by **Abhijith JAYAKARA** as a hands-on learning project for Anthropic Claude API mastery.  
All modules written and tested on Windows 11, Python 3.14, Node.js v24.
