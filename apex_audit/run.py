"""Generate, perturb, and grade. Every model call is cached, so reruns only fill in what failed.

python -m apex_audit.run --per-domain 10 --run study40 --conditions honest,honest_regrade,pad,hedge,contradict_all,falsify,truncate
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from . import data, generate, perturb
from .grade import GRADER_MODEL, grade
from .llm import DailyQuotaExhausted

CONDITIONS = ["honest", "honest_regrade", "greybox", *perturb.PERTURBATIONS]


def build(cond: str, case: data.Case, pool: list[data.Case], seed: int, honest_cache: dict) -> str:
    if cond == "greybox":
        return generate.greybox(case, pool, seed=seed)
    key = (case.task_id, seed)
    if key not in honest_cache:
        honest_cache[key] = generate.honest(case, seed=seed)
    if cond in ("honest", "honest_regrade"):
        return honest_cache[key]
    return perturb.PERTURBATIONS[cond](honest_cache[key], seed)


def select(cases: list[data.Case], args) -> list[data.Case]:
    if args.domain:
        cases = [c for c in cases if c.domain.lower() == args.domain.lower()]
    random.Random(0).shuffle(cases)
    if args.task_ids:
        want = {t.strip() for t in args.task_ids.split(",")}
        return [c for c in cases if c.task_id in want]
    if args.per_domain:
        seen: dict[str, int] = {}
        picked = []
        for c in cases:
            if seen.get(c.domain, 0) < args.per_domain:
                seen[c.domain] = seen.get(c.domain, 0) + 1
                picked.append(c)
        return picked
    return cases[: args.n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--per-domain", type=int, default=0)
    ap.add_argument("--task-ids", default=None)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--conditions", default="honest,honest_regrade,pad,hedge,contradict_all,falsify,truncate")
    ap.add_argument("--grader", default=GRADER_MODEL)
    ap.add_argument("--run", default=time.strftime("%Y%m%d-%H%M"))
    args = ap.parse_args()

    conds = [c.strip() for c in args.conditions.split(",")]
    unknown = set(conds) - set(CONDITIONS)
    if unknown:
        ap.error(f"unknown conditions {sorted(unknown)}; choose from {CONDITIONS}")

    pool = data.load_cases()
    cases = select(pool, args)
    out = Path("results") / f"{args.run}__{args.grader.split('/')[-1].replace('-preview', '')}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"judge={args.grader}  ->  {out}")

    honest_cache: dict = {}
    with (out / "responses.jsonl").open("a") as resp_f, (out / "grades.jsonl").open("a") as grade_f:
        for case in cases:
            for seed in range(args.seeds):
                for cond in conds:
                    t0 = time.time()
                    try:
                        resp = build(cond, case, pool, seed, honest_cache)
                        g = grade(case.prompt, resp, case.criteria, model=args.grader,
                                  seed=seed + 1000 if cond == "honest_regrade" else seed)
                    except Exception as e:
                        root = e
                        while root.__cause__ is not None:
                            root = root.__cause__
                        if isinstance(root, DailyQuotaExhausted):
                            print(f"\nStopping: {root}. Rerun after the quota resets to continue.")
                            return
                        print(f"{case.task_id:>6} {case.domain:<12} {cond:<15} seed={seed} FAILED: {str(e)[:120]}")
                        continue
                    for item, m in zip(g["items"], case.meta):
                        item["weight"], item["ctype"] = m.weight, m.ctype
                    rec = dict(task_id=case.task_id, domain=case.domain, cond=cond, seed=seed, n_chars=len(resp),
                               score=g["score"], n_criteria=g["n_criteria"], n_unparsed=g["n_unparsed"])
                    resp_f.write(json.dumps({**rec, "response": resp}) + "\n")
                    grade_f.write(json.dumps({**rec, "items": g["items"]}) + "\n")
                    resp_f.flush(); grade_f.flush()
                    print(f"{case.task_id:>6} {case.domain:<12} {cond:<15} seed={seed} score={g['score']:.3f} "
                          f"chars={len(resp):>6} unparsed={g['n_unparsed']} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
