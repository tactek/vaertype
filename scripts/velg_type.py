#!/usr/bin/env python3
"""Pick which weather type the front-page weather strip should show. Standard library only.

Reads Harald's per-paper weather files (the same numbers the strip shows), the paper's
locations and MET's current weather alerts, applies the rules in README.md and writes
public/<domain>.json. The strip reads only "weathertype"; the other fields explain the choice.

Run with --dry-run to print the result without writing anything.
"""
import csv
import json
import statistics
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
LOG_DIR = ROOT / "logg"
OSLO = ZoneInfo("Europe/Oslo")

DOMAINS = ("vestnytt.no", "av-avis.no")
DATA_URL = "https://smps3.ams3.digitaloceanspaces.com/weather-data/{domain}/{kind}_data.json"
LOCATIONS_URL = "https://smpdev.no/weather-location/locations/{domain}"
ALERTS_URL = "https://api.met.no/weatherapi/metalerts/2.0/current.json"
# MET requires a User-Agent that identifies the app and how to reach its owner.
USER_AGENT = "vaertype/1.0 (+https://github.com/tactek/vaertype)"

# Thresholds are first guesses; tune them after the silent trial period (see logg/).
WIND_SPEED = 10.8  # m/s mean wind, "liten kuling"
WIND_GUST = 17.0  # m/s
RAIN_MAX = 3.0  # mm/h at a single place
RAIN_WIDESPREAD = 1.0  # mm/h ...
RAIN_WIDESPREAD_SHARE = 0.5  # ... at this share of places
# Unusually warm when the warmest place reaches WARM_FROM[month], unusually cold when the
# coldest place drops to COLD_TO[month]. Hand-set for the coast around Bergen.
WARM_FROM = {1: 10, 2: 10, 3: 12, 4: 16, 5: 20, 6: 23, 7: 25, 8: 24, 9: 20, 10: 16, 11: 12, 12: 10}
COLD_TO = {1: -5, 2: -5, 3: -3, 4: -1, 5: 2, 6: 5, 7: 7, 8: 6, 9: 3, 10: 0, 11: -2, 12: -4}
# Never default to precipitation: on a dry day the strip would show only zeros.
SEASON_DEFAULT = {12: "cold", 1: "cold", 2: "cold", 9: "wind", 10: "wind", 11: "wind"}  # else warm
MIN_HOLD = timedelta(hours=3)
MAX_DATA_AGE = timedelta(hours=2)

# Only land alerts that start at sea level count. Marine gale warnings cover the outer
# islands most autumn days and would otherwise keep the strip on wind.
ALERT_TYPES = {
    "wind": "wind", "polarLow": "wind", "blowingSnow": "wind",
    "rain": "precipitation", "rainFlood": "precipitation", "snow": "precipitation",
}
ALERT_COLOURS = {"yellow": "Gult", "orange": "Oransje", "red": "Rødt"}
RULE_PRIORITY = {"farevarsel": 1, "vind": 2, "nedbør": 3, "temperatur": 4, "årstid": 5}
MONTHS = ("januar", "februar", "mars", "april", "mai", "juni", "juli",
          "august", "september", "oktober", "november", "desember")
TYPES = ("warm", "cold", "wind", "precipitation")


def fmt(value):
    return f"{value:.1f}".replace(".", ",")


def place(entry):
    return entry["areaname"].split(",")[0]


def candidate(rule, weathertype, reason):
    return {"weathertype": weathertype, "rule": rule, "reason": reason}


def in_ring(lon, lat, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def in_geometry(lon, lat, geometry):
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return any(in_ring(lon, lat, poly[0]) and not any(in_ring(lon, lat, hole) for hole in poly[1:])
               for poly in polygons)


def alert_rule(alerts, locations):
    """Return the most serious land alert covering at least one of the paper's places."""
    best = None
    for feature in alerts:
        props = feature["properties"]
        weathertype = ALERT_TYPES.get(props.get("event"))
        if (weathertype is None or props.get("geographicDomain") != "land"
                or (props.get("altitude_above_sea_level") or 0) > 0):
            continue
        if not any(in_geometry(loc["lon"], loc["lat"], feature["geometry"]) for loc in locations):
            continue
        level, colour = props["awareness_level"].split("; ")[:2]
        # Ties go to wind, which comes first in the rule order.
        rank = (int(level), weathertype == "wind")
        if best is None or rank > best[0]:
            reason = f"{ALERT_COLOURS.get(colour, colour)} farevarsel: {props['eventAwarenessName']}, {props['area']}"
            best = (rank, candidate("farevarsel", weathertype, reason))
    return best[1] if best else None


def evaluate(now, temps, winds, rain, alerts, locations):
    """Apply the rules in priority order and return the first that matches."""
    found = alert_rule(alerts, locations)
    if found:
        return found

    windiest = max(winds, key=lambda e: e["wind_speed"])
    gustiest = max(winds, key=lambda e: e["wind_speed_of_gust"])
    if windiest["wind_speed"] >= WIND_SPEED:
        return candidate("vind", "wind", f"Middelvind {fmt(windiest['wind_speed'])} m/s på {place(windiest)}")
    if gustiest["wind_speed_of_gust"] >= WIND_GUST:
        return candidate("vind", "wind", f"Vindkast {fmt(gustiest['wind_speed_of_gust'])} m/s på {place(gustiest)}")

    wettest = max(rain, key=lambda e: e["precipitation_rate"])
    raining = sum(e["precipitation_rate"] >= RAIN_WIDESPREAD for e in rain)
    if wettest["precipitation_rate"] >= RAIN_MAX:
        return candidate("nedbør", "precipitation", f"{fmt(wettest['precipitation_rate'])} mm/t på {place(wettest)}")
    if raining >= RAIN_WIDESPREAD_SHARE * len(rain):
        return candidate("nedbør", "precipitation", f"Minst {fmt(RAIN_WIDESPREAD)} mm/t på {raining} av {len(rain)} steder")

    warmest = max(temps, key=lambda e: e["air_temperature"])
    coldest = min(temps, key=lambda e: e["air_temperature"])
    warm_excess = warmest["air_temperature"] - WARM_FROM[now.month]
    cold_excess = COLD_TO[now.month] - coldest["air_temperature"]
    if max(warm_excess, cold_excess) >= 0:
        entry, weathertype = (warmest, "warm") if warm_excess >= cold_excess else (coldest, "cold")
        return candidate("temperatur", weathertype,
                         f"{fmt(entry['air_temperature'])} grader på {place(entry)}, uvanlig for {MONTHS[now.month - 1]}")

    return candidate("årstid", SEASON_DEFAULT.get(now.month, "warm"),
                     f"Ikke noe uvanlig vær nå, standard for {MONTHS[now.month - 1]}")


def apply_hold(now, found, previous):
    """Keep the shown type for MIN_HOLD unless a more important rule takes over."""
    stamp = now.isoformat(timespec="minutes")
    try:
        since = datetime.fromisoformat(previous["since"])
        valid = previous["weathertype"] in TYPES
    except (TypeError, KeyError, ValueError):
        valid = False
    if valid:
        if found["weathertype"] == previous["weathertype"]:
            return {**found, "since": previous["since"], "updated": stamp}
        more_important = RULE_PRIORITY[found["rule"]] < RULE_PRIORITY.get(previous.get("rule"), 5)
        if not more_important and now - since < MIN_HOLD:
            return {key: previous[key] for key in ("weathertype", "rule", "reason", "since")} | {"updated": stamp}
    return {**found, "since": stamp, "updated": stamp}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response), response.headers.get("Last-Modified")


def fetch_weather(domain, now):
    """Return the three lists the rules need, or raise if any file is missing or old."""
    lists = {}
    for kind in ("warm", "wind", "precipitation"):
        body, modified = fetch(DATA_URL.format(domain=domain, kind=kind))
        # updated_time in the files is year-day-month, so trust the HTTP header instead.
        if modified and now - parsedate_to_datetime(modified) > MAX_DATA_AGE:
            raise RuntimeError(f"{kind}_data.json er eldre enn {MAX_DATA_AGE}")
        if not body.get("data"):
            raise RuntimeError(f"{kind}_data.json er tom")
        lists[kind] = body["data"]
    return lists["warm"], lists["wind"], lists["precipitation"]


def read_previous(domain):
    try:
        return json.loads((PUBLIC / f"{domain}.json").read_text())
    except (FileNotFoundError, ValueError):
        return None


def log_row(now, domain, found, result, temps, winds, rain, alert_status):
    path = LOG_DIR / f"{now:%Y-%m}.csv"
    new_file = not path.exists()
    LOG_DIR.mkdir(exist_ok=True)
    with path.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["tid", "avis", "vises", "regel", "grunn", "forslag_nå", "regel_nå",
                             "maks_vind", "maks_kast", "maks_nedbør", "median_nedbør",
                             "maks_temp", "min_temp", "farevarsel"])
        writer.writerow([
            now.isoformat(timespec="minutes"), domain, result["weathertype"], result["rule"], result["reason"],
            found["weathertype"], found["rule"],
            max(e["wind_speed"] for e in winds), max(e["wind_speed_of_gust"] for e in winds),
            max(e["precipitation_rate"] for e in rain),
            statistics.median(e["precipitation_rate"] for e in rain),
            max(e["air_temperature"] for e in temps), min(e["air_temperature"] for e in temps),
            alert_status,
        ])


def main():
    dry_run = "--dry-run" in sys.argv
    now = datetime.now(OSLO)
    failed = False

    try:
        alerts, alert_status = fetch(ALERTS_URL)[0]["features"], "ok"
    except Exception as error:  # noqa: BLE001 - the other rules still work without alerts
        alerts, alert_status = [], f"utilgjengelig: {error}"
        print(f"Advarsel: farevarsler fra MET er utilgjengelige ({error})", file=sys.stderr)

    for domain in DOMAINS:
        try:
            temps, winds, rain = fetch_weather(domain, now.astimezone(timezone.utc))
            try:
                locations, status = fetch(LOCATIONS_URL.format(domain=domain))[0]["data"], alert_status
            except Exception as error:  # noqa: BLE001 - without places no alert can match
                locations, status = [], f"steder utilgjengelige: {error}"
            found = evaluate(now, temps, winds, rain, alerts, locations)
        except Exception as error:  # noqa: BLE001 - leave the old file so its "updated" goes stale
            print(f"{domain}: FEIL, beholder forrige valg ({error})", file=sys.stderr)
            failed = True
            continue

        result = apply_hold(now, found, read_previous(domain))
        held = "" if result["weathertype"] == found["weathertype"] else f" (holder, nå: {found['weathertype']}/{found['rule']})"
        print(f"{domain}: {result['weathertype']} - {result['reason']}{held}")
        if not dry_run:
            PUBLIC.mkdir(exist_ok=True)
            (PUBLIC / f"{domain}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            log_row(now, domain, found, result, temps, winds, rain, status)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
