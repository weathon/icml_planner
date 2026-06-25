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

## Input

- The conference schedule JSON (array of paper entries under `results`). Each entry has fields: `name` (title), `abstract`, `authors` (list of `{fullname, institution}`), `decision`, `event_type`, `session`, `starttime`, `endtime`, `room_name`, `paper_url`, `virtualsite_url`.
- User's interest statement, e.g. "I'm interested in reinforcement learning for robotics and LLM reasoning"

## Step 1: Load and index papers

Include **both title and abstract** in the search corpus for better recall.

```python
import json
from rank_bm25 import BM25Okapi

with open("data.json") as f:
    papers = json.load(f)["results"]

corpus = []
for p in papers:
    authors_str = " ".join(a["fullname"] for a in p["authors"])
    abstract = p.get("abstract", "")
    text = f"{p['name']} {abstract} {authors_str} {p.get('session', '')} {' '.join(p.get('keywords', []))}"
    corpus.append(text.lower().split())

bm25 = BM25Okapi(corpus)
```

## Step 2: Query and rank

```python
query = "reinforcement learning for robotics"
tokens = query.lower().split()
scores = bm25.get_scores(tokens)

top_k = 50
ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
candidates = [(papers[i], score) for i, score in ranked if score > 0]
```

Use a generous `top_k` (40–60) since the verification step will filter out false positives. For multiple distinct topics, run separate queries and merge results, deduplicating by paper `id`.

## Step 3: Verify relevance

BM25 keyword matching produces false positives (e.g. a paper mentioning "reinforcement" in a different context). Each candidate must be verified before going into the final reading list.

**The agent should verify every single candidate.** For each paper, read its title and abstract and judge whether the paper is genuinely relevant to the user's stated interests, not just a keyword overlap.

If the agent supports subagents or workflows, use them to parallelize verification:
- Spawn one subagent per candidate (or batch into small groups)
- Each subagent receives: the user's interest description, the paper title, and the paper abstract
- The subagent returns a verdict: `relevant` or `not_relevant`, with a one-line reason

If subagents are not available, the agent should verify papers itself in a loop.

After verification, split candidates into two lists:
- `confirmed` — papers verified as relevant → `reading_list.md` + `schedule.ics`
- `rejected` — papers that matched BM25 but were judged not relevant → `maybe_relevant.md`

## Step 4: Write Markdown outputs

### reading_list.md (confirmed papers)

```python
with open("reading_list.md", "w") as f:
    f.write("# Conference Reading List\n\n")
    for paper, score in confirmed:
        authors = ", ".join(a["fullname"] for a in paper["authors"])
        f.write(f"### {paper['name']}\n")
        f.write(f"- **Authors**: {authors}\n")
        f.write(f"- **Type**: {paper['event_type']} | **Decision**: {paper['decision']}\n")
        if paper.get("session"):
            f.write(f"- **Session**: {paper['session']}\n")
        if paper.get("starttime"):
            f.write(f"- **Time**: {paper['starttime']} — {paper['endtime']}\n")
        if paper.get("room_name"):
            f.write(f"- **Room**: {paper['room_name']}\n")
        if paper.get("paper_url"):
            f.write(f"- **Paper**: {paper['paper_url']}\n")
        if paper.get("abstract"):
            f.write(f"- **Abstract**: {paper['abstract'][:300]}...\n")
        f.write(f"- **Relevance score**: {score:.2f}\n\n")
```

### maybe_relevant.md (rejected candidates for human review)

```python
with open("maybe_relevant.md", "w") as f:
    f.write("# Maybe Relevant — Human Review Needed\n\n")
    f.write("These papers matched the keyword search but were judged not directly relevant.\n\n")
    for paper, score, reason in rejected:
        f.write(f"### {paper['name']}\n")
        f.write(f"- **Why flagged**: {reason}\n")
        if paper.get("paper_url"):
            f.write(f"- **Paper**: {paper['paper_url']}\n")
        if paper.get("abstract"):
            f.write(f"- **Abstract**: {paper['abstract'][:200]}...\n")
        f.write("\n")
```

## Step 5: Write ICS calendar file

Only include confirmed papers that have `starttime` and `endtime` set.

```python
from icalendar import Calendar, Event
from datetime import datetime

cal = Calendar()
cal.add("prodid", "-//Conference Planner//EN")
cal.add("version", "2.0")

for paper, score in confirmed:
    if not paper.get("starttime") or not paper.get("endtime"):
        continue
    ev = Event()
    ev.add("summary", paper["name"])
    ev.add("dtstart", datetime.fromisoformat(paper["starttime"]))
    ev.add("dtend", datetime.fromisoformat(paper["endtime"]))
    description = f"Authors: {', '.join(a['fullname'] for a in paper['authors'])}"
    if paper.get("abstract"):
        description += f"\n\n{paper['abstract'][:500]}"
    if paper.get("paper_url"):
        description += f"\n\n{paper['paper_url']}"
    description += f"\nType: {paper['event_type']} | Decision: {paper['decision']}"
    ev.add("description", description)
    if paper.get("room_name"):
        ev.add("location", paper["room_name"])
    cal.add_component(ev)

with open("schedule.ics", "wb") as f:
    f.write(cal.to_ical())
```

## Agent behavior notes

- When the user describes interests casually, extract the key topics and form BM25 queries from them.
- Spotlight and oral papers are generally higher impact — the agent may note these in the output or let the user ask to filter by decision type.
- If the user asks to focus on orals only, filter by `event_type == "Oral"` before indexing.
- If time conflicts exist among confirmed papers, flag them to the user.
- The JSON file name varies by conference. The agent should use whichever JSON file is present in the working directory.
- The abstract field may be empty for some papers (e.g. journal track papers). In that case, verify based on title alone and note the missing abstract.
- Err on the side of keeping papers in `reading_list.md` if uncertain — better to include a borderline paper than miss a relevant one. Reserve `maybe_relevant.md` for clear false positives.
