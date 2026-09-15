import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# FAM PUBLIC ENGAGEMENT EVENT COLLECTOR
# ============================================================
#
# This script will collect public event information from
# configured Michigan sources and create one standardized
# events.json feed for the FAM Squarespace member portal.
#
# Additional source collectors will be added below.
# ============================================================


TIMEZONE = ZoneInfo("America/Detroit")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / "events.json"


# ============================================================
# SOURCE CONFIGURATION
# ============================================================

SOURCES = [
    {
        "id": "ingham",
        "county": "Ingham",
        "name": "Ingham County Democratic Party",
        "url": "",
        "enabled": False
    },
    {
        "id": "wayne",
        "county": "Wayne",
        "name": "Wayne County Democratic Party",
        "url": "",
        "enabled": False
    },
    {
        "id": "oakland",
        "county": "Oakland",
        "name": "Oakland County Democratic Party",
        "url": "https://www.oaklandcountydemocrats.org/events",
        "enabled": True
    },
    {
        "id": "washtenaw",
        "county": "Washtenaw",
        "name": "Washtenaw County Democratic Party",
        "url": "https://www.washtenawdems.org/calendar/list/",
        "enabled": True
    }
]


# ============================================================
# EVENT STRUCTURE
# ============================================================

def create_event(
    title,
    county,
    date,
    time="",
    location="",
    host="",
    event_type="Public Event",
    source_name="",
    source_url="",
    description=""
):
    """
    Creates one standardized FAM event record.
    """

    return {
        "title": title,
        "county": county,
        "date": date,
        "time": time,
        "location": location,
        "host": host,
        "type": event_type,
        "source_name": source_name,
        "source_url": source_url,
        "description": description
    }


# ============================================================
# COLLECTORS
# ============================================================

def collect_oakland_events():
    """
    Oakland County collector.

    The website-specific extraction logic will be added
    after the base GitHub workflow is confirmed working.
    """

    return []


def collect_washtenaw_events():
    """
    Washtenaw County collector.

    The website-specific extraction logic will be added
    after the base GitHub workflow is confirmed working.
    """

    return []


def collect_ingham_events():
    """
    Ingham County collector.

    Source URL will be added after the official event
    calendar is confirmed.
    """

    return []


def collect_wayne_events():
    """
    Wayne County, Michigan collector.

    Source URL will be added only after confirming the
    correct Michigan organization/calendar.
    """

    return []


# ============================================================
# REMOVE EXPIRED EVENTS
# ============================================================

def remove_expired_events(events):
    """
    Removes events whose calendar date has already passed.
    """

    today = datetime.now(TIMEZONE).date()

    upcoming = []

    for event in events:

        try:
            event_date = datetime.strptime(
                event["date"],
                "%Y-%m-%d"
            ).date()

        except (ValueError, KeyError):
            continue

        if event_date >= today:
            upcoming.append(event)

    return upcoming


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(events):

    unique_events = []
    seen = set()

    for event in events:

        key = (
            event.get("title", "").strip().lower(),
            event.get("date", ""),
            event.get("county", "").strip().lower()
        )

        if key in seen:
            continue

        seen.add(key)
        unique_events.append(event)

    return unique_events


# ============================================================
# SORT EVENTS
# ============================================================

def sort_events(events):

    return sorted(
        events,
        key=lambda event: (
            event.get("date", "9999-12-31"),
            event.get("time", ""),
            event.get("title", "")
        )
    )


# ============================================================
# WRITE JSON FEED
# ============================================================

def write_event_feed(events):

    now = datetime.now(TIMEZONE)

    feed = {
        "last_updated": now.isoformat(),
        "timezone": "America/Detroit",
        "event_count": len(events),
        "counties": [
            "Ingham",
            "Wayne",
            "Oakland",
            "Washtenaw"
        ],
        "events": events
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            feed,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"FAM event feed updated with "
        f"{len(events)} upcoming events."
    )


# ============================================================
# MAIN COLLECTOR
# ============================================================

def main():

    print(
        "Starting FAM Public Engagement Event Collector..."
    )

    all_events = []

    collectors = [
        collect_ingham_events,
        collect_wayne_events,
        collect_oakland_events,
        collect_washtenaw_events
    ]

    for collector in collectors:

        try:

            events = collector()

            all_events.extend(events)

            print(
                f"{collector.__name__}: "
                f"{len(events)} events collected."
            )

        except Exception as error:

            print(
                f"{collector.__name__} failed: {error}"
            )

    all_events = remove_expired_events(
        all_events
    )

    all_events = remove_duplicates(
        all_events
    )

    all_events = sort_events(
        all_events
    )

    write_event_feed(
        all_events
    )

    print(
        "Event collection complete."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
