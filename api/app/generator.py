import requests, json, textwrap, os

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GEN_MODEL  = os.getenv("GEN_MODEL_NAME", "llama3.1:8b-instruct-q4_K_M")

SYS_PROMPT = """You are a lore-accurate RPG archivist. Use ONLY the provided context. 
Cite like [Session {sessionNo} §{heading}] or [Character {doc_title}] after claims.
If the context is insufficient, say so and ask a follow-up question."""

def build_prompt(query: str, context_blocks: list[dict]) -> str:
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

def generate_answer(query: str, context_blocks: list[dict], max_tokens: int = 400) -> str:
    prompt = build_prompt(query, context_blocks)
    resp = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": GEN_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens}
    }, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()
