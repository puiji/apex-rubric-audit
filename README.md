# apex-rubric-audit

Does the APEX-v1 rubric score penalize a response for asserting the opposite of its own conclusions? No. This
repository contains the pre-registration, code, raw judge outputs, and analysis behind that measurement, plus the
research proposal built on it.

| Perturbation of the honest response | Rubric score change | Blind judge prefers original |
|---|---|---|
| Append a section reversing every conclusion | 0.000 (90% CI ±0.026) | 95% |
| Rewrite every claim as a hedge | 0.000 | 85% |
| Add seven boilerplate sections | +0.002 | 90% |
| Make every fact wrong, same structure | −0.280 | 82% |
| Delete the second half | −0.177 | 100% |
| Regrade identical text (noise floor) | +0.004 | n/a |

40 tasks from the public APEX-v1 split, 10 per domain. Rubric judge: Gemini 3 Flash, one criterion per call,
binary pass/fail. Blind judge: GPT-4.1, no rubric, both presentation orders. Full tables, the failed prediction,
and what the data does not show are in [RESULTS.md](RESULTS.md). Hypotheses and falsifiers written before the
data existed are in [PREREG.md](PREREG.md). The one-page proposal is [PROPOSAL.md](PROPOSAL.md).

## Layout

```
apex_audit/
  data.py       load the APEX-v1 CSV and attachments
  llm.py        provider-agnostic chat call with a content-addressed cache
  generate.py   honest baseline and the grey-box checkbox-stuffing attack
  perturb.py    hedge, contradict, contradict_all, falsify, pad, truncate
  grade.py      rubric judge
  quality.py    blind pairwise quality proxy
  run.py        generate -> perturb -> grade
  analyze.py    equivalence tests, sign tests, bootstrap CIs, judge agreement
results/
  study40__gemini-3-flash/    grades.jsonl, responses.jsonl, quality.jsonl, analysis.txt
  study40__gemini-3.1-pro/    calibration subset (Pro is capped at 250 requests/day)
  pilot20__gemini-3-flash/    exploratory pilot that informed the design
scripts/run_study.sh          the full study, end to end
```

`grades.jsonl` holds one row per (task, condition) with every criterion's verdict and the judge's explanation.
`responses.jsonl` holds the response text that was graded.

## Reproduce

```bash
pip install -r requirements.txt
python -c "from huggingface_hub import snapshot_download; snapshot_download('mercor/apex-v1', repo_type='dataset', local_dir='data')"
printf 'GEMINI_API_KEY=...\nOPENAI_API_KEY=...\n' > .env
python -m apex_audit.data          # sanity check: 100 cases, 176 attachments found
scripts/run_study.sh
```

Every model call is cached under `cache/` by content, so a rerun only makes the calls that failed. Rerunning the
analysis alone on the shipped results needs no API keys:

```bash
python -m apex_audit.analyze results/study40__gemini-3-flash --new-only results/pilot20__gemini-3-flash --agree results/study40__gemini-3.1-pro
```

## Notes

The grader prompt is a reconstruction from the APEX-v1 paper, not Mercor's. The paper's judge (Gemini 2.5 Pro)
is no longer served to new API keys; Gemini 3.1 Pro agrees with Flash at κ = 0.92 on the calibration subset
graded so far. Condition `greybox` appears as `greybox_stuff` in the raw result files.
