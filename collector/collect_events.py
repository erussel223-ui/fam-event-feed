import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


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
# CURRENT LIVE COLLECTION:
# - Washtenaw County Democratic Party
#
# Additional live collectors will be added for:
# - Oakland
# - Ingham
# - Wayne
#
# ============================================================


# ============================================================
# GLOBAL SETTINGS
# ============================================================

TIMEZONE = ZoneInfo("America/Detroit")

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_FILE = ROOT_DIR / "events.json"

REQUEST_TIMEOUT = 30


HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36 "
        "FAM-Public-Engagement-Collector/1.0"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "*/*;q=0.8"
    ),

    "Accept-Language":
        "en-US,en;q=0.9"

}


# ============================================================
# SOURCE CONFIGURATION
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
        "enabled": False,
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
# GENERAL HELPERS
# ============================================================

def get_source(source_id):

    for source in SOURCES:

        if source.get("id") == source_id:
            return source

    return None


def source_is_enabled(source_id):

    source = get_source(source_id)

    if not source:
        return False

    return bool(
        source.get(
            "enabled",
            False
        )
    )


def clean_text(value):

    if value is None:
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def download_page(url):

    print(
        f"  Requesting: {url}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT
    )

    print(
        f"  HTTP status: "
        f"{response.status_code}"
    )

    response.raise_for_status()

    print(
        f"  Downloaded "
        f"{len(response.text):,} characters."
    )

    return response.text


# ============================================================
# EVENT TYPE CLASSIFICATION
# ============================================================
#
# These are neutral classifications.
# The collector does NOT assign political priority.
#
# ============================================================

def classify_event(
    title,
    description=""
):

    text = clean_text(
        f"{title} {description}"
    ).lower()


    if any(
        phrase in text
        for phrase in [
            "town hall",
            "townhall"
        ]
    ):

        return (
            "Town Hall",
            "town-hall"
        )


    if any(
        phrase in text
        for phrase in [
            "county committee",
            "monthly meeting",
            "committee meeting",
            "club meeting",
            "membership meeting",
            "executive committee",
            "general membership"
        ]
    ):

        return (
            "Party Meeting",
            "party-meeting"
        )


    if any(
        phrase in text
        for phrase in [
            "voter registration",
            "register voters",
            "voter outreach",
            "voter education"
        ]
    ):

        return (
            "Voter Outreach",
            "voter-outreach"
        )


    if any(
        phrase in text
        for phrase in [
            "door knock",
            "door knocking",
            "knocking doors",
            "knocking on doors",
            "canvass",
            "canvassing"
        ]
    ):

        return (
            "Canvassing",
            "canvassing"
        )


    if any(
        phrase in text
        for phrase in [
            "postcard",
            "phone bank",
            "volunteer"
        ]
    ):

        return (
            "Volunteer",
            "volunteer"
        )


    if any(
        phrase in text
        for phrase in [
            "rally",
            "protest",
            "demonstration",
            "march"
        ]
    ):

        return (
            "Public Demonstration",
            "demonstration"
        )


    if any(
        phrase in text
        for phrase in [
            "training",
            "workshop",
            "seminar"
        ]
    ):

        return (
            "Training / Workshop",
            "training"
        )


    if any(
        phrase in text
        for phrase in [
            "candidate forum",
            "candidate event",
            "candidate meet",
            "meet the candidate"
        ]
    ):

        return (
            "Candidate Event",
            "candidate-event"
        )


    if any(
        phrase in text
        for phrase in [
            "public hearing",
            "commission meeting",
            "board meeting",
            "city council",
            "county commission"
        ]
    ):

        return (
            "Government Meeting",
            "government-meeting"
        )


    if any(
        phrase in text
        for phrase in [
            "farmer's market",
            "farmers market",
            "festival",
            "community event",
            "resource fair"
        ]
    ):

        return (
            "Community Event",
            "community"
        )


    return (
        "Public Event",
        "civic"
    )


# ============================================================
# STANDARD EVENT STRUCTURE
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

    title = clean_text(title)

    county = clean_text(county)

    date = clean_text(date)

    time = clean_text(time)

    end_time = clean_text(end_time)

    location = clean_text(location)

    city = clean_text(city)

    host = clean_text(host)

    event_type = clean_text(event_type)

    category = clean_text(category)

    source_name = clean_text(source_name)

    source_url = clean_text(source_url)

    event_url = clean_text(event_url)

    description = clean_text(description)


    unique_string = (
        f"{title}|"
        f"{county}|"
        f"{date}|"
        f"{time}|"
        f"{event_url}"
    )


    event_id = hashlib.sha1(
        unique_string.encode(
            "utf-8"
        )
    ).hexdigest()[:16]


    return {

        "id":
            event_id,

        "title":
            title,

        "county":
            county,

        "date":
            date,

        "time":
            time,

        "end_time":
            end_time,

        "location":
            location,

        "city":
            city,

        "host":
            host,

        "type":
            event_type,

        "category":
            category,

        "source_name":
            source_name,

        "source_url":
            source_url,

        "event_url":
            event_url,

        "description":
            description

    }


# ============================================================
# DATE HELPERS
# ============================================================

MONTHS = {

    "january": 1,

    "february": 2,

    "march": 3,

    "april": 4,

    "may": 5,

    "june": 6,

    "july": 7,

    "august": 8,

    "september": 9,

    "october": 10,

    "november": 11,

    "december": 12

}


def parse_event_date(text):

    text = clean_text(text)

    if not text:
        return ""


    # --------------------------------------------------------
    # Example:
    # September 15, 2026
    # --------------------------------------------------------

    pattern_with_year = (
        r"("
        + "|".join(MONTHS.keys())
        + r")"
        r"\s+"
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r",?\s+"
        r"(20\d{2})"
    )


    match = re.search(
        pattern_with_year,
        text,
        re.IGNORECASE
    )


    if match:

        month = MONTHS[
            match.group(1).lower()
        ]

        day = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )


        try:

            parsed = datetime(
                year,
                month,
                day
            )


            return parsed.strftime(
                "%Y-%m-%d"
            )


        except ValueError:

            return ""


    # --------------------------------------------------------
    # Example:
    # September 15
    # --------------------------------------------------------

    pattern_without_year = (
        r"("
        + "|".join(MONTHS.keys())
        + r")"
        r"\s+"
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?"
    )


    match = re.search(
        pattern_without_year,
        text,
        re.IGNORECASE
    )


    if not match:
        return ""


    month = MONTHS[
        match.group(1).lower()
    ]

    day = int(
        match.group(2)
    )


    today = datetime.now(
        TIMEZONE
    ).date()


    year = today.year


    try:

        candidate = datetime(
            year,
            month,
            day
        ).date()


    except ValueError:

        return ""


    # If the calendar has rolled into the next year,
    # don't incorrectly assign the old year.

    if (
        candidate - today
    ).days < -120:

        year += 1


    try:

        parsed = datetime(
            year,
            month,
            day
        )


    except ValueError:

        return ""


    return parsed.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# TIME HELPERS
# ============================================================

def normalize_time(value):

    value = clean_text(value)

    if not value:
        return ""


    value = (
        value
        .replace(".", "")
        .upper()
    )


    formats = [

        "%I:%M %p",

        "%I %p"

    ]


    for fmt in formats:

        try:

            parsed = datetime.strptime(
                value,
                fmt
            )


            return parsed.strftime(
                "%H:%M"
            )


        except ValueError:

            continue


    return value


def parse_event_times(text):

    text = clean_text(text)


    pattern = (
        r"(?:@\s*)?"
        r"(\d{1,2}"
        r"(?::\d{2})?"
        r"\s*"
        r"[ap]\.?m\.?)"
        r"(?:"
        r"\s*(?:-|–|—|to)\s*"
        r"(\d{1,2}"
        r"(?::\d{2})?"
        r"\s*"
        r"[ap]\.?m\.?)"
        r")?"
    )


    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )


    if not match:

        return (
            "",
            ""
        )


    start = normalize_time(
        match.group(1)
    )


    end = ""


    if match.group(2):

        end = normalize_time(
            match.group(2)
        )


    return (
        start,
        end
    )


# ============================================================
# WASHTENAW CITY DETECTION
# ============================================================

def detect_washtenaw_city(location):

    text = clean_text(
        location
    ).lower()


    city_map = {

        "ann arbor":
            "Ann Arbor",

        "ypsilanti":
            "Ypsilanti",

        "dexter":
            "Dexter",

        "chelsea":
            "Chelsea",

        "saline":
            "Saline",

        "manchester":
            "Manchester",

        "milan":
            "Milan",

        "whitmore lake":
            "Whitmore Lake",

        "pittsfield":
            "Pittsfield Township",

        "superior township":
            "Superior Township"

    }


    for keyword, city in city_map.items():

        if keyword in text:

            return city


    return ""


# ============================================================
# INGHAM COUNTY
# ============================================================

def collect_ingham_democratic_party_events():

    source = get_source(
        "ingham-democrats"
    )


    if not source:
        return []


    if not source.get(
        "enabled",
        False
    ):

        print(
            "  Ingham Democratic Party: "
            "calendar URL awaiting confirmation."
        )

        return []


    if not source.get(
        "url",
        ""
    ):

        print(
            "  Ingham Democratic Party: "
            "calendar URL awaiting confirmation."
        )

        return []


    return []


def collect_ingham_government_events():

    if not source_is_enabled(
        "ingham-county-government"
    ):

        return []


    # Live parser will be added later.

    return []


def collect_ingham_democratic_caucus_events():

    if not source_is_enabled(
        "ingham-democratic-caucus"
    ):

        return []


    # Live parser will be added later.

    return []


def collect_ingham_events():

    events = []


    collectors = [

        collect_ingham_democratic_party_events,

        collect_ingham_government_events,

        collect_ingham_democratic_caucus_events

    ]


    for collector in collectors:

        try:

            events.extend(
                collector()
            )


        except Exception as error:

            print(
                "Ingham source error "
                f"({collector.__name__}): "
                f"{error}"
            )


    return events


# ============================================================
# WAYNE COUNTY
# ============================================================

def collect_wayne_government_events():

    if not source_is_enabled(
        "wayne-county-government"
    ):

        return []


    # Live parser will be added later.

    return []


def collect_wayne_precinct_delegate_events():

    if not source_is_enabled(
        "wayne-democratic-precinct-delegates"
    ):

        return []


    # Live parser will be added later.

    return []


def collect_wayne_events():

    events = []


    collectors = [

        collect_wayne_government_events,

        collect_wayne_precinct_delegate_events

    ]


    for collector in collectors:

        try:

            events.extend(
                collector()
            )


        except Exception as error:

            print(
                "Wayne source error "
                f"({collector.__name__}): "
                f"{error}"
            )


    return events


# ============================================================
# OAKLAND COUNTY
# ============================================================

def collect_oakland_democratic_party_events():

    source = get_source(
        "oakland-democrats"
    )


    if not source:
        return []


    if not source_is_enabled(
        "oakland-democrats"
    ):

        return []


    # Live Oakland parser will be added after
    # Washtenaw has been verified.

    return []


def collect_oakland_events():

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
# LIVE EVENT COLLECTOR
# ============================================================

def collect_washtenaw_democratic_party_events():

    source = get_source(
        "washtenaw-democrats"
    )


    if not source:

        print(
            "  Washtenaw source configuration "
            "not found."
        )

        return []


    if not source.get(
        "enabled",
        False
    ):

        print(
            "  Washtenaw source is disabled."
        )

        return []


    source_url = source.get(
        "url",
        ""
    )


    if not source_url:

        print(
            "  Washtenaw source URL is missing."
        )

        return []


    # ========================================================
    # THIS SHOULD NOW APPEAR IN GITHUB ACTIONS
    # ========================================================

    print(
        "  Downloading Washtenaw calendar..."
    )


    html = download_page(
        source_url
    )


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    events = []


    # ========================================================
    # THE EVENTS CALENDAR / WORDPRESS SELECTORS
    # ========================================================

    selectors = [

        ".tribe-events-calendar-list__event-row",

        "article.tribe-events-calendar-list__event",

        ".tribe-events-calendar-list__event",

        "article.type-tribe_events",

        ".type-tribe_events"

    ]


    event_nodes = []


    for selector in selectors:

        nodes = soup.select(
            selector
        )


        if nodes:

            event_nodes = nodes


            print(
                f"  Working selector: "
                f"{selector}"
            )


            break


    print(
        f"  Found {len(event_nodes)} "
        "Washtenaw calendar records."
    )


    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    if not event_nodes:

        print(
            "  No event rows found using "
            "standard calendar selectors."
        )


        event_links = soup.select(
            "a[href*='/event/']"
        )


        print(
            f"  Diagnostic: found "
            f"{len(event_links)} links "
            "containing /event/."
        )


        page_title = ""


        if (
            soup.title
            and soup.title.string
        ):

            page_title = clean_text(
                soup.title.string
            )


        print(
            f"  Page title: {page_title}"
        )


    # ========================================================
    # PROCESS EVENT RECORDS
    # ========================================================

    for node in event_nodes:

        try:


            # ------------------------------------------------
            # TITLE + EVENT URL
            # ------------------------------------------------

            title_link = node.select_one(
                ".tribe-events-calendar-list__event-title a"
            )


            if not title_link:

                title_link = node.select_one(
                    "h3 a"
                )


            if not title_link:

                title_link = node.select_one(
                    "a[href*='/event/']"
                )


            if not title_link:

                continue


            title = clean_text(
                title_link.get_text(
                    " ",
                    strip=True
                )
            )


            if not title:

                continue


            event_url = urljoin(
                source_url,
                title_link.get(
                    "href",
                    ""
                )
            )


            # ------------------------------------------------
            # DATE + TIME
            # ------------------------------------------------

            event_date = ""

            start_time = ""

            end_time = ""


            time_elements = node.select(
                "time"
            )


            for time_element in time_elements:

                datetime_value = clean_text(
                    time_element.get(
                        "datetime",
                        ""
                    )
                )


                if not datetime_value:

                    continue


                # --------------------------------------------
                # ISO datetime
                # --------------------------------------------

                try:

                    iso_value = (
                        datetime_value
                        .replace(
                            "Z",
                            "+00:00"
                        )
                    )


                    parsed_datetime = (
                        datetime.fromisoformat(
                            iso_value
                        )
                    )


                    event_date = (
                        parsed_datetime.strftime(
                            "%Y-%m-%d"
                        )
                    )


                    if (
                        parsed_datetime.hour != 0
                        or
                        parsed_datetime.minute != 0
                    ):

                        start_time = (
                            parsed_datetime.strftime(
                                "%H:%M"
                            )
                        )


                    break


                except ValueError:

                    pass


                # --------------------------------------------
                # Plain YYYY-MM-DD
                # --------------------------------------------

                try:

                    parsed_date = (
                        datetime.strptime(
                            datetime_value[:10],
                            "%Y-%m-%d"
                        )
                    )


                    event_date = (
                        parsed_date.strftime(
                            "%Y-%m-%d"
                        )
                    )


                    break


                except ValueError:

                    continue


            # ------------------------------------------------
            # DISPLAYED DATE/TIME
            # ------------------------------------------------

            date_element = node.select_one(
                ".tribe-events-calendar-list__event-datetime"
            )


            date_text = ""


            if date_element:

                date_text = clean_text(
                    date_element.get_text(
                        " ",
                        strip=True
                    )
                )


            if not date_text:

                date_text = clean_text(
                    node.get_text(
                        " ",
                        strip=True
                    )
                )


            if not event_date:

                event_date = parse_event_date(
                    date_text
                )


            parsed_start, parsed_end = (
                parse_event_times(
                    date_text
                )
            )


            if parsed_start:

                start_time = parsed_start


            if parsed_end:

                end_time = parsed_end


            # ------------------------------------------------
            # LOCATION
            # ------------------------------------------------

            location = ""


            venue_selectors = [

                ".tribe-events-calendar-list__event-venue",

                ".tribe-events-calendar-list__event-venue-title",

                ".tribe-events-venue-details",

                ".tribe-address"

            ]


            for selector in venue_selectors:

                venue_element = (
                    node.select_one(
                        selector
                    )
                )


                if venue_element:

                    location = clean_text(
                        venue_element.get_text(
                            " ",
                            strip=True
                        )
                    )


                    if location:

                        break


            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = ""


            description_selectors = [

                ".tribe-events-calendar-list__event-description",

                ".tribe-events-content",

                ".tribe-events-calendar-list__event-details p"

            ]


            for selector in description_selectors:

                description_element = (
                    node.select_one(
                        selector
                    )
                )


                if description_element:

                    description = clean_text(
                        description_element.get_text(
                            " ",
                            strip=True
                        )
                    )


                    if description:

                        break


            # ------------------------------------------------
            # CITY
            # ------------------------------------------------

            city = detect_washtenaw_city(
                location
            )


            # ------------------------------------------------
            # EVENT TYPE
            # ------------------------------------------------

            event_type, category = (
                classify_event(
                    title,
                    description
                )
            )


            # ------------------------------------------------
            # DATE IS REQUIRED
            # ------------------------------------------------

            if not event_date:

                print(
                    "  Skipping event because "
                    "date could not be read: "
                    f"{title}"
                )

                continue


            # ------------------------------------------------
            # CREATE STANDARD EVENT
            # ------------------------------------------------

            event = create_event(

                title=title,

                county="Washtenaw",

                date=event_date,

                time=start_time,

                end_time=end_time,

                location=location,

                city=city,

                host=(
                    "Washtenaw County "
                    "Democratic Party Calendar"
                ),

                event_type=event_type,

                category=category,

                source_name=source.get(
                    "name",
                    ""
                ),

                source_url=source_url,

                event_url=event_url,

                description=description

            )


            events.append(
                event
            )


            print(
                "  Collected: "
                f"{event_date} | "
                f"{title}"
            )


        except Exception as error:

            print(
                "  Washtenaw event "
                "parse error: "
                f"{error}"
            )


    print(
        f"  Washtenaw parser produced "
        f"{len(events)} events."
    )


    return events


def collect_washtenaw_events():

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

    valid_events = []


    allowed_counties = {

        "ingham",

        "wayne",

        "oakland",

        "washtenaw"

    }


    for event in events:

        title = clean_text(
            event.get(
                "title",
                ""
            )
        )


        county = clean_text(
            event.get(
                "county",
                ""
            )
        )


        date = clean_text(
            event.get(
                "date",
                ""
            )
        )


        if not title:

            print(
                "Event skipped: missing title."
            )

            continue


        if (
            county.lower()
            not in allowed_counties
        ):

            print(
                "Event skipped: invalid county "
                f"for {title}."
            )

            continue


        if not date:

            print(
                "Event skipped: missing date "
                f"for {title}."
            )

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
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(events):

    unique_events = []

    seen = set()


    for event in events:

        event_url = clean_text(
            event.get(
                "event_url",
                ""
            )
        ).lower()


        title = clean_text(
            event.get(
                "title",
                ""
            )
        ).lower()


        date = clean_text(
            event.get(
                "date",
                ""
            )
        )


        county = clean_text(
            event.get(
                "county",
                ""
            )
        ).lower()


        if event_url:

            key = (
                "url",
                event_url
            )


        else:

            key = (
                "event",
                title,
                date,
                county
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

    return sorted(

        events,

        key=lambda event: (

            event.get(
                "date",
                "9999-12-31"
            ),

            (
                event.get(
                    "time",
                    ""
                )
                or
                "99:99"
            ),

            event.get(
                "title",
                ""
            )

        )

    )


# ============================================================
# COUNTY COUNTS
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
# CATEGORY COUNTS
# ============================================================

def get_category_counts(events):

    counts = {}


    for event in events:

        category = clean_text(
            event.get(
                "category",
                "civic"
            )
        )


        if not category:

            category = "civic"


        counts[category] = (
            counts.get(
                category,
                0
            )
            + 1
        )


    return counts


# ============================================================
# SOURCE STATUS
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
                        "url",
                        ""
                    )
                ),

            "url":
                source.get(
                    "url",
                    ""
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


    category_counts = (
        get_category_counts(
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

        "category_counts":
            category_counts,

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
        "Category totals:"
    )


    if category_counts:

        for category, count in category_counts.items():

            print(
                f"  {category}: {count}"
            )

    else:

        print(
            "  No event categories yet."
        )


    print()

    print(
        f"Output file: "
        f"{OUTPUT_FILE}"
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
            f"Checking "
            f"{county_name} County..."
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


    # ========================================================
    # INGHAM
    # ========================================================

    all_events.extend(

        run_collector(
            "Ingham",
            collect_ingham_events
        )

    )


    # ========================================================
    # WAYNE
    # ========================================================

    all_events.extend(

        run_collector(
            "Wayne",
            collect_wayne_events
        )

    )


    # ========================================================
    # OAKLAND
    # ========================================================

    all_events.extend(

        run_collector(
            "Oakland",
            collect_oakland_events
        )

    )


    # ========================================================
    # WASHTENAW
    # ========================================================

    all_events.extend(

        run_collector(
            "Washtenaw",
            collect_washtenaw_events
        )

    )


    # ========================================================
    # CLEAN DATA
    # ========================================================

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


    # ========================================================
    # WRITE FEED
    # ========================================================

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
