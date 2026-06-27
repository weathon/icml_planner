#!/usr/bin/env python3
"""Render annotated candidates into reading_list.md, maybe_relevant.md, and schedule.ics."""

import argparse
import json
from datetime import datetime
from icalendar import Calendar, Event


def render_markdown(papers, title, description=None):
    lines = [f"# {title}\n"]
    if description:
        lines.append(f"{description}\n")
    for p in papers:
        lines.append(f"### {p['title']}\n")
        lines.append(f"- **Authors**: {', '.join(p['authors'])}\n")
        lines.append(f"- **Type**: {p['event_type']} | **Decision**: {p['decision']}\n")
        if p.get("session"):
            lines.append(f"- **Session**: {p['session']}\n")
        if p.get("starttime"):
            lines.append(f"- **Time**: {p['starttime']} — {p['endtime']}\n")
        if p.get("room_name"):
            lines.append(f"- **Room**: {p['room_name']}\n")
        if p.get("paper_url"):
            pdf_url = p['paper_url'].replace("openreview.net/forum", "openreview.net/pdf")
            lines.append(f"- **Paper**: {pdf_url}\n")
        if p.get("abstract"):
            lines.append(f"- **Abstract**: {p['abstract'][:300]}...\n")
        if p.get("reason"):
            lines.append(f"- **Note**: {p['reason']}\n")
        lines.append(f"- **Relevance score**: {p['score']}\n")
        lines.append("")
    return "\n".join(lines)


def render_ics(papers):
    cal = Calendar()
    cal.add("prodid", "-//Conference Planner//EN")
    cal.add("version", "2.0")

    for p in papers:
        if not p.get("starttime") or not p.get("endtime"):
            continue
        ev = Event()
        ev.add("summary", p["title"])
        ev.add("dtstart", datetime.fromisoformat(p["starttime"]))
        ev.add("dtend", datetime.fromisoformat(p["endtime"]))
        desc = f"Authors: {', '.join(p['authors'])}"
        if p.get("abstract"):
            desc += f"\n\n{p['abstract'][:500]}"
        if p.get("paper_url"):
            desc += f"\n\n{p['paper_url'].replace('openreview.net/forum', 'openreview.net/pdf')}"
        desc += f"\nType: {p['event_type']} | Decision: {p['decision']}"
        ev.add("description", desc)
        if p.get("room_name"):
            ev.add("location", p["room_name"])
        cal.add_component(ev)

    return cal.to_ical()


def main():
    parser = argparse.ArgumentParser(description="Render annotated candidates into output files")
    parser.add_argument("candidates", help="Annotated candidates JSON (with status field)")
    parser.add_argument("--reading-list", default="reading_list.md")
    parser.add_argument("--maybe", default="maybe_relevant.md")
    parser.add_argument("--ics", default="schedule.ics")
    args = parser.parse_args()

    with open(args.candidates) as f:
        candidates = json.load(f)

    confirmed = [p for p in candidates if p.get("status") == "confirmed"]
    rejected = [p for p in candidates if p.get("status") == "rejected"]
    pending = [p for p in candidates if p.get("status") == "pending"]

    if pending:
        print(f"Warning: {len(pending)} papers still have status 'pending' — treating as confirmed")
        confirmed.extend(pending)

    confirmed.sort(key=lambda p: p["score"], reverse=True)
    rejected.sort(key=lambda p: p["score"], reverse=True)

    with open(args.reading_list, "w") as f:
        f.write(render_markdown(confirmed, "Conference Reading List"))
    print(f"  {args.reading_list}: {len(confirmed)} papers")

    with open(args.maybe, "w") as f:
        f.write(render_markdown(
            rejected,
            "Maybe Relevant — Human Review Needed",
            "These papers matched the keyword search but were judged not directly relevant.",
        ))
    print(f"  {args.maybe}: {len(rejected)} papers")

    ics_data = render_ics(confirmed)
    with open(args.ics, "wb") as f:
        f.write(ics_data)
    scheduled = sum(1 for p in confirmed if p.get("starttime"))
    print(f"  {args.ics}: {scheduled} calendar events")


if __name__ == "__main__":
    main()
