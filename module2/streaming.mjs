import Anthropic from "@anthropic-ai/sdk";
const client = new Anthropic();

// ============================================================
// DEMO 1 — Basic streaming
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 1: Basic streaming");
console.log("=".repeat(50));
process.stdout.write("Claude: ");

const stream1 = await client.messages.stream({
  model: "claude-sonnet-4-6",
  max_tokens: 300,
  messages: [
    { role: "user", content: "Count from 1 to 20 slowly, one number per line." }
  ]
});

for await (const chunk of stream1) {
  if (chunk.type === "content_block_delta" && chunk.delta.type === "text_delta") {
    process.stdout.write(chunk.delta.text); // print each chunk immediately
  }
}
console.log("\n");

// ============================================================
// DEMO 2 — Streaming a code review
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 2: Streaming a code review");
console.log("=".repeat(50));
process.stdout.write("Claude: ");

const stream2 = await client.messages.stream({
  model: "claude-sonnet-4-6",
  max_tokens: 500,
  system: "You are a brutal code reviewer. Be detailed.",
  messages: [
    { role: "user", content: "Review this: def get_user(id): return db.query(f'SELECT * FROM users WHERE id={id}')" }
  ]
});

for await (const chunk of stream2) {
  if (chunk.type === "content_block_delta" && chunk.delta.type === "text_delta") {
    process.stdout.write(chunk.delta.text);
  }
}
console.log("\n");

// ============================================================
// DEMO 3 — Stream AND collect metadata
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 3: Stream AND collect metadata");
console.log("=".repeat(50));
process.stdout.write("Claude: ");

let fullResponse = "";

const stream3 = client.messages.stream({
  model: "claude-sonnet-4-6",
  max_tokens: 300,
  messages: [
    { role: "user", content: "Explain what SQL injection is in 3 sentences." }
  ]
});

stream3.on("text", (text) => {
  process.stdout.write(text);
  fullResponse += text;
});

const final = await stream3.finalMessage();
console.log("\n");
console.log("Total chars streamed :", fullResponse.length);
console.log("Input tokens         :", final.usage.input_tokens);
console.log("Output tokens        :", final.usage.output_tokens);
console.log("Stop reason          :", final.stop_reason);

// ============================================================
// DEMO 4 — Streaming + multi-turn combined
// ============================================================

console.log("\n" + "=".repeat(50));
console.log("DEMO 4: Streaming + multi-turn combined");
console.log("=".repeat(50));

const conversationHistory = [];

async function chatStream(userMessage) {
  conversationHistory.push({ role: "user", content: userMessage });

  console.log(`\nYou: ${userMessage}`);
  process.stdout.write("Claude: ");

  let fullReply = "";

  const s = client.messages.stream({
    model: "claude-sonnet-4-6",
    max_tokens: 400,
    system: "You are a senior developer mentor. Be concise.",
    messages: conversationHistory
  });

  s.on("text", (text) => {
    process.stdout.write(text);
    fullReply += text;
  });

  await s.finalMessage();
  console.log();

  conversationHistory.push({ role: "assistant", content: fullReply });
  return fullReply;
}

await chatStream("What is the single most important thing to learn in backend development?");
await chatStream("How long does it take to learn that well?");
await chatStream("Give me a 3 step action plan.");