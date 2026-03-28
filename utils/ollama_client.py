"""
INDECLOW by AxeroAI
Ollama LLM Client
"""

import json
import time
import requests
from typing import Optional, Generator
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_LLM_RETRIES, MAX_TOKENS
from utils.logger import logger


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=10)
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def chat(
        self,
        messages: list,
        system: str = "",
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": MAX_TOKENS,
            },
        }
        if system:
            payload["system"] = system

        for attempt in range(MAX_LLM_RETRIES):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=120,
                    stream=stream,
                )
                resp.raise_for_status()

                if stream:
                    full = ""
                    for line in resp.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            full += content
                            if chunk.get("done"):
                                break
                    return full
                else:
                    data = resp.json()
                    return data["message"]["content"]

            except Exception as e:
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}")
                if attempt < MAX_LLM_RETRIES - 1:
                    time.sleep(2)

        return "⚠️ LLM call failed after retries. Please check Ollama is running."

    def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": MAX_TOKENS},
        }
        if system:
            payload["system"] = system

        for attempt in range(MAX_LLM_RETRIES):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate", json=payload, timeout=120
                )
                resp.raise_for_status()
                return resp.json().get("response", "")
            except Exception as e:
                logger.warning(f"Ollama generate attempt {attempt + 1} failed: {e}")
                if attempt < MAX_LLM_RETRIES - 1:
                    time.sleep(2)

        return "⚠️ LLM generation failed."


# Singleton
ollama = OllamaClient()
