# Conference Event Planner

An agent skill that searches conference papers by your research interests and generates a reading list (Markdown) and calendar (ICS) for the sessions you should attend.

## Setup

```bash
pip install rank_bm25 icalendar
```

## Getting the conference data

Most ML conferences (ICML, NeurIPS, ICLR, etc.) use the same virtual site platform. The paper schedule is served as a JSON file that you can download directly.

To find the JSON URL for any conference:

1. Go to the conference's paper listing page, e.g. `https://icml.cc/virtual/2026/papers.html`
2. Open the browser DevTools (F12) → Network tab
3. Reload the page and look for a `.json` request containing the paper data
4. Download it:

```bash
wget https://icml.cc/static/virtual/data/icml-2026-orals-posters.json
```

For a different conference, replace the base URL. For example, NeurIPS might look like:
```
https://neurips.cc/static/virtual/data/neurips-2026-orals-posters.json
```

The exact filename varies, but the DevTools Network tab will show you the right one.

## Usage

Place the downloaded JSON in this directory, then describe your research interests to the agent. It will:

1. Search paper titles, authors, sessions, and keywords using BM25 ranking
2. Output `reading_list.md` with ranked papers and metadata
3. Output `schedule.ics` that you can import into Google Calendar, Apple Calendar, Outlook, etc.

## How it works

The agent tokenizes your interest description and runs BM25 (Okapi) against all paper entries. Papers are ranked by relevance, and the top matches become your reading list. Each paper with a scheduled session time gets an ICS calendar event so you know when and where to show up.

See `SKILL.md` for the full agent instructions and code snippets.
