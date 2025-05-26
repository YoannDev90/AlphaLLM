import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer " + OPENROUTER_API_KEY
  },
  data=json.dumps({
    "model": "microsoft/phi-4-reasoning:free",
    "messages": [
      {
        "role": "user",
        "content": "What is the best French cheese?"
      }
    ]
  })
)

response_json = response.json()
print(response_json['choices'][0]['message']['content'])
