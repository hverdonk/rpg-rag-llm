import requests
import json
import textwrap
from abc import ABC, abstractmethod
from typing import List, Dict
import google.generativeai as genai
from app.config import settings

SYS_PROMPT = """You are a lore-accurate RPG archivist. Use ONLY the provided context. 
Cite like [Session {sessionNo} §{heading}] or [Character {doc_title}] after claims.
If the context is insufficient, say so and ask a follow-up question."""

def build_prompt(query: str, context_blocks: List[Dict]) -> str:
    parts = [f"[System]\n{SYS_PROMPT}", "\n[Context]"]
    for c in context_blocks:
        ses = f"Session {c.get('sessionNo')}" if c.get("sessionNo") else c.get("doc_title","")
        heading = c.get("heading") or "(no heading)"
        parts.append(textwrap.dedent(f"""
        --- {ses} · {c.get('doc_title','')} · {heading}
        {c['text'].strip()}
        """).strip())
    parts += ["\n[User Question]", query.strip()]
    return "\n\n".join(parts).strip()

class GeneratorProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        pass

class OllamaProvider(GeneratorProvider):
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url
        self.model_name = model_name
    
    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        resp = requests.post(f"{self.base_url}/api/generate", json={
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()

class GeminiProvider(GeneratorProvider):
    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when using Gemini provider")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.1,
        )
        
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text.strip()

def get_generator_provider() -> GeneratorProvider:
    if settings.generator_provider.lower() == "gemini":
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model_name)
    else:  # Default to ollama
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model_name)

def generate_answer(query: str, context_blocks: List[Dict], max_tokens: int = 400) -> str:
    prompt = build_prompt(query, context_blocks)
    provider = get_generator_provider()
    return provider.generate(prompt, max_tokens)
