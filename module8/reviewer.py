#!/usr/bin/env python3
"""
Team Code Review Assistant
Uses Claude API — Modules 1-7 techniques combined.

Usage:
  python reviewer.py <file>          — review a file
  python reviewer.py <file> --chat   — review then chat about it
  python reviewer.py --folder <dir>  — batch review entire folder
"""

import anthropic
import json
import sys
import os
import time
import random
import argparse
from pathlib import Path

# ── Setup ────────────────────────────────────────────────────
client = anthropic.Anthropic()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".mjs", ".ts", ".java",
    ".cpp", ".c", ".go", ".rs", ".rb"
}

# ── System prompt (cached for cost efficiency) ───────────────
SYSTEM_PROMPT = """You are a senior software engineer conducting code reviews.

<rules>
- Be direct, specific, and actionable
- Always reference exact line numbers or function names
- Severity: CRITICAL (security/data loss) | HIGH (bugs/logic) | MEDIUM (quality) | LOW (style)
- Respond ONLY in valid JSON matching the schema below
- Find between 2 and 6 issues per review
</rules>

<output_schema>
{
  "score": <int 1-10>,
  "verdict": "<APPROVE|REQUEST_CHANGES|REJECT>",
  "language": "<detected language>",
  "issues": [
    {
      "severity": "<CRITICAL|HIGH|MEDIUM|LOW>",
      "location": "<function name or line reference>",
      "description": "<what is wrong>",
      "fix": "<exactly how to fix it>"
    }
  ],
  "strengths": ["<things done well>"],
  "one_line_summary": "<single sentence verdict>"
}
</output_schema>

<examples>
Input: def get_user(id): return db.query(f"SELECT * FROM users WHERE id={id}")
Output: {"score": 1, "verdict": "REJECT", "language": "Python", "issues": [{"severity": "CRITICAL", "location": "get_user()", "description": "SQL injection via f-string interpolation", "fix": "Use parameterized query: db.query('SELECT * FROM users WHERE id=?', (id,))"}], "strengths": [], "one_line_summary": "Critical SQL injection vulnerability makes this unsafe for any production use."}
</examples>"""

# ── Cost tracking ─────────────────────────────────────────────
session_costs = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

def track_cost(response):
    session_costs["input_tokens"]  += response.usage.input_tokens
    session_costs["output_tokens"] += response.usage.output_tokens
    session_costs["calls"]         += 1

def print_session_cost():
    cost = (session_costs["input_tokens"]  / 1_000_000 * 3.00 +
            session_costs["output_tokens"] / 1_000_000 * 15.00)
    print(f"\n💰 Session cost: ${cost:.5f} ({session_costs['calls']} calls, "
          f"{session_costs['input_tokens']:,} input + "
          f"{session_costs['output_tokens']:,} output tokens)")

# ── Production API call with retry ───────────────────────────
def call_claude(messages, stream=False, max_retries=3):
    for attempt in range(max_retries):
        try:
            if stream:
                return client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=[{
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}  # Module 7 caching
                    }],
                    messages=messages
                )
            else:
                r = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=[{
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"}
                    }],
                    messages=messages
                )
                track_cost(r)
                return r

        except anthropic.RateLimitError:
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"  ⏳ Rate limited — retrying in {wait:.1f}s...")
            time.sleep(wait)
        except anthropic.AuthenticationError:
            print("❌ Invalid API key — check ANTHROPIC_API_KEY")
            sys.exit(1)
        except anthropic.APIConnectionError:
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"  🔌 Connection error — retrying in {wait:.1f}s...")
            time.sleep(wait)

    print("❌ Failed after retries")
    sys.exit(1)

# ── Pretty print a review report ─────────────────────────────
def print_report(data: dict, filename: str):
    score   = data.get("score", 0)
    verdict = data.get("verdict", "UNKNOWN")
    issues  = data.get("issues", [])
    strengths = data.get("strengths", [])

    # Score emoji
    emoji = "✅" if score >= 8 else "⚠️" if score >= 5 else "❌"

    print(f"\n{'='*60}")
    print(f"  {emoji}  {filename}")
    print(f"  Score: {score}/10   Verdict: {verdict}")
    print(f"  {data.get('one_line_summary', '')}")
    print(f"{'='*60}")

    # Issues by severity
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}

    for sev in severity_order:
        sev_issues = [i for i in issues if i.get("severity") == sev]
        for issue in sev_issues:
            print(f"\n{severity_emoji[sev]} [{sev}] {issue.get('location', '')}")
            print(f"   Problem: {issue.get('description', '')}")
            print(f"   Fix:     {issue.get('fix', '')}")

    if strengths:
        print(f"\n✨ Strengths:")
        for s in strengths:
            print(f"   • {s}")

# ── Review a single file ──────────────────────────────────────
def review_file(filepath: str, chat_mode: bool = False):
    path = Path(filepath)

    if not path.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    if path.suffix not in SUPPORTED_EXTENSIONS:
        print(f"⚠️  Unsupported file type: {path.suffix}")

    code = path.read_text(encoding="utf-8", errors="replace")

    if not code.strip():
        print("❌ File is empty")
        sys.exit(1)

    print(f"\n🔍 Reviewing {path.name} ({len(code):,} chars)...")

    # Count tokens before sending (Module 7)
    token_check = client.messages.count_tokens(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": f"Review this {path.suffix} code:\n\n{code}"}]
    )
    print(f"   Tokens: ~{token_check.input_tokens:,} input")

    # Stream the review (Module 2 streaming)
    print("\n📋 Review (streaming):\n")
    full_response = ""

    with call_claude(
        messages=[{"role": "user", "content": f"Review this {path.suffix} code:\n\n{code}"}],
        stream=True
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text
        final = stream.get_final_message()
        track_cost(final)

    print("\n")

    # Parse and pretty-print
    try:
        # Strip markdown fences if present
        clean = full_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        data = json.loads(clean.strip())
        print_report(data, path.name)
    except json.JSONDecodeError:
        print("(Could not parse JSON — raw output shown above)")
        data = {}

    # Chat mode — multi-turn conversation about the code (Module 2)
    if chat_mode and data:
        print(f"\n{'='*60}")
        print("💬 Chat mode — ask questions about this review")
        print("   Type 'exit' to quit")
        print(f"{'='*60}\n")

        history = [
            {"role": "user",      "content": f"Review this {path.suffix} code:\n\n{code}"},
            {"role": "assistant", "content": full_response}
        ]

        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if question.lower() in ("exit", "quit", "q"):
                break
            if not question:
                continue

            history.append({"role": "user", "content": question})

            print("Claude: ", end="", flush=True)
            reply = ""

            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system="You are a senior code reviewer. Answer questions about the code review you just performed. Be specific and helpful.",
                messages=history
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    reply += text
                final = stream.get_final_message()
                track_cost(final)

            print("\n")
            history.append({"role": "assistant", "content": reply})

    print_session_cost()

# ── Batch review an entire folder ────────────────────────────
def review_folder(folder: str):
    path = Path(folder)

    if not path.exists() or not path.is_dir():
        print(f"❌ Directory not found: {folder}")
        sys.exit(1)

    # Find all supported files
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(path.rglob(f"*{ext}"))

    # Skip node_modules and __pycache__
    files = [f for f in files if "node_modules" not in str(f)
             and "__pycache__" not in str(f)]

    if not files:
        print(f"❌ No supported code files found in {folder}")
        sys.exit(1)

    print(f"\n📁 Found {len(files)} files to review in {folder}")
    print("🚀 Submitting batch review (50% cheaper than normal)...\n")

    # Build batch requests (Module 7)
    batch_requests = []
    for idx, f in enumerate(files):
        code = f.read_text(encoding="utf-8", errors="replace")
        if code.strip():
            batch_requests.append({
                "custom_id": f"file_{idx}",
                "params": {
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 2048,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user",
                                  "content": f"Review this {f.suffix} code:\n\n{code[:8000]}"}]
                }
            })

    if not batch_requests:
        print("❌ No non-empty files found")
        sys.exit(1)

    # Submit batch
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"✅ Batch submitted: {batch.id}")
    print(f"   {len(batch_requests)} files queued\n")

    # Poll for results
    print("⏳ Waiting for results...")
    for i in range(120):
        time.sleep(5)
        batch = client.messages.batches.retrieve(batch.id)
        done = batch.request_counts.succeeded + batch.request_counts.errored
        total = len(batch_requests)
        print(f"   [{i+1}] {done}/{total} complete — status: {batch.processing_status}")

        if batch.processing_status == "ended":
            break

    # Print results
    print(f"\n{'='*60}")
    print(f"  📊 BATCH REVIEW RESULTS")
    print(f"{'='*60}")

    results = []
    for result in client.messages.batches.results(batch.id):
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            try:
                clean = text.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                data = json.loads(clean.strip())
                fname = Path(files[int(result.custom_id.split("_")[1])]).name
                results.append((data.get("score", 0), fname, data))
            except:
                pass

    # Sort by score (worst first)
    results.sort(key=lambda x: x[0])

    for score, fname, data in results:
        emoji = "✅" if score >= 8 else "⚠️" if score >= 5 else "❌"
        issues = data.get("issues", [])
        critical = sum(1 for i in issues if i.get("severity") == "CRITICAL")
        print(f"  {emoji} {fname:<40} {score}/10  "
              f"{'🔴 '+str(critical)+' critical' if critical else ''}")

    # Save full report
    report_path = path / "review_report.json"
    with open(report_path, "w") as f:
        json.dump([{"file": r[1], "score": r[0], "data": r[2]} for r in results],
                  f, indent=2)
    print(f"\n📄 Full report saved: {report_path}")

# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AI Code Review Assistant powered by Claude"
    )
    parser.add_argument("file",    nargs="?",           help="File to review")
    parser.add_argument("--chat",  action="store_true", help="Chat about the review")
    parser.add_argument("--folder",                     help="Review entire folder")

    args = parser.parse_args()

    print("\n🤖 Claude Code Review Assistant")
    print(   "   Powered by Anthropic Claude API\n")

    if args.folder:
        review_folder(args.folder)
    elif args.file:
        review_file(args.file, chat_mode=args.chat)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()