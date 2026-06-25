import openreview
import json
from urllib.parse import urlparse, parse_qs

client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')

venues = [
    'ICML.cc/2026/Conference',
    'ICML.cc/2026/Position_Paper_Track',
]

print("Fetching abstracts from OpenReview...")
abstracts_by_id = {}
abstracts_by_title = {}
for venue_id in venues:
    notes = client.get_all_notes(content={'venueid': venue_id})
    print(f"  {venue_id}: {len(notes)} papers")
    for note in notes:
        abstract = note.content.get('abstract', {}).get('value', '')
        abstracts_by_id[note.id] = abstract
        title = note.content.get('title', {}).get('value', '').strip().lower()
        if title:
            abstracts_by_title[title] = abstract

print(f"Total abstracts: {len(abstracts_by_id)}")

with open("icml-2026-orals-posters.json") as f:
    data = json.load(f)

matched_id, matched_title, unmatched = 0, 0, 0
for paper in data["results"]:
    url = paper.get("paper_url", "") or ""
    forum_id = None
    if "openreview.net/forum" in url:
        parsed = parse_qs(urlparse(url).query)
        forum_id = parsed.get("id", [None])[0]

    if forum_id and forum_id in abstracts_by_id:
        paper["abstract"] = abstracts_by_id[forum_id]
        matched_id += 1
    elif paper["name"].strip().lower() in abstracts_by_title:
        paper["abstract"] = abstracts_by_title[paper["name"].strip().lower()]
        matched_title += 1
    else:
        paper["abstract"] = ""
        unmatched += 1

print(f"Matched by ID: {matched_id}, by title: {matched_title}, no abstract: {unmatched}")

with open("icml-2026-orals-posters.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved merged JSON.")
