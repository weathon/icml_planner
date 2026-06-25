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

## Adding abstracts

The schedule JSON only has titles but not abstracts. Run `merge_abstracts.py` to fetch abstracts from OpenReview and add them to the JSON:

```bash
pip install openreview-py
python merge_abstracts.py
```

You'll need to edit the venue IDs in the script to match your conference. The script first joins on the `paper_url` field (OpenReview forum ID), then falls back to title matching for papers without an OpenReview URL. A small number of papers from journal tracks (TMLR, JMLR, ANN-STATS) are not hosted on OpenReview and will remain without abstracts.

## Usage

Place the downloaded JSON (with abstracts merged) in this directory, then describe your research interests to the agent. It will:

1. Search paper titles, abstracts, authors, and sessions using BM25 ranking
2. Verify each candidate to filter out false positives (keyword overlap without real relevance)
3. Output `reading_list.md` with confirmed relevant papers
4. Output `schedule.ics` that you can import into Google Calendar, Apple Calendar, Outlook, etc.
5. Output `maybe_relevant.md` with rejected candidates for human review

## How it works

The agent tokenizes your interest description and runs BM25 (Okapi) against all paper titles and abstracts. Candidates are then verified one by one (using subagents if available) to catch false positives where a keyword appears in a different context. Confirmed papers go into the reading list and calendar; borderline matches go into a separate file for you to skim.

See `SKILL.md` for the full agent instructions and code snippets.
