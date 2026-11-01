"""Loan application as a LangGraph: parallel checks, rule-based routing, human pauses, resume.

  python loan_graph.py start  <app_id>              run until done or a human pause
  python loan_graph.py resume <app_id> <approve|decline>   answer the pause, continue
State is saved in loans.db (override with LOANS_DB), so resume works from a separate process (or after a restart).
No LLM is needed to run it; the two draft_* nodes are where a model would write the letter.
"""
import operator
import os
import sys
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

APPLICANTS = {   # stand-in for a database / documents
    "A-100": {"name": "Asha",  "id_valid": True,  "income": 90000, "debts": 20000, "credit": 780},
    "B-200": {"name": "Ben",   "id_valid": True,  "income": 60000, "debts": 28000, "credit": 690},
    "C-300": {"name": "Chen",  "id_valid": True,  "income": 40000, "debts": 30000, "credit": 540},
    "D-400": {"name": "Dana",  "id_valid": False, "income": 80000, "debts": 10000, "credit": 760},
}

class State(TypedDict, total=False):
    app_id: str
    id_ok: bool
    dti: float
    credit: int
    risk: str                      # approve | decline | borderline
    decision: str
    by_human: bool
    letter: str
    status: str
    log: Annotated[list, operator.add]   # parallel nodes append; reducer merges

def intake(s):
    return {"log": [f"intake {s['app_id']}"]}

def check_id(s):
    ok = APPLICANTS[s["app_id"]]["id_valid"]
    return {"id_ok": ok, "log": [f"id check: {'ok' if ok else 'FAILED'}"]}

def check_income(s):
    a = APPLICANTS[s["app_id"]]
    dti = round(a["debts"] / a["income"], 2)
    return {"dti": dti, "log": [f"debt-to-income: {dti}"]}

def check_credit(s):
    c = APPLICANTS[s["app_id"]]["credit"]
    return {"credit": c, "log": [f"credit score: {c}"]}

def risk_rules(s):                       # a business rule, not a model opinion
    if not s["id_ok"] or s["credit"] < 600:
        r = "decline"
    elif s["credit"] >= 720 and s["dti"] <= 0.35:
        r = "approve"
    else:
        r = "borderline"
    return {"risk": r, "log": [f"rules -> {r}"]}

def route_risk(s):
    return {"approve": "draft_offer", "decline": "draft_decline", "borderline": "underwriter"}[s["risk"]]

def underwriter(s):                      # PAUSE: waits for a person, however long
    ans = interrupt({"ask": "Underwriter decision needed", "app": s["app_id"],
                     "dti": s["dti"], "credit": s["credit"], "options": ["approve", "decline"]})
    return {"decision": ans, "by_human": True, "log": [f"underwriter says {ans}"]}

def route_underwriter(s):
    return "draft_offer" if s["decision"] == "approve" else "draft_decline"

def draft_offer(s):                      # a model would draft this
    name = APPLICANTS[s["app_id"]]["name"]
    return {"decision": "approve", "letter": f"Dear {name}, your loan is approved.", "log": ["offer drafted"]}

def route_offer(s):
    return "send" if s.get("by_human") else "approve_offer"

def approve_offer(s):                    # PAUSE: second pair of eyes on clear approvals
    ans = interrupt({"ask": "Approve this offer before sending?", "app": s["app_id"],
                     "letter": s["letter"], "options": ["approve", "decline"]})
    if ans != "approve":
        return {"decision": "decline", "letter": "", "log": ["offer rejected by reviewer"]}
    return {"by_human": True, "log": ["offer approved by reviewer"]}

def route_after_review(s):
    return "send" if s["decision"] == "approve" else "draft_decline"

def draft_decline(s):
    name = APPLICANTS[s["app_id"]]["name"]
    return {"decision": "decline", "letter": f"Dear {name}, we cannot offer a loan at this time.",
            "log": ["decline letter drafted"]}

def send(s):
    return {"status": f"sent_{s['decision']}", "log": ["letter sent"]}

g = StateGraph(State)
for n, f in [("intake", intake), ("check_id", check_id), ("check_income", check_income),
             ("check_credit", check_credit), ("risk_rules", risk_rules),
             ("underwriter", underwriter), ("draft_offer", draft_offer),
             ("approve_offer", approve_offer), ("draft_decline", draft_decline), ("send", send)]:
    g.add_node(n, f)
g.add_edge(START, "intake")
for c in ("check_id", "check_income", "check_credit"):     # PARALLEL fan-out
    g.add_edge("intake", c)
g.add_edge(["check_id", "check_income", "check_credit"], "risk_rules")   # join
g.add_conditional_edges("risk_rules", route_risk,
    {"draft_offer": "draft_offer", "draft_decline": "draft_decline", "underwriter": "underwriter"})
g.add_conditional_edges("underwriter", route_underwriter,
    {"draft_offer": "draft_offer", "draft_decline": "draft_decline"})
g.add_conditional_edges("draft_offer", route_offer, {"send": "send", "approve_offer": "approve_offer"})
g.add_conditional_edges("approve_offer", route_after_review,
    {"send": "send", "draft_decline": "draft_decline"})
g.add_edge("draft_decline", "send")
g.add_edge("send", END)

def report(app, cfg):
    st = app.get_state(cfg)
    if st.next:
        ask = st.tasks[0].interrupts[0].value
        print(f"  PAUSED before '{st.next[0]}': {ask}")
    else:
        print(f"  DONE status={st.values.get('status')}")
    print("  log:", " | ".join(st.values.get("log", [])))

if __name__ == "__main__":
    cmd, app_id = sys.argv[1], sys.argv[2]
    cfg = {"configurable": {"thread_id": app_id}}
    with SqliteSaver.from_conn_string(os.environ.get("LOANS_DB", "loans.db")) as cp:
        app = g.compile(checkpointer=cp)
        if cmd == "start":
            app.invoke({"app_id": app_id, "log": []}, cfg)
        elif cmd == "resume":
            app.invoke(Command(resume=sys.argv[3]), cfg)
        print(f"{cmd} {app_id}")
        report(app, cfg)
