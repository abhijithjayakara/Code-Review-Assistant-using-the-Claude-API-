import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

// ============================================================
// FEATURE 1 — PROMPT CACHING
// ============================================================

console.log("=".repeat(55));
console.log("FEATURE 1: Prompt Caching (JS)");
console.log("=".repeat(55));

const LONG_SYSTEM = `You are an expert code reviewer for a fintech company.

COMPANY STANDARDS:
- All functions must have type hints
- All public functions must have docstrings  
- No bare except clauses
- SQL queries must use parameterized queries
- All user inputs must be validated
- Sensitive data must never be logged

OUTPUT FORMAT: Always respond in valid JSON:
{"score": <1-10>, "verdict": "<APPROVE|REQUEST_CHANGES|REJECT>", "issues": [], "summary": "<one sentence>"}
`.repeat(3);

console.log(`System prompt size: ${LONG_SYSTEM.length.toLocaleString()} chars\n`);

// Without caching
const r1 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 256,
  system: LONG_SYSTEM,
  messages: [{ role: "user", content: "Review: def add(a,b): return a+b" }]
});
console.log("[No cache]  input tokens:", r1.usage.input_tokens);

// With caching — first call
const r2 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 256,
  system: [{ type: "text", text: LONG_SYSTEM, cache_control: { type: "ephemeral" } }],
  messages: [{ role: "user", content: "Review: def add(a,b): return a+b" }]
});
console.log("[Cache 1st] input tokens:", r2.usage.input_tokens,
  "| cache_creation:", r2.usage.cache_creation_input_tokens ?? 0);

// With caching — second call (reads from cache)
const r3 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 256,
  system: [{ type: "text", text: LONG_SYSTEM, cache_control: { type: "ephemeral" } }],
  messages: [{ role: "user", content: "Review: def divide(a,b): return a/b" }]
});
console.log("[Cache 2nd] input tokens:", r3.usage.input_tokens,
  "| cache_read:", r3.usage.cache_read_input_tokens ?? 0);

const normalCost  = (r1.usage.input_tokens / 1_000_000) * 3.00;
const cachedCost  = ((r3.usage.cache_read_input_tokens ?? 0) / 1_000_000) * 0.30;
console.log(`\nCost WITHOUT cache: $${normalCost.toFixed(5)}`);
console.log(`Cost WITH cache:    $${cachedCost.toFixed(5)}`);

// ============================================================
// FEATURE 2 — BATCH API
// ============================================================

console.log("\n" + "=".repeat(55));
console.log("FEATURE 2: Batch API (JS)");
console.log("=".repeat(55));

const requests = [
  { id: "req_001", code: "def login(u,p): return db.query(f'SELECT * FROM users WHERE pwd={p}')" },
  { id: "req_002", code: "def add(a: int, b: int) -> int:\n    '''Add two numbers.'''\n    return a + b" },
  { id: "req_003", code: "def process(data):\n    try:\n        return data['key']\n    except:\n        pass" },
];

const batchRequests = requests.map(r => ({
  custom_id: r.id,
  params: {
    model: "claude-sonnet-4-6",
    max_tokens: 200,
    system: "Code reviewer. JSON only: {score, verdict, main_issue}",
    messages: [{ role: "user", content: `Review: ${r.code}` }]
  }
}));

console.log(`Submitting batch of ${batchRequests.length} requests...`);
const batch = await client.messages.batches.create({ requests: batchRequests });
console.log(`Batch ID: ${batch.id}`);
console.log(`Status: ${batch.processing_status}`);

// Poll for completion
let done = false;
for (let i = 0; i < 24 && !done; i++) {
  await new Promise(r => setTimeout(r, 5000));
  const updated = await client.messages.batches.retrieve(batch.id);
  console.log(`  Poll ${i+1}: ${updated.processing_status} | succeeded: ${updated.request_counts.succeeded}`);

  if (updated.processing_status === "ended") {
    console.log("\nResults:");
    for await (const result of await client.messages.batches.results(batch.id)) {
      if (result.result.type === "succeeded") {
        try {
          const d = JSON.parse(result.result.message.content[0].text);
          console.log(`  ${result.custom_id}: ${d.score}/10 | ${d.verdict} | ${d.main_issue?.substring(0,50)}`);
        } catch {
          console.log(`  ${result.custom_id}:`, result.result.message.content[0].text.substring(0,80));
        }
      }
    }
    done = true;
  }
}

// ============================================================
// FEATURE 3 — PRODUCTION ERROR HANDLING
// ============================================================

console.log("\n" + "=".repeat(55));
console.log("FEATURE 3: Production error handling (JS)");
console.log("=".repeat(55));

async function callClaudeProduction(prompt, maxRetries = 3) {
  let lastError;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const r = await client.messages.create({
        model: "claude-sonnet-4-6",
        max_tokens: 100,
        messages: [{ role: "user", content: prompt }]
      });
      return r.content[0].text;
    } catch (e) {
      if (e instanceof Anthropic.RateLimitError || e instanceof Anthropic.APIConnectionError) {
        const wait = (2 ** attempt + Math.random()) * 1000;
        console.log(`  Retrying in ${(wait/1000).toFixed(1)}s... (attempt ${attempt+1})`);
        await new Promise(r => setTimeout(r, wait));
        lastError = e;
      } else if (e instanceof Anthropic.AuthenticationError) {
        console.log("  Bad API key — fix before retrying");
        throw e;
      } else {
        throw e;
      }
    }
  }
  throw new Error(`Failed after ${maxRetries} attempts: ${lastError}`);
}

const result = await callClaudeProduction("What is 2+2? One word answer.");
console.log("Production call result:", result);

// Token counting
const tokens = await client.messages.countTokens({
  model: "claude-sonnet-4-6",
  messages: [{ role: "user", content: "Explain recursion with a Python example." }]
});
console.log(`\nToken count before sending: ${tokens.input_tokens}`);
console.log(`Estimated cost: $${(tokens.input_tokens / 1_000_000 * 3).toFixed(6)}`);