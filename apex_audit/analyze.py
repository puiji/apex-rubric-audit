"""Confirmatory analysis as fixed in PREREG.md.

python -m apex_audit.analyze results/study40__gemini-3-flash [--new-only results/pilot20__gemini-3-flash] [--agree results/study40__gemini-3.1-pro]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EQUIV = 0.03
BOOT = 10_000
RNG = np.random.default_rng(0)
RENAME = {"greybox_stuff": "greybox"}


def load(run_dir: str) -> tuple[pd.DataFrame, list[dict]]:
    rows = [json.loads(l) for l in (Path(run_dir) / "grades.jsonl").open()]
    if not rows:
        sys.exit(f"no graded rows in {run_dir}")
    for r in rows:
        r["cond"] = RENAME.get(r["cond"], r["cond"])
    df = pd.DataFrame(rows).drop(columns=["items"]).drop_duplicates(subset=["task_id", "cond", "seed"], keep="last")
    return df, rows


def boot_ci(d: np.ndarray, level: float) -> tuple[float, float]:
    means = d[RNG.integers(0, len(d), size=(BOOT, len(d)))].mean(axis=1)
    a = 100 * (1 - level) / 2
    return float(np.percentile(means, a)), float(np.percentile(means, 100 - a))


def sign_test(d: np.ndarray) -> float:
    nz = d[d != 0]
    n = len(nz)
    if n == 0:
        return 1.0
    k = min(int((nz > 0).sum()), n - int((nz > 0).sum()))
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def paired(df: pd.DataFrame, label: str) -> dict:
    hon = df[df.cond == "honest"].set_index(["task_id", "seed"])["score"]
    print(f"\n== {label}: paired delta vs honest ==")
    print(f"{'condition':<15} {'n':>3} {'delta':>7} {'95% CI':>18} {'90% CI':>18} {'equiv±.03':>10} {'sign p':>7} {'up/flat/down':>13}")
    out = {}
    for cond in [c for c in df.cond.unique() if c != "honest"]:
        x = df[df.cond == cond].set_index(["task_id", "seed"])["score"]
        j = pd.concat([hon.rename("h"), x.rename("x")], axis=1).dropna()
        if len(j) < 3:
            continue
        d = (j.x - j.h).values
        lo95, hi95 = boot_ci(d, 0.95)
        lo90, hi90 = boot_ci(d, 0.90)
        equiv = "YES" if (lo90 > -EQUIV and hi90 < EQUIV) else "no"
        out[cond] = dict(n=len(d), delta=d.mean(), lo95=lo95, hi95=hi95, equiv=equiv)
        print(f"{cond:<15} {len(d):>3} {d.mean():>+7.3f} [{lo95:>+.3f}, {hi95:>+.3f}] [{lo90:>+.3f}, {hi90:>+.3f}] "
              f"{equiv:>10} {sign_test(d):>7.3f} {(d > 0).sum():>4}/{(d == 0).sum()}/{(d < 0).sum()}")
    return out


def prereg_checks(res: dict, df: pd.DataFrame) -> None:
    ok = lambda b: "PASS" if b else "FAIL"
    g = lambda c, k: res.get(c, {}).get(k, float("nan"))
    print("\n== pre-registered checks ==")
    print(f"sanity  truncate delta <= -0.10 ........ {g('truncate', 'delta'):+.3f}  {ok(g('truncate', 'delta') <= -0.10)}")
    if "honest_regrade" in res:
        hon = df[df.cond == "honest"].set_index(["task_id", "seed"])["score"]
        rg = df[df.cond == "honest_regrade"].set_index(["task_id", "seed"])["score"]
        mad = (rg - hon).abs().dropna().mean()
        print(f"sanity  regrade mean|delta| <= 0.02 .... {mad:.3f}  {ok(mad <= 0.02)}")
    for c in ("contradict_all", "pad"):
        if c in res:
            print(f"H1      {c:<15} equivalent within ±{EQUIV} ... {res[c]['equiv']}   (falsifier delta <= -0.05: {ok(res[c]['delta'] > -0.05)})")
    if "falsify" in res:
        h, f = df[df.cond == "honest"].score.mean(), df[df.cond == "falsify"].score.mean()
        print(f"H2      falsify {f:.3f} vs honest {h:.3f} (ratio {f / h:.2f}); predicted >= 0.5 ... {ok(f >= 0.5 * h)}")
        print(f"H2      falsifier: falsify delta ({g('falsify', 'delta'):+.3f}) <= truncate delta ({g('truncate', 'delta'):+.3f}) ... "
              f"{'CLAIM FALSIFIED' if g('falsify', 'delta') <= g('truncate', 'delta') else 'not triggered'}")
    if "greybox" in res:
        r = res["greybox"]
        dom = df.pivot_table(index="domain", columns="cond", values="score", aggfunc="mean")
        dd = (dom["greybox"] - dom["honest"]).round(3).to_dict()
        print(f"H3      greybox CI includes 0: {ok(r['lo95'] <= 0 <= r['hi95'])};  per-domain {dd}")


def criterion_breakdown(rows: list[dict]) -> None:
    items = [dict(task_id=r["task_id"], cond=r["cond"], ctype=i.get("ctype", "?"), p=int(i["pass"]))
             for r in rows for i in r["items"] if i.get("pass") is not None]
    it = pd.DataFrame(items).drop_duplicates()
    print("\n== pass rate by criterion type x condition ==")
    print(it.pivot_table(index="ctype", columns="cond", values="p", aggfunc="mean").round(3).to_string())


def agreement(run_a: str, run_b: str) -> None:
    def items(run):
        d = {}
        for l in (Path(run) / "grades.jsonl").open():
            r = json.loads(l)
            for i in r["items"]:
                if i.get("pass") is not None:
                    d[(r["task_id"], r["cond"], r["seed"], i["criterion"])] = int(i["pass"])
        return d
    a, b = items(run_a), items(run_b)
    keys = sorted(set(a) & set(b))
    if not keys:
        print("\nno overlapping graded criteria for agreement")
        return
    x, y = np.array([a[k] for k in keys]), np.array([b[k] for k in keys])
    po = (x == y).mean()
    pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean())
    print(f"\n== judge agreement {Path(run_a).name} vs {Path(run_b).name} ==")
    print(f"n criteria={len(keys)}  raw agreement={po:.3f}  Cohen's kappa={(po - pe) / (1 - pe):.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--new-only", default=None, help="pilot run dir; also report tasks not in it")
    ap.add_argument("--agree", default=None, help="second run dir for per-criterion judge agreement")
    args = ap.parse_args()

    df, rows = load(args.run)
    print(f"run: {args.run}   tasks={df.task_id.nunique()}   conditions={sorted(df.cond.unique())}")
    print("\n== mean score by condition ==")
    print(df.groupby("cond")["score"].agg(["mean", "std", "count"]).sort_values("mean", ascending=False).round(3).to_string())

    res = paired(df, "all tasks")
    prereg_checks(res, df)

    if args.new_only:
        pilot = set(pd.read_json(Path(args.new_only) / "grades.jsonl", lines=True).task_id.astype(str))
        new = df[~df.task_id.astype(str).isin(pilot)]
        if new.task_id.nunique() >= 3:
            paired(new, f"tasks not in pilot (n={new.task_id.nunique()})")

    print("\n== length vs score (Spearman, within condition) ==")
    for cond, g in df.groupby("cond"):
        if len(g) > 4:
            print(f"{cond:<15} rho={g[['n_chars', 'score']].corr(method='spearman').iloc[0, 1]:+.2f}")

    print("\n== by domain ==")
    print(df.pivot_table(index="domain", columns="cond", values="score", aggfunc="mean").round(3).to_string())
    criterion_breakdown(rows)
    if args.agree:
        agreement(args.run, args.agree)


if __name__ == "__main__":
    main()
