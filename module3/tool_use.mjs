import Anthropic from "@anthropic-ai/sdk";
import { execSync } from "child_process";

const client = new Anthropic();

// ============================================================
// DEMO 1 — One tool: get_weather
// ============================================================

console.log("=".repeat(50));
console.log("DEMO 1: One tool — get_weather");
console.log("=".repeat(50));

const tools = [
  {
    name: "get_weather",
    description: "Get the current weather for a city.",
    input_schema: {
      type: "object",
      properties: {
        city: { type: "string", description: "City name" },
        unit: { type: "string", enum: ["celsius", "fahrenheit"] }
      },
      required: ["city"]
    }
  }
];

function getWeather(city, unit = "celsius") {
  const fakeData = {
    "mumbai":    { temp: 32, condition: "Humid and hot",  humidity: 85 },
    "london":    { temp: 12, condition: "Cloudy",         humidity: 70 },
    "bangalore": { temp: 24, condition: "Pleasant",       humidity: 65 },
  };
  const data = fakeData[city.toLowerCase()] || { temp: 22, condition: "Clear", humidity: 55 };
  return { city, temperature: data.temp, unit, condition: data.condition, humidity: data.humidity };
}

let r1 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  tools,
  messages: [{ role: "user", content: "What's the weather like in Mumbai?" }]
});

console.log("Stop reason:", r1.stop_reason); // tool_use

if (r1.stop_reason === "tool_use") {
  const toolBlock = r1.content.find(b => b.type === "tool_use");
  console.log(`\nClaude wants to call: ${toolBlock.name}`);
  console.log(`With arguments:`, toolBlock.input);

  const result = getWeather(toolBlock.input.city, toolBlock.input.unit);
  console.log(`Function returned:`, result);

  const final = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    tools,
    messages: [
      { role: "user", content: "What's the weather like in Mumbai?" },
      { role: "assistant", content: r1.content },
      {
        role: "user",
        content: [{
          type: "tool_result",
          tool_use_id: toolBlock.id,
          content: JSON.stringify(result)
        }]
      }
    ]
  });
  console.log("\nClaude's final answer:\n", final.content[0].text);
}

// ============================================================
// DEMO 2 — run_python tool
// ============================================================

console.log("\n" + "=".repeat(50));
console.log("DEMO 2: run_python tool");
console.log("=".repeat(50));

const codeTools = [
  {
    name: "run_python",
    description: "Execute Python code and return the output.",
    input_schema: {
      type: "object",
      properties: {
        code: { type: "string", description: "Python code to execute" }
      },
      required: ["code"]
    }
  }
];

function runPython(code) {
  try {
    const output = execSync(`python -c "${code.replace(/"/g, '\\"')}"`, { timeout: 10000 }).toString().trim();
    return { stdout: output, success: true };
  } catch (e) {
    return { stdout: "", stderr: e.message, success: false };
  }
}

const r2 = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  tools: codeTools,
  system: "Always use run_python to verify calculations.",
  messages: [{ role: "user", content: "What is the sum of all prime numbers below 100?" }]
});

if (r2.stop_reason === "tool_use") {
  const tb = r2.content.find(b => b.type === "tool_use");
  console.log("Claude wrote this code:\n", tb.input.code);

  const result = runPython(tb.input.code);
  console.log("Code output:", result.stdout);

  const final2 = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 512,
    tools: codeTools,
    messages: [
      { role: "user", content: "What is the sum of all prime numbers below 100?" },
      { role: "assistant", content: r2.content },
      { role: "user", content: [{ type: "tool_result", tool_use_id: tb.id, content: JSON.stringify(result) }] }
    ]
  });
  console.log("\nClaude's answer:", final2.content[0].text);
}

// ============================================================
// DEMO 3 — Multiple tools, Claude picks the right one
// ============================================================

console.log("\n" + "=".repeat(50));
console.log("DEMO 3: Multiple tools — Claude picks the right one");
console.log("=".repeat(50));

const multiTools = [
  {
    name: "get_weather",
    description: "Get weather for a city.",
    input_schema: { type: "object", properties: { city: { type: "string" } }, required: ["city"] }
  },
  {
    name: "calculate",
    description: "Perform a mathematical calculation.",
    input_schema: { type: "object", properties: { expression: { type: "string" } }, required: ["expression"] }
  }
];

function handleToolCall(name, inputs) {
  if (name === "get_weather") return getWeather(inputs.city);
  if (name === "calculate") {
    try {
      return { expression: inputs.expression, result: eval(inputs.expression) };
    } catch (e) {
      return { error: e.message };
    }
  }
}

const questions = [
  "What's the weather in Bangalore?",
  "Calculate 2 to the power of 32."
];

for (const question of questions) {
  console.log(`\nQuestion: ${question}`);

  const r = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 512,
    tools: multiTools,
    messages: [{ role: "user", content: question }]
  });

  if (r.stop_reason === "tool_use") {
    const tb = r.content.find(b => b.type === "tool_use");
    console.log(`Claude chose tool: ${tb.name} with args:`, tb.input);

    const result = handleToolCall(tb.name, tb.input);

    const final = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 256,
      tools: multiTools,
      messages: [
        { role: "user", content: question },
        { role: "assistant", content: r.content },
        { role: "user", content: [{ type: "tool_result", tool_use_id: tb.id, content: JSON.stringify(result) }] }
      ]
    });
    console.log("Answer:", final.content[0].text);
  }
}