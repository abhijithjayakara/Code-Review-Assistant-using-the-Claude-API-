import anthropic
import json

client = anthropic.Anthropic()

# ============================================================
# TECHNIQUE 1 — Be Explicit: Vague vs Precise prompts
# ============================================================

print("=" * 50)
print("TECHNIQUE 1: Vague vs Explicit prompts")
print("=" * 50)

# BAD prompt — vague
bad = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=150,
    messages=[{"role": "user", "content": "Tell me about Python."}]
)
print("VAGUE prompt output:")
print(bad.content[0].text[:300])

print()

# GOOD prompt — explicit
good = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=150,
    messages=[{"role": "user", "content": """
Tell me about Python. Specifically:
- Target audience: a Java developer switching to Python
- Focus only on: differences in syntax, typing, and OOP
- Format: 3 bullet points maximum
- Tone: direct and technical
"""}]
)
print("EXPLICIT prompt output:")
print(good.content[0].text)

# ============================================================
# TECHNIQUE 2 — XML Tags for clean structure
# ============================================================

print("\n" + "=" * 50)
print("TECHNIQUE 2: XML tags for structure")
print("=" * 50)

# Without XML tags — Claude might confuse code and instructions
messy_prompt = """
Review this Python function and check if it handles edge cases.
def divide(a, b): return a/b
Focus on security and reliability. Give me a score out of 10.
"""

# With XML tags — crystal clear separation
clean_prompt = """
<task>Review the Python function below for edge cases, security, and reliability.</task>

<code>
def divide(a, b):
    return a/b
</code>

<instructions>
- Identify all edge cases
- Check for security issues
- Rate reliability from 1-10
- Suggest one improved version
</instructions>

<output_format>
Respond ONLY as JSON with keys: edge_cases (list), security_issues (list), score (int), improved_code (string)
</output_format>
"""

r = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=600,
    messages=[{"role": "user", "content": clean_prompt}]
)

print("XML-structured prompt output:")
print(r.content[0].text)

# Parse the JSON
try:
    parsed = json.loads(r.content[0].text)
    print(f"\nParsed score: {parsed['score']}/10")
    print(f"Edge cases found: {len(parsed['edge_cases'])}")
except:
    print("(JSON parsing skipped)")

# ============================================================
# TECHNIQUE 3 — Few-shot examples
# ============================================================

print("\n" + "=" * 50)
print("TECHNIQUE 3: Few-shot examples")
print("=" * 50)

# Without examples — Claude guesses the format you want
no_examples = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[{"role": "user", "content": "Classify this bug: App crashes when user submits empty form"}]
)
print("Without examples:")
print(no_examples.content[0].text)

print()

# With examples — Claude learns your exact format
with_examples = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    system="""You are a bug classifier. Classify bugs using EXACTLY this format:
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
CATEGORY: [UI/BACKEND/DATABASE/SECURITY/PERFORMANCE]
EFFORT: [hours estimate]
SUMMARY: [one line]

Examples:
Input: Login button doesn't respond on mobile
Output:
SEVERITY: HIGH
CATEGORY: UI
EFFORT: 2-4 hours
SUMMARY: Mobile touch event not bound to login handler

Input: SQL query takes 30 seconds on large dataset
Output:
SEVERITY: HIGH
CATEGORY: PERFORMANCE
EFFORT: 4-8 hours
SUMMARY: Missing index on frequently queried column""",
    messages=[{"role": "user", "content": "App crashes when user submits empty form"}]
)
print("With few-shot examples:")
print(with_examples.content[0].text)

# ============================================================
# TECHNIQUE 4 — Chain of Thought
# ============================================================

print("\n" + "=" * 50)
print("TECHNIQUE 4: Chain of thought (step by step reasoning)")
print("=" * 50)

# Without CoT — Claude jumps to answer, may be wrong
no_cot = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[{"role": "user", "content": "Is it better to use a list or dict to store 1 million user records for fast lookup by user_id?"}]
)
print("Without chain of thought:")
print(no_cot.content[0].text[:200])

print()

# With CoT — forces Claude to reason before answering
with_cot = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=400,
    messages=[{"role": "user", "content": """
Is it better to use a list or dict to store 1 million user records for fast lookup by user_id?

Think through this step by step:
1. First analyze the time complexity of each approach
2. Then consider memory usage
3. Then consider the specific use case (lookup by user_id)
4. Then give your final recommendation with reasoning
"""}]
)
print("With chain of thought:")
print(with_cot.content[0].text)

# ============================================================
# TECHNIQUE 5 — Output Format Control
# ============================================================

print("\n" + "=" * 50)
print("TECHNIQUE 5: Controlling output format precisely")
print("=" * 50)

code_to_review = "def process(data): return [x*2 for x in data if x > 0]"

formats = [
    ("JSON only",
     "Respond ONLY with valid JSON. No markdown, no explanation. Keys: issues (list of strings), score (int 1-10)"),

    ("Markdown report",
     "Respond as a markdown report with sections: ## Issues, ## Score, ## Fixed Code"),

    ("One sentence only",
     "Respond in exactly ONE sentence. Maximum 20 words. Be blunt."),

    ("Table format",
     "Respond as a markdown table with columns: Issue | Severity | Fix"),
]

for fmt_name, system in formats:
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": f"Review this code: {code_to_review}"}]
    )
    print(f"\n[Format: {fmt_name}]")
    print(r.content[0].text)

# ============================================================
# TECHNIQUE 6 — Positive framing (DO vs DON'T)
# ============================================================

print("\n" + "=" * 50)
print("TECHNIQUE 6: Positive framing — DO not DON'T")
print("=" * 50)

question = "How do I center a div in CSS?"

# BAD — telling Claude what NOT to do
negative = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    system="Don't use old CSS methods. Don't give long explanations. Don't use tables.",
    messages=[{"role": "user", "content": question}]
)
print("NEGATIVE framing (don't/don't/don't):")
print(negative.content[0].text[:300])

print()

# GOOD — telling Claude exactly what TO do
positive = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    system="Use only modern CSS (flexbox or grid). Give exactly 2 code examples. Each example max 3 lines. No explanation text.",
    messages=[{"role": "user", "content": question}]
)
print("POSITIVE framing (exactly what to do):")
print(positive.content[0].text)

# ============================================================
# BONUS — All techniques combined (production pattern)
# ============================================================

print("\n" + "=" * 50)
print("BONUS: All techniques combined — production pattern")
print("=" * 50)

production_system = """You are a senior code reviewer API.

<rules>
- Respond ONLY in valid JSON — no markdown, no extra text
- Always find between 2 and 5 issues
- Be specific — reference exact line numbers or variable names
- Severity must be one of: critical, high, medium, low
</rules>

<output_schema>
{
  "overall_score": <int 1-10>,
  "verdict": "<approve|request_changes|reject>",
  "issues": [
    {
      "severity": "<critical|high|medium|low>",
      "description": "<what is wrong>",
      "fix": "<exactly how to fix it>"
    }
  ],
  "one_line_summary": "<single sentence verdict>"
}
</output_schema>

<examples>
Input code: x=1
Output: {"overall_score": 2, "verdict": "reject", "issues": [{"severity": "high", "description": "No type hints", "fix": "Add x: int = 1"}, {"severity": "medium", "description": "Meaningless variable name", "fix": "Use descriptive name like count or index"}], "one_line_summary": "Untyped, meaningless variable — not production ready."}
</examples>"""

code = """
def get_users(db, active=True):
    users = db.execute("SELECT * FROM users WHERE active=" + str(active))
    result = []
    for u in users:
        result.append(u)
    return result
"""

r = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=800,
    system=production_system,
    messages=[{
        "role": "user",
        "content": f"<code>{code}</code>"
    }]
)

print("Raw output:")
print(r.content[0].text)

parsed = json.loads(r.content[0].text)
print(f"\nScore: {parsed['overall_score']}/10")
print(f"Verdict: {parsed['verdict']}")
print(f"Summary: {parsed['one_line_summary']}")
print(f"Issues found: {len(parsed['issues'])}")
for issue in parsed['issues']:
    print(f"  [{issue['severity'].upper()}] {issue['description']}")