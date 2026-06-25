# Conference Paper Planner — Agent Skill

Required packages (install before running any snippets):
```
pip install rank_bm25 icalendar
```

## Overview

Given a user's natural language description of their research interests, search the conference JSON data for relevant papers using BM25 ranking. Produce two outputs:

1. A **Markdown list** of matching papers (with title, authors, session, time, decision, and link)
2. An **ICS calendar file** with events for each matched paper's session

## Input

- `data.json` — the conference schedule JSON (array of paper entries under `results`). Each entry has fields: `name` (title), `authors` (list of `{fullname, institution}`), `decision`, `event_type`, `session`, `starttime`, `endtime`, `room_name`, `paper_url`, `virtualsite_url`.
- User's interest statement, e.g. "I'm interested in reinforcement learning for robotics and LLM reasoning"

## Step 1: Load and index papers

```python
import json
from rank_bm25 import BM25Okapi

with open("data.json") as f:
    papers = json.load(f)["results"]

corpus = []
for p in papers:
    authors_str = " ".join(a["fullname"] for a in p["authors"])
    text = f"{p['name']} {authors_str} {p.get('session', '')} {' '.join(p.get('keywords', []))}"
    corpus.append(text.lower().split())

bm25 = BM25Okapi(corpus)
```

## Step 2: Query and rank

```python
query = "reinforcement learning for robotics"
tokens = query.lower().split()
scores = bm25.get_scores(tokens)

top_k = 30
ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
results = [(papers[i], score) for i, score in ranked if score > 0]
```

The agent should choose `top_k` based on how broad the user's interests are. For a narrow topic, 10–20 is fine; for broad interests, go up to 50. Filter out zero-score entries.

If the user provides multiple distinct topics (e.g. "RL for robotics and also LLM safety"), run separate queries for each topic and merge results, deduplicating by paper `id`.

## Step 3: Write Markdown output

```python
with open("reading_list.md", "w") as f:
    f.write("# Conference Reading List\n\n")
    for paper, score in results:
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
        f.write(f"- **Relevance score**: {score:.2f}\n\n")
```

## Step 4: Write ICS calendar file

Only include papers that have `starttime` and `endtime` set.

```python
from icalendar import Calendar, Event
from datetime import datetime

cal = Calendar()
cal.add("prodid", "-//Conference Planner//EN")
cal.add("version", "2.0")

for paper, score in results:
    if not paper.get("starttime") or not paper.get("endtime"):
        continue
    ev = Event()
    ev.add("summary", paper["name"])
    ev.add("dtstart", datetime.fromisoformat(paper["starttime"]))
    ev.add("dtend", datetime.fromisoformat(paper["endtime"]))
    description = f"Authors: {', '.join(a['fullname'] for a in paper['authors'])}"
    if paper.get("paper_url"):
        description += f"\n{paper['paper_url']}"
    description += f"\nType: {paper['event_type']} | Decision: {paper['decision']}"
    description += f"\nRelevance: {score:.2f}"
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
- If time conflicts exist among selected papers, flag them.
- The JSON file name varies by conference. The agent should use whichever JSON file is present in the working directory.
