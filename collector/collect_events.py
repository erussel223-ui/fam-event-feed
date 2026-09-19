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

TIMEZONE = ZoneInfo("America/Detroit")
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / "events.json"
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36 "
        "FAM-Public-Engagement-Collector/1.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9"
}


# ============================================================
# SOURCE CONFIGURATION
# ============================================================

SOURCES = [

    # INGHAM
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

    # WAYNE
    {
        "id": "wayne-county-government",
        "county": "Wayne",
        "name": "Wayne County, Michigan",
        "url": "https://www.waynecountymi.gov/Events-directory",
        "enabled": False,
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

    # MICHIGAN DEMOCRATIC PARTY — STATEWIDE CONTROLShift FEED
    {
        "id": "mdp-controlshift",
        "county": "Statewide",
        "name": "Michigan Democratic Party",
        "url": "https://midems.controlshift.app/api/local.json",
        "enabled": True,
        "source_type": "political"
    },

    # OAKLAND
    {
        "id": "oakland-democrats",
        "county": "Oakland",
        "name": "Oakland County Democratic Party",
        "url": "https://www.oaklandcountydemocrats.org/events",
        "enabled": True,
        "source_type": "political"
    },

    # WASHTENAW
    {
        "id": "washtenaw-democrats",
        "county": "Washtenaw",
        "name": "Washtenaw County Democratic Party",
        "url": "https://www.washtenawdems.org/calendar/list/",
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
    return bool(source.get("enabled", False))


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def download_page(url):
    print(f"  Requesting: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT
    )

    print(f"  HTTP status: {response.status_code}")
    response.raise_for_status()

    print(
        f"  Downloaded {len(response.text):,} characters."
    )

    return response.text


# ============================================================
# EVENT CLASSIFICATION
# ============================================================

def classify_event(title, description=""):

    text = clean_text(
        f"{title} {description}"
    ).lower()

    if "town hall" in text or "townhall" in text:
        return "Town Hall", "town-hall"

    if any(
        phrase in text
        for phrase in [
            "county committee",
            "monthly meeting",
            "committee meeting",
            "club meeting",
            "membership meeting",
            "executive committee",
            "general membership",
            "roundtable"
        ]
    ):
        return "Party Meeting", "party-meeting"

    if any(
        phrase in text
        for phrase in [
            "voter registration",
            "register voters",
            "voter outreach",
            "voter education"
        ]
    ):
        return "Voter Outreach", "voter-outreach"

    if any(
        phrase in text
        for phrase in [
            "door knock",
            "door knocking",
            "canvass",
            "canvassing"
        ]
    ):
        return "Canvassing", "canvassing"

    if any(
        phrase in text
        for phrase in [
            "postcard",
            "post card",
            "phone bank",
            "volunteer"
        ]
    ):
        return "Volunteer", "volunteer"

    if any(
        phrase in text
        for phrase in [
            "rally",
            "protest",
            "demonstration",
            "march"
        ]
    ):
        return "Public Demonstration", "demonstration"

    if any(
        phrase in text
        for phrase in [
            "training",
            "workshop",
            "seminar"
        ]
    ):
        return "Training / Workshop", "training"

    if any(
        phrase in text
        for phrase in [
            "candidate forum",
            "candidate event",
            "meet the candidate"
        ]
    ):
        return "Candidate Event", "candidate-event"

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
        return "Government Meeting", "government-meeting"

    if any(
        phrase in text
        for phrase in [
            "dinner",
            "gala",
            "fundraiser",
            "fundraising"
        ]
    ):
        return "Fundraising Event", "fundraising"

    if any(
        phrase in text
        for phrase in [
            "festival",
            "community event",
            "resource fair",
            "farmers market",
            "farmer's market"
        ]
    ):
        return "Community Event", "community"

    return "Public Event", "civic"


# ============================================================
# STANDARD EVENT RECORD
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
        f"{title}|{county}|{date}|"
        f"{time}|{event_url}"
    )

    event_id = hashlib.sha1(
        unique_string.encode("utf-8")
    ).hexdigest()[:16]

    return {
        "id": event_id,
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

    pattern_with_year = (
        r"("
        + "|".join(MONTHS.keys())
        + r")\s+"
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

        day = int(match.group(2))
        year = int(match.group(3))

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

    pattern_without_year = (
        r"("
        + "|".join(MONTHS.keys())
        + r")\s+"
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

    day = int(match.group(2))

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

    if (candidate - today).days < -120:
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

    for fmt in [
        "%I:%M %p",
        "%I %p"
    ]:

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
        r"\s*[ap]\.?m\.?)"
        r"(?:\s*(?:-|–|—|to)\s*"
        r"(\d{1,2}"
        r"(?::\d{2})?"
        r"\s*[ap]\.?m\.?))?"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return "", ""

    start = normalize_time(
        match.group(1)
    )

    end = ""

    if match.group(2):
        end = normalize_time(
            match.group(2)
        )

    return start, end


# ============================================================
# CITY HELPERS
# ============================================================

def detect_washtenaw_city(location):

    text = clean_text(
        location
    ).lower()

    cities = {
        "ann arbor": "Ann Arbor",
        "ypsilanti": "Ypsilanti",
        "dexter": "Dexter",
        "chelsea": "Chelsea",
        "saline": "Saline",
        "manchester": "Manchester",
        "milan": "Milan",
        "whitmore lake": "Whitmore Lake",
        "pittsfield": "Pittsfield Township",
        "superior township": "Superior Township"
    }

    for keyword, city in cities.items():

        if keyword in text:
            return city

    return ""


def detect_oakland_city(location):

    text = clean_text(
        location
    ).lower()

    cities = {
        "southfield": "Southfield",
        "pontiac": "Pontiac",
        "royal oak": "Royal Oak",
        "ferndale": "Ferndale",
        "oak park": "Oak Park",
        "troy": "Troy",
        "novi": "Novi",
        "farmington hills": "Farmington Hills",
        "farmington": "Farmington",
        "birmingham": "Birmingham",
        "bloomfield": "Bloomfield",
        "rochester hills": "Rochester Hills",
        "rochester": "Rochester",
        "auburn hills": "Auburn Hills",
        "hazel park": "Hazel Park",
        "madison heights": "Madison Heights",
        "clawson": "Clawson",
        "berkley": "Berkley",
        "waterford": "Waterford",
        "west bloomfield": "West Bloomfield"
    }

    for keyword, city in cities.items():

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

    if not source.get("url"):

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

    return []


def collect_ingham_democratic_caucus_events():

    source = get_source("ingham-democratic-caucus")

    if not source:
        print("  Ingham Democratic Caucus source configuration not found.")
        return []

    if not source.get("enabled", False):
        print("  Ingham Democratic Caucus source is disabled.")
        return []

    source_url = source.get("url", "")
    if not source_url:
        print("  Ingham Democratic Caucus source URL is missing.")
        return []

    print("  Downloading Ingham Democratic Caucus meeting page...")
    html = download_page(source_url)
    soup = BeautifulSoup(html, "html.parser")
    page_text = clean_text(soup.get_text(" ", strip=True))

    # Read only the official "Upcoming Meeting Dates" section so
    # archived minutes are not accidentally published as events.
    section = re.search(
        r"Upcoming\s+Meeting\s+Dates\s*:\s*(.*?)(?:Archived\s+Minutes|Contacts|$)",
        page_text,
        re.IGNORECASE | re.DOTALL
    )

    if not section:
        print("  Could not locate the 'Upcoming Meeting Dates' section.")
        return []

    upcoming_text = clean_text(section.group(1))

    date_pattern = re.compile(
        r"\b(" + "|".join(month.title() for month in MONTHS.keys()) + r")\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b",
        re.IGNORECASE
    )

    date_matches = list(date_pattern.finditer(upcoming_text))

    print(
        f"  Found {len(date_matches)} Ingham Democratic Caucus "
        "upcoming meeting dates."
    )

    events = []

    for date_match in date_matches:
        raw_date = clean_text(date_match.group(0))
        event_date = parse_event_date(raw_date)

        if not event_date:
            print(f"  Ingham Caucus date skipped: {raw_date}")
            continue

        title = "Ingham County Democratic Caucus Meeting"

        event = create_event(
            title=title,
            county="Ingham",
            date=event_date,
            time="",
            end_time="",
            location="",
            city="",
            host="Ingham County Democratic Caucus",
            event_type="Government Meeting",
            category="government-meeting",
            source_name=source.get("name", ""),
            source_url=source_url,
            event_url=source_url,
            description=(
                "Upcoming Democratic Caucus meeting date "
                "published by Ingham County."
            )
        )

        events.append(event)
        print(f"  Collected Ingham Caucus: {event_date} | {title}")

    print(
        f"  Ingham Democratic Caucus parser produced "
        f"{len(events)} events."
    )

    return events

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

    source = get_source("wayne-county-government")

    if not source:
        print("  Wayne County Government source configuration not found.")
        return []

    if not source.get("enabled", False):
        print("  Wayne County Government source is disabled.")
        return []

    source_url = source.get("url", "")
    if not source_url:
        print("  Wayne County Government source URL is missing.")
        return []

    print("  Downloading Wayne County Events Directory...")
    html = download_page(source_url)
    soup = BeautifulSoup(html, "html.parser")
    events = []

    # --------------------------------------------------------
    # First preference: structured Event JSON-LD, if supplied
    # by the county website.
    # --------------------------------------------------------
    json_ld_records = []

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        stack = data if isinstance(data, list) else [data]

        while stack:
            item = stack.pop()

            if isinstance(item, list):
                stack.extend(item)
                continue

            if not isinstance(item, dict):
                continue

            graph = item.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph)

            item_type = item.get("@type", "")
            if (
                item_type == "Event"
                or (
                    isinstance(item_type, list)
                    and "Event" in item_type
                )
            ):
                json_ld_records.append(item)

    print(
        f"  Found {len(json_ld_records)} Wayne structured event records."
    )

    for item in json_ld_records:
        try:
            title = clean_text(item.get("name", ""))
            start_value = clean_text(item.get("startDate", ""))

            if not title or not start_value:
                continue

            event_date = ""
            start_time = ""
            end_time = ""

            try:
                parsed_start = datetime.fromisoformat(
                    start_value.replace("Z", "+00:00")
                )
                event_date = parsed_start.strftime("%Y-%m-%d")
                if "T" in start_value:
                    start_time = parsed_start.strftime("%I:%M %p").lstrip("0")
            except ValueError:
                event_date = parse_event_date(start_value)

            end_value = clean_text(item.get("endDate", ""))
            if end_value and "T" in end_value:
                try:
                    parsed_end = datetime.fromisoformat(
                        end_value.replace("Z", "+00:00")
                    )
                    end_time = parsed_end.strftime("%I:%M %p").lstrip("0")
                except ValueError:
                    pass

            location = ""
            city = ""

            location_data = item.get("location", {})
            if isinstance(location_data, dict):
                location_name = clean_text(location_data.get("name", ""))
                address_data = location_data.get("address", {})

                address_parts = []
                if isinstance(address_data, dict):
                    for key in [
                        "streetAddress",
                        "addressLocality",
                        "addressRegion",
                        "postalCode"
                    ]:
                        value = clean_text(address_data.get(key, ""))
                        if value:
                            address_parts.append(value)

                    city = clean_text(
                        address_data.get("addressLocality", "")
                    )

                location = clean_text(
                    " | ".join(
                        part for part in [
                            location_name,
                            ", ".join(address_parts)
                        ]
                        if part
                    )
                )

            description = clean_text(item.get("description", ""))
            event_url = clean_text(item.get("url", "")) or source_url

            event_type, category = classify_event(title, description)

            events.append(
                create_event(
                    title=title,
                    county="Wayne",
                    date=event_date,
                    time=start_time,
                    end_time=end_time,
                    location=location,
                    city=city,
                    host="Wayne County, Michigan",
                    event_type=event_type,
                    category=category,
                    source_name=source.get("name", ""),
                    source_url=source_url,
                    event_url=urljoin(source_url, event_url),
                    description=description
                )
            )

            print(f"  Collected Wayne: {event_date} | {title}")

        except Exception as error:
            print(f"  Wayne structured event parse error: {error}")

    if events:
        print(f"  Wayne parser produced {len(events)} events.")
        return events

    # --------------------------------------------------------
    # Fallback: Wayne County's OpenCities-style listing cards.
    # Several selectors are tried so a minor template change
    # does not immediately break collection.
    # --------------------------------------------------------
    selectors = [
        ".content-list-item",
        ".list-item",
        ".event-list-item",
        ".events-listing .item",
        "[class*='event-list'] article",
        "[class*='event-list'] li",
        "article"
    ]

    event_nodes = []
    working_selector = ""

    for selector in selectors:
        candidates = soup.select(selector)
        filtered = []

        for node in candidates:
            node_text = clean_text(node.get_text(" ", strip=True))
            if (
                parse_event_date(node_text)
                and node.find("a", href=True)
            ):
                filtered.append(node)

        if filtered:
            event_nodes = filtered
            working_selector = selector
            break

    if working_selector:
        print(f"  Working Wayne selector: {working_selector}")

    print(f"  Found {len(event_nodes)} Wayne event records.")

    for node in event_nodes:
        try:
            full_text = clean_text(node.get_text(" ", strip=True))
            event_date = parse_event_date(full_text)

            if not event_date:
                continue

            link = node.find("a", href=True)
            if not link:
                continue

            title = clean_text(link.get_text(" ", strip=True))
            if not title:
                heading = node.find(["h2", "h3", "h4"])
                title = clean_text(
                    heading.get_text(" ", strip=True)
                ) if heading else ""

            if not title:
                continue

            event_url = urljoin(source_url, link.get("href", ""))
            start_time, end_time = parse_event_times(full_text)

            # Keep the complete card text as the description on
            # the first live pass. Individual event pages can be
            # used later for richer location/time extraction.
            description = full_text
            event_type, category = classify_event(title, description)

            event = create_event(
                title=title,
                county="Wayne",
                date=event_date,
                time=start_time,
                end_time=end_time,
                location="",
                city="",
                host="Wayne County, Michigan",
                event_type=event_type,
                category=category,
                source_name=source.get("name", ""),
                source_url=source_url,
                event_url=event_url,
                description=description
            )

            events.append(event)
            print(f"  Collected Wayne: {event_date} | {title}")

        except Exception as error:
            print(f"  Wayne event parse error: {error}")

    if not events:
        print(
            "  Wayne diagnostics: no event cards were parsed. "
            "The page downloaded successfully, but its HTML "
            "structure needs another selector pass."
        )

        event_like_links = []
        for link in soup.find_all("a", href=True):
            text = clean_text(link.get_text(" ", strip=True))
            href = clean_text(link.get("href", ""))
            if text and (
                "event" in href.lower()
                or parse_event_date(text)
            ):
                event_like_links.append((text, href))

        print(
            f"  Wayne diagnostic event-like links: "
            f"{len(event_like_links)}"
        )

        for text, href in event_like_links[:15]:
            print(f"  Wayne diagnostic link: {text} | {href}")

    print(f"  Wayne parser produced {len(events)} events.")
    return events


def collect_wayne_precinct_delegate_events():

    if not source_is_enabled(
        "wayne-democratic-precinct-delegates"
    ):
        return []

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
# MICHIGAN DEMOCRATIC PARTY — CONTROLSHIFT STATEWIDE FEED
# ============================================================

WAYNE_CITIES = {
    "allen park", "belleville", "dearborn", "dearborn heights",
    "detroit", "ecorse", "flat rock", "garden city", "gibraltar",
    "grosse pointe", "grosse pointe farms", "grosse pointe park",
    "grosse pointe shores", "grosse pointe woods", "hamtramck",
    "harper woods", "highland park", "inkster", "lincoln park",
    "livonia", "melvindale", "northville", "plymouth", "river rouge",
    "riverview", "rockwood", "romulus", "southgate", "taylor",
    "trenton", "wayne", "westland", "woodhaven", "wyandotte"
}

INGHAM_CITIES = {
    "east lansing", "lansing", "leslie", "mason", "williamston"
}

OAKLAND_CITIES = {
    "auburn hills", "berkley", "birmingham", "bloomfield hills",
    "clawson", "farmington", "farmington hills", "ferndale",
    "hazel park", "huntington woods", "keego harbor", "lake angelus",
    "lathrup village", "madison heights", "novi", "oak park",
    "orchard lake village", "pleasant ridge", "pontiac", "rochester",
    "rochester hills", "royal oak", "south lyon", "southfield",
    "sylvan lake", "troy", "walled lake", "wixom"
}

WASHTENAW_CITIES = {
    "ann arbor", "chelsea", "dexter", "manchester", "milan",
    "saline", "ypsilanti"
}


def county_from_mdp_location(locality="", location_text=""):

    locality_key = clean_text(locality).lower()
    haystack = clean_text(location_text).lower()

    city_sets = [
        ("Wayne", WAYNE_CITIES),
        ("Ingham", INGHAM_CITIES),
        ("Oakland", OAKLAND_CITIES),
        ("Washtenaw", WASHTENAW_CITIES)
    ]

    for county, cities in city_sets:
        if locality_key in cities:
            return county

    for county, cities in city_sets:
        for city in cities:
            if re.search(r"\b" + re.escape(city) + r"\b", haystack):
                return county

    return ""


def collect_mdp_controlshift_events():

    source = get_source("mdp-controlshift")

    if not source or not source.get("enabled", False):
        print("MDP ControlShift source is disabled.")
        return []

    source_url = source.get("url", "")
    calendar_slug = "mi-statewide"

    print("Checking Michigan Democratic Party statewide event feed...")

    params = {
        "filter[calendars]": calendar_slug,
        "per_page": 100,
        "page": 1
    }

    response = requests.get(
        source_url,
        params=params,
        headers={
            **HEADERS,
            "Accept": "application/json"
        },
        timeout=REQUEST_TIMEOUT
    )

    print(f"  Requesting: {response.url}")
    print(f"  HTTP status: {response.status_code}")

    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, dict):
        print(
            "  MDP response keys: "
            + ", ".join(sorted(payload.keys()))
        )

    records = []

    if isinstance(payload, dict):
        for key in ("data", "events", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                records = value
                break
    elif isinstance(payload, list):
        records = payload

    print(f"  Found {len(records)} MDP feed records.")

    if records:
        sample = records[0]
        if isinstance(sample, dict):
            print(
                "  MDP sample record keys: "
                + ", ".join(sorted(sample.keys()))
            )

    events = []

    for record in records:

        if not isinstance(record, dict):
            continue

        attributes = record.get("attributes", {})
        if not isinstance(attributes, dict):
            attributes = {}

        def value(*keys):
            for key in keys:
                candidate = record.get(key)
                if candidate not in (None, "", []):
                    return candidate
                candidate = attributes.get(key)
                if candidate not in (None, "", []):
                    return candidate
            return ""

        record_type = clean_text(value("type"))
        if record_type and record_type.lower() not in {
            "event", "externalevent", "external_event"
        }:
            continue

        title = clean_text(value("title", "name"))
        description = clean_text(value("description"))
        start_value = clean_text(value("start_at", "startAt", "start_date"))
        end_value = clean_text(value("end_at", "endAt", "end_date"))

        if not title or not start_value:
            continue

        event_date = ""
        start_time = ""
        end_time = ""

        try:
            parsed_start = datetime.fromisoformat(
                start_value.replace("Z", "+00:00")
            ).astimezone(TIMEZONE)
            event_date = parsed_start.strftime("%Y-%m-%d")
            start_time = parsed_start.strftime("%I:%M %p").lstrip("0")
        except Exception:
            event_date = parse_event_date(start_value)

        if end_value:
            try:
                parsed_end = datetime.fromisoformat(
                    end_value.replace("Z", "+00:00")
                ).astimezone(TIMEZONE)
                end_time = parsed_end.strftime("%I:%M %p").lstrip("0")
            except Exception:
                pass

        location_data = value("location")
        if not isinstance(location_data, dict):
            location_data = {}

        locality = clean_text(
            location_data.get("locality", "")
            or value("locality", "city")
        )

        region = clean_text(
            location_data.get("region", "")
            or value("region", "state")
        )

        postal_code = clean_text(
            location_data.get("postal_code", "")
            or value("postal_code", "zip")
        )

        venue = clean_text(
            value("location_venue", "venue")
        )

        query = clean_text(
            location_data.get("query", "")
            or value("address", "location_name")
        )

        location_parts = [
            part for part in [
                venue,
                query,
                locality,
                region,
                postal_code
            ]
            if part
        ]

        # Preserve order while removing repeated location pieces.
        location_parts = list(dict.fromkeys(location_parts))
        location_text = " | ".join(location_parts)

        county = county_from_mdp_location(
            locality,
            " ".join([
                location_text,
                title,
                description
            ])
        )

        if not county:
            print(
                "  Skipping MDP event outside/unresolved "
                f"tracked counties: {title}"
            )
            continue

        event_id_or_slug = clean_text(
            value("slug", "id")
        )

        event_url = clean_text(
            value("url", "event_url")
        )

        if not event_url and event_id_or_slug:
            if event_id_or_slug.startswith("http"):
                event_url = event_id_or_slug
            else:
                event_url = (
                    "https://midems.controlshift.app/events/"
                    + event_id_or_slug
                )

        event_type, category = classify_event(
            title,
            description
        )

        host = clean_text(
            value("host_name", "host", "organizer")
        )
        if isinstance(value("host"), dict):
            host = clean_text(
                value("host").get("full_name", "")
            )

        if not host:
            host = "Michigan Democratic Party"

        event = create_event(
            title=title,
            county=county,
            date=event_date,
            time=start_time,
            end_time=end_time,
            location=location_text,
            city=locality,
            host=host,
            event_type=event_type,
            category=category,
            source_name=source.get("name", ""),
            source_url=(
                "https://midems.controlshift.app/"
                "calendars/mi-statewide"
            ),
            event_url=event_url,
            description=description
        )

        events.append(event)

        print(
            f"  Collected MDP → {county}: "
            f"{event_date} | {title}"
        )

    print(
        f"MDP ControlShift: {len(events)} "
        "tracked-county events collected."
    )

    return events


# ============================================================
# OAKLAND COUNTY — LIVE COLLECTOR
# ============================================================

def collect_oakland_democratic_party_events():

    source = get_source(
        "oakland-democrats"
    )

    if not source:
        print(
            "  Oakland source configuration not found."
        )
        return []

    if not source.get(
        "enabled",
        False
    ):
        print(
            "  Oakland source is disabled."
        )
        return []

    source_url = source.get(
        "url",
        ""
    )

    if not source_url:
        print(
            "  Oakland source URL is missing."
        )
        return []

    print(
        "  Downloading Oakland events page..."
    )

    html = download_page(
        source_url
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    events = []


    # --------------------------------------------------------
    # Squarespace event collections commonly expose event
    # entries as article/eventlist structures. We test several
    # structures rather than depending on one class.
    # --------------------------------------------------------

    selectors = [
        "article.eventlist-event",
        ".eventlist-event",
        "article.event",
        ".event-item",
        "[data-item-id]"
    ]

    event_nodes = []

    for selector in selectors:

        nodes = soup.select(
            selector
        )

        # data-item-id is broad, so only use it if the
        # earlier event-specific selectors fail.
        if nodes:

            if selector == "[data-item-id]":

                filtered = []

                for node in nodes:

                    node_text = clean_text(
                        node.get_text(
                            " ",
                            strip=True
                        )
                    ).lower()

                    if (
                        any(
                            month in node_text
                            for month in MONTHS
                        )
                        and node.find("a")
                    ):
                        filtered.append(node)

                nodes = filtered

            if nodes:

                event_nodes = nodes

                print(
                    f"  Working Oakland selector: "
                    f"{selector}"
                )

                break

    print(
        f"  Found {len(event_nodes)} "
        "Oakland event records."
    )


    # --------------------------------------------------------
    # Diagnostics if Squarespace structure changes.
    # --------------------------------------------------------

    if not event_nodes:

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

        all_links = soup.find_all(
            "a",
            href=True
        )

        event_like_links = []

        for link in all_links:

            href = clean_text(
                link.get(
                    "href",
                    ""
                )
            )

            text = clean_text(
                link.get_text(
                    " ",
                    strip=True
                )
            )

            if (
                "/events/" in href.lower()
                or "/event/" in href.lower()
            ):
                event_like_links.append(
                    (text, href)
                )

        print(
            f"  Diagnostic: found "
            f"{len(event_like_links)} "
            "event-like links."
        )

        for text, href in event_like_links[:10]:

            print(
                "  Diagnostic event link: "
                f"{text} | {href}"
            )

        return []


    # --------------------------------------------------------
    # Parse each event card.
    # --------------------------------------------------------

    for node in event_nodes:

        try:

            full_text = clean_text(
                node.get_text(
                    " ",
                    strip=True
                )
            )

            if not full_text:
                continue


            # =================================================
            # TITLE + URL
            # =================================================

            title_link = None

            title_selectors = [
                ".eventlist-title-link",
                ".eventlist-title a",
                ".event-title a",
                "h1 a",
                "h2 a",
                "h3 a",
                "a[href*='/events/']",
                "a[href*='/event/']"
            ]

            for selector in title_selectors:

                candidate = node.select_one(
                    selector
                )

                if candidate:

                    candidate_text = clean_text(
                        candidate.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if candidate_text:

                        title_link = candidate
                        break


            title = ""
            event_url = ""


            if title_link:

                title = clean_text(
                    title_link.get_text(
                        " ",
                        strip=True
                    )
                )

                event_url = urljoin(
                    source_url,
                    title_link.get(
                        "href",
                        ""
                    )
                )


            if not title:

                heading = node.find(
                    [
                        "h1",
                        "h2",
                        "h3",
                        "h4"
                    ]
                )

                if heading:

                    title = clean_text(
                        heading.get_text(
                            " ",
                            strip=True
                        )
                    )


            if not title:

                print(
                    "  Oakland record skipped: "
                    "no title found."
                )

                continue


            # =================================================
            # DATE
            # =================================================

            event_date = ""

            time_element = node.find(
                "time"
            )

            if time_element:

                datetime_value = clean_text(
                    time_element.get(
                        "datetime",
                        ""
                    )
                )

                if datetime_value:

                    try:

                        parsed = (
                            datetime.fromisoformat(
                                datetime_value
                                .replace(
                                    "Z",
                                    "+00:00"
                                )
                            )
                        )

                        event_date = (
                            parsed.strftime(
                                "%Y-%m-%d"
                            )
                        )

                    except ValueError:

                        try:

                            parsed = (
                                datetime.strptime(
                                    datetime_value[:10],
                                    "%Y-%m-%d"
                                )
                            )

                            event_date = (
                                parsed.strftime(
                                    "%Y-%m-%d"
                                )
                            )

                        except ValueError:
                            pass


            if not event_date:

                event_date = parse_event_date(
                    full_text
                )


            # =================================================
            # TIME
            # =================================================

            start_time, end_time = (
                parse_event_times(
                    full_text
                )
            )


            # =================================================
            # LOCATION
            # =================================================

            location = ""

            location_selectors = [
                ".eventlist-meta-address",
                ".eventlist-address",
                ".event-address",
                ".event-location",
                ".location",
                "[class*='address']",
                "[class*='location']"
            ]

            for selector in location_selectors:

                location_element = (
                    node.select_one(
                        selector
                    )
                )

                if location_element:

                    location = clean_text(
                        location_element.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if location:
                        break


            # =================================================
            # DESCRIPTION
            # =================================================

            description = ""

            description_selectors = [
                ".eventlist-description",
                ".event-description",
                ".eventlist-excerpt",
                ".summary",
                ".excerpt"
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


            # =================================================
            # CITY
            # =================================================

            city = detect_oakland_city(
                location
            )


            # =================================================
            # EVENT TYPE
            # =================================================

            event_type, category = (
                classify_event(
                    title,
                    description
                )
            )


            # =================================================
            # REQUIRE VALID DATE
            # =================================================

            if not event_date:

                print(
                    "  Oakland event skipped "
                    "because date could not be read: "
                    f"{title}"
                )

                continue


            # =================================================
            # CREATE EVENT
            # =================================================

            event = create_event(
                title=title,
                county="Oakland",
                date=event_date,
                time=start_time,
                end_time=end_time,
                location=location,
                city=city,
                host=(
                    "Oakland County "
                    "Democratic Party"
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
                "  Collected Oakland: "
                f"{event_date} | {title}"
            )

        except Exception as error:

            print(
                "  Oakland event parse error: "
                f"{error}"
            )


    print(
        f"  Oakland parser produced "
        f"{len(events)} events."
    )

    return events


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
# WASHTENAW COUNTY — LIVE COLLECTOR
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

    for node in event_nodes:

        try:

            # TITLE + URL
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


            # DATE/TIME
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

                try:

                    parsed_datetime = (
                        datetime.fromisoformat(
                            datetime_value.replace(
                                "Z",
                                "+00:00"
                            )
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


            # LOCATION
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


            # DESCRIPTION
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


            city = detect_washtenaw_city(
                location
            )

            event_type, category = (
                classify_event(
                    title,
                    description
                )
            )

            if not event_date:

                print(
                    "  Skipping event because "
                    "date could not be read: "
                    f"{title}"
                )

                continue

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
                f"{event_date} | {title}"
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
# VALIDATION
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
            continue

        if (
            county.lower()
            not in allowed_counties
        ):
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
# SORT
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
# COUNTS
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
            "id": source.get(
                "id",
                ""
            ),
            "county": source.get(
                "county",
                ""
            ),
            "name": source.get(
                "name",
                ""
            ),
            "source_type": source.get(
                "source_type",
                ""
            ),
            "enabled": source.get(
                "enabled",
                False
            ),
            "configured": bool(
                source.get(
                    "url",
                    ""
                )
            ),
            "url": source.get(
                "url",
                ""
            )
        })

    return status


# ============================================================
# WRITE JSON
# ============================================================

def write_event_feed(events):

    now = datetime.now(
        TIMEZONE
    )

    county_counts = get_county_counts(
        events
    )

    category_counts = get_category_counts(
        events
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
        f"Output file: {OUTPUT_FILE}"
    )
    print(
        "=========================================="
    )


# ============================================================
# RUN COUNTY
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
# MAIN
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

    all_events.extend(
        run_collector(
            "Ingham",
            collect_ingham_events
        )
    )

    all_events.extend(
        run_collector(
            "Wayne",
            collect_wayne_events
        )
    )

    all_events.extend(
        run_collector(
            "MDP statewide",
            collect_mdp_controlshift_events
        )
    )

    all_events.extend(
        run_collector(
            "Oakland",
            collect_oakland_events
        )
    )

    all_events.extend(
        run_collector(
            "Washtenaw",
            collect_washtenaw_events
        )
    )

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

    write_event_feed(
        all_events
    )

    print()
    print(
        "Event collection complete."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
