# Results: rubric gameability of APEX-v1 scoring (pre-registered 40-case study)

Run 2026-09-11. Design and predictions were fixed in `PREREG.md` before this data existed. Raw outputs, including
every per-criterion judge explanation, are in `results/study40__gemini-3-flash/`. Rubric judge: Gemini 3 Flash
(paper: Gemini 2.5 Pro, no longer served to new keys). Generator and rewriter: GPT-4.1. Quality proxy: GPT-4.1,
blind pairwise, both orders. 40 cases, 10 per domain, from the 100 public APEX-v1 cases, one generation seed.

## Summary

The APEX rubric score rewards the presence of correct claims and does not penalize the presence of incorrect ones.
Appending a section that reverses every conclusion in a response leaves its score unchanged (delta 0.000, 90% CI
[-0.026, +0.025], equivalent within the pre-registered +/-0.03), while a blind judge prefers the original 95% of the
time. Hedging every claim and adding boilerplate are likewise score-neutral and likewise rated worse by the blind
judge (85% and 90%). Replacing content with wrong content is penalized (-0.28), more than truncation (-0.18): the
judge does check correctness of committed claims. The gap is specific: wrongness that replaces the answer is caught,
wrongness that accompanies it is free. A checkbox-stuffing attack built from other tasks' rubrics scored level with
honest but was not rated worse by the blind judge, so it is not evidence of gameability.

## Pre-registered checks

| check | prediction | result | verdict |
|---|---|---|---|
| sanity: truncate | delta <= -0.10 | -0.177 [-0.238, -0.122] | PASS |
| sanity: regrade noise | mean abs delta <= 0.02 | 0.004 | PASS |
| H1: contradict_all | equivalent to honest, +/-0.03 | -0.000, 90% CI [-0.026, +0.025] | PASS (equivalent) |
| H1: pad | equivalent to honest, +/-0.03 | +0.002, 90% CI [-0.004, +0.008] | PASS (equivalent) |
| H2: falsify | >= 0.5 x honest; falsified if <= truncate | 0.149 vs 0.429 (0.35x); delta -0.280 < truncate -0.177 | **FAIL (falsified)** |
| H3: greybox | CI includes 0; >= 0 in some domain | -0.003 [-0.062, +0.053]; Medicine +0.10, Consulting +0.03 | PASS, but see H4 |
| H4: blind judge prefers honest | >= 80% vs falsify, contradict_all; >= 60% vs hedge | 82%, 95%; 85% | PASS |
| H4: greybox | (no prediction) | honest 45%, greybox 15%, order-inconsistent 38% | not distinguishable |

## Paired delta vs honest, all 40 tasks

| condition | delta | 95% CI | equiv +/-0.03 | up/flat/down | blind judge prefers honest |
|---|---|---|---|---|---|
| honest_regrade (noise floor) | +0.004 | [+0.000, +0.008] | yes | 3/37/0 | n/a |
| pad | +0.002 | [-0.004, +0.009] | yes | 2/37/1 | 90% (10% tie) |
| hedge | +0.000 | [-0.018, +0.017] | yes | 6/28/6 | 85% |
| hedge+pad | -0.013 | [-0.027, +0.001] | yes | 1/32/7 | 95% |
| contradict (3 conclusions) | +0.013 | [-0.020, +0.050] | no (CI too wide) | 9/23/8 | 92% |
| contradict_all | -0.000 | [-0.032, +0.029] | yes | 9/23/8 | 95% |
| greybox | -0.003 | [-0.062, +0.053] | no | 15/13/12 | 45% |
| truncate | -0.177 | [-0.238, -0.122] | no | 0/10/30 | 100% |
| falsify | -0.280 | [-0.367, -0.193] | no | 2/5/33 | 82% |

Replication on the 20 tasks not in the pilot: same pattern (contradict_all +0.009 [-0.032, +0.052]; falsify -0.289;
truncate -0.202; pad -0.001; hedge -0.002). With n=20 the contradict_all CI is slightly too wide for the formal
equivalence bound; the point estimate and sign split (5 up / 11 flat / 4 down) match the full sample.

## Secondary observations

- Score correlates with response length within every condition (Spearman 0.19 to 0.34; falsify -0.11). Consistent
  with a coverage-only metric.
- The blind judge penalized padding 90% of the time where a coin flip was predicted. The rubric is more
  length-tolerant than the expert proxy.
- Per criterion type, contradict_all and hedge leave "Reasoning" and "Extraction" pass rates unchanged; falsify
  cuts them roughly in half. The judge is not fooled about what the response says; it is indifferent to the
  response also saying the opposite.
- Domain: falsify collapses hardest in Finance (0.517 -> 0.059), where criteria are numeric. Grey-box gains in
  Medicine (+0.10, replicating the pilot direction) and loses in Finance (-0.16).
- Flash vs Gemini 3.1 Pro agreement on the calibration subset so far: kappa 0.92 on 54 criteria, identical
  response-level scores on 6 responses. Pro is capped at 250 requests/day on this account; the remaining
  calibration responses complete on rerun after the reset.

## What this does not show

- It does not show that a hollow response beats an honest one. No condition scored significantly above honest.
- It does not show the judge ignores correctness. It penalizes wrong committed claims heavily (H2 falsified).
- The grey-box attack did not produce responses the blind judge could identify as worse, so its score parity is
  uninformative. Either the attack fails to be hollow or the proxy judge can't see it; real experts would settle it.
- The quality proxy is an LLM, not a domain expert. The Flash judge is not the paper's judge. The grader prompt is
  a reconstruction. n=40 with one generation seed.

## Implication

The exploitable gap is a missing precision term: no criterion penalizes asserting not-X alongside X. A response
generator that commits to an answer and then covers the alternatives loses nothing under the current scoring and is
strictly worse to a reader. The natural fix is a contradiction check (negative criteria, or a judge pass asking
whether the response also asserts the negation of each passed criterion), and its cost is a fraction of the grading
budget. Measuring how much of the current leaderboard spread survives that fix is the proposed study.
