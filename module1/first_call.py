import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "As an API, All things you can handel in my GIT account"}
    ]
)

print(response.content[0].text)
print("\n--- Metadata ---")
print("Input tokens :", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
print("Stop reason  :", response.stop_reason)