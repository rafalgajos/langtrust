import requests


def call_api(prompt, options, context):

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:14b",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return {
        "output": data["message"]["content"]
    }
