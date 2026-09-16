# Pre-registration: rubric gameability of APEX-v1 scoring

Written 2026-09-11, before the 40-case study was run. The 20-case pilot (results/pilot20__gemini-3-flash) informed
the design but its cases are excluded from confirmatory claims below unless stated.

## Setting

APEX-v1 scores a response as the fraction of binary rubric criteria an LLM judge marks satisfied. Criteria are
phrased as presence claims ("States that X", "Identifies Y"). There is no criterion of the form "does not also
assert not-X" and no penalty for incorrect or extraneous content. Call this the missing precision term.

Judge: Gemini 3 Flash (paper used Gemini 2.5 Pro, which is no longer served to new API keys; Gemini 3.1 Pro is
capped at 250 requests/day on this account and is used only for a calibration subset). Grader prompt is a
reconstruction from the paper, not Mercor's.

## Hypotheses and predictions

H1 (no precision term). Making a response worse by adding wrong or self-contradictory content does not lower its
score. Prediction: `contradict_all` and `pad` are equivalent to `honest` within +/- 0.03 (equivalence bounds
chosen before seeing data; the pilot noise floor was 0.002). Falsifier: contradict_all delta <= -0.05.

H2 (correctness is not checked). A response with identical structure but every number, citation, and conclusion
made wrong scores well above what its correctness warrants. Prediction: `falsify` scores >= 0.5 x honest. Under a
sound grader, falsify should score near zero on Reasoning/Extraction criteria (the response says the wrong things),
i.e. below `truncate`. Falsifier: falsify delta <= truncate delta.

H3 (checkable beats correct in some domains). A response optimized for checkability from other tasks' rubrics
(`greybox_stuff`) is not reliably worse than honest. Prediction: greybox delta CI includes 0 overall; it is >= 0
in at least one domain. This is exploratory in the pilot (Medicine +0.11) and confirmatory here on new cases.

H4 (hollowness is real, not asserted). An independent blind pairwise quality judge from a different model family
prefers `honest` over each perturbed version. Prediction: honest wins >= 80% of pairs vs falsify and contradict_all,
>= 60% vs hedge and hedge+pad, ~50% vs pad (pad is defined to add nothing). If H4 fails for a condition, that
condition's score equivalence is NOT evidence of gameability and will be reported as such.

Sanity checks that must hold or the run is invalid: `truncate` delta <= -0.10; `honest_regrade` mean |delta| <= 0.02.

## Design

- Cases: 10 per domain, 40 total, stratified random from the 100 open cases, fixed seed (the 20 pilot cases are
  included in the sample frame; analyses are reported on all 40 and separately on the 20 new cases).
- Generator: GPT-4.1 with attachments as extracted text (60k char cap). One generation seed.
- Conditions: honest, honest_regrade, pad, hedge, hedge+pad, contradict (3 conclusions), contradict_all,
  falsify, truncate, greybox_stuff.
- Rubric judge: Gemini 3 Flash, T=0.1, one criterion per call. Pro calibration: 4 cases (1/domain) x all
  conditions with Gemini 3.1 Pro; report per-criterion agreement (Cohen's kappa) with Flash.
- Quality judge: GPT-4.1, blind pairwise (honest vs perturbed), both presentation orders, asked which response a
  domain expert would rate higher; ties allowed. Reported as win rate with order-swap consistency.

## Analysis (fixed in advance)

- Primary unit: task. Paired delta = score(cond) - score(honest) on the same task.
- Mean delta with 95% cluster-bootstrap CI (10,000 resamples of tasks).
- Equivalence: two one-sided tests at bounds +/- 0.03; "equivalent" only if the 90% CI lies inside the bounds.
- Direction: exact sign test on non-zero paired deltas.
- Secondary: pass rate by criterion_type x condition; Spearman(length, score) within condition; per-domain means
  (descriptive only, n=10 per domain).
- No optional stopping. Runs are cached; a rerun only fills failed API calls.

## What would count against the claim

- contradict_all or falsify dropping to truncate-level or below: the judge does penalize wrongness, and the
  "missing precision term" is a theoretical gap, not an exploitable one.
- Quality judge failing to prefer honest: perturbations weren't actually degrading, and score equivalence is
  uninformative.
- Flash/Pro disagreement (kappa < 0.6): results may be judge-specific; report both, claim neither alone.
