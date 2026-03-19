import Anthropic from "@anthropic-ai/sdk";
const client = new Anthropic();

// ============================================================
// DEMO 1 — No memory
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 1: No memory (default behavior)");
console.log("=".repeat(50));

const r1 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 100,
  messages: [{ role: "user", content: "My name is Abhijeet. Remember that." }]
});
console.log("Claude:", r1.content[0].text);

const r2 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 100,
  messages: [{ role: "user", content: "What is my name?" }] // no history
});
console.log("Claude:", r2.content[0].text);
console.log("^ Claude forgot! Each call is isolated.\n");

// ============================================================
// DEMO 2 — With memory
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 2: With memory (passing history)");
console.log("=".repeat(50));

const conversationHistory = [];

async function chat(userMessage) {
  // Add user message
  conversationHistory.push({
    role: "user",
    content: userMessage
  });

  // Send full history every time
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 300,
    system: "You are a helpful coding assistant. You remember everything said.",
    messages: conversationHistory  // <-- the whole history
  });

  const reply = response.content[0].text;

  // Add Claude's reply to history
  conversationHistory.push({
    role: "assistant",
    content: reply
  });

  console.log(`Tokens used so far: ${response.usage.input_tokens} input`);
  return reply;
}

console.log("\nYou: My name is Abhijeet and I code in Python.");
console.log("Claude:", await chat("My name is Abhijeet and I code in Python."));

console.log("\nYou: I prefer short, clean functions.");
console.log("Claude:", await chat("I prefer short, clean functions."));

console.log("\nYou: What do you know about me so far?");
console.log("Claude:", await chat("What do you know about me so far?"));

console.log("\nYou: Write me a function that sorts a list of names.");
console.log("Claude:", await chat("Write me a function that sorts a list of names."));

// ============================================================
// DEMO 3 — Inspect the history
// ============================================================

console.log("\n" + "=".repeat(50));
console.log("DEMO 3: What the history array looks like");
console.log("=".repeat(50));
console.log(`Total messages in history: ${conversationHistory.length}`);
conversationHistory.forEach((msg, i) => {
  const preview = msg.content.substring(0, 60).replace(/\n/g, ' ');
  console.log(`  [${i}] ${msg.role.padEnd(10)} → ${preview}...`);
});