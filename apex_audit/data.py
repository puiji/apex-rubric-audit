"""Load the public APEX-v1 split (mercor/apex-v1 on Hugging Face) into Case objects."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")


@dataclass
class Criterion:
    text: str
    weight: str = ""
    ctype: str = ""
    sources: str = ""


@dataclass
class Case:
    task_id: str
    domain: str
    prompt: str
    meta: list[Criterion]
    attachments: list[str] = field(default_factory=list)
    _attach_text: str | None = None

    @property
    def criteria(self) -> list[str]:
        return [m.text for m in self.meta]

    def attachment_text(self, max_chars: int = 60000) -> str:
        if self._attach_text is None:
            parts = []
            for name in self.attachments:
                p = DATA_DIR / name
                hits = [p] if p.exists() else list(DATA_DIR.glob(f"**/{Path(name).name}"))
                parts.append(f"=== {name} ===\n" + (_read(hits[0]) if hits else "[file not found]"))
            self._attach_text = "\n\n".join(parts)
        t = self._attach_text
        return t if len(t) <= max_chars else t[:max_chars] + "\n[... truncated ...]"


def _read(p: Path) -> str:
    ext = p.suffix.lower()
    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
        if ext in (".csv", ".tsv"):
            df = pd.read_csv(p, sep=None, engine="python", on_bad_lines="skip")
            return f"[{len(df)} rows x {len(df.columns)} cols]\n" + df.to_csv(index=False)
        if ext in (".xlsx", ".xls"):
            sheets = pd.read_excel(p, sheet_name=None)
            return "\n\n".join(f"--- {n} ---\n{d.to_csv(index=False)}" for n, d in sheets.items())
        if ext == ".docx":
            import docx
            return "\n".join(par.text for par in docx.Document(str(p)).paragraphs)
        return p.read_text(errors="ignore")
    except Exception as e:
        return f"[extraction failed: {e}]"


def parse_rubric(raw: str) -> list[Criterion]:
    obj = json.loads(raw)
    order = lambda k: int(m.group()) if (m := re.search(r"\d+", k)) else 0
    out = []
    for k in sorted(obj, key=order):
        v = obj[k]
        ct = v.get("criterion_type", "")
        out.append(Criterion(
            text=str(v["description"]).strip(),
            weight=str(v.get("weight", "")),
            ctype="; ".join(ct) if isinstance(ct, list) else str(ct),
            sources=str(v.get("sources", "")),
        ))
    return out


def find_csv() -> Path:
    for p in (DATA_DIR / "data" / "train.csv", DATA_DIR / "train.csv"):
        if p.exists():
            return p
    sys.exit(f"No train.csv under {DATA_DIR}/. See README for the download step.")


def load_cases(path: Path | None = None) -> list[Case]:
    df = pd.read_csv(path or find_csv())
    cases = []
    for _, r in df.iterrows():
        att = [a.strip() for a in str(r["File Attachments"]).split("\n") if a.strip()]
        cases.append(Case(str(r["Task ID"]), str(r["Domain"]), str(r["Prompt"]), parse_rubric(r["Rubric JSON"]), att))
    return cases


if __name__ == "__main__":
    cases = load_cases()
    n = [len(c.meta) for c in cases]
    print(f"{len(cases)} cases; criteria/case mean={sum(n) / len(n):.1f} min={min(n)} max={max(n)}")
    print("domains:", pd.Series([c.domain for c in cases]).value_counts().to_dict())
    allm = [m for c in cases for m in c.meta]
    print("weight:", pd.Series([m.weight for m in allm]).value_counts().to_dict())
    print("type:", pd.Series([m.ctype for m in allm]).value_counts().to_dict())
    found = sum((DATA_DIR / a).exists() for c in cases for a in c.attachments)
    print(f"attachments found: {found} / {sum(len(c.attachments) for c in cases)}")
