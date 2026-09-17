# The missing precision term: contradiction-blindness in APEX scoring

*Research proposal for the Mercor APEX Fellowship. September 2026.*

**Claim.** APEX-v1 scores a response as the fraction of binary rubric criteria a judge marks present. No criterion asks whether the response also asserts the opposite. That gap is exploitable, I've measured it, and it has a cheap fix. The project is to size it on the held-out set with real experts, test the fix, and report how much of the leaderboard spread survives.

**What I measured.** A pre-registered study on the 100 public APEX-v1 cases: 40 tasks, 10 per domain, hypotheses and falsifiers written before the data existed. GPT-4.1 wrote an honest response per task with attachments. I applied perturbations that make a response worse without removing correct content, then regraded with a reconstruction of the APEX judge (Gemini 3 Flash, one criterion per call). A second judge compared original against perturbed blind, both orders, no rubric.

| Perturbation of the honest response | Rubric score change | Blind judge prefers original |
|---|---|---|
| Append a section reversing every conclusion | 0.000  (90% CI ±0.026) | 95% |
| Rewrite every claim as a hedge | 0.000 | 85% |
| Add seven boilerplate sections | +0.002 | 90% |
| Make every fact wrong, same structure | −0.280 | 82% |
| Delete the second half | −0.177 | 100% |
| Regrade identical text (noise floor) | +0.004 | n/a |

The first three rows are the finding: responses a blind judge rates worse nine times in ten score the same.

**What the zero hides.** The aggregate is not indifference, and this is the part that sharpens the claim. Reversing every conclusion flips 14 of 443 criteria from pass to fail and 15 from fail to pass: 6.5% churn against a 0.7% regrade noise floor. The judge reacts. The reactions cancel. The second direction is the damaging one, because the contradicting section *earns* credit — criteria the honest response missed are marked satisfied because the reversal happens to state them. In 29 cases the judge's own explanation names both assertions and awards the point anyway: *"correctly identifies Step 1 of the five-step sequential evaluation process as 'Substantial Gainful Activity (SGA)' in both the primary and alternative assessments."* It sees the contradiction, writes it down, and scores it.

**The failed prediction.** I'd pre-registered "wrong content scores like truncation" as the falsifier for "the judge doesn't check correctness." It triggered — falsify −0.280 against truncate −0.177, with 135 of 443 criteria flipping to fail — so I'm not claiming that. The judge checks correctness, hard. The surviving mechanism is narrower and more useful: wrongness that *replaces* the correct claim is caught, wrongness that *accompanies* it is free. The metric is recall of correct assertions and nothing else. A checkbox-stuffing attack built from other tasks' rubrics scored level with honest, but the blind judge couldn't tell it from honest either. Not evidence. Open.

**Why it matters.** A model tuned on this metric learns to commit to an answer, then cover the alternatives. That response is worse for the client and scores the same. The leaderboard can't separate a model that knows the answer from one that lists the candidates. Any presence-only rubric benchmark has this property. APEX is where it can be measured because the rubrics and recipe are public.

**What would sink this.** My grader prompt tells the judge to "judge only the criterion as stated." That sentence is my reconstruction, not Mercor's, and it may be manufacturing the result: the falsifier for H1 required the judge to reason past the criterion, and I instructed it not to. I can't resolve this from outside — it needs the real prompt, and it is the first thing I'd run. If the blindness disappears without that instruction, the finding is an artifact of my harness and I'd report it as one. If it survives, the gap is in the metric and the rest of the plan follows.

**Plan.** (1) Ablate the grader instruction against the real APEX prompt and judge: same criteria, three grader variants, measure how much of the blindness is prompt and how much is metric. (2) Replace the LLM proxy with expert ratings: blind pairwise, committed vs hedged, four domains. (3) Run the suite on the held-out 400, three generator families. (4) Build and test the fix: a negation pass in the judge (for each passed criterion, ask whether the response also asserts its negation) and expert-written negative criteria. Measure cost, expert agreement, gap closed. (5) Rescore the leaderboard under the patched metric and report which rank gaps hold.

**Caveats.** One generator, one seed, n = 40. Flash judge, not the paper's Pro (κ = 0.92 with Pro on a 54-criterion subset). The quality proxy is an LLM, and it may be detecting tampering rather than judging quality — the padding row is the tell, where I predicted a coin flip because the padding adds nothing and got 90%. Only experts settle that, which is why they are step (2). Each of these is a reason to do the study properly, not a reason to doubt the direction.

Pre-registration, full results, and code: github.com/puiji/apex-rubric-audit
