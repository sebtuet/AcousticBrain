from ollama import chat

response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": "Bonjour AcousticBrain"
        }
    ]
)

print(response.message.content)
