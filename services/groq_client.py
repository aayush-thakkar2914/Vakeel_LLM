import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict, AsyncGenerator

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

def call_groq_llm(messages):
    """Non-streaming version of LLM call"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7
    }

    response = requests.post(BASE_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

async def stream_groq_llm(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """Async streaming version of LLM call"""
    import httpx
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "stream": True  # Enable streaming
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", BASE_URL, headers=headers, json=body, timeout=60.0) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    line = line[6:]  # Remove "data: " prefix
                    if line.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        if "choices" in chunk and chunk["choices"]:
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        print(f"Failed to parse line: {line}")
                        continue