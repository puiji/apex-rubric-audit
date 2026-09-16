"""Rubric judge: one call per (criterion, response), binary pass/fail, following the APEX-v1 recipe."""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from .llm import chat

GRADER_MODEL = os.environ.get("GRADER_MODEL", "gemini/gemini-3-flash-preview")
WORKERS = int(os.environ.get("GRADER_WORKERS", "3"))

SYSTEM = (
    "You are an expert grader. You will be shown a task prompt, a candidate response, and one "
    "grading criterion. Decide whether the response satisfies the criterion. Judge only the "
    "criterion as stated. Respond with JSON only: "
    '{"pass": true|false, "explanation": "<one or two sentences>"}'
)

USER = """<task_prompt>
{prompt}
</task_prompt>

<response>
{response}
</response>

<criterion>
{criterion}
</criterion>

Does the response satisfy the criterion? Return JSON only."""


def _parse(text: str) -> tuple[bool | None, str]:
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            p = obj.get("pass")
            if isinstance(p, str):
                p = p.strip().lower() in ("true", "yes", "pass", "1")
            return (bool(p) if p is not None else None), str(obj.get("explanation", ""))[:300]
        except json.JSONDecodeError:
            pass
    pm = re.search(r'"pass"\s*:\s*(true|false)', text, re.I)
    if pm:
        em = re.search(r'"explanation"\s*:\s*"([^"]*)', text)
        return pm.group(1).lower() == "true", (em.group(1) if em else "")[:300]
    return None, text[:200]


def grade_one(prompt: str, response: str, criterion: str, model: str, seed: int) -> dict:
    out = chat(model, USER.format(prompt=prompt, response=response, criterion=criterion),
               system=SYSTEM, temperature=0.1, max_tokens=4000, seed=seed, thinking=True)
    p, expl = _parse(out)
    return {"criterion": criterion, "pass": p, "explanation": expl}


def grade(prompt: str, response: str, criteria: list[str], model: str = GRADER_MODEL, seed: int = 0) -> dict:
    with ThreadPoolExecutor(WORKERS) as ex:
        items = list(ex.map(lambda c: grade_one(prompt, response, c, model, seed), criteria))
    valid = [i for i in items if i["pass"] is not None]
    score = sum(i["pass"] for i in valid) / len(valid) if valid else float("nan")
    return {"score": score, "n_criteria": len(criteria), "n_unparsed": len(items) - len(valid), "items": items}
