"""Semantic validation gate demo. Runs offline, no API key needed.

The 'judge' here is a keyword stub so you can see the flow. In real use,
replace judge_clause() with an LLM call that compares summary and source.

Run:  python semantic_gate_demo.py
"""

# Key clauses come from the SOURCE document (an extraction step or a rubric
# per document type), never from the summary being checked.
KEY_CLAUSES = {
    "payment": ["net 30"],
    "termination": ["terminate", "60 days"],
    "liability cap": ["liability", "$1m"],
    "auto-renewal": ["renew", "90"],
}

GOOD = (
    "Payment is net 30. Either party may terminate with 60 days notice. "
    "Liability is capped at $1M. The contract auto-renews unless 90 days "
    "notice is given."
)
BAD = "Payment is net 30. Either party may terminate with notice."


# ---- Check 1: structure (plain code, cheap, run first) ---------------------
def structure_ok(summary):
    words = len(summary.split())
    return 5 <= words <= 200


# ---- Check 2: coverage (stub for an LLM judge) ----------------------------
def judge_clause(summary, terms):
    """Return 'covered', 'partial' or 'missing' for one key clause."""
    text = summary.lower()
    hits = sum(1 for t in terms if t in text)
    if hits == len(terms):
        return "covered"
    return "partial" if hits else "missing"


def gate(summary):
    """Return (passed, gaps). Fail closed: any gap means not accepted."""
    if not structure_ok(summary):
        return False, ["structure: bad length"]
    gaps = []
    for clause, terms in KEY_CLAUSES.items():
        status = judge_clause(summary, terms)
        if status != "covered":
            gaps.append(f"{clause} ({status})")
    return not gaps, gaps


# ---- The loop: retry with specific feedback, then escalate -----------------
def summarize_with_gate(doc_id, summarize, max_attempts=3):
    feedback = None
    for attempt in range(1, max_attempts + 1):
        summary = summarize(doc_id, feedback)  # HTTP 200 happens here
        passed, gaps = gate(summary)
        if passed:
            return {"doc": doc_id, "status": "accepted", "attempts": attempt}
        feedback = "Your summary is missing or incomplete on: " + ", ".join(gaps)
    return {"doc": doc_id, "status": "needs_human_review", "attempts": max_attempts, "gaps": gaps}


# ---- Fake summarizer: always returns HTTP 200, quality varies --------------
BEHAVIOR = {"d1": "good", "d2": "fixable", "d3": "stubborn", "d4": "good", "d5": "fixable"}


def fake_summarizer(doc_id, feedback):
    kind = BEHAVIOR[doc_id]
    if kind == "good":
        return GOOD
    if kind == "fixable":
        return GOOD if feedback else BAD  # improves once told the gaps
    return BAD  # stubborn: never improves


if __name__ == "__main__":
    results = [summarize_with_gate(d, fake_summarizer) for d in BEHAVIOR]
    for r in results:
        print(r)

    total = len(results)
    first_try = sum(1 for r in results if r["status"] == "accepted" and r["attempts"] == 1)
    retried = sum(1 for r in results if r["status"] == "accepted" and r["attempts"] > 1)
    review = sum(1 for r in results if r["status"] == "needs_human_review")
    print()
    print("HTTP error rate:           0 / %d  (looks perfect)" % total)
    print("Semantic pass, first try:  %d / %d" % (first_try, total))
    print("Fixed by retry:            %d / %d" % (retried, total))
    print("Sent to human review:      %d / %d" % (review, total))
