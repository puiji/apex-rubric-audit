# The missing precision term: contradiction-blindness in APEX scoring

*Research proposal for the Mercor APEX Fellowship. September 2026.*

**Claim.** APEX-v1 scores a response as the fraction of binary rubric criteria a judge marks present. No criterion asks whether the response also asserts the opposite. That gap is exploitable, I've measured it, and it has a cheap fix. The project is to size it on the held-out set with real experts, test the fix, and report how much of the leaderboard spread survives.

**What I measured.** A pre-registered study on the 100 public APEX-v1 cases: 40 tasks, 10 per domain, hypotheses and falsifiers written before the data existed. GPT-4.1 wrote an honest response per task with attachments. I applied perturbations that make a response worse without removing correct content, then regraded with a reconstruction of the APEX judge (Gemini 3 Flash, one criterion per call). A second model family judged original vs perturbed blind, both orders, no rubric.

| Perturbation of the honest response | Rubric score change | Blind judge prefers original |
|---|---|---|
| Append a section reversing every conclusion | 0.000  (90% CI ±0.026) | 95% |
| Rewrite every claim as a hedge | 0.000 | 85% |
| Add seven boilerplate sections | +0.002 | 90% |
| Make every fact wrong, same structure | −0.280 | 82% |
| Delete the second half | −0.177 | 100% |
| Regrade identical text (noise floor) | +0.004 | n/a |

The first three rows are the finding: responses a blind judge rates worse nine times in ten score the same. The fourth row is the failed prediction. I'd pre-registered "wrong content scores like truncation" as the falsifier for "the judge doesn't check correctness," and it triggered, so I'm not claiming that. The mechanism is narrower: wrongness that replaces the correct claim is caught, wrongness that sits beside it is free. The metric is recall of correct assertions and nothing else. A checkbox-stuffing attack built from other tasks' rubrics scored level with honest, but the blind judge couldn't tell it from honest either. Not evidence. Open.

**Why it matters.** A model tuned on this metric learns to commit to an answer, then cover the alternatives. That response is worse for the client and scores the same. The leaderboard can't separate a model that knows the answer from one that lists the candidates. Any presence-only rubric benchmark has this property. APEX is where it can be measured because the rubrics and recipe are public.

**Plan.** (1) Replace the LLM proxy with expert ratings: blind pairwise, committed vs hedged, four domains. (2) Run the suite against the real judge and prompt on the held-out 400, three generator families. (3) Build and test the fix: a negation pass in the judge (for each passed criterion, ask if the response also asserts its negation) and expert-written negative criteria. Measure cost, expert agreement, gap closed. (4) Rescore the leaderboard under the patched metric and report which rank gaps hold.

**Caveats.** One generator. Flash judge, not the paper's Pro (κ = 0.92 with Pro on a 54-criterion subset). LLM quality proxy. n = 40, one seed. Each is a reason to do the study properly, not a reason to doubt the direction.

Pre-registration, full results, and code: github.com/puiji/apex-rubric-audit
