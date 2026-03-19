import anthropic
import json

client = anthropic.Anthropic()

# ============================================================
# DEMO 1 — Basic system prompt: give Claude a role
# ============================================================

print("=" * 50)
print("DEMO 1: System prompt gives Claude a role")
print("=" * 50)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system="You are a senior Python developer with 10 years experience. \
You review code brutally and honestly. You always find at least 3 issues. \
Keep responses under 150 words.",  # <-- THIS is the system prompt
    messages=[
        {"role": "user", "content": "Review this code: def add(a,b): return a+b"}
    ]
)
print(response.content[0].text)

# ============================================================
# DEMO 2 — Force structured JSON output
# ============================================================

print("\n" + "=" * 50)
print("DEMO 2: Force JSON output format")
print("=" * 50)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system="""You are a code analysis API. 
You ONLY respond in valid JSON. No explanation, no markdown, no extra text.
Always use this exact structure:
{
  "score": <number 1-10>,
  "issues": [<list of strings>],
  "suggestions": [<list of strings>],
  "verdict": "<good|needs_work|bad>"
}""",
    messages=[
        {"role": "user", "content": "Review this: def divide(a,b): return a/b"}
    ]
)

raw = response.content[0].text
print("Raw response:", raw)

# Parse it as actual JSON
parsed = json.loads(raw)
print("\nParsed score:", parsed["score"])
print("Parsed verdict:", parsed["verdict"])
print("Issues found:", parsed["issues"])

# ============================================================
# DEMO 3 — Same question, totally different system prompts
# ============================================================

print("\n" + "=" * 50)
print("DEMO 3: Same question, 3 different personas")
print("=" * 50)

question = "What is a database index?"

personas = [
    ("Professor", "You are a university professor. Use academic language and cite concepts formally."),
    ("5-year-old teacher", "Explain everything like the user is 5 years old. Use simple words and fun analogies."),
    ("Startup CTO", "You are a busy CTO. Give ultra-short answers. Max 2 sentences. No fluff.")
]

for name, system in personas:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    print(f"\n[{name}]:", response.content[0].text)