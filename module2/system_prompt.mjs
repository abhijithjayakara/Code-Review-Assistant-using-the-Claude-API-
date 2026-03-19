import Anthropic from "@anthropic-ai/sdk";
const client = new Anthropic();

// DEMO 1 — Role-based system prompt
console.log("=".repeat(50));
console.log("DEMO 1: System prompt gives Claude a role");
console.log("=".repeat(50));

const r1 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 512,
  system: "You are a senior Python developer with 10 years experience. \
You review code brutally and honestly. Always find at least 3 issues. \
Keep responses under 150 words.",
  messages: [
    { role: "user", content: "Review this code: def add(a,b): return a+b" }
  ]
});
console.log(r1.content[0].text);

// DEMO 2 — Force JSON output
console.log("\n" + "=".repeat(50));
console.log("DEMO 2: Force JSON output");
console.log("=".repeat(50));

const r2 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 512,
  system: `You are a code analysis API.
You ONLY respond in valid JSON. No explanation, no markdown, no extra text.
Always use this exact structure:
{
  "score": <number 1-10>,
  "issues": [<list of strings>],
  "suggestions": [<list of strings>],
  "verdict": "<good|needs_work|bad>"
}`,
  messages: [
    { role: "user", content: "Review this: def divide(a,b): return a/b" }
  ]
});

const raw = r2.content[0].text;
console.log("Raw response:", raw);
const parsed = JSON.parse(raw);
console.log("\nParsed score:", parsed.score);
console.log("Parsed verdict:", parsed.verdict);
console.log("Issues found:", parsed.issues);

// DEMO 3 — Same question, 3 personas
console.log("\n" + "=".repeat(50));
console.log("DEMO 3: Same question, 3 different personas");
console.log("=".repeat(50));

const personas = [
  ["Professor",        "You are a university professor. Use academic language."],
  ["5-year-old teacher","Explain like the user is 5. Use simple words and fun analogies."],
  ["Startup CTO",      "You are a busy CTO. Max 2 sentences. No fluff."]
];

for (const [name, system] of personas) {
  const r = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 150,
    system,
    messages: [{ role: "user", content: "What is a database index?" }]
  });
  console.log(`\n[${name}]:`, r.content[0].text);
}