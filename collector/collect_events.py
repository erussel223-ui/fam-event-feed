import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# FREEDMEN AGENDA LEAGUE OF MICHIGAN
# PUBLIC ENGAGEMENT EVENT COLLECTOR
# ============================================================
#
# PURPOSE:
# Collect public political, civic, government, community,
# and advocacy events that may be useful to FAM members.
#
# INITIAL COUNTIES:
# - Ingham
# - Wayne
# - Oakland
# - Washtenaw
#
# The collector will eventually pull events from multiple
# sources, standardize them, remove expired events and
# duplicates, sort them chronologically, and write the
# results to events.json.
#
# ============================================================


# ============================================================
# GLOBAL SETTINGS
# ============================================================

TIMEZONE = ZoneInfo("America/Detroit")

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_FILE = ROOT_DIR / "events.json"


# ============================================================
# SOURCE CONFIGURATION
# ============================================================
#
# Multiple sources may be monitored for the same county.
#
# source_type values may include:
#
# political
# government
# community
# civic
# college
# black-community
# legislative
#
# ============================================================

SOURCES = [


    # ========================================================
    # INGHAM COUNTY
    # ========================================================

    {
        "id": "ingham-democrats",
        "county": "Ingham",
        "name": "Ingham County Democratic Party",
        "url": "",
        "enabled": True,
        "source_type": "political"
    },


    {
        "id": "ingham-county-government",
        "county": "Ingham",
        "name": "Ingham County Government",
        "url": "https://www.ingham.org/",
        "enabled": True,
        "source_type": "government"
    },


    {
        "id": "ingham-democratic-caucus",
        "county": "Ingham",
        "name": "Ingham County Democratic Caucus",
        "url": (
            "https://docs.ingham.org/"
            "departments_and_officials/"
            "county_clerk/democratic_caucus.php"
        ),
        "enabled": True,
        "source_type": "government"
    },


    # ========================================================
    # WAYNE COUNTY
    # ========================================================

    {
        "id": "wayne-county-government",
        "county": "Wayne",
        "name": "Wayne County, Michigan",
        "url": "https://www.waynecountymi.gov/",
        "enabled": True,
        "source_type": "government"
    },


    {
        "id": "wayne-democratic-precinct-delegates",
        "county": "Wayne",
        "name": "Wayne County Democratic Precinct Delegates",
        "url": "https://miwcpd.com/",
        "enabled": True,
        "source_type": "political"
    },


    # ========================================================
    # OAKLAND COUNTY
    # ========================================================

    {
        "id": "oakland-democrats",
        "county": "Oakland",
        "name": "Oakland County Democratic Party",
        "url": (
            "https://www.oaklandcountydemocrats.org/events"
        ),
        "enabled": True,
        "source_type": "political"
    },


    # ========================================================
    # WASHTENAW COUNTY
    # ========================================================

    {
        "id": "washtenaw-democrats",
        "county": "Washtenaw",
        "name": "Washtenaw County Democratic Party",
        "url": (
            "https://www.washtenawdems.org/calendar/list/"
        ),
        "enabled": True,
        "source_type": "political"
    }

]


# ============================================================
# SOURCE HELPERS
# ============================================================

def get_source(source_id):
    """
    Returns a configured source by its ID.
    """

    for source in SOURCES:

        if source["id"] == source_id:
            return source

    return None


def source_is_enabled(source_id):
    """
    Checks whether a source exists and is enabled.
    """

    source = get_source(source_id)

    if not source:
        return False

    return source.get("enabled", False)


# ============================================================
# STANDARD EVENT STRUCTURE
# ============================================================
#
# Every source will eventually be converted into this same
# structure so Squarespace does not need to understand the
# different formats used by the source websites.
#
# ============================================================

def create_event(
    title,
    county,
    date,
    time="",
    end_time="",
    location="",
    city="",
    host="",
    event_type="Public Event",
    category="civic",
    source_name="",
    source_url="",
    event_url="",
    description=""
):

    return {

        "title": title,

        "county": county,

        "date": date,

        "time": time,

        "end_time": end_time,

        "location": location,

        "city": city,

        "host": host,

        "type": event_type,

        "category": category,

        "source_name": source_name,

        "source_url": source_url,

        "event_url": event_url,

        "description": description

    }


# ============================================================
# INGHAM COUNTY
# ============================================================

def collect_ingham_democratic_party_events():
    """
    Ingham County Democratic Party.

    The official event-calendar endpoint still needs to be
    confirmed before website-specific extraction is enabled.

    This function remains active in the architecture so the
    source can be added without changing the Squarespace feed.
    """

    source = get_source(
        "ingham-democrats"
    )

    if not source:
        return []

    if not source.get("enabled"):
        return []

    if not source.get("url"):
        print(
            "Ingham Democratic Party: "
            "calendar URL awaiting confirmation."
        )

        return []

    return []


def collect_ingham_government_events():
    """
    General Ingham County public-event source.

    Website-specific parsing will be added after the automated
    workflow itself has been confirmed.
    """

    source = get_source(
        "ingham-county-government"
    )

    if not source_is_enabled(
        "ingham-county-government"
    ):
        return []

    return []


def collect_ingham_democratic_caucus_events():
    """
    Ingham County Democratic Caucus public meetings.

    This source is separated from the general county website
    because it has its own public meeting page.
    """

    source = get_source(
        "ingham-democratic-caucus"
    )

    if not source_is_enabled(
        "ingham-democratic-caucus"
    ):
        return []

    return []


def collect_ingham_events():
    """
    Master Ingham County collector.
    """

    events = []

    collectors = [

        collect_ingham_democratic_party_events,

        collect_ingham_government_events,

        collect_ingham_democratic_caucus_events

    ]

    for collector in collectors:

        try:

            collected = collector()

            events.extend(
                collected
            )

        except Exception as error:

            print(
                f"Ingham source error "
                f"({collector.__name__}): "
                f"{error}"
            )

    return events


# ============================================================
# WAYNE COUNTY
# ============================================================

def collect_wayne_government_events():
    """
    Wayne County, Michigan government events.

    This source can eventually include public meetings,
    resource fairs, public forums and other engagement
    opportunities.
    """

    source = get_source(
        "wayne-county-government"
    )

    if not source_is_enabled(
        "wayne-county-government"
    ):
        return []

    return []


def collect_wayne_precinct_delegate_events():
    """
    Wayne County Democratic Precinct Delegates.

    IMPORTANT:
    This source is intended for Wayne County, MICHIGAN.

    It prevents the collector from accidentally using similarly
    named Wayne County Democratic organizations in other states.
    """

    source = get_source(
        "wayne-democratic-precinct-delegates"
    )

    if not source_is_enabled(
        "wayne-democratic-precinct-delegates"
    ):
        return []

    return []


def collect_wayne_events():
    """
    Master Wayne County collector.
    """

    events = []

    collectors = [

        collect_wayne_government_events,

        collect_wayne_precinct_delegate_events

    ]

    for collector in collectors:

        try:

            collected = collector()

            events.extend(
                collected
            )

        except Exception as error:

            print(
                f"Wayne source error "
                f"({collector.__name__}): "
                f"{error}"
            )

    return events


# ============================================================
# OAKLAND COUNTY
# ============================================================

def collect_oakland_democratic_party_events():
    """
    Oakland County Democratic Party event collector.

    Website-specific parsing will be added in the next stage.
    """

    source = get_source(
        "oakland-democrats"
    )

    if not source_is_enabled(
        "oakland-democrats"
    ):
        return []

    return []


def collect_oakland_events():
    """
    Master Oakland County collector.
    """

    events = []

    try:

        events.extend(
            collect_oakland_democratic_party_events()
        )

    except Exception as error:

        print(
            "Oakland source error: "
            f"{error}"
        )

    return events


# ============================================================
# WASHTENAW COUNTY
# ============================================================

def collect_washtenaw_democratic_party_events():
    """
    Washtenaw County Democratic Party event collector.

    Website-specific parsing will be added in the next stage.
    """

    source = get_source(
        "washtenaw-democrats"
    )

    if not source_is_enabled(
        "washtenaw-democrats"
    ):
        return []

    return []


def collect_washtenaw_events():
    """
    Master Washtenaw County collector.
    """

    events = []

    try:

        events.extend(
            collect_washtenaw_democratic_party_events()
        )

    except Exception as error:

        print(
            "Washtenaw source error: "
            f"{error}"
        )

    return events


# ============================================================
# VALIDATE EVENTS
# ============================================================

def validate_events(events):
    """
    Removes malformed records.

    At minimum, an event needs:
    - title
    - county
    - date
    """

    valid_events = []

    allowed_counties = {
        "ingham",
        "wayne",
        "oakland",
        "washtenaw"
    }

    for event in events:

        title = str(
            event.get(
                "title",
                ""
            )
        ).strip()

        county = str(
            event.get(
                "county",
                ""
            )
        ).strip()

        date = str(
            event.get(
                "date",
                ""
            )
        ).strip()

        if not title:
            continue

        if not county:
            continue

        if county.lower() not in allowed_counties:
            continue

        if not date:
            continue

        try:

            datetime.strptime(
                date,
                "%Y-%m-%d"
            )

        except ValueError:

            print(
                "Invalid event date skipped: "
                f"{title} ({date})"
            )

            continue

        valid_events.append(
            event
        )

    return valid_events


# ============================================================
# REMOVE EXPIRED EVENTS
# ============================================================

def remove_expired_events(events):
    """
    Removes events after their calendar date has passed.

    Events occurring today remain visible.
    """

    today = datetime.now(
        TIMEZONE
    ).date()

    upcoming = []

    for event in events:

        try:

            event_date = datetime.strptime(
                event["date"],
                "%Y-%m-%d"
            ).date()

        except (
            ValueError,
            KeyError,
            TypeError
        ):

            continue

        if event_date >= today:

            upcoming.append(
                event
            )

    return upcoming


# ============================================================
# REMOVE DUPLICATE EVENTS
# ============================================================

def remove_duplicates(events):
    """
    Prevents the same event from appearing multiple times.

    This becomes particularly important when an event appears
    on both a county-government website and a political
    organization's calendar.
    """

    unique_events = []

    seen = set()

    for event in events:

        title = (
            event
            .get(
                "title",
                ""
            )
            .strip()
            .lower()
        )

        date = event.get(
            "date",
            ""
        )

        county = (
            event
            .get(
                "county",
                ""
            )
            .strip()
            .lower()
        )

        city = (
            event
            .get(
                "city",
                ""
            )
            .strip()
            .lower()
        )

        key = (
            title,
            date,
            county,
            city
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_events.append(
            event
        )

    return unique_events


# ============================================================
# SORT EVENTS
# ============================================================

def sort_events(events):
    """
    Sorts events from soonest to latest.
    """

    return sorted(

        events,

        key=lambda event: (

            event.get(
                "date",
                "9999-12-31"
            ),

            event.get(
                "time",
                ""
            ),

            event.get(
                "title",
                ""
            )

        )

    )


# ============================================================
# COUNT EVENTS BY COUNTY
# ============================================================

def get_county_counts(events):

    counts = {

        "Ingham": 0,

        "Wayne": 0,

        "Oakland": 0,

        "Washtenaw": 0

    }

    for event in events:

        county = event.get(
            "county"
        )

        if county in counts:

            counts[county] += 1

    return counts


# ============================================================
# ACTIVE SOURCE INFORMATION
# ============================================================

def get_source_status():

    status = []

    for source in SOURCES:

        status.append({

            "id":
                source.get(
                    "id",
                    ""
                ),

            "county":
                source.get(
                    "county",
                    ""
                ),

            "name":
                source.get(
                    "name",
                    ""
                ),

            "source_type":
                source.get(
                    "source_type",
                    ""
                ),

            "enabled":
                source.get(
                    "enabled",
                    False
                ),

            "configured":
                bool(
                    source.get(
                        "url"
                    )
                )

        })

    return status


# ============================================================
# WRITE JSON FEED
# ============================================================

def write_event_feed(events):

    now = datetime.now(
        TIMEZONE
    )

    county_counts = (
        get_county_counts(
            events
        )
    )

    feed = {

        "organization":
            "Freedmen Agenda League of Michigan",

        "feed":
            "Public Engagement Opportunities",

        "last_updated":
            now.isoformat(),

        "timezone":
            "America/Detroit",

        "event_count":
            len(events),

        "counties_tracked": [

            "Ingham",

            "Wayne",

            "Oakland",

            "Washtenaw"

        ],

        "county_counts":
            county_counts,

        "sources":
            get_source_status(),

        "events":
            events

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

    print()

    print(
        "=========================================="
    )

    print(
        "FAM EVENT FEED UPDATED"
    )

    print(
        "=========================================="
    )

    print(
        f"Total upcoming events: "
        f"{len(events)}"
    )

    print()

    print(
        "County totals:"
    )

    for county, count in county_counts.items():

        print(
            f"  {county}: {count}"
        )

    print()

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print(
        "=========================================="
    )


# ============================================================
# RUN ONE COUNTY COLLECTOR
# ============================================================

def run_collector(
    county_name,
    collector
):

    try:

        print()

        print(
            f"Checking {county_name} County..."
        )

        events = collector()

        print(
            f"{county_name}: "
            f"{len(events)} events collected."
        )

        return events

    except Exception as error:

        print(
            f"{county_name} collector failed: "
            f"{error}"
        )

        return []


# ============================================================
# MAIN COLLECTOR
# ============================================================

def main():

    print(
        "=========================================="
    )

    print(
        "FAM PUBLIC ENGAGEMENT EVENT COLLECTOR"
    )

    print(
        "=========================================="
    )

    print(
        "Starting event collection..."
    )

    all_events = []


    # --------------------------------------------------------
    # INGHAM
    # --------------------------------------------------------

    all_events.extend(

        run_collector(
            "Ingham",
            collect_ingham_events
        )

    )


    # --------------------------------------------------------
    # WAYNE
    # --------------------------------------------------------

    all_events.extend(

        run_collector(
            "Wayne",
            collect_wayne_events
        )

    )


    # --------------------------------------------------------
    # OAKLAND
    # --------------------------------------------------------

    all_events.extend(

        run_collector(
            "Oakland",
            collect_oakland_events
        )

    )


    # --------------------------------------------------------
    # WASHTENAW
    # --------------------------------------------------------

    all_events.extend(

        run_collector(
            "Washtenaw",
            collect_washtenaw_events
        )

    )


    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------

    print()

    print(
        "Validating events..."
    )

    all_events = validate_events(
        all_events
    )


    print(
        "Removing expired events..."
    )

    all_events = remove_expired_events(
        all_events
    )


    print(
        "Removing duplicate events..."
    )

    all_events = remove_duplicates(
        all_events
    )


    print(
        "Sorting upcoming events..."
    )

    all_events = sort_events(
        all_events
    )


    # --------------------------------------------------------
    # WRITE FEED
    # --------------------------------------------------------

    write_event_feed(
        all_events
    )


    print()

    print(
        "Event collection complete."
    )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()
