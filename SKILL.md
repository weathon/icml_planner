# Conference Paper Planner — Agent Skill

Required packages (install before running any snippets):
```
pip install rank_bm25 icalendar
```

## Overview

Given a user's natural language description of their research interests, search the conference JSON data for relevant papers using BM25 ranking over titles and abstracts. Then verify each candidate to filter out false positives. Produce three outputs:

1. `reading_list.md` — confirmed relevant papers with metadata
2. `schedule.ics` — calendar events for confirmed papers that have session times
3. `maybe_relevant.md` — papers that matched BM25 but failed verification, for human review

## CLI Tools

### search.py

BM25 search over paper titles, abstracts, authors, and sessions.

```
python search.py "reinforcement learning for robotics" \
    --data icml-2026-orals-posters.json \
    --top-k 50 \
    --out candidates.json
```

Options:
- `--data FILE` — conference JSON file (default: `icml-2026-orals-posters.json`)
- `--top-k N` — number of results (default: 50)
- `--out FILE` — output path (default: `candidates.json`)
- `--orals-only` — restrict to oral presentations

Output: a JSON array where each entry has paper metadata, a `score`, and `status: "pending"`.

### render.py

Render annotated candidates into the three output files.

```
python render.py candidates.json \
    --reading-list reading_list.md \
    --maybe maybe_relevant.md \
    --ics schedule.ics
```

Expects each entry in the JSON to have a `status` field set to `"confirmed"` or `"rejected"`, and optionally a `reason` field. Papers still marked `"pending"` are treated as confirmed.

## Agent Workflow

### Step 1: Search

Extract key topics from the user's interest statement. If the user mentions multiple distinct areas (e.g. "RL for robotics and also LLM safety"), run separate searches and merge the output files, deduplicating by `id`.

```bash
python search.py "reinforcement learning robotics" --top-k 50 --out candidates.json
```

Use a generous top_k (40–60) since verification will filter out false positives.

### Step 2: Verify each candidate

Read `candidates.json`. For each paper, judge whether it is genuinely relevant to the user's interests based on its title and abstract, not just keyword overlap.

For each paper, set:
- `status` to `"confirmed"` if relevant, `"rejected"` if not
- `reason` to a one-line explanation (especially for rejections)

If the agent supports subagents or workflows, use them to parallelize verification — spawn one per candidate (or batch into small groups). Each subagent receives the user's interest description, the paper title, and the paper abstract, and returns a verdict.

If subagents are not available, verify in a loop. Write the updated JSON back to `candidates.json` when done.

### Step 3: Render

```bash
python render.py candidates.json
```

This produces all three output files.

## Agent behavior notes

- When the user describes interests casually, extract the key topics and form BM25 queries from them.
- Spotlight and oral papers are generally higher impact — the agent may note these in the output or let the user ask to filter by decision type.
- If the user asks to focus on orals only, pass `--orals-only` to search.py.
- If time conflicts exist among confirmed papers, flag them to the user.
- The JSON file name varies by conference. The agent should use whichever JSON file is present in the working directory.
- The abstract field may be empty for some papers (e.g. journal track papers). In that case, verify based on title alone and note the missing abstract.
- Err on the side of keeping papers in `reading_list.md` if uncertain — better to include a borderline paper than miss a relevant one. Reserve `maybe_relevant.md` for clear false positives.
