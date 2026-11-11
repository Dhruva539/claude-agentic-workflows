---
name: tool-chain
description: Runs a fixed sequence of tools where each step's output feeds the next, with a check after every step. Use for repeatable pipelines such as fetch, clean, analyze, report.
---

# Tool chain

## Pipeline
1. Fetch: get the raw data (search, API, or file read).
2. Clean: remove duplicates and bad rows, save to a file.
3. Analyze: run the numbers in code, never estimate by hand.
4. Report: write the result in the format I asked for.

## Workflow
- Run steps in order. Do not skip ahead.
- After each step, check the output exists and looks right (row count, no errors).
- Pass data between steps through files, not by pasting into chat.
- If a step fails, retry once with a fix. If it still fails, stop and tell me which step and why.

## Step contract
Each step states:
- Input: what it reads
- Output: what it writes and where
- Check: how to know it worked

## Rules
- Keep intermediate files; do not delete them.
- Do not run later steps on partial data.
- Final answer: result first, then one line on what was checked.
