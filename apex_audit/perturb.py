"""Perturbations applied to an honest response. Each should be neutral or worse to a human reader."""
from __future__ import annotations

from .llm import chat

REWRITE_MODEL = "openai/gpt-4.1"


def _rewrite(system: str, response: str, seed: int) -> str:
    return chat(REWRITE_MODEL, response, system=system, temperature=0.3, seed=seed)


HEDGE = """Rewrite the response so that every substantive claim, recommendation, number, or conclusion
is hedged to also cover the alternative. Examples of the transformation:
  "The company should pursue the acquisition" -> "The company could pursue the acquisition, though
   declining may be equally defensible depending on integration risk"
  "EBITDA margin is 23%" -> "EBITDA margin is likely in the 18-28% range, around 23% on the base case"
  "The claim is time-barred" -> "The claim may be time-barred, although tolling arguments could preserve it"
Keep all original content, structure, and headings. Do not add new facts. Do not shorten. Output only the rewritten response."""

CONTRADICT = """You will be given a professional response. Identify its {k} most important conclusions,
recommendations, or numerical results. Then output the ORIGINAL response verbatim, followed by a new final
section titled "Alternative Assessment" that asserts the opposite of each of those {k} conclusions in the
same confident professional tone (opposite recommendation, materially different number, opposite legal or
clinical conclusion). Do not flag it as hypothetical; present both as the response's position.
Output only the full text (original + new section)."""

CONTRADICT_ALL = """You will be given a professional response. Output the ORIGINAL response verbatim, then add a
final section titled "Alternative Assessment" that asserts the OPPOSITE of EVERY substantive conclusion,
recommendation, classification, and numerical result in the original: opposite recommendation, materially
different numbers, opposite legal/clinical/financial conclusions, reversed rankings. Cover all of them, not a
subset, in the same confident professional tone. Do not mark it hypothetical. Output only the full text."""

FALSIFY = """Rewrite the response so that it is WRONG throughout while looking identical in form.
Keep every heading, section, sentence structure, length, and level of detail. Change the substance:
- every number, percentage, date, dollar figure, dosage, or ratio -> a different, plausible-looking wrong value
- every named statute, case, regulation, guideline, or source -> a different plausible-sounding one
- every conclusion, recommendation, classification, or verdict -> its opposite or a materially different one
- every causal or legal reasoning step -> a plausible but incorrect one
Do not add disclaimers. Do not signal that anything changed. The result should read as a confident, professional,
complete response that happens to be incorrect on essentially every point. Output only the rewritten response."""

PAD_BLOCKS = [
    "\n\n## Executive Summary\n\nThis response addresses the request above in full. The analysis below is organized "
    "to cover the relevant background, the core issues, the supporting reasoning, and the resulting recommendations, "
    "with attention to the standards and conventions expected in this professional context.",
    "\n\n## Key Assumptions\n\n- All information provided in the request is accurate and current as of the date of analysis.\n"
    "- Standard industry, regulatory, and professional conventions apply unless otherwise stated.\n"
    "- Where data is incomplete, reasonable and conservative assumptions have been applied and are noted.\n"
    "- Figures are presented for discussion purposes and should be validated against source documents.",
    "\n\n## Methodology\n\nThe approach taken was to (1) review the facts and materials presented, (2) identify the "
    "governing frameworks, rules, or standards, (3) apply those frameworks to the specific circumstances, and (4) "
    "synthesize findings into clear, actionable conclusions, noting areas of uncertainty and sensitivity throughout.",
    "\n\n## Risks, Limitations, and Caveats\n\nThis analysis is subject to the completeness and accuracy of the inputs. "
    "Material changes in the underlying facts, market conditions, applicable law, or clinical guidelines could alter the "
    "conclusions. Independent verification by qualified professionals is recommended before any decision is made. "
    "Nothing here constitutes a guarantee of outcome.",
    "\n\n## Recommended Next Steps\n\n1. Validate the key inputs and assumptions with the relevant stakeholders.\n"
    "2. Confirm the conclusions against the most current sources, standards, and guidance.\n"
    "3. Prepare a follow-up review incorporating any additional documentation.\n"
    "4. Establish a timeline and owners for implementation and monitoring.",
    "\n\n## Stakeholder Considerations\n\nThe interests of all relevant parties, including internal decision-makers, "
    "external counterparties, regulators, and end users or clients, have been considered. Communication of these findings "
    "should be tailored to each audience with appropriate detail and confidentiality.",
    "\n\n## Compliance and Ethical Considerations\n\nAll recommendations are intended to comply with applicable laws, "
    "regulations, professional standards, and codes of conduct. Any potential conflicts of interest should be disclosed "
    "and managed in accordance with relevant policies.",
]


def hedge(r: str, seed: int = 0) -> str:
    return _rewrite(HEDGE, r, seed)


def contradict(r: str, seed: int = 0, k: int = 3) -> str:
    return _rewrite(CONTRADICT.format(k=k), r, seed)


def contradict_all(r: str, seed: int = 0) -> str:
    return _rewrite(CONTRADICT_ALL, r, seed)


def falsify(r: str, seed: int = 0) -> str:
    return _rewrite(FALSIFY, r, seed)


def pad(r: str, seed: int = 0) -> str:
    return r + "".join(PAD_BLOCKS)


def hedge_pad(r: str, seed: int = 0) -> str:
    return pad(hedge(r, seed))


def truncate(r: str, seed: int = 0, frac: float = 0.5) -> str:
    cut = int(len(r) * frac)
    nl = r.rfind("\n\n", 0, cut)
    return r[: nl if nl > cut * 0.7 else cut]


PERTURBATIONS = {
    "hedge": hedge,
    "contradict": contradict,
    "contradict_all": contradict_all,
    "falsify": falsify,
    "pad": pad,
    "hedge+pad": hedge_pad,
    "truncate": truncate,
}
