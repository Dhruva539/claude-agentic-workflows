---
name: subagent-delegation
description: Delegates broad codebase exploration or research to a subagent so the main context stays small. Use when a task needs reading many files, searching across a repo, or gathering facts before making changes.
---

# Subagent delegation

## When to delegate
- The task needs reading more than ~5 files.
- The file contents are needed only briefly, not during implementation.
- The work is independent of what I'm doing in the main thread.

## When NOT to delegate
- A single known file or symbol: read it directly.
- Work that needs my back-and-forth input.

## Workflow
1. Write a clear brief for the subagent: the question, the scope (folders), and the stop condition.
2. Ask for a short return: max 15 lines, with file paths and line numbers, no file dumps.
3. Run independent subagents in parallel (one message, several calls).
4. Use only the summary in the main thread. Do not re-read the same files yourself.

## Brief template
Goal: <what to find out>
Scope: <folders or file patterns>
Return: findings as bullets with path:line, max 15 lines
Do not: edit files

## Rules
- Use a read-only agent type (like Explore) for searching.
- Use a cheaper model for pure search tasks.
