"""
code_reviewer.py — AI-powered code review tool using the Claude API.

Usage:
    python code_reviewer.py <filename>

Output:
    A JSON report with score, issues, verdict, and summary printed to stdout.
"""

import sys
import json
import os
import anthropic

SYSTEM_PROMPT = """You are a senior code reviewer API. Your job is to review code and return a structured report.

<rules>
- Respond ONLY in valid JSON — no markdown, no code fences, no extra text
- Find between 1 and 10 issues (proportional to code size and quality)
- Reference specific variable names, line patterns, or function names where possible
- severity must be one of: critical, high, medium, low
- verdict must be one of: approve, request_changes, reject
  - approve: score 8-10, no critical/high issues
  - request_changes: score 5-7, or has high issues but no critical
  - reject: score 1-4, or has any critical issues
</rules>

<output_schema>
{
  "overall_score": <int 1-10>,
  "verdict": "<approve|request_changes|reject>",
  "language": "<detected programming language>",
  "issues": [
    {
      "severity": "<critical|high|medium|low>",
      "description": "<what is wrong and where>",
      "fix": "<exactly how to fix it>"
    }
  ],
  "one_line_summary": "<single sentence verdict>"
}
</output_schema>

<examples>
Input code: def divide(a, b): return a/b
Output: {"overall_score": 4, "verdict": "reject", "language": "Python", "issues": [{"severity": "critical", "description": "No division-by-zero guard — crashes when b=0", "fix": "Add 'if b == 0: raise ValueError(\"divisor cannot be zero\")' before return"}, {"severity": "medium", "description": "No type hints on parameters or return value", "fix": "Change signature to: def divide(a: float, b: float) -> float"}], "one_line_summary": "Unguarded division will crash at runtime — not safe to ship."}
</examples>"""


def read_source_file(path: str) -> str:
    if not os.path.exists(path):
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(path):
        print(f"Error: path is not a file: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Error: cannot read '{path}' as text (binary file?)", file=sys.stderr)
        sys.exit(1)


def review_code(filename: str, source: str) -> dict:
    client = anthropic.Anthropic()

    user_message = f"""<filename>{filename}</filename>

<code>
{source}
</code>

Review this code thoroughly and return your JSON report."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.AuthenticationError:
        print("Error: invalid or missing ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)
    except anthropic.RateLimitError:
        print("Error: API rate limit reached. Try again in a moment.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("Error: could not connect to the Anthropic API. Check your network.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIStatusError as e:
        print(f"Error: API returned status {e.status_code}: {e.message}", file=sys.stderr)
        sys.exit(1)

    raw = response.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("Error: API response was not valid JSON:", file=sys.stderr)
        print(raw, file=sys.stderr)
        sys.exit(1)


def print_report(report: dict, filename: str) -> None:
    print(json.dumps(report, indent=2))

    # Human-readable summary to stderr so stdout stays pure JSON
    score = report.get("overall_score", "?")
    verdict = report.get("verdict", "?").upper()
    summary = report.get("one_line_summary", "")
    issues = report.get("issues", [])

    print(f"\n--- {filename} ---", file=sys.stderr)
    print(f"Score  : {score}/10", file=sys.stderr)
    print(f"Verdict: {verdict}", file=sys.stderr)
    print(f"Summary: {summary}", file=sys.stderr)
    print(f"Issues : {len(issues)}", file=sys.stderr)
    for issue in issues:
        sev = issue.get("severity", "?").upper()
        desc = issue.get("description", "")
        print(f"  [{sev}] {desc}", file=sys.stderr)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python code_reviewer.py <filename>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]
    source = read_source_file(filename)

    if not source.strip():
        print(f"Error: '{filename}' is empty.", file=sys.stderr)
        sys.exit(1)

    report = review_code(filename, source)
    print_report(report, filename)


if __name__ == "__main__":
    main()
