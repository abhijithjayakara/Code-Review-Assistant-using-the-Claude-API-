import anthropic
import json
import time

client = anthropic.Anthropic()

# ============================================================
# FEATURE 1 — PROMPT CACHING
# Most impactful feature for production apps
# ============================================================

print("=" * 55)
print("FEATURE 1: Prompt Caching")
print("=" * 55)

# The problem without caching:
# You have a 10,000 token system prompt (big ruleset, docs, context)
# You make 1000 calls per day
# = 10,000,000 input tokens/day × $3/M = $30/day JUST for the system prompt
#
# With caching:
# First call: pay full price — tokens get cached
# All subsequent calls: pay 10% of normal price for cached tokens
# = $3/day instead of $30/day → 90% savings

LONG_SYSTEM_PROMPT = """You are an expert code reviewer for a fintech company.

COMPANY STANDARDS:
- All functions must have type hints
- All public functions must have docstrings
- No bare except clauses — always catch specific exceptions
- SQL queries must use parameterized queries — never string concatenation
- All user inputs must be validated before processing
- Functions longer than 30 lines should be refactored
- All API calls must have timeout parameters
- Sensitive data (passwords, tokens, PII) must never be logged
- All database connections must be closed in finally blocks
- Error messages shown to users must never expose internal details

SEVERITY LEVELS:
- CRITICAL: Security vulnerabilities, data loss risks
- HIGH: Logic errors, missing error handling
- MEDIUM: Code quality, maintainability issues  
- LOW: Style, naming, documentation

OUTPUT FORMAT:
Always respond in valid JSON matching this schema exactly:
{
  "score": <int 1-10>,
  "verdict": "<APPROVE|REQUEST_CHANGES|REJECT>",
  "issues": [{"severity": "...", "description": "...", "fix": "..."}],
  "summary": "<one sentence>"
}

EXAMPLES OF GOOD CODE:
def get_user(user_id: int, db: Connection) -> Optional[User]:
    \"\"\"Fetch a user by ID. Returns None if not found.\"\"\"
    try:
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return User.from_row(row) if row else None
    except sqlite3.Error as e:
        logger.error("DB error fetching user %d", user_id)
        raise DatabaseError("Failed to fetch user") from e
    finally:
        cursor.close()

EXAMPLES OF BAD CODE (always flag these):
- db.execute(f"SELECT * FROM users WHERE id={user_id}")  # SQL injection
- except: pass  # swallowing errors
- password = request.data['password']; logger.info(password)  # logging secrets
""" * 2  # Making it longer to demonstrate caching value

print(f"System prompt size: {len(LONG_SYSTEM_PROMPT):,} characters")
print(f"Estimated tokens: ~{len(LONG_SYSTEM_PROMPT)//4:,}")

# ── Without caching ──────────────────────────────────────
print("\n[Without caching]")
start = time.time()

r_no_cache = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system=LONG_SYSTEM_PROMPT,  # sent fresh every call
    messages=[{"role": "user", "content": "Review: def add(a,b): return a+b"}]
)

t_no_cache = time.time() - start
print(f"Time: {t_no_cache:.2f}s")
print(f"Input tokens: {r_no_cache.usage.input_tokens:,}")
print(f"Output tokens: {r_no_cache.usage.output_tokens:,}")

# ── With caching ─────────────────────────────────────────
print("\n[With caching — first call, populates cache]")
start = time.time()

r_cache1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}  # ← THIS enables caching
        }
    ],
    messages=[{"role": "user", "content": "Review: def add(a,b): return a+b"}]
)

t_cache1 = time.time() - start
print(f"Time: {t_cache1:.2f}s")
print(f"Input tokens: {r_cache1.usage.input_tokens:,}")
print(f"Cache creation tokens: {getattr(r_cache1.usage, 'cache_creation_input_tokens', 0):,}")
print(f"Cache read tokens: {getattr(r_cache1.usage, 'cache_read_input_tokens', 0):,}")

print("\n[With caching — second call, reads from cache]")
start = time.time()

r_cache2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": "Review: def divide(a,b): return a/b"}]
)

t_cache2 = time.time() - start
print(f"Time: {t_cache2:.2f}s")
print(f"Input tokens: {r_cache2.usage.input_tokens:,}")
print(f"Cache creation tokens: {getattr(r_cache2.usage, 'cache_creation_input_tokens', 0):,}")
print(f"Cache read tokens: {getattr(r_cache2.usage, 'cache_read_input_tokens', 0):,}")

# Cost comparison
normal_cost = (r_no_cache.usage.input_tokens / 1_000_000) * 3.00
cached_cost = (getattr(r_cache2.usage, 'cache_read_input_tokens', 0) / 1_000_000) * 0.30
print(f"\nCost per call WITHOUT caching: ${normal_cost:.5f}")
print(f"Cost per call WITH caching:    ${cached_cost:.5f}")
if cached_cost > 0:
    print(f"Savings: {((normal_cost - cached_cost) / normal_cost * 100):.0f}%")

# ============================================================
# FEATURE 2 — BATCH API
# Process many requests asynchronously at 50% discount
# ============================================================

print("\n" + "=" * 55)
print("FEATURE 2: Batch API")
print("=" * 55)

print("""
Batch API is for when you have lots of work that isn't time-sensitive.

Real use cases:
- Nightly review of all PRs merged today
- Processing 10,000 customer support tickets
- Generating reports for all users overnight
- Analyzing entire codebase weekly

Key facts:
- 50% cheaper than regular API
- Submit up to 10,000 requests at once  
- Results ready within 24 hours
- You poll for completion or get a webhook
""")

# Build batch requests
codes_to_review = [
    ("req_001", "def login(user, pwd): return db.query(f'SELECT * FROM users WHERE pwd={pwd}')"),
    ("req_002", "def add(a: int, b: int) -> int:\n    '''Add two numbers.'''\n    return a + b"),
    ("req_003", "def process(data):\n    try:\n        return data['key']\n    except:\n        pass"),
    ("req_004", "import hashlib\ndef hash_password(pwd: str) -> str:\n    return hashlib.sha256(pwd.encode()).hexdigest()"),
    ("req_005", "def get_users():\n    conn = db.connect()\n    return conn.execute('SELECT * FROM users').fetchall()"),
]

print(f"Preparing batch of {len(codes_to_review)} code reviews...")

batch_requests = []
for req_id, code in codes_to_review:
    batch_requests.append({
        "custom_id": req_id,
        "params": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "system": "You are a code reviewer. Respond only in JSON with keys: score (int 1-10), verdict (string), main_issue (string).",
            "messages": [{"role": "user", "content": f"Review this code:\n{code}"}]
        }
    })

print("Submitting batch to API...")
try:
    batch = client.messages.batches.create(requests=batch_requests)
    print(f"Batch created!")
    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.processing_status}")
    print(f"Request counts: {batch.request_counts}")
    print(f"\nIn production you would:")
    print(f"  1. Save batch.id to your database")
    print(f"  2. Come back in minutes/hours to check status")
    print(f"  3. Call client.messages.batches.results(batch.id)")
    print(f"\nPolling for results (may take 1-2 minutes)...")

    # Poll for completion
    max_polls = 24
    for i in range(max_polls):
        time.sleep(5)
        batch = client.messages.batches.retrieve(batch.id)
        print(f"  Poll {i+1}: status={batch.processing_status} | "
              f"succeeded={batch.request_counts.succeeded} "
              f"processing={batch.request_counts.processing}")

        if batch.processing_status == "ended":
            print("\nBatch complete! Fetching results...")
            print("-" * 40)
            for result in client.messages.batches.results(batch.id):
                code_snippet = dict(codes_to_review)[result.custom_id][:50]
                if result.result.type == "succeeded":
                    try:
                        data = json.loads(result.result.message.content[0].text)
                        print(f"{result.custom_id}: score={data.get('score')}/10 | "
                              f"verdict={data.get('verdict')} | "
                              f"issue={data.get('main_issue','')[:50]}")
                    except:
                        print(f"{result.custom_id}: {result.result.message.content[0].text[:80]}")
                else:
                    print(f"{result.custom_id}: FAILED - {result.result.error}")
            break
    else:
        print("Batch still processing — in production you'd check back later")
        print(f"Check with: client.messages.batches.retrieve('{batch.id}')")

except Exception as e:
    print(f"Batch API note: {e}")

# ============================================================
# FEATURE 3 — RATE LIMITS + PRODUCTION ERROR HANDLING
# Every production app needs this
# ============================================================

print("\n" + "=" * 55)
print("FEATURE 3: Rate limits + production error handling")
print("=" * 55)

import random

def call_claude_production(prompt: str, max_retries: int = 3) -> str:
    """
    Production-grade Claude API call.
    Handles all error types with proper retry logic.
    This is the pattern to use in every real application.
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0  # always set a timeout
            )
            return response.content[0].text

        except anthropic.RateLimitError as e:
            # 429 — you hit the rate limit
            wait = (2 ** attempt) + random.uniform(0, 1)  # exponential backoff + jitter
            print(f"  Rate limited (attempt {attempt+1}/{max_retries}) — waiting {wait:.1f}s")
            time.sleep(wait)
            last_error = e

        except anthropic.APIConnectionError as e:
            # Network error — retry
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"  Connection error (attempt {attempt+1}/{max_retries}) — waiting {wait:.1f}s")
            time.sleep(wait)
            last_error = e

        except anthropic.AuthenticationError as e:
            # Bad API key — don't retry, fix the key
            print(f"  Authentication failed — check your API key")
            raise  # re-raise immediately, no point retrying

        except anthropic.BadRequestError as e:
            # Bad input — don't retry
            print(f"  Bad request: {e}")
            raise

        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                # Server error — retry
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  Server error {e.status_code} (attempt {attempt+1}/{max_retries}) — waiting {wait:.1f}s")
                time.sleep(wait)
                last_error = e
            else:
                raise

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")


print("Testing production error handler...")
result = call_claude_production("What is 2 + 2? Answer in one word.")
print(f"Result: {result}")

# ── Token counting (before sending) ─────────────────────────
print("\n--- Token counting before sending ---")

token_count = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Explain recursion with a Python example."}
    ]
)
print(f"This request will use: {token_count.input_tokens} input tokens")
print(f"Estimated cost: ${token_count.input_tokens / 1_000_000 * 3:.6f}")
print("Use this BEFORE sending expensive requests to check cost first.")

# ── Cost calculator ──────────────────────────────────────────
print("\n--- Production cost projections ---")

scenarios = [
    ("Small app",      100,    500,   200),
    ("Medium product", 10_000, 1000,  500),
    ("Large platform", 500_000,2000,  1000),
]

print(f"{'Scenario':<20} {'Daily calls':>12} {'$/day':>10} {'$/month':>10}")
print("-" * 56)

for name, daily_calls, avg_input, avg_output in scenarios:
    daily_cost = daily_calls * (
        (avg_input  / 1_000_000 * 3.00) +
        (avg_output / 1_000_000 * 15.00)
    )
    print(f"{name:<20} {daily_calls:>12,} {daily_cost:>10.2f} {daily_cost*30:>10.2f}")

print("\nWith prompt caching (90% off input tokens):")
print(f"{'Scenario':<20} {'Daily calls':>12} {'$/day':>10} {'$/month':>10}")
print("-" * 56)

for name, daily_calls, avg_input, avg_output in scenarios:
    cached_input = avg_input * 0.10  # 90% cheaper
    daily_cost = daily_calls * (
        (cached_input / 1_000_000 * 3.00) +
        (avg_output   / 1_000_000 * 15.00)
    )
    print(f"{name:<20} {daily_calls:>12,} {daily_cost:>10.2f} {daily_cost*30:>10.2f}")