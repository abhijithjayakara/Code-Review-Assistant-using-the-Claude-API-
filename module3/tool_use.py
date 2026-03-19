import anthropic
import json
import subprocess
import sys

client = anthropic.Anthropic()

# ============================================================
# DEMO 1 — One tool: get_weather
# Claude decides when to call it, you "fake" the data
# ============================================================

print("=" * 50)
print("DEMO 1: One tool — get_weather")
print("=" * 50)

# Step 1 — Define your tools (just a JSON description)
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Call this whenever the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name e.g. London, Mumbai, New York"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["city"]
        }
    }
]

# Step 2 — Your actual function (in real life this calls a weather API)
def get_weather(city, unit="celsius"):
    # Simulated weather data — in real life call OpenWeatherMap API here
    fake_data = {
        "mumbai":    {"temp": 32, "condition": "Humid and hot",  "humidity": 85},
        "london":    {"temp": 12, "condition": "Cloudy",         "humidity": 70},
        "new york":  {"temp": 18, "condition": "Partly cloudy",  "humidity": 60},
        "bangalore": {"temp": 24, "condition": "Pleasant",       "humidity": 65},
    }
    data = fake_data.get(city.lower(), {"temp": 22, "condition": "Clear", "humidity": 55})
    return {
        "city": city,
        "temperature": data["temp"],
        "unit": unit,
        "condition": data["condition"],
        "humidity": data["humidity"]
    }

# Step 3 — Send message with tools available
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather like in Mumbai right now?"}
    ]
)

print(f"Stop reason: {response.stop_reason}")  # will print "tool_use"
print(f"Response content: {response.content}")

# Step 4 — Check if Claude wants to use a tool
if response.stop_reason == "tool_use":
    # Find the tool call block
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    tool_name = tool_use_block.name
    tool_input = tool_use_block.input
    tool_use_id = tool_use_block.id

    print(f"\nClaude wants to call: {tool_name}")
    print(f"With arguments: {tool_input}")

    # Step 5 — YOU execute the function
    if tool_name == "get_weather":
        result = get_weather(**tool_input)
    
    print(f"Function returned: {result}")

    # Step 6 — Send result back to Claude
    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather like in Mumbai right now?"},
            {"role": "assistant", "content": response.content},  # Claude's tool call
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)  # your function's output
                    }
                ]
            }
        ]
    )

    print(f"\nClaude's final answer:\n{final_response.content[0].text}")

# ============================================================
# DEMO 2 — Tool that actually runs Python code
# Claude writes code, you execute it, Claude sees the output
# ============================================================

print("\n" + "=" * 50)
print("DEMO 2: run_python tool — Claude writes + runs code")
print("=" * 50)

code_tools = [
    {
        "name": "run_python",
        "description": "Execute Python code and return the output. Use this to do calculations, data processing, or verify code works.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                }
            },
            "required": ["code"]
        }
    }
]

def run_python(code):
    """Actually executes Python code and returns stdout."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=10
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "success": False}

# Ask Claude to solve a math problem by actually running code
r1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=code_tools,
    system="When asked to calculate something, always use the run_python tool to verify your answer.",
    messages=[
        {"role": "user", "content": "What is the sum of all prime numbers below 100?"}
    ]
)

if r1.stop_reason == "tool_use":
    tool_block = next(b for b in r1.content if b.type == "tool_use")
    print(f"Claude wrote this code:\n{tool_block.input['code']}\n")

    result = run_python(tool_block.input['code'])
    print(f"Code output: {result['stdout']}")

    final = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        tools=code_tools,
        messages=[
            {"role": "user", "content": "What is the sum of all prime numbers below 100?"},
            {"role": "assistant", "content": r1.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(result)
                    }
                ]
            }
        ]
    )
    print(f"\nClaude's answer: {final.content[0].text}")

# ============================================================
# DEMO 3 — Multiple tools, Claude picks the right one
# ============================================================

print("\n" + "=" * 50)
print("DEMO 3: Multiple tools — Claude picks the right one")
print("=" * 50)

multi_tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current time in a timezone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone e.g. Asia/Kolkata, America/New_York"
                }
            },
            "required": ["timezone"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform a mathematical calculation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression e.g. '2 ** 10' or 'sum(range(1,101))'"
                }
            },
            "required": ["expression"]
        }
    }
]

def handle_tool_call(name, inputs):
    """Route tool calls to the right function."""
    if name == "get_weather":
        return get_weather(inputs["city"])
    elif name == "get_time":
        from datetime import datetime
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(inputs["timezone"])
            now = datetime.now(tz)
            return {"timezone": inputs["timezone"], "time": now.strftime("%H:%M:%S"), "date": now.strftime("%Y-%m-%d")}
        except Exception as e:
            return {"error": str(e)}
    elif name == "calculate":
        try:
            result = eval(inputs["expression"])
            return {"expression": inputs["expression"], "result": result}
        except Exception as e:
            return {"error": str(e)}

# Ask something that needs a tool — Claude picks which one
questions = [
    "What's the weather in Bangalore?",
    "What time is it in India right now?",
    "Calculate 2 to the power of 32."
]

for question in questions:
    print(f"\nQuestion: {question}")
    
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        tools=multi_tools,
        messages=[{"role": "user", "content": question}]
    )

    if r.stop_reason == "tool_use":
        tb = next(b for b in r.content if b.type == "tool_use")
        print(f"Claude chose tool: {tb.name} with args: {tb.input}")
        
        result = handle_tool_call(tb.name, tb.input)
        
        final = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            tools=multi_tools,
            messages=[
                {"role": "user", "content": question},
                {"role": "assistant", "content": r.content},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tb.id, "content": json.dumps(result)}]}
            ]
        )
        print(f"Answer: {final.content[0].text}")
    else:
        print(f"Answer (no tool needed): {r.content[0].text}")