#!/usr/bin/env bash
# Pre-registered 40-case study (PREREG.md). Safe to rerun: all model calls are cached.
set -euo pipefail
cd "$(dirname "$0")/.."
COND=honest,honest_regrade,pad,hedge,hedge+pad,contradict,contradict_all,falsify,truncate,greybox

python -m apex_audit.run --per-domain 10 --run study40 --conditions "$COND"

PRO_IDS=$(python - <<'PY'
import random
from apex_audit import data
cases = data.load_cases(); random.Random(0).shuffle(cases)
first = {}
for c in cases:
    first.setdefault(c.domain, c.task_id)
print(",".join(first.values()))
PY
)
GRADER_WORKERS=2 python -m apex_audit.run --task-ids "$PRO_IDS" --run study40 --grader gemini/gemini-3.1-pro-preview --conditions "$COND"

python -m apex_audit.quality results/study40__gemini-3-flash
python -m apex_audit.analyze results/study40__gemini-3-flash \
  --new-only results/pilot20__gemini-3-flash --agree results/study40__gemini-3.1-pro
