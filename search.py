#!/usr/bin/env python3
"""BM25 search over conference paper titles and abstracts."""

import argparse
import json
import sys
from rank_bm25 import BM25Okapi


def main():
    parser = argparse.ArgumentParser(description="Search conference papers by keyword/BM25")
    parser.add_argument("query", help="Search query (natural language)")
    parser.add_argument("--data", default="icml-2026-orals-posters.json", help="Conference JSON file")
    parser.add_argument("--top-k", type=int, default=50, help="Number of results to return")
    parser.add_argument("--out", default="candidates.json", help="Output file for candidates")
    parser.add_argument("--orals-only", action="store_true", help="Only search oral presentations")
    args = parser.parse_args()

    with open(args.data) as f:
        papers = json.load(f)["results"]

    if args.orals_only:
        papers = [p for p in papers if p.get("event_type") == "Oral"]

    corpus = []
    for p in papers:
        authors_str = " ".join(a["fullname"] for a in p["authors"])
        abstract = p.get("abstract", "")
        text = f"{p['name']} {abstract} {authors_str} {p.get('session', '')} {' '.join(p.get('keywords', []))}"
        corpus.append(text.lower().split())

    bm25 = BM25Okapi(corpus)
    tokens = args.query.lower().split()
    scores = bm25.get_scores(tokens)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:args.top_k]
    candidates = []
    for i, score in ranked:
        if score <= 0:
            continue
        p = papers[i]
        candidates.append({
            "id": p["id"],
            "title": p["name"],
            "abstract": p.get("abstract", ""),
            "authors": [a["fullname"] for a in p["authors"]],
            "decision": p.get("decision"),
            "event_type": p.get("event_type"),
            "session": p.get("session"),
            "starttime": p.get("starttime"),
            "endtime": p.get("endtime"),
            "room_name": p.get("room_name"),
            "paper_url": p.get("paper_url"),
            "score": round(score, 4),
            "status": "pending",
            "reason": "",
        })

    with open(args.out, "w") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)

    print(f"Found {len(candidates)} candidates (query: \"{args.query}\")", file=sys.stderr)
    print(f"Saved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
