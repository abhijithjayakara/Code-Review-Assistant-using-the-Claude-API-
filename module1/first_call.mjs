import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

const response = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  messages: [
    { role: "user", content: "Say hello and tell me 3 things you can do as an API." }
  ]
});

console.log(response.content[0].text);
console.log("\n--- Metadata ---");
console.log("Input tokens :", response.usage.input_tokens);
console.log("Output tokens:", response.usage.output_tokens);
console.log("Stop reason  :", response.stop_reason);