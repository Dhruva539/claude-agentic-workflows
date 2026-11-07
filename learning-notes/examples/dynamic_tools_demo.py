"""Dynamic tool loading with the Claude API.

Part 1: built-in tool search (defer_loading + the BM25 search tool).
Part 2: your own search over a tool registry (swap in embeddings, a DB, etc.).

Run:
    python dynamic_tools_demo.py builtin    # needs ANTHROPIC_API_KEY
    python dynamic_tools_demo.py custom     # needs ANTHROPIC_API_KEY
    python dynamic_tools_demo.py selftest   # offline, no API key
"""
import re
import sys

MODEL = "claude-sonnet-5-5"


# ---------------------------------------------------------------------------
# 1. A tool registry. In real life this comes from a DB, config repo or MCP.
# ---------------------------------------------------------------------------
def tool(name, description, **props):
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {k: {"type": "string", "description": v} for k, v in props.items()},
            "required": list(props),
        },
    }


REGISTRY = [
    tool("get_service_metrics", "Get latency and error-rate metrics for a service.", service="Service name"),
    tool("list_recent_deploys", "List recent deployments for a service.", service="Service name"),
    tool("page_oncall", "Page the on-call engineer for a service.", service="Service name", message="What to tell them"),
    tool("restart_service", "Restart all instances of a service.", service="Service name"),
    tool("track_shipment", "Get the current status of a shipment.", shipment_id="Shipment ID"),
    tool("create_account", "Create a user account for a new employee.", employee_id="Employee ID"),
]

# Fake implementations so the demo runs end to end.
HANDLERS = {
    "get_service_metrics": lambda service: f"{service}: p95 latency 2.4s (normal 300ms), errors 4%",
    "list_recent_deploys": lambda service: f"{service}: deploy v142 finished 12 minutes ago",
    "page_oncall": lambda service, message: f"Paged on-call for {service}: {message}",
    "restart_service": lambda service: f"Restarted {service}",
    "track_shipment": lambda shipment_id: f"{shipment_id}: delayed at port",
    "create_account": lambda employee_id: f"Account created for {employee_id}",
}

HOT_TOOLS = {"page_oncall"}  # keep your 3-5 most used tools always loaded


# ---------------------------------------------------------------------------
# 2. Built-in tool search: flag tools with defer_loading, add the search tool.
# ---------------------------------------------------------------------------
def build_tools_builtin():
    tools = [{"type": "tool_search_tool_bm25_20251119", "name": "tool_search_tool_bm25"}]
    for t in REGISTRY:
        # Every definition is still sent on every request. Deferred ones stay
        # out of the model's context until the search tool finds them.
        tools.append(t if t["name"] in HOT_TOOLS else {**t, "defer_loading": True})
    return tools


# ---------------------------------------------------------------------------
# 3. Custom tool search: your own function decides which tools to reveal.
# ---------------------------------------------------------------------------
def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower().replace("_", " ")))


def search_registry(query, limit=5):
    q = _tokens(query)
    scored = []
    for t in REGISTRY:
        score = len(q & _tokens(t["name"] + " " + t["description"]))
        if score:
            scored.append((score, t["name"]))
    scored.sort(reverse=True)
    return [name for _, name in scored[:limit]]


FIND_TOOLS = {
    "name": "find_tools",
    "description": (
        "Search the internal tool catalog. Call this first to find tools by what "
        "you need to do, for example 'recent deployments' or 'page on-call'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What you want to do"}},
        "required": ["query"],
    },
}


def build_tools_custom():
    # find_tools is NOT deferred. Every tool it can return must still be
    # defined here, with defer_loading, so the API can expand the reference.
    return [FIND_TOOLS] + [{**t, "defer_loading": True} for t in REGISTRY]


def run_tool_custom(block):
    if block.name == "find_tools":
        names = search_registry(block.input["query"])
        content = (
            [{"type": "tool_reference", "tool_name": n} for n in names]
            if names
            else "No matching tools found."
        )
        return {"type": "tool_result", "tool_use_id": block.id, "content": content}
    return run_tool_local(block)


def run_tool_local(block):
    out = HANDLERS[block.name](**block.input)
    return {"type": "tool_result", "tool_use_id": block.id, "content": out}


# ---------------------------------------------------------------------------
# 4. The agent loop (same for both modes).
# ---------------------------------------------------------------------------
def run_agent(user_msg, tools, tool_runner):
    import anthropic

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_msg}]
    while True:
        resp = client.messages.create(
            model=MODEL, max_tokens=2048, tools=tools, messages=messages
        )
        # Pass the assistant content back unchanged, including search blocks.
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for block in resp.content:
            # Only YOUR tools show up as tool_use. The built-in search runs on
            # the API side as server_tool_use, so never answer that one.
            if block.type == "tool_use":
                results.append(tool_runner(block))
        messages.append({"role": "user", "content": results})


def selftest():
    tools = build_tools_builtin()
    assert tools[0]["type"] == "tool_search_tool_bm25_20251119"
    assert "defer_loading" not in tools[0]
    assert sum(1 for t in tools if t.get("defer_loading")) == len(REGISTRY) - len(HOT_TOOLS)
    assert any("defer_loading" not in t for t in tools[1:]), "need a non-deferred tool"
    assert search_registry("service latency metrics")[0] == "get_service_metrics"
    assert "list_recent_deploys" in search_registry("recent deployments")
    assert search_registry("page on-call")[0] == "page_oncall"
    assert search_registry("zzz nothing") == []
    print("selftest ok")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    request = "Checkout API is slow. Find out why and page the on-call engineer."
    if mode == "builtin":
        print(run_agent(request, build_tools_builtin(), run_tool_local))
    elif mode == "custom":
        print(run_agent(request, build_tools_custom(), run_tool_custom))
    else:
        selftest()
