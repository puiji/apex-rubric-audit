"""Provider-agnostic chat call with content-addressed disk cache.

Model strings: "gemini/<model>", "openai/<model>", "anthropic/<model>".
Keys are read from the environment or a .env file in the working directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential


class DailyQuotaExhausted(RuntimeError):
    pass


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


_load_dotenv()
CACHE_DIR = Path(os.environ.get("APEX_CACHE", "cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _retry_after(err: Exception) -> float | None:
    m = re.search(r"retry in ([\d.]+)s|retryDelay['\"]?: ?['\"](\d+)s", str(err), re.I)
    return float(m.group(1) or m.group(2)) if m else None


@retry(stop=stop_after_attempt(8), wait=wait_exponential(min=2, max=90), retry=retry_if_not_exception_type(DailyQuotaExhausted))
def _call(model: str, system: str | None, user: str, temperature: float, max_tokens: int, thinking: bool) -> str:
    provider, name = model.split("/", 1)

    if provider == "gemini":
        from google import genai
        from google.genai import errors, types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        cfg = dict(temperature=temperature, max_output_tokens=max_tokens, system_instruction=system)
        if "2.5" in name:
            cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=-1 if thinking else 0)
        try:
            r = client.models.generate_content(model=name, contents=user, config=types.GenerateContentConfig(**cfg))
        except errors.ClientError as e:
            if e.code == 429:
                wait = _retry_after(e) or 30
                if wait > 600:
                    raise DailyQuotaExhausted(f"{name}: daily quota hit, retry in {wait / 3600:.1f}h") from e
                print(f"[gemini 429] waiting {wait:.0f}s", file=sys.stderr, flush=True)
                time.sleep(wait + 1)
            raise
        return r.text or ""

    if provider == "openai":
        from openai import OpenAI

        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
        r = OpenAI().chat.completions.create(model=name, messages=msgs, temperature=temperature, max_tokens=max_tokens)
        return r.choices[0].message.content or ""

    if provider == "anthropic":
        import anthropic

        r = anthropic.Anthropic().messages.create(
            model=name, system=system or "", messages=[{"role": "user", "content": user}],
            temperature=temperature, max_tokens=max_tokens,
        )
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")

    raise ValueError(f"unknown provider: {provider}")


def chat(model: str, user: str, system: str | None = None, temperature: float = 0.7,
         max_tokens: int = 8000, seed: int = 0, thinking: bool = False) -> str:
    key = hashlib.sha256(json.dumps([model, system, user, temperature, seed]).encode()).hexdigest()[:32]
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())["text"]
    text = _call(model, system, user, temperature, max_tokens, thinking)
    path.write_text(json.dumps({"model": model, "text": text}))
    return text
