import anthropic

client = anthropic.Anthropic()

# ============================================================
# DEMO 1 — Prove Claude has NO memory without history
# ============================================================

print("=" * 50)
print("DEMO 1: No memory (default behavior)")
print("=" * 50)

# Call 1 — tell Claude your name
r1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "My name is Abhijeet. Remember that."}
    ]
)
print("Claude:", r1.content[0].text)

# Call 2 — ask Claude your name in a SEPARATE call (no history)
r2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "What is my name?"}  # fresh call, no history
    ]
)
print("Claude:", r2.content[0].text)
print("^ Claude forgot! Each call is isolated.\n")

# ============================================================
# DEMO 2 — Give Claude memory by passing history
# ============================================================

print("=" * 50)
print("DEMO 2: With memory (passing history)")
print("=" * 50)

# We build this array manually and grow it each turn
conversation_history = []

def chat(user_message):
    """Send a message and automatically maintain history."""
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Send FULL history every time
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system="You are a helpful coding assistant. You remember everything said in the conversation.",
        messages=conversation_history  # <-- the whole history
    )
    
    assistant_reply = response.content[0].text
    
    # Add Claude's reply to history too
    conversation_history.append({
        "role": "assistant",
        "content": assistant_reply
    })
    
    print(f"Tokens used so far: {response.usage.input_tokens} input")
    return assistant_reply

# Multi-turn conversation — watch Claude remember!
print("\nYou: My name is Abhijeet and I code in Python.")
print("Claude:", chat("My name is Abhijeet and I code in Python."))

print("\nYou: I prefer short, clean functions.")
print("Claude:", chat("I prefer short, clean functions."))

print("\nYou: What do you know about me so far?")
print("Claude:", chat("What do you know about me so far?"))

print("\nYou: Write me a function that matches my style.")
print("Claude:", chat("Write me a function that sorts a list of names."))

# ============================================================
# DEMO 3 — Inspect the history array (see what gets sent)
# ============================================================

print("\n" + "=" * 50)
print("DEMO 3: What the history array looks like")
print("=" * 50)
print(f"Total messages in history: {len(conversation_history)}")
for i, msg in enumerate(conversation_history):
    preview = msg['content'][:60].replace('\n', ' ')
    print(f"  [{i}] {msg['role']:10} → {preview}...")