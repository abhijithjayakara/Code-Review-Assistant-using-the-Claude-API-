import anthropic
import time

client = anthropic.Anthropic()

# ============================================================
# DEMO 1 — Basic streaming (see words appear in real time)
# ============================================================

print("=" * 50)
print("DEMO 1: Basic streaming")
print("=" * 50)
print("Claude: ", end="", flush=True)

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "Count from 1 to 20 slowly, one number per line."}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # print each chunk immediately, no newline

print("\n")  # newline after streaming finishes

# ============================================================
# DEMO 2 — Streaming with system prompt
# ============================================================

print("=" * 50)
print("DEMO 2: Streaming a code review")
print("=" * 50)
print("Claude: ", end="", flush=True)

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=500,
    system="You are a brutal code reviewer. Be detailed. Take your time.",
    messages=[
        {"role": "user", "content": "Review this: def get_user(id): return db.query(f'SELECT * FROM users WHERE id={id}')"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

print("\n")

# ============================================================
# DEMO 3 — Streaming + collect full response + get token usage
# ============================================================

print("=" * 50)
print("DEMO 3: Stream AND collect metadata after")
print("=" * 50)
print("Claude: ", end="", flush=True)

full_response = ""

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "Explain what SQL injection is in 3 sentences."}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
        full_response += text  # collect it too

    # After stream ends, get the final message with metadata
    final = stream.get_final_message()

print("\n")
print(f"Total chars streamed : {len(full_response)}")
print(f"Input tokens         : {final.usage.input_tokens}")
print(f"Output tokens        : {final.usage.output_tokens}")
print(f"Stop reason          : {final.stop_reason}")

# ============================================================
# DEMO 4 — Streaming inside multi-turn (the real world pattern)
# ============================================================

print("\n" + "=" * 50)
print("DEMO 4: Streaming + multi-turn combined")
print("=" * 50)

conversation_history = []

def chat_stream(user_message):
    """Multi-turn chat with streaming output."""
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    print(f"\nYou: {user_message}")
    print("Claude: ", end="", flush=True)

    full_reply = ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system="You are a senior developer mentor. Be concise.",
        messages=conversation_history
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_reply += text

    print()  # newline

    # Add assistant reply to history
    conversation_history.append({
        "role": "assistant",
        "content": full_reply
    })

    return full_reply

# Real conversation with streaming
chat_stream("What is the single most important thing to learn in backend development?")
chat_stream("How long does it take to learn that well?")
chat_stream("Give me a 3 step action plan.")