# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A hands-on learning course for the Anthropic Claude API, with each module teaching one concept. Every module has both a Python implementation (`.py`) and a JavaScript implementation (`.mjs`).

## Running the scripts

### Python (any module)
Requires `ANTHROPIC_API_KEY` set in the environment and the `anthropic` package installed.

```bash
pip install anthropic
python module1/first_call.py
python module2/streaming.py
python module3/tool_use.py
python module4/prompt_engineering.py
```

### JavaScript (modules 1–3)
Each module has its own `node_modules`. Run from inside the module directory.

```bash
cd module1 && node first_call.mjs
cd module2 && node streaming.mjs
cd module3 && node tool_use.mjs
```

Note: `module1` uses `"type": "module"` (ESM); `module2` uses `"type": "commonjs"` — keep this in mind if adding new `.mjs`/`.js` files.

### code_reviewer.py (root-level tool)
```bash
python code_reviewer.py <path/to/file>
```
Sends the file to Claude and prints a JSON report to stdout plus a human-readable summary to stderr.

## Architecture

### Module progression
Each module builds on the previous concept:

| Module | Python entry point | Concept |
|--------|-------------------|---------|
| module1 | `first_call.py` | Single API call, inspecting usage metadata |
| module2 | `system_prompt.py`, `multi_turn.py`, `streaming.py` | System prompts + personas, stateful conversation via manual history array, streaming with `messages.stream()` |
| module3 | `tool_use.py` | Tool-calling loop: define schema → Claude requests call → you execute → return result → Claude finalizes |
| module4 | `prompt_engineering.py` | Six prompt techniques: explicit prompts, XML tags, few-shot, chain-of-thought, output format control, positive framing |

### Key API patterns used across the repo

**Client instantiation** — always reads `ANTHROPIC_API_KEY` from environment automatically:
```python
client = anthropic.Anthropic()
```

**Conversation history** — Claude has no memory between calls; statefulness is achieved by growing and re-sending the full `messages` array on every turn (see `module2/multi_turn.py`).

**Tool use loop** — the standard pattern is two API calls per tool invocation:
1. Send message with `tools=` list → Claude responds with `stop_reason: "tool_use"`
2. Execute the tool locally, append `tool_result` to messages, call API again → Claude gives final text answer

**Structured output** — enforced via system prompt with XML `<output_schema>` tags + a few-shot example. The model is instructed to return only valid JSON with no markdown fences.

**Streaming** — use `client.messages.stream()` as a context manager; iterate `stream.text_stream` for chunks, call `stream.get_final_message()` after the `with` block for token usage.

### code_reviewer.py design
- `read_source_file()` → validates path and encoding
- `review_code()` → calls Claude with a strict system prompt (XML tags + output schema + few-shot example); handles all `anthropic` API exceptions explicitly; `max_tokens=4096` to handle large files
- `print_report()` → JSON to stdout (pipeable), human summary to stderr
- Exit codes: `0` success, `1` any error
