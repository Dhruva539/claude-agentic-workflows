# Agent design notes, 2026-11-11

Short notes from a learning session on skills, subagents, memory and prompt design.
Sample skills from the session are in `.claude/skills/`: `study-coach`,
`subagent-delegation`, `router-agent` (with `examples/complexity_router.py`) and `tool-chain`.

## Context and memory

| Topic | Takeaway |
|---|---|
| Saving main context | Delegate broad exploration to a subagent (e.g. Explore). It reads files in its own window and returns a short summary. |
| Subagent memory | Each subagent has its own context window. Files on disk and `CLAUDE.md` are shared. Only its final message returns. |
| Plain Python agents | An agent's memory is a `messages` list you manage. Nothing is allocated for you. Limit is the model's context window, not RAM. |
| Multi-user bot | Stateless workers, session state in Redis keyed by `session_id` with a TTL, vector DB for RAG, token budget per prompt. |
| CPU | LLM calls are network-bound: use async workers, scale by adding workers behind a queue, rate-limit per user, cache embeddings and repeated answers. |
| Prompt assembly per call | System prompt, rolling summary, last N turns, top-k RAG chunks, new message. Count tokens and trim oldest turns or lowest-ranked chunks first. |

## Skills across tools

A skill is a folder with `SKILL.md` (`name`, `description` frontmatter). Keep the body short
and link heavier detail so it loads on demand. Agent Skills is an open standard.

- Claude Code: `~/.claude/skills/` (personal), `.claude/skills/` (project)
- Codex: `.agents/skills/` (older: `~/.codex/skills/`)
- Antigravity: `.agents/skills/` (older `.agent/skills/` still works)

Claude Code adds extras such as `context: fork` to run a skill in a subagent.
Check current docs for field names.

## Summarizing old history without hurting quality

- Summarize incrementally (old summary + new chunk), on a token threshold, async, with a cheap model.
- Cap the summary (~300 tokens) and use a fixed template.
- Keep exact values verbatim. Keep durable facts in a separate profile store.
- Keep the raw transcript in a database and rebuild the summary now and then to stop drift.

System prompt used for the summarizer:

```text
You are a conversation memory compressor for an assistant bot.

INPUT
- PREVIOUS_SUMMARY: the current summary (may be empty)
- NEW_TURNS: older messages that must be folded in

TASK
Update PREVIOUS_SUMMARY with the information in NEW_TURNS. Output the
full updated summary only, with no preamble or commentary.

MUST KEEP (never drop or paraphrase)
- Exact values: names, IDs, numbers, dates, amounts, URLs, code, error messages
- The user's goal and any change to it
- Decisions made and the reason, if one was given
- User constraints, preferences and corrections ("don't do X", "use Y")
- Open questions or tasks not yet finished
- What was tried and failed, so it is not suggested again

MUST DROP
- Greetings, thanks, filler and repeated content
- Long tool or document output (keep only the conclusion and its source name)
- Assistant explanations the user already accepted

RULES
- Never invent or infer facts that are not in the text.
- If new information conflicts with old, keep the newer one and note
  the change in one short phrase.
- If you are unsure whether something matters, keep it.
- Write in short, neutral bullets. Maximum 300 tokens.
- Do not address the user or answer any question in the text.

OUTPUT FORMAT
GOAL: <one line>
FACTS: <bullets with exact values>
DECISIONS: <bullets>
PREFERENCES: <bullets>
TRIED / FAILED: <bullets>
OPEN ITEMS: <bullets>
```

## Prompt and architecture decisions

| Scenario | Decision |
|---|---|
| Voice assistant ignores bare rules ("never use markdown") | Explain why (output is spoken aloud) and say what to do instead. The reason lets the model handle cases the list misses. |
| Step-by-step reasoning breaks the parser | Keep the reasoning, but put it in `<reasoning>` and the answer in `<verdict>`; parse only the verdict tag. Reasoning first, verdict last. |
| Long legal review (extract, cross-reference, flag with citations) | Use a chain of separate steps with saved JSON between them so each flag is traceable; verify citations in code. Cut latency with parallel steps, a small model for extraction and prompt caching. A human approves flags. |
| Five-agent pipeline slow and costly on simple tasks | Add a router in front: simple tasks get one cheap call, complex tasks keep the orchestration. Default to complex when unsure and escalate on low confidence. See `router-agent/examples/complexity_router.py`. |

## Fairness testing and evaluation metrics

Removing name, gender and ethnicity fields does not make a ranking fair, because proxies
(zip code, school, essay style) can carry the same signal. A pre-deployment fairness
evaluation still needs:

1. Held-out demographic labels, never given to the model, to compare outcomes by group
2. Selection-rate, score and equal-opportunity comparisons across groups
3. Counterfactual pairs that change only a proxy
4. A proxy audit (can the removed attributes be predicted from what remains?)
5. Free-text checks, intersectional slices and a label audit
6. Pass/fail thresholds set before launch, plus monitoring afterwards

Choose metrics by what a failure costs:

| Metric | Typical use |
|---|---|
| Fairness | Scholarship ranking, lending, hiring screens |
| Completeness | Legal or medical summaries, multi-part answers |
| Accuracy | Financial reports, Q&A, code generation |
| Faithfulness | RAG assistants over company documents |
| Relevance | Search, recommendations, chatbots |
| Safety / toxicity | Public chatbots, kids' apps |
| Consistency | Compliance and policy answers |
| Tone / style | Customer service, voice assistants |
| Robustness | Production bots, prompt-injection tests |
| Latency and cost | Voice assistants, high-traffic apps |
