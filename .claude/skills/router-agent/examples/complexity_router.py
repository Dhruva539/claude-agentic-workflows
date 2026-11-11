"""Route tasks by complexity: simple -> one cheap call, complex -> 5-agent orchestration."""
import json
import logging

import anthropic

client = anthropic.Anthropic()
CHEAP = "claude-haiku-5-5"   # router + simple path
STRONG = "claude-sonnet-5-5"  # complex path agents

log = logging.getLogger("router")

ROUTER_PROMPT = """Classify the user task as SIMPLE or COMPLEX.
SIMPLE: single fact lookup, short answer, at most one tool call, no multi-step reasoning.
COMPLEX: needs planning, several sources, analysis, or changes across files or systems.
When unsure, answer COMPLEX.
Reply with JSON only: {"route": "SIMPLE" or "COMPLEX", "reason": "<one line>"}"""

SIMPLE_PROMPT = """Answer briefly and accurately.
If you are not confident, or the task needs more than a lookup, reply exactly: ESCALATE"""


def ask(model: str, system: str, user: str, max_tokens: int = 500) -> str:
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def classify(task: str) -> str:
    """Return 'SIMPLE' or 'COMPLEX'. Any failure defaults to COMPLEX (safe side)."""
    try:
        out = ask(CHEAP, ROUTER_PROMPT, task, max_tokens=100)
        route = json.loads(out)["route"]
        return route if route in ("SIMPLE", "COMPLEX") else "COMPLEX"
    except Exception:
        return "COMPLEX"


def simple_path(task: str) -> str | None:
    """One cheap call. Returns None if the model asks to escalate."""
    answer = ask(CHEAP, SIMPLE_PROMPT, task)
    return None if answer == "ESCALATE" else answer


def run_agent(role: str, prompt: str) -> str:
    return ask(STRONG, f"You are the {role} agent.", prompt, max_tokens=1500)


def complex_path(task: str) -> str:
    """Your existing five-agent orchestration (simplified here)."""
    plan = run_agent("planner", task)
    research = run_agent("researcher", f"Task: {task}\nPlan: {plan}")
    draft = run_agent("writer", f"Task: {task}\nResearch: {research}")
    review = run_agent("reviewer", f"Task: {task}\nDraft: {draft}")
    return run_agent("finalizer", f"Draft: {draft}\nReview: {review}")


def handle(task: str) -> str:
    route = classify(task)
    if route == "SIMPLE":
        answer = simple_path(task)
        if answer is not None:
            log.info("route=simple")
            return answer
        log.info("route=escalated")  # simple path was unsure
    else:
        log.info("route=complex")
    return complex_path(task)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(handle("What is the capital of France?"))
    print(handle("Compare our three vendor contracts and draft a migration plan."))
