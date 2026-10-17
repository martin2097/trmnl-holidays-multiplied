"""PTO Multiplier: one self-contained TRMNL Python Serverless script.

run() accepts TRMNL globals and polled Nager year arrays. The explicit fixture
envelope is {holiday_calendar, years: {YYYY: [...]}, uk: {...}, trmnl: {...}}.
TRMNL polls the local calendars and the shared Cloudflare world feed. This
script only transforms supplied data: no network calls, cache or saved state.
"""

from datetime import date, datetime, timedelta, timezone
from calendar import monthrange
import re
import random

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


# Available Nager catalogue refreshed 2026-10-01. Embedded: no runtime lookup.
NAGER_COUNTRIES = {
    'AD': 'Andorra',
    'AG': 'Antigua and Barbuda',
    'AI': 'Anguilla',
    'AL': 'Albania',
    'AM': 'Armenia',
    'AO': 'Angola',
    'AR': 'Argentina',
    'AT': 'Austria',
    'AU': 'Australia',
    'AW': 'Aruba',
    'AX': 'Åland Islands',
    'BA': 'Bosnia and Herzegovina',
    'BB': 'Barbados',
    'BD': 'Bangladesh',
    'BE': 'Belgium',
    'BF': 'Burkina Faso',
    'BG': 'Bulgaria',
    'BH': 'Bahrain',
    'BI': 'Burundi',
    'BJ': 'Benin',
    'BL': 'Saint Barthélemy',
    'BM': 'Bermuda',
    'BO': 'Bolivia',
    'BQ': 'Caribbean Netherlands',
    'BR': 'Brazil',
    'BS': 'Bahamas',
    'BW': 'Botswana',
    'BY': 'Belarus',
    'BZ': 'Belize',
    'CA': 'Canada',
    'CC': 'Cocos (Keeling) Islands',
    'CD': 'DR Congo',
    'CF': 'Central African Republic',
    'CG': 'Congo',
    'CH': 'Switzerland',
    'CI': 'Ivory Coast',
    'CK': 'Cook Islands',
    'CL': 'Chile',
    'CM': 'Cameroon',
    'CN': 'China',
    'CO': 'Colombia',
    'CR': 'Costa Rica',
    'CU': 'Cuba',
    'CV': 'Cape Verde',
    'CW': 'Curaçao',
    'CX': 'Christmas Island',
    'CY': 'Cyprus',
    'CZ': 'Czechia',
    'DE': 'Germany',
    'DJ': 'Djibouti',
    'DK': 'Denmark',
    'DM': 'Dominica',
    'DO': 'Dominican Republic',
    'DZ': 'Algeria',
    'EC': 'Ecuador',
    'EE': 'Estonia',
    'EG': 'Egypt',
    'ER': 'Eritrea',
    'ES': 'Spain',
    'ET': 'Ethiopia',
    'FI': 'Finland',
    'FK': 'Falkland Islands',
    'FM': 'Micronesia',
    'FO': 'Faroe Islands',
    'FR': 'France',
    'GA': 'Gabon',
    'GB': 'United Kingdom',
    'GD': 'Grenada',
    'GE': 'Georgia',
    'GF': 'French Guiana',
    'GG': 'Guernsey',
    'GH': 'Ghana',
    'GI': 'Gibraltar',
    'GL': 'Greenland',
    'GM': 'Gambia',
    'GN': 'Guinea',
    'GP': 'Guadeloupe',
    'GQ': 'Equatorial Guinea',
    'GR': 'Greece',
    'GT': 'Guatemala',
    'GW': 'Guinea-Bissau',
    'GY': 'Guyana',
    'HK': 'Hong Kong',
    'HN': 'Honduras',
    'HR': 'Croatia',
    'HT': 'Haiti',
    'HU': 'Hungary',
    'ID': 'Indonesia',
    'IE': 'Ireland',
    'IM': 'Isle of Man',
    'IQ': 'Iraq',
    'IS': 'Iceland',
    'IT': 'Italy',
    'JE': 'Jersey',
    'JM': 'Jamaica',
    'JP': 'Japan',
    'KE': 'Kenya',
    'KH': 'Cambodia',
    'KI': 'Kiribati',
    'KM': 'Comoros',
    'KN': 'Saint Kitts and Nevis',
    'KR': 'South Korea',
    'KY': 'Cayman Islands',
    'KZ': 'Kazakhstan',
    'LC': 'Saint Lucia',
    'LI': 'Liechtenstein',
    'LR': 'Liberia',
    'LS': 'Lesotho',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'LV': 'Latvia',
    'LY': 'Libya',
    'MA': 'Morocco',
    'MC': 'Monaco',
    'MD': 'Moldova',
    'ME': 'Montenegro',
    'MF': 'Saint Martin',
    'MG': 'Madagascar',
    'MH': 'Marshall Islands',
    'MK': 'North Macedonia',
    'ML': 'Mali',
    'MN': 'Mongolia',
    'MP': 'Northern Mariana Islands',
    'MQ': 'Martinique',
    'MR': 'Mauritania',
    'MS': 'Montserrat',
    'MT': 'Malta',
    'MW': 'Malawi',
    'MX': 'Mexico',
    'MZ': 'Mozambique',
    'NA': 'Namibia',
    'NC': 'New Caledonia',
    'NE': 'Niger',
    'NF': 'Norfolk Island',
    'NG': 'Nigeria',
    'NI': 'Nicaragua',
    'NL': 'Netherlands',
    'NO': 'Norway',
    'NR': 'Nauru',
    'NU': 'Niue',
    'NZ': 'New Zealand',
    'PA': 'Panama',
    'PE': 'Peru',
    'PF': 'French Polynesia',
    'PG': 'Papua New Guinea',
    'PH': 'Philippines',
    'PL': 'Poland',
    'PM': 'Saint Pierre and Miquelon',
    'PN': 'Pitcairn Islands',
    'PR': 'Puerto Rico',
    'PT': 'Portugal',
    'PW': 'Palau',
    'PY': 'Paraguay',
    'RO': 'Romania',
    'RS': 'Serbia',
    'RU': 'Russia',
    'RW': 'Rwanda',
    'SB': 'Solomon Islands',
    'SC': 'Seychelles',
    'SD': 'Sudan',
    'SE': 'Sweden',
    'SG': 'Singapore',
    'SH': 'Saint Helena, Ascension and Tristan da Cunha',
    'SI': 'Slovenia',
    'SJ': 'Svalbard and Jan Mayen',
    'SK': 'Slovakia',
    'SL': 'Sierra Leone',
    'SM': 'San Marino',
    'SN': 'Senegal',
    'SO': 'Somalia',
    'SR': 'Suriname',
    'SS': 'South Sudan',
    'ST': 'São Tomé and Príncipe',
    'SV': 'El Salvador',
    'SX': 'Sint Maarten',
    'SY': 'Syria',
    'SZ': 'Eswatini',
    'TC': 'Turks and Caicos Islands',
    'TD': 'Chad',
    'TG': 'Togo',
    'TK': 'Tokelau',
    'TN': 'Tunisia',
    'TO': 'Tonga',
    'TR': 'Türkiye',
    'TT': 'Trinidad and Tobago',
    'TV': 'Tuvalu',
    'TZ': 'Tanzania',
    'UA': 'Ukraine',
    'UG': 'Uganda',
    'US': 'United States',
    'UY': 'Uruguay',
    'VA': 'Vatican City',
    'VC': 'Saint Vincent and the Grenadines',
    'VE': 'Venezuela',
    'VG': 'British Virgin Islands',
    'VI': 'United States Virgin Islands',
    'VN': 'Vietnam',
    'VU': 'Vanuatu',
    'WF': 'Wallis and Futuna',
    'WS': 'Samoa',
    'YE': 'Yemen',
    'ZA': 'South Africa',
    'ZM': 'Zambia',
    'ZW': 'Zimbabwe',
}

DE_STATES = {
    "bw": "Baden-Württemberg", "by": "Bavaria", "be": "Berlin",
    "bb": "Brandenburg", "hb": "Bremen", "hh": "Hamburg", "he": "Hesse",
    "mv": "Mecklenburg-Vorpommern", "ni": "Lower Saxony",
    "nw": "North Rhine-Westphalia", "rp": "Rhineland-Palatinate",
    "sl": "Saarland", "sn": "Saxony", "st": "Saxony-Anhalt",
    "sh": "Schleswig-Holstein", "th": "Thuringia",
}
CALENDARS = {
    "be": {"label": "Belgium", "country": "BE",
           "scope_note": "Employer-selected replacement days are not included."},
    "ca-ab": {"label": "Canada — Alberta", "country": "CA", "subdivision": "CA-AB",
              "scope_note": "Provincial statutory holidays; optional workplace days excluded."},
    "ca-bc": {"label": "Canada — British Columbia", "country": "CA", "subdivision": "CA-BC",
              "scope_note": "Provincial statutory holidays; employer replacements excluded."},
    "ca-on": {"label": "Canada — Ontario", "country": "CA", "subdivision": "CA-ON",
              "scope_note": "Nine provincial holidays; employer replacements excluded."},
    "cz": {"label": "Czechia", "country": "CZ"},
    "ie": {"label": "Ireland", "country": "IE",
           "scope_note": "Employer-selected replacement days are not included."},
    "nl": {"label": "Netherlands", "country": "NL",
           "scope_note": "Public holidays; workplace days off may differ."},
    "pl": {"label": "Poland", "country": "PL",
           "scope_note": "Employer-selected replacement days are not included."},
    "sg": {"label": "Singapore", "country": "SG",
           "scope_note": "Monday–Friday week; fixed Sunday replacements included."},
    "za": {"label": "South Africa", "country": "ZA",
           "scope_note": "Monday–Friday week; fixed Sunday replacements included."},
    "us-federal": {"label": "USA — Federal holidays", "country": "US",
                   "scope_note": "Federal holiday calendar; standard Mon–Fri week."},
    "gb-eng-wls": {"label": "UK — England & Wales", "country": "GB",
                   "subdivision": "GB-ENG", "division": "england-and-wales"},
    "gb-sct": {"label": "UK — Scotland", "country": "GB",
               "subdivision": "GB-SCT", "division": "scotland"},
    "gb-nir": {"label": "UK — Northern Ireland", "country": "GB",
               "subdivision": "GB-NIR", "division": "northern-ireland"},
}
for _code, _name in DE_STATES.items():
    CALENDARS["de-" + _code] = {
        "label": "Germany — " + _name, "country": "DE",
        "subdivision": "DE-" + _code.upper(),
        "scope_note": "State-wide holidays; municipal exceptions excluded.",
    }

# Keep the reviewed profiles and their identifiers stable. Every other API
# country gets a national-source baseline, not guessed regional/workplace rules.
REGIONAL_BASELINE_COUNTRIES = {"AT", "AU", "BA", "BR", "CA", "CH", "ES", "FR", "IT", "NZ", "PT"}
for _country, _name in NAGER_COUNTRIES.items():
    if _country in {"US", "GB", "DE"}:
        continue  # Federal / UK divisions / German states already cover these.
    CALENDARS.setdefault(_country.lower(), {
        "label": _name + (" — National holidays" if _country in REGIONAL_BASELINE_COUNTRIES else ""),
        "country": _country,
        "source_baseline": True,
        "scope_note": "National source dates; Monday–Friday week. Regional days, working-weekend changes and unverified substitutes are not added.",
    })

US_FEDERAL_NAMES = {
    "new year's day", "martin luther king, jr. day", "martin luther king jr. day",
    "presidents day", "washington's birthday", "memorial day",
    "juneteenth national independence day", "independence day", "labour day",
    "labor day", "columbus day", "veterans day", "thanksgiving day", "christmas day",
}
# Provincial inclusion must override Nager's over-broad Canadian national flag.
# Sources: alberta.ca/alberta-general-holidays; Ontario ESA public holidays;
# gov.bc.ca Employment Standards statutory-holidays (reviewed 2026-09-30).
CA_COMMON_NAMES = {
    "new year's day", "family day", "good friday", "victoria day", "canada day",
    "labour day", "thanksgiving", "thanksgiving day", "christmas day",
}
CA_EXTRA_NAMES = {
    "CA-AB": {"remembrance day"},
    "CA-BC": {"remembrance day", "british columbia day", "national day for truth and reconciliation"},
    "CA-ON": {"boxing day", "st. stephen's day", "saint stephen's day"},
}
MONTHS = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
DAY = timedelta(days=1)


class CalendarError(ValueError):
    """A context/source failure that must be visible instead of guessed around."""


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CalendarError("A holiday date has an unexpected format.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CalendarError("A holiday date is invalid.") from exc


def name_key(name):
    return name.strip().replace("’", "'").replace("‘", "'").lower()


def add_months(day, months):
    offset = day.year * 12 + day.month - 1 + months
    year, month = divmod(offset, 12)
    return date(year, month + 1, min(day.day, monthrange(year, month + 1)[1]))


def read_context(payload):
    if not isinstance(payload, dict):
        raise CalendarError("The calendar response is not an object.")
    trmnl = payload.get("trmnl") or {}
    settings = trmnl.get("plugin_settings") or {}
    fields = settings.get("custom_fields_values") or {}
    calendar_id = payload.get("holiday_calendar", fields.get("holiday_calendar", ""))
    if calendar_id not in CALENDARS:
        raise CalendarError("Choose a supported holiday calendar in plugin settings.")
    user = trmnl.get("user") or {}
    stamp = (trmnl.get("system") or {}).get("timestamp_utc")
    try:
        if isinstance(stamp, (int, float)) or (isinstance(stamp, str) and stamp.isdigit()):
            now = datetime.fromtimestamp(float(stamp), timezone.utc)
        elif isinstance(stamp, str):
            now = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        else:
            now = datetime.now(timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise CalendarError("TRMNL's current time could not be read.") from exc
    zone = None
    if ZoneInfo is not None and user.get("time_zone_iana"):
        try:
            zone = ZoneInfo(user["time_zone_iana"])
        except (ValueError, KeyError, TypeError):
            pass
    if zone is None and user.get("utc_offset") is not None:
        try:
            offset = int(user["utc_offset"])
            if not -43200 <= offset <= 50400:
                raise ValueError("Invalid UTC offset")
            zone = timezone(timedelta(seconds=offset))
        except (ValueError, TypeError, OverflowError):
            pass
    if zone is None:
        raise CalendarError("Your TRMNL time zone is unavailable. Check device settings.")
    return calendar_id, now.astimezone(zone).date()


def polling_nodes(payload):
    """Unwrap TRMNL response nodes without depending on URL positions."""
    nodes = [value for key, value in payload.items() if re.fullmatch(r"IDX_?\d+", str(key))]
    if not nodes and "data" in payload:
        nodes = [payload["data"]]
    for node in nodes:
        if isinstance(node, dict) and isinstance(node.get("data"), (list, dict)):
            node = node["data"]
        yield node


def read_polling_data(payload):
    """Accept explicit year maps or TRMNL's indexed polling response nodes.

    A root array can appear as {data: [...]}; GOV.UK is identified by its
    division keys. Year inference only uses validated dates, never IDX order.
    """
    years = payload.get("years")
    uk = payload.get("uk")
    if years is not None:
        if not isinstance(years, dict):
            raise CalendarError("The annual calendar response has an unexpected shape.")
        return years, uk
    years = {}
    for node in polling_nodes(payload):
        if isinstance(node, dict) and "england-and-wales" in node:
            uk = node
        elif isinstance(node, list) and node:
            source_years = {parse_date(row.get("date")).year for row in node if isinstance(row, dict)}
            if len(source_years) != 1 or len([r for r in node if isinstance(r, dict)]) != len(node):
                raise CalendarError("An annual holiday file contains mixed or invalid dates.")
            year = str(next(iter(source_years)))
            if year in years:
                raise CalendarError("Holiday data was received more than once.")
            years[year] = node
    if not years:
        raise CalendarError("No usable annual holiday data was received.")
    return years, uk


def applies(record, profile):
    types = record["holidayTypes"]
    key = name_key(record["name"])
    if profile["country"] == "US":
        # Columbus Day is national Bank-only in Nager; it is a federal holiday.
        return key in US_FEDERAL_NAMES and record["nationalHoliday"] and bool(set(types) & {"Public", "Bank"})
    regional = profile.get("subdivision") in (record["subdivisionCodes"] or [])
    if "Public" not in types or not (record["nationalHoliday"] or regional):
        return False
    if profile["country"] == "CA" and profile.get("subdivision") in CA_EXTRA_NAMES:
        return key in CA_COMMON_NAMES | CA_EXTRA_NAMES[profile["subdivision"]]
    if profile["country"] == "DE":
        state = profile.get("subdivision")
        if key in {"peace festival", "augsburg peace festival"}:
            return False
        if key in {"assumption day", "assumption of mary", "assumption of the virgin mary"} and state == "DE-BY":
            return False
        if key == "corpus christi" and state in {"DE-SN", "DE-TH"}:
            return False
    return True


def validate_years(years, profile):
    valid = {}
    for year, rows in years.items():
        if not re.fullmatch(r"\d{4}", str(year)) or not isinstance(rows, list) or not rows:
            raise CalendarError("An annual holiday file is missing or empty.")
        expected_year = int(year)
        selected = []
        for row in rows:
            if not isinstance(row, dict):
                raise CalendarError("A holiday entry has an unexpected shape.")
            actual_date = parse_date(row.get("date"))
            if actual_date.year != expected_year or row.get("countryCode") != profile["country"]:
                raise CalendarError("Holiday data does not match the selected calendar.")
            if (not isinstance(row.get("name"), str) or not row["name"].strip()
                    or not isinstance(row.get("nationalHoliday"), bool)
                    or not isinstance(row.get("holidayTypes"), list)
                    or not all(isinstance(kind, str) for kind in row["holidayTypes"])
                    or not (row.get("subdivisionCodes") is None or
                            isinstance(row["subdivisionCodes"], list) and
                            all(isinstance(code, str) for code in row["subdivisionCodes"]))):
                raise CalendarError("A holiday entry is missing required calendar fields.")
            if applies(row, profile):
                selected.append(row)
        if not selected and not profile.get("source_baseline"):
            raise CalendarError("No applicable holidays were found in the published dates.")
        valid[expected_year] = selected
    return valid


def event(name, nominal, effective, source):
    return {"id": nominal.isoformat() + ":" + name_key(name), "name": name,
            "nominal": nominal, "effective": effective, "source": source}


def uk_match_key(name):
    key = name_key(name)
    return {
        "st. stephen's day": "boxing day", "saint stephen's day": "boxing day",
        "2nd january": "2 january",
        "saint patrick's day": "st patrick's day", "st. patrick's day": "st patrick's day",
        "battle of the boyne": "battle of the boyne (orangemen's day)",
    }.get(key, key)


def normalize_holidays(years, profile, uk=None):
    """Return canonical identities and effective dates; never union UK sources."""
    valid = validate_years(years, profile)
    nominal = [row for rows in valid.values() for row in rows]
    events = []
    if profile["country"] == "GB":
        division = (uk or {}).get(profile["division"], {})
        rows = division.get("events")
        if not isinstance(rows, list) or not rows:
            raise CalendarError("The official UK bank-holiday calendar is unavailable.")
        official = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("title"), str):
                raise CalendarError("The official UK calendar has an unexpected entry.")
            actual_date = parse_date(row.get("date"))
            if actual_date.year in valid:
                official.append((actual_date, row))
        # Each published full-year UK division includes both New Year and Christmas.
        for year in list(valid):
            dates = [day for day, _ in official if day.year == year]
            if len(dates) < 5 or not any(day.month == 1 for day in dates) or not any(day.month == 12 for day in dates):
                del valid[year]
        for effective, row in official:
            if effective.year not in valid:
                continue
            matches = [item for item in nominal
                       if uk_match_key(item["name"]) == uk_match_key(row["title"])
                       and abs((parse_date(item["date"]) - effective).days) <= 7]
            match = min(matches, key=lambda item: abs((parse_date(item["date"]) - effective).days)) if matches else None
            origin = parse_date(match["date"]) if match else effective
            events.append(event(match["name"] if match else row["title"], origin, effective, "gov.uk"))
    else:
        occupied = {parse_date(row["date"]) for row in nominal}
        for row in nominal:
            origin = parse_date(row["date"])
            effective = origin
            if profile["country"] == "US":
                if origin.weekday() == 5:
                    effective -= DAY
                elif origin.weekday() == 6:
                    effective += DAY
            elif profile["country"] == "ZA" and origin.weekday() == 6:
                # Public Holidays Act: the following Monday, even if another
                # holiday already occupies it. Never invent a Tuesday.
                effective += DAY
            elif profile["country"] == "CA" and name_key(row["name"]) == "canada day" and origin.weekday() == 6:
                # Canada Holidays Act s2(2): July 2 when July 1 is Sunday.
                # All other employer-selected substitutions stay unassigned.
                effective += DAY
            elif profile["country"] == "SG" and origin.weekday() == 6:
                # MOM: for a five-day workweek Sunday is the rest day;
                # the next working day is off. Saturday compensation is
                # employer-decided and deliberately left on Saturday.
                effective += DAY
                while effective.weekday() >= 5 or effective in occupied:
                    effective += DAY
                occupied.add(effective)
            events.append(event(row["name"], origin, effective, "nager"))
    for item in events:
        item["country"] = profile["country"]
    deduped = {(item["id"], item["effective"]): item for item in events}
    return sorted(deduped.values(), key=lambda item: (item["nominal"], item["name"])), set(valid)


def make_calendar(events, years, today):
    if today.year not in years:
        raise CalendarError("Current holiday dates are unavailable.")
    first = last = today.year
    while first - 1 in years:
        first -= 1
    while last + 1 in years:
        last += 1
    horizon = add_months(today, 12)
    start = max(date(first, 1, 1), today - timedelta(days=32))
    end = min(date(last, 12, 31), horizon + timedelta(days=32))
    by_date = {}
    for item in events:
        by_date.setdefault(item["effective"], []).append(item)
    days = []
    cursor = start
    while cursor <= end:
        rest = cursor.weekday() >= 5
        holidays = by_date.get(cursor, [])
        days.append({"date": cursor, "rest": rest, "free": rest or bool(holidays),
                     "relief": bool(holidays) and not rest, "events": holidays})
        cursor += DAY
    return days, horizon, end


def find_bridges(days):
    """Join complete natural free blocks; requested days can only be inner gaps."""
    blocks = []
    index = 0
    while index < len(days):
        if not days[index]["free"]:
            index += 1
            continue
        start = index
        while index + 1 < len(days) and days[index + 1]["free"]:
            index += 1
        # A block at a coverage edge may have unseen adjacent free days.
        if start > 0 and index < len(days) - 1:
            blocks.append((start, index))
        index += 1
    candidates = []
    for left, (start, _) in enumerate(blocks):
        cost = 0
        for right in range(left, len(blocks)):
            if right > left:
                cost += blocks[right][0] - blocks[right - 1][1] - 1
            if cost > 4:
                break
            end = blocks[right][1]
            span = days[start:end + 1]
            relief = [day["date"] for day in span if day["relief"]]
            if not relief:
                continue
            contributing = {item["id"]: item for day in span if day["relief"] for item in day["events"]}
            candidates.append({"start": span[0]["date"], "end": span[-1]["date"],
                               "cost": cost, "total": len(span), "days": span,
                               "leave": [day["date"] for day in span if not day["free"]],
                               "relief": relief, "events": list(contributing.values()),
                               "contains_rest": any(day["rest"] for day in span)})
    return candidates


def request_runs(dates):
    groups = []
    for day in sorted(set(dates)):
        if groups and day == groups[-1][-1] + DAY:
            groups[-1].append(day)
        else:
            groups.append([day])
    return groups


def candidate_rank(candidate):
    return (candidate["start"], -candidate["total"], len(request_runs(candidate["leave"])), candidate["end"])


def short_date(day, weekday=False):
    return ((WEEKDAYS[day.weekday()] + " ") if weekday else "") + str(day.day) + " " + MONTHS[day.month]


def date_range(start, end):
    cross_year = start.year != end.year
    if start == end:
        return short_date(start)
    if cross_year:
        return short_date(start) + "–" + short_date(end)
    if start.month == end.month:
        return str(start.day) + "–" + short_date(end)
    return short_date(start) + "–" + short_date(end)


def request_label(dates):
    groups = request_runs(dates)
    if not groups:
        return "No leave needed."
    common_month = len({(day.year, day.month) for day in dates}) == 1
    labels = []
    for group in groups:
        if len(group) == 1:
            labels.append((str(group[0].day) if common_month else short_date(group[0])))
        elif common_month:
            labels.append(str(group[0].day) + "–" + str(group[-1].day))
        else:
            labels.append(date_range(group[0], group[-1]))
    return " & ".join(labels) + ((" " + MONTHS[dates[0].month]) if common_month else "")


def break_countdown(days):
    if days < 0:
        return "Already underway"
    if days == 0:
        return "Starts today"
    if days == 1:
        return "Starts tomorrow"
    if days <= 14:
        return "Starts in " + str(days) + " days"
    if days < 56:
        return "Starts in " + ("" if days % 7 == 0 else "about ") + str((days + 3) // 7) + " weeks"
    return "Starts in about " + str(max(2, (days + 15) // 30)) + " months"


def holiday_family(item):
    key, origin = name_key(item["name"]), item["nominal"]
    if item.get("country") == "CZ":
        compact_names = {"independent czechoslovak state day": "Independence Day",
                         "struggle for freedom and democracy day": "Freedom & Democracy Day"}
        if key in compact_names:
            return compact_names[key]
    if item.get("country") == "ZA":
        if key == "family day" and origin.month in {3, 4} and origin.weekday() == 0:
            return "Easter"
        if key == "day of goodwill" and (origin.month, origin.day) == (12, 26):
            return "Christmas"
    if origin.month == 12 and origin.day in {24, 25, 26} and key in {
            "christmas eve", "christmas day", "christmas", "boxing day",
            "st. stephen's day", "saint stephen's day", "second day of christmas"}:
        return "Christmas"
    if origin.month == 1 and origin.day in {1, 2} and key in {"new year's day", "new year", "2 january"}:
        return "New Year"
    if origin.month in {3, 4, 5} and key in {"good friday", "easter monday", "easter sunday", "holy thursday", "maundy thursday"}:
        return "Easter"
    if origin.month in {3, 4, 5} and key in {"orthodox good friday", "orthodox easter monday", "orthodox easter sunday"}:
        return "Orthodox Easter"
    return item["name"]


def holiday_title(events):
    groups = []
    for item in sorted(events, key=lambda item: (item["effective"], item["name"])):
        title = holiday_family(item)
        if title not in groups:
            groups.append(title)
    if "Christmas" in groups and "New Year" in groups:
        position = min(groups.index("Christmas"), groups.index("New Year"))
        groups = [group for group in groups if group not in {"Christmas", "New Year"}]
        groups.insert(position, "Christmas & New Year")
    if len(groups) > 2:
        return groups[0] + " + " + str(len(groups) - 1) + " holidays"
    return " + ".join(groups)


def timeline(candidate):
    return [{"date": day["date"].isoformat(), "day": day["date"].day,
             "weekday": WEEKDAYS[day["date"].weekday()], "month": MONTHS[day["date"].month],
             "style": "holiday" if day["events"] else "rest" if day["rest"] else "leave",
             "label": "Holiday" if day["events"] else "Weekend" if day["rest"] else "Take off"}
            for day in candidate["days"]]


def format_card(candidate, today):
    days_until = (candidate["start"] - today).days
    names = list(dict.fromkeys(item["name"] for item in candidate["events"]))
    title = holiday_title(candidate["events"])
    return {"status": "available", "leave_cost": candidate["cost"],
            "title": title, "title_parts": title.split(" + ", 1), "holiday_names": names,
            "total_days": candidate["total"], "result": str(candidate["total"]) + " days off",
            "start_date": candidate["start"].isoformat(), "end_date": candidate["end"].isoformat(),
            "leave_dates": [day.isoformat() for day in candidate["leave"]],
            "holiday_relief_dates": [day.isoformat() for day in candidate["relief"]],
            "timeline": timeline(candidate),
            "request_label": request_label(candidate["leave"]),
            "break_label": date_range(candidate["start"], candidate["end"]),
            "days_until_start": days_until, "countdown_label": break_countdown(days_until)}


def ticket_candidate(candidate, today, horizon):
    # A free break already underway can still contain today's holiday.
    return (candidate["start"] < horizon and candidate["end"] >= today
            and candidate["contains_rest"] and candidate["total"] > 2
            and (not candidate["leave"] or candidate["start"] >= today and candidate["leave"][0] > today))


def ticket_from_bridge(candidate, events, today, combined=False):
    card = format_card(candidate, today)
    covered = [item for item in events if candidate["start"] <= item["effective"] <= candidate["end"]]
    anchors = [min(day for day in {item["nominal"], item["effective"]} if day >= today)
               for item in covered if max(item["nominal"], item["effective"]) >= today]
    anchor = min(anchors)
    card.update({"kind": "combined" if combined else "natural" if candidate["cost"] == 0 else "bridge",
                 "holiday_date": anchor.isoformat(), "holiday_ids": sorted(item["id"] for item in covered),
                 "countdown_label": break_countdown((anchor - today).days).removeprefix("Starts ")})
    return card


def ticket_for_date(items, today):
    # There is no extra leave opportunity when a holiday stays on a rest day,
    # or when the useful leave request is already too late to make.
    anchor = min(day for item in items for day in {item["nominal"], item["effective"]} if day >= today)
    weekend = all(item["effective"].weekday() >= 5 for item in items)
    weekday = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[items[0]["effective"].weekday()]
    title = holiday_title(items)
    return {"status": "weekend" if weekend else "day", "kind": "weekend" if weekend else "day",
            "leave_cost": None, "title": title, "holiday_names": list(dict.fromkeys(item["name"] for item in items)),
            "holiday_date": anchor.isoformat(), "holiday_ids": sorted(item["id"] for item in items),
            "countdown_label": break_countdown((anchor - today).days).removeprefix("Starts "),
            "total_days": 0 if weekend else 1, "leave_dates": [], "holiday_relief_dates": [],
            "start_date": anchor.isoformat(), "end_date": anchor.isoformat(),
            "break_label": short_date(anchor), "request_label": "",
            "weekend_line": [f"{weekday} called dibs.", f"{weekday}. Terrible timing.", f"{weekday} was already off. Oh no."][anchor.toordinal() % 3]
                            if weekend else "A day off. Still worth celebrating."}


def choose_tickets(events, candidates, today, horizon):
    """One useful entry per occasion; paid holiday combinations replace singles.

    Single holidays use their cheapest complete weekend bridge (0/1/2 PTO).
    A paid combination needs two distinct weekday holiday dates and a longer
    result than any of its component entries. Four PTO is reserved for a
    combination of separate holiday blocks longer than the ordinary nine-day,
    full-week-off result.
    """
    upcoming = [item for item in events if today <= max(item["nominal"], item["effective"]) < horizon]
    groups = {}
    for item in upcoming:
        groups.setdefault(item["effective"], []).append(item)
    available = [item for item in candidates if ticket_candidate(item, today, horizon)]
    natural = [(candidate, {item["id"] for day in candidate["days"] for item in day["events"]})
               for candidate in available if candidate["cost"] == 0]

    def build_singles(excluded=frozenset()):
        singles, accounted = [], set()
        for _, items in sorted(groups.items()):
            ids = {item["id"] for item in items}
            if ids <= accounted:
                continue
            free = [candidate for candidate, identities in natural if ids.intersection(identities)]
            if free:
                # Include weekend holiday dates inside the same natural break,
                # even when its weekday holiday is later in the date order.
                best = min(free, key=lambda item: (-item["total"], item["start"]))
            else:
                items = [item for item in items if item["id"] not in excluded | accounted]
                if not items:
                    continue
                ids = {item["id"] for item in items}
                related = []
                for candidate in available:
                    contributing = {item["id"] for item in candidate["events"]}
                    if (1 <= candidate["cost"] <= 2 and ids.intersection(contributing)
                            and not contributing.intersection(excluded | (accounted - ids))):
                        related.append(candidate)
                best = min(related, key=lambda item: (item["cost"], -item["total"], item["start"])) if related else None
            card = ticket_from_bridge(best, events, today) if best else ticket_for_date(items, today)
            if best and best["cost"]:
                card["holiday_ids"] = sorted(item["id"] for item in best["events"])
            accounted.update(card["holiday_ids"])
            singles.append(card)
        return singles

    singles = build_singles()

    combinations = {}
    for candidate in available:
        if not 1 <= candidate["cost"] <= 4 or len(set(candidate["relief"])) < 2:
            continue
        if candidate["cost"] == 4 and candidate["total"] <= 9:
            continue
        if candidate["cost"] == 4:
            holiday_blocks, counted = 0, False
            for day in candidate["days"]:
                if not day["free"]:
                    counted = False
                elif day["relief"] and not counted:
                    holiday_blocks += 1
                    counted = True
            if holiday_blocks < 2:
                continue
        card = ticket_from_bridge(candidate, events, today, combined=True)
        ids = set(card["holiday_ids"])
        components = [item for item in singles if ids.intersection(item["holiday_ids"])]
        if not components or candidate["total"] <= max(item["total_days"] for item in components):
            continue
        key = frozenset(item["id"] for item in candidate["events"])
        prior = combinations.get(key)
        if prior is None or (-card["total_days"], card["leave_cost"], card["start_date"]) < (
                -prior["total_days"], prior["leave_cost"], prior["start_date"]):
            combinations[key] = card

    selected, covered = [], set()
    for card in sorted(combinations.values(), key=lambda item: (item["holiday_date"], -item["total_days"], item["leave_cost"])):
        ids = set(card["holiday_ids"])
        overlap = any(card["start_date"] <= other["end_date"] and other["start_date"] <= card["end_date"] for other in selected)
        if ids.intersection(covered) or overlap:
            continue
        selected.append(card)
        covered.update(ids)
    # Recompute remaining paid singles without already-used holidays. Simply
    # dropping overlapping cards can silently lose the uncovered half of one.
    selected.extend(build_singles(covered))
    return sorted(selected, key=lambda item: (item["holiday_date"], item["leave_cost"] != 0, item["start_date"], item["title"]))


def daily_line(variants, today):
    """Rotate a scenario's wording by the reader's local date, without state."""
    return variants[today.toordinal() % len(variants)]


def leave_phrase(count):
    return f"{count} {'day' if count == 1 else 'days'} of leave"


def choose_hero(events, candidates, today):
    display = []
    for item in events:
        for day in {item["nominal"], item["effective"]}:
            if day >= today:
                display.append((day, item))
    if not display:
        return {"status": "empty", "name": "No upcoming holiday listed", "headline": "More holidays will come.",
                "date_label": "", "countdown_label": "", "story": "Waiting for the next published dates.", "timeline": []}
    next_date = min(day for day, _ in display)
    selected = {item["id"]: item for day, item in display if day == next_date}
    items = list(selected.values())
    names = list(dict.fromkeys(item["name"] for item in items))
    display_names = list(dict.fromkeys(
        item["name"] + (" (observed)" if next_date == item["effective"] != item["nominal"] else "")
        for item in items))
    effective_dates = {item["effective"] for item in items if item["effective"].weekday() < 5}
    distance = (next_date - today).days
    hero = {"status": "holiday", "holiday_date": next_date.isoformat(), "holiday_names": names,
            "name": " + ".join(display_names), "date_label": short_date(next_date, weekday=True),
            "day": next_date.day, "month": MONTHS[next_date.month], "weekday": WEEKDAYS[next_date.weekday()],
            "days_until": distance, "countdown_label": "Today" if distance == 0 else "Tomorrow" if distance == 1 else "In " + str(distance) + " days",
            "headline": "A day to look forward to.", "story": "", "request_label": "", "break_label": "",
            "total_days": 0, "leave_cost": 0, "timeline": [], "observed_label": ""}
    observed = [item for item in items if item["effective"] != item["nominal"]]
    if observed:
        hero["observed_label"] = "Day off: " + " & ".join(short_date(item["effective"], weekday=True) for item in observed)
    related = [candidate for candidate in candidates if candidate["contains_rest"]
               and effective_dates.intersection(candidate["relief"])
               and candidate["end"] >= today
               and (not candidate["leave"] or candidate["leave"][0] > today and candidate["start"] >= today)]
    chosen = min(related, key=lambda item: (item["cost"],) + candidate_rank(item)) if related else None
    if chosen:
        hero.update({key: value for key, value in format_card(chosen, today).items()
                     if key not in {"holiday_names", "title", "status", "countdown_label"}})
        hero["timeline"] = timeline(chosen)
        if chosen["cost"] == 0:
            hero["status"] = "natural"
            total = chosen["total"]
            hero["headline"] = daily_line([
                f"{total} days. All yours.", f"{total} days off. No forms.",
                f"A free {total}-day escape.", f"{total} days off, on the house."], today)
            hero["story"] = "Enjoy the extra day." if distance == 0 else "A longer weekend. No leave needed."
            if chosen["start"] < today:
                hero["story"] = "Your longer break is already underway."
        else:
            hero["status"] = "bridge"
            total = chosen["total"]
            hero["headline"] = daily_line([
                f"Fancy {total} days off?", f"{total} days off? Yes, please.",
                f"Use {chosen['cost']} {'day' if chosen['cost'] == 1 else 'days'}. Get {total} off.", f"Make room for {total} days off."], today)
            hero["story"] = "Use " + leave_phrase(chosen["cost"]) + ". Enjoy " + str(chosen["total"]) + " days off."
    elif not effective_dates and next_date.weekday() >= 5:
        hero["status"] = "weekend"
        hero["headline"] = daily_line([
            "Already a weekend.", "The weekend called dibs.",
            "A holiday with bad timing.", "Oh no. A weekend holiday."], today)
        hero["story"] = "Falls on " + ("Saturday" if next_date.weekday() == 5 else "Sunday") + ". Unfortunate timing."
        # Show the holiday in its weekend context; this is not an extra break.
        saturday = next_date - timedelta(days=next_date.weekday() - 5)
        named_dates = {item["nominal"] for item in events}
        hero["timeline"] = [{"date": day.isoformat(), "day": day.day, "weekday": WEEKDAYS[day.weekday()],
                             "month": MONTHS[day.month], "style": "holiday" if day in named_dates else "rest",
                             "label": "Holiday" if day in named_dates else "Weekend"}
                            for day in (saturday, saturday + DAY)]
    else:
        hero["headline"] = daily_line([
            "A day to look forward to.", "A little pause, all yours.",
            "Your calendar says: relax.", "One holiday. Many good plans."], today)
        hero["story"] = "Enjoy your holiday." if distance == 0 else "An extra day to make your own."
    return hero


def build_model(calendar_id, years, today, uk=None):
    if calendar_id not in CALENDARS:
        raise CalendarError("Choose a supported holiday calendar in plugin settings.")
    if not isinstance(today, date) or isinstance(today, datetime):
        raise CalendarError("The planning date is invalid.")
    profile = CALENDARS[calendar_id]
    events, valid_years = normalize_holidays(years, profile, uk)
    days, horizon, verified_through = make_calendar(events, valid_years, today)
    # A Saturday New Year is observed on the preceding Friday. Without that
    # adjacent source year, Dec 31 cannot be treated as an ordinary workday.
    if (profile["country"] == "US" and verified_through.month == 12 and verified_through.day == 31
            and date(verified_through.year + 1, 1, 1).weekday() == 5
            and verified_through.year + 1 not in valid_years):
        days = days[:-1]
        verified_through -= DAY
    partial = verified_through < horizon + timedelta(days=7)
    candidates = find_bridges(days)
    last_known_year = today.year
    while last_known_year + 1 in valid_years:
        last_known_year += 1
    # Do not call an event "next" by jumping over an unpublished source year.
    hero_events = [item for item in events
                   if min(item["nominal"], item["effective"]).year <= last_known_year]
    hero = choose_hero(hero_events, candidates, today)
    tickets = choose_tickets(hero_events, candidates, today, horizon)
    if not events and profile.get("source_baseline"):
        hero.update({"name": "No national holidays listed", "headline": "No nationwide dates to plan around.",
                     "story": "The source has no national public holidays to plan around."})
    return {"schema_version": 1, "status": "partial" if partial else "ok",
            "planning_date": today.isoformat(), "snapshot_label": short_date(today),
            "calendar": {"id": calendar_id, "label": profile["label"], "status": "partial" if partial else "ok",
                         "scope_note": profile.get("scope_note", "Standard Monday–Friday workweek."),
                         "source_baseline": profile.get("source_baseline", False)},
            "horizon": {"months": 12, "end_exclusive": horizon.isoformat()},
            "hero": hero,
            "tickets": tickets[:5],
            "data_quality": {"status": "partial" if partial else "ok", "verified_through": verified_through.isoformat()},
            "notice": "Some future holiday dates are unavailable." if partial else ""}


WORLD_MATH_COUNTRIES = frozenset(("CZ", "BE", "IE", "NL", "PL", "SG", "ZA", "DE", "SK", "HR", "FR", "US"))
WORLD_NO_FIXED_SHIFT = {"CZ", "DE", "SK", "HR", "FR"}


def world_unavailable():
    return {"status": "unavailable", "heading": "Somewhere, it's a holiday.",
            "location_label": "A little world tour, on pause.", "name": "Checking the next holiday dates.",
            "headline": "The world calendar is taking a breather."}


def world_now(payload):
    stamp = ((payload.get("trmnl") or {}).get("system") or {}).get("timestamp_utc")
    try:
        if isinstance(stamp, (int, float)) or isinstance(stamp, str) and stamp.isdigit():
            return datetime.fromtimestamp(float(stamp), timezone.utc)
        if isinstance(stamp, str):
            value = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        pass
    return datetime.now(timezone.utc)


def validate_world_opportunity(value, row):
    if value is None:
        return None
    if not isinstance(value, dict) or row["country_code"] not in WORLD_MATH_COUNTRIES:
        raise CalendarError("Unreviewed world opportunity rules.")
    kind, cost, total = value.get("kind"), value.get("cost"), value.get("total")
    if kind not in {"break", "weekend", "day"} or type(cost) is not int or not 0 <= cost <= 4 or type(total) is not int:
        raise CalendarError("Invalid world opportunity values.")
    effective = parse_date(value.get("effective_date"))
    if type(value.get("observed")) is not bool or value["observed"] != (effective.isoformat() != row["date"]):
        raise CalendarError("Invalid world observed date.")
    pto_dates = value.get("pto_dates")
    if not isinstance(pto_dates, list) or len(pto_dates) != cost or pto_dates != sorted(set(pto_dates)):
        raise CalendarError("Invalid world leave dates.")
    if kind == "break":
        start, end = parse_date(value.get("break_start")), parse_date(value.get("break_end"))
        if not start <= effective <= end or total != (end - start).days + 1 or total <= 2:
            raise CalendarError("Invalid world break range.")
        if any(not start <= parse_date(day) <= end or parse_date(day).weekday() >= 5 for day in pto_dates):
            raise CalendarError("Invalid world leave range.")
    elif cost != 0 or total != 0 or pto_dates or value.get("break_start") is not None or value.get("break_end") is not None:
        raise CalendarError("Invalid world single-day opportunity.")
    if kind == "weekend" and effective.weekday() < 5:
        raise CalendarError("Invalid world weekend date.")
    return dict(value)


def world_calendar_times(value):
    """Source age survives republication; old feeds use their global minimum."""
    generated = datetime.fromisoformat(value["generated_at"].replace("Z", "+00:00"))
    stamps = value.get("country_calendar_at")
    if "country_calendar_at" not in value:
        oldest = value["coverage"].get("oldest_calendar_at")
        stamps = {code: oldest for code in value["countries"]} if oldest else {}
    if not isinstance(stamps, dict) or any(code not in value["countries"] for code in stamps):
        raise CalendarError("Invalid world calendar timestamps.")
    times = {}
    for code, stamp in stamps.items():
        if not isinstance(stamp, str):
            raise CalendarError("Invalid world calendar timestamp.")
        fetched = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if fetched.tzinfo is None or fetched > generated:
            raise CalendarError("Invalid world calendar clock.")
        times[code] = fetched
    return times


def validate_world_feed(value, today, now):
    if (not isinstance(value, dict) or value.get("schema_version") != 1 or value.get("source") != "nager-v4"
            or value.get("policy_version") != "pto-world-math-1"):
        raise CalendarError("Unsupported world snapshot.")
    first, last = parse_date(value.get("coverage_start")), parse_date(value.get("coverage_end"))
    if not first <= today <= last or (last - first).days > 40:
        raise CalendarError("World dates do not cover today.")
    generated = datetime.fromisoformat(value["generated_at"].replace("Z", "+00:00"))
    if generated.tzinfo is None or not -900 <= (now - generated).total_seconds() < 72 * 3600:
        raise CalendarError("World snapshot is too old or has an invalid clock.")
    countries, coverage, days = value.get("countries"), value.get("coverage"), value.get("days")
    if (not isinstance(countries, dict) or not 1 <= len(countries) <= 500 or not isinstance(coverage, dict)
            or not isinstance(days, dict)):
        raise CalendarError("Invalid world coverage.")
    if any(not re.fullmatch(r"[A-Z]{2}", code) or not isinstance(name, str) or not name.strip()
           for code, name in countries.items()):
        raise CalendarError("Invalid world countries.")
    counts = [coverage.get(key) for key in ("fresh", "stale", "missing")]
    if any(type(count) is not int or count < 0 for count in counts) or sum(counts) != len(countries):
        raise CalendarError("Invalid world coverage counts.")
    if coverage.get("catalogue_countries") != len(countries):
        raise CalendarError("Invalid world catalogue size.")
    for key, count in (("stale_country_codes", coverage["stale"]), ("missing_country_codes", coverage["missing"])):
        codes = coverage.get(key)
        if not isinstance(codes, list) or len(set(codes)) != count or any(code not in countries for code in codes):
            raise CalendarError("Invalid world quality metadata.")
    source_times = world_calendar_times(value)
    usable = {code for code, fetched in source_times.items() if (now - fetched).total_seconds() < 72 * 3600}
    rows, seen = [], set()
    for day, on_day in days.items():
        actual = parse_date(day)
        if not first <= actual <= last or not isinstance(on_day, list):
            raise CalendarError("Invalid world candidate window.")
        for raw in on_day:
            if (not isinstance(raw, dict) or raw.get("date") != day or raw.get("country_code") not in countries
                    or not isinstance(raw.get("name"), str) or not raw["name"].strip() or len(raw["name"]) > 1000):
                raise CalendarError("Invalid world holiday.")
            row = dict(raw)
            row["opportunity"] = validate_world_opportunity(row.get("opportunity"), row)
            row["id"] = row["country_code"] + ":" + day + ":" + row["name"]
            if row["country_code"] in usable and row["id"] not in seen:
                seen.add(row["id"])
                rows.append(row)
    return rows


def build_world(payload, model, today, rng=None):
    """Consume one shared snapshot; select randomly and choose copy by date."""
    rng = rng or random.SystemRandom()
    snapshot = payload.get("world_snapshot")
    if "world_snapshot" not in payload:
        snapshots = [node for node in polling_nodes(payload)
                     if isinstance(node, dict) and node.get("source") == "nager-v4"]
        snapshot = snapshots[0] if len(snapshots) == 1 else None
    try:
        rows = validate_world_feed(snapshot, today, world_now(payload))
        own_country = model["calendar"]["id"].split("-")[0].upper()
        pool = [row for row in rows if row["country_code"] != own_country and row["date"] >= today.isoformat()]
        if not pool:
            return world_unavailable()
        nearest = min(row["date"] for row in pool)
        featured = rng.choice([row for row in pool if row["date"] == nearest])
        opportunity = featured["opportunity"]
        if opportunity:
            opportunity = dict(opportunity)
            opportunity["past_request"] = bool(opportunity["pto_dates"] and parse_date(opportunity["pto_dates"][0]) <= today)
        headline = world_commentary(featured, opportunity, today)
        anchor = parse_date(featured["date"])
        distance = (anchor - today).days
        location = "Today in " if distance == 0 else "Tomorrow in " if distance == 1 else short_date(anchor) + " in "
        quality = snapshot["coverage"]
        source_times = world_calendar_times(snapshot)
        expired = any(code not in source_times or (world_now(payload) - source_times[code]).total_seconds() >= 72 * 3600
                      for code in snapshot["countries"])
        partial = quality["missing"] > 0 or quality.get("catalogue_stale", False) or expired
        cached = quality["stale"] > 0 or (world_now(payload) - datetime.fromisoformat(snapshot["generated_at"].replace("Z", "+00:00"))).total_seconds() > 36 * 3600
        note = "Partial world coverage" if partial else "Cached world dates" if cached else ""
        return {"status": "cached" if note else "ok", "heading": "Somewhere, it's a holiday.",
                "location_label": location + snapshot["countries"][featured["country_code"]],
                "name": featured["name"], "country_code": featured["country_code"], "date": featured["date"],
                "id": featured["id"], "headline": headline, "opportunity": opportunity,
                "source": "Nager v4", "source_note": note, "snapshot_version": snapshot["version"],
                "selection": "today" if distance == 0 else "nearest_known_date"}
    except (CalendarError, ValueError, TypeError, KeyError, AttributeError):
        return world_unavailable()


WORLD_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# These countries have date facts but no reviewed leave entitlement. Give each
# weekday its own voice without turning a tempting date into a promised break.
WORLD_DATE_LINES = (
    ("Monday arrives with a holiday. A surprisingly good opening argument.",
     "A holiday on Monday. Someone gave the start of the week a personality.",
     "Monday has a holiday in its diary. That's one way to improve its reputation.",
     "Monday gets top billing over there. Usually a difficult booking.",
     "A Monday holiday. Even the calendar can make a decent first impression.",
     "Monday brought an occasion. Better than its usual conversation starter.",
     "Their holiday picked Monday. An unusually charming entrance.",
     "Monday has something to celebrate. An unexpected plot twist over there."),
    ("A Tuesday holiday. Close enough to Monday to start a little daydreaming.",
     "Tuesday gets the occasion. Monday is reading the invitation with interest.",
     "A holiday on Tuesday. An excellent plot twist near the start of the week.",
     "Tuesday has festive plans. Monday is pretending it isn't jealous.",
     "Their holiday picked Tuesday. A date with interesting neighbours.",
     "Tuesday brought a holiday. Monday is trying to get on the guest list.",
     "A Tuesday celebration. Plenty for a calendar enthusiast to think about.",
     "Tuesday gets a starring role. Monday is auditioning for the supporting part."),
    ("A Wednesday holiday. A plot twist right in the middle of the week.",
     "Wednesday gets the occasion. The week now has a rather interesting centre.",
     "A holiday on Wednesday. The calendar has installed an intermission.",
     "Wednesday brought a holiday. Excellent placement for a change of scene.",
     "Their holiday picked Wednesday. Both ends of the week are taking notes.",
     "Wednesday is the main event over there. The week has a new centre of gravity.",
     "A Wednesday celebration. The middle of the diary suddenly looks promising.",
     "Wednesday gets a festive chapter. A welcome twist in the usual storyline."),
    ("A Thursday holiday. Friday is reading the invitation with interest.",
     "Thursday gets the occasion. Friday is pretending it isn't jealous.",
     "A holiday on Thursday. The calendar has saved a late-week surprise.",
     "Thursday brought a holiday. Friday is trying to join the conversation.",
     "Their holiday picked Thursday. Calendar enthusiasts can see the potential.",
     "Thursday has festive plans. Friday is hovering near the guest list.",
     "A Thursday celebration. The diary is practically winking at Friday.",
     "Thursday gets the spotlight. Friday is auditioning for the supporting part."),
    ("A Friday holiday. The date certainly knows how to make an entrance.",
     "Friday gets the occasion. A strong finish for that page of the diary.",
     "A holiday on Friday. The calendar saved its best headline for last.",
     "Friday brought a holiday. Subtle timing was never the plan.",
     "Their holiday picked Friday. An excellent instinct for scheduling.",
     "Friday has festive plans. The diary ends the week with a flourish.",
     "A Friday celebration. That date came dressed for the occasion.",
     "Friday gets top billing. The calendar clearly understands an encore."),
    ("Saturday gets the holiday. Two occasions, one square on the calendar.",
     "A Saturday holiday. The date is double-booked for good reasons.",
     "Saturday brought an occasion. Apparently one headline wasn't enough.",
     "Their holiday picked Saturday. The diary is hosting a double feature.",
     "Saturday has a holiday to its name. A small square with a full social life.",
     "A holiday on Saturday. That date won't be short of conversation.",
     "Saturday gets the spotlight. The calendar has dressed up the occasion.",
     "A Saturday celebration. One date, an extra reason to remember it."),
    ("Sunday gets the holiday. One date with rather a lot on the invitation.",
     "A Sunday holiday. The calendar is layering its occasions.",
     "Sunday brought a celebration. A lively footnote to that week's diary.",
     "Their holiday picked Sunday. The date has acquired a second title.",
     "Sunday has festive plans. That's a fuller diary square than usual.",
     "A holiday on Sunday. One date doing double duty on the calendar.",
     "Sunday gets the occasion. A memorable closing line for the week.",
     "A Sunday celebration. The calendar put a little extra ink on that date."),
)


def world_leave_days(opportunity):
    """Name the actual bridge dates, without ambiguous repeated weekdays."""
    dates = [parse_date(day) for day in opportunity.get("pto_dates", [])]
    if not dates:
        return ""
    if (dates[-1] - dates[0]).days >= 7:
        return ", ".join(date_range(group[0], group[-1]) for group in request_runs(dates))
    labels = []
    for group in request_runs(dates):
        first, last = WORLD_WEEKDAYS[group[0].weekday()], WORLD_WEEKDAYS[group[-1].weekday()]
        if len(group) == 1:
            labels.append(first)
        elif len(group) == 2:
            labels.append(first + " + " + last)
        else:
            labels.append(first + " to " + last)
    return " + ".join(labels)


def world_commentary(featured, opportunity, today):
    day = parse_date(featured["date"])
    weekday = WORLD_WEEKDAYS[day.weekday()]
    swallowed = bool(opportunity and opportunity["kind"] == "weekend" and featured["country_code"] in WORLD_NO_FIXED_SHIFT)
    if swallowed:
        variants = [f"{weekday} ate their holiday. No extra day off; absolutely no manners.",
                    f"A {weekday} holiday, with no weekday rescue. The calendar owes them one.",
                    f"Their holiday and {weekday} share a seat. One fewer reason to love this calendar.",
                    f"{weekday} keeps the holiday. Their leave balance gets no consolation prize.",
                    f"A holiday on {weekday}. Even the calendar can be a terrible negotiator.",
                    f"{weekday} double-booked itself. A celebration, but no extra weekday off.",
                    f"Their holiday landed on {weekday}. The occasion survives; the extra day doesn't.",
                    f"{weekday} got a holiday upgrade. Their working week got nothing."]
    elif opportunity and opportunity["kind"] == "break":
        total, cost = opportunity["total"], opportunity["cost"]
        leave = leave_phrase(cost)
        effective_day = WORLD_WEEKDAYS[parse_date(opportunity["effective_date"]).weekday()]
        moved = opportunity["observed"]
        if cost == 0 and moved:
            variants = [f"Their day off moves to {effective_day}: {total} days off, no leave spent. A tidy rescue.",
                        f"Observed on {effective_day}. They get {total} days off; the leave balance stays put.",
                        f"{effective_day} catches their holiday. A {total}-day break, no leave needed.",
                        f"The date moves; their leave balance doesn't. {effective_day} brings {total} days off.",
                        f"A substitute {effective_day}, a {total}-day break for them. No leave forms in this story.",
                        f"Their holiday gets a {effective_day} encore: {total} days off, no leave to book.",
                        f"{effective_day} saves the occasion. They get {total} days off without spending leave.",
                        f"Observed on {effective_day}: {total} days off for them. Their calendar picks up the bill."]
        elif cost == 0:
            variants = [f"A {weekday} holiday brings {total} days off. Their leave balance can sit this one out.",
                        f"{total} days off, no leave needed. Their {weekday} holiday came with good neighbours.",
                        f"{weekday} does the heavy lifting for them: {total} days off, zero leave spent.",
                        f"Their {total}-day break is on the house. No leave forms were involved.",
                        f"They get {total} days off without spending leave. Their diary is feeling generous.",
                        f"Their holiday brought company: {total} days off, no leave to book.",
                        f"They get {total} days off. No leave spent. Sometimes their calendar gets it exactly right.",
                        f"A {total}-day break for no leave at all. Their calendar deserves a thank-you note."]
        else:
            bridge = world_leave_days(opportunity)
            past = opportunity["past_request"]
            if moved:
                # Use the effective weekday and preserve retrospective tense.
                tense = "could have made" if past else "could make"
                variants = [f"Their observed {effective_day}: {leave} {tense} {total} days off. Nice save.",
                            f"Their moved {effective_day} holiday {tense} {total} days off with {leave}.",
                            f"Their substitute {effective_day} {tense} a {total}-day escape with {leave}.",
                            f"{effective_day} rescues their date. {leave} {tense} {total} days off.",
                            f"A {effective_day} encore for them. {leave} {tense} {total} days off.",
                            f"Observed on {effective_day}. With {leave}, they {tense} {total} days off.",
                            f"A {effective_day} rescue for them: {leave} {tense} {total} days off.",
                            f"Their substitute {effective_day}: {leave} {tense} {total} days off. A tidy trade."]
                if bridge:
                    action = f"They needed {bridge}." if past else f"Their bridge: {bridge}."
                    variants = [line + " " + action for line in variants]
            elif past:
                needed = f"They needed {bridge}: " if bridge else f"Their {weekday} holiday: "
                variants = [f"{needed}{leave} could have made {total} days off. Early birds win this one.",
                            f"A bridge with a deadline. {needed}{leave} could have made {total} days off.",
                            f"Their calendar had hidden talent. {needed}{leave} could have made {total} days off.",
                            f"{needed}{leave} could have made {total} days off. A small request, a big escape.",
                            f"One for the organised. {needed}{leave} could have made {total} days off.",
                            f"{needed}{leave} could have made {total} days off. The trick was asking earlier.",
                            f"A missed connection in the diary. {needed}{leave} could have made {total} days off.",
                            f"{needed}{leave} could have made {total} days off. Good deal; early booking required."]
            else:
                on_days = f"on {bridge}" if bridge else "to bridge the gap"
                taking_days = f"by taking {bridge} off" if bridge else "by bridging the gap"
                connector = f"{bridge} off" if bridge else "A little bridge"
                variants = [f"Their {weekday} holiday could stretch to {total} days off with {leave} {on_days}.",
                            f"{connector} could give them {total} days off for {leave}. Quite the calendar trick.",
                            f"They could turn {leave} {on_days} into {total} days off. Small request, big escape.",
                            f"They could get {total} days off {taking_days}. A lot of breathing room for {leave}.",
                            f"A little leave goes a long way over there: {leave} {on_days} could mean {total} days off.",
                            f"Their holiday has hidden talent: {total} days off for {leave} {on_days}.",
                            f"Their calendar left a gap worth closing: {leave} {on_days} could mean {total} days off.",
                            f"They could get {total} days off with just {leave} {on_days}. Their calendar does the rest."]
    elif opportunity and opportunity["kind"] == "day":
        weekday = WORLD_WEEKDAYS[parse_date(opportunity.get("effective_date", featured["date"])).weekday()]
        variants = [f"A {weekday} off for them. A small island of freedom in their working week.",
                    f"Their {weekday} holiday stands alone. Even a one-day intermission has its charms.",
                    f"Their {weekday} gets a pause button. One day off can still change the mood of a week.",
                    f"A standalone {weekday} off for them. No grand escape, just a welcome change of pace.",
                    f"Their holiday gives {weekday} a different job description: one day to themselves.",
                    f"One {weekday} off for them. A modest calendar rebellion, but a welcome one.",
                    f"{weekday} steps out of their working week. A little breathing room counts too.",
                    f"Their {weekday} holiday has no longer break attached. Still a good excuse for a slower day."]
    else:
        variants = WORLD_DATE_LINES[day.weekday()]
    return daily_line(variants, today)


def run(input):
    calendar_id = ""
    try:
        calendar_id, today = read_context(input)
        years, uk = read_polling_data(input)
        model = build_model(calendar_id, years, today, uk)
        try:
            model["world"] = build_world(input, model, today)
        except Exception:
            # Discovery is optional: its failure must never replace local plans.
            model["world"] = world_unavailable()
        return model
    except (CalendarError, TypeError, KeyError, ValueError) as exc:
        return {"schema_version": 1, "status": "error", "planning_date": "", "snapshot_label": "",
                "calendar": {"id": calendar_id, "label": CALENDARS.get(calendar_id, {}).get("label", "Holiday Multiplier"), "status": "error"},
                "hero": {"status": "unavailable", "name": "Holiday calendar unavailable", "headline": "Let's get your dates back.",
                         "story": str(exc), "date_label": "", "countdown_label": "", "timeline": []},
                "tickets": [],
                "data_quality": {"status": "unavailable"}, "notice": str(exc)}
