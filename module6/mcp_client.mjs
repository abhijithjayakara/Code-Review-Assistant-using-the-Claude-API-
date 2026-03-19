import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";

const client = new Anthropic();
const PROJECT_PATH = "C:\\Users\\LENOVO\\claude-mastery";

console.log("=".repeat(55));
console.log("MODULE 6: MCP — Model Context Protocol (JS)");
console.log("=".repeat(55));

// MCP filesystem tools — same as Python version
const mcpTools = [
  {
    name: "read_file",
    description: "Read the complete contents of a file.",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" } },
      required: ["path"]
    }
  },
  {
    name: "write_file",
    description: "Write content to a file.",
    input_schema: {
      type: "object",
      properties: {
        path: { type: "string" },
        content: { type: "string" }
      },
      required: ["path", "content"]
    }
  },
  {
    name: "list_directory",
    description: "List files in a directory.",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" } },
      required: ["path"]
    }
  }
];

// Tool handlers
function handleMcpTool(name, input) {
  if (name === "read_file") {
    try {
      const content = fs.readFileSync(input.path, "utf8");
      return { content, lines: content.split("\n").length };
    } catch (e) {
      return { error: e.message };
    }
  }
  if (name === "write_file") {
    try {
      fs.mkdirSync(path.dirname(input.path), { recursive: true });
      fs.writeFileSync(input.path, input.content, "utf8");
      return { success: true, path: input.path };
    } catch (e) {
      return { error: e.message };
    }
  }
  if (name === "list_directory") {
    try {
      const items = fs.readdirSync(input.path).map(name => {
        const full = path.join(input.path, name);
        const stat = fs.statSync(full);
        return { name, type: stat.isDirectory() ? "directory" : "file" };
      });
      return { items, count: items.length };
    } catch (e) {
      return { error: e.message };
    }
  }
  return { error: `Unknown tool: ${name}` };
}

// MCP agentic loop
async function runMcpConversation(userMessage, maxTurns = 5) {
  const messages = [{ role: "user", content: userMessage }];
  let turn = 0;

  while (turn < maxTurns) {
    turn++;
    const response = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 2048,
      system: "You are a helpful coding assistant with filesystem access. Use tools to explore before answering.",
      tools: mcpTools,
      messages
    });

    if (response.stop_reason === "end_turn") {
      return response.content.find(b => b.type === "text")?.text || "";
    }

    if (response.stop_reason === "tool_use") {
      messages.push({ role: "assistant", content: response.content });

      const toolResults = [];
      for (const block of response.content) {
        if (block.type === "tool_use") {
          console.log(`  [MCP] Claude calling: ${block.name}(${JSON.stringify(block.input).substring(0, 60)}...)`);
          const result = handleMcpTool(block.name, block.input);
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result)
          });
        }
      }
      messages.push({ role: "user", content: toolResults });
    }
  }
  return "Max turns reached";
}

// Run the demos
console.log("\n--- JS Demo: Claude explores project via MCP ---\n");

const answer1 = await runMcpConversation(
  `List the directory at ${PROJECT_PATH} and tell me how many Python files exist total across all modules.`
);
console.log("Answer:", answer1);

console.log("\n--- JS Demo: Claude writes a file via MCP ---\n");

const answer2 = await runMcpConversation(
  `Create a file at ${PROJECT_PATH}\\module6\\js_mcp_output.txt with a 3-bullet summary of why MCP matters for enterprise software teams.`
);
console.log("Answer:", answer2);

// Verify
const jsOutput = path.join(PROJECT_PATH, "module6", "js_mcp_output.txt");
if (fs.existsSync(jsOutput)) {
  console.log("\n✅ JS MCP output file created:");
  console.log(fs.readFileSync(jsOutput, "utf8"));
}