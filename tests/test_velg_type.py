import json
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import velg_type as v  # noqa: E402

OCTOBER = datetime(2026, 10, 9, 14, 0, tzinfo=v.OSLO)
JULY = datetime(2026, 7, 9, 14, 0, tzinfo=v.OSLO)
JANUARY = datetime(2026, 1, 9, 14, 0, tzinfo=v.OSLO)
LOCATIONS = [{"name": "Hernar", "lat": 60.6, "lon": 4.9}, {"name": "Fjell", "lat": 60.33, "lon": 5.08}]
SQUARE = {"type": "Polygon", "coordinates": [[[4.8, 60.5], [5.0, 60.5], [5.0, 60.7], [4.8, 60.7], [4.8, 60.5]]]}


def temps(*values):
    return [{"areaname": f"Sted{i}, Øygarden", "air_temperature": t} for i, t in enumerate(values)]


def winds(*pairs):
    return [{"areaname": f"Sted{i}, Øygarden", "wind_speed": s, "wind_speed_of_gust": g} for i, (s, g) in enumerate(pairs)]


def rain(*values):
    return [{"areaname": f"Sted{i}, Øygarden", "precipitation_rate": r} for i, r in enumerate(values)]


def alert(event, domain="land", level="2; yellow; Moderate", geometry=SQUARE, altitude=0):
    return {"geometry": geometry, "properties": {
        "event": event, "geographicDomain": domain, "awareness_level": level,
        "altitude_above_sea_level": altitude, "eventAwarenessName": event, "area": "Vestland"}}


CALM = dict(temps=temps(9, 10), winds=winds((3, 5), (4, 6)), rain=rain(0, 0), alerts=[], locations=LOCATIONS)


def run(now=OCTOBER, **changes):
    return v.evaluate(now, **(CALM | changes))


class Rules(unittest.TestCase):
    # Real case 9 Oct 2026: marine gale "Slåtterøy - Fedje" covered 15 Vestnytt places, land max gust 11.6 m/s.
    def test_marine_gale_is_ignored(self):
        self.assertEqual(run(alerts=[alert("gale", domain="marine")])["rule"], "årstid")

    def test_land_wind_alert_wins_over_everything(self):
        found = run(alerts=[alert("wind")], rain=rain(9, 9))
        self.assertEqual((found["weathertype"], found["rule"]), ("wind", "farevarsel"))
        self.assertIn("Gult farevarsel", found["reason"])

    def test_alert_must_cover_a_place(self):
        far = {"type": "Polygon", "coordinates": [[[10, 59], [11, 59], [11, 60], [10, 60], [10, 59]]]}
        self.assertEqual(run(alerts=[alert("wind", geometry=far)])["rule"], "årstid")

    def test_alert_above_sea_level_is_ignored(self):
        self.assertEqual(run(alerts=[alert("snow", altitude=1600)])["rule"], "årstid")

    def test_more_serious_alert_wins(self):
        found = run(alerts=[alert("wind"), alert("rain", level="3; orange; Severe")])
        self.assertEqual(found["weathertype"], "precipitation")

    def test_mean_wind_at_small_gale(self):
        self.assertEqual(run(winds=winds((10.8, 14), (4, 6)))["weathertype"], "wind")

    def test_strong_gusts(self):
        self.assertEqual(run(winds=winds((9, 17.0), (4, 6)))["weathertype"], "wind")

    def test_wind_beats_rain(self):
        self.assertEqual(run(winds=winds((12, 18), (4, 6)), rain=rain(5, 5))["weathertype"], "wind")

    def test_heavy_rain_at_one_place(self):
        self.assertEqual(run(rain=rain(3.0, 0))["weathertype"], "precipitation")

    def test_widespread_rain(self):
        self.assertEqual(run(rain=rain(1.2, 1.0, 0, 0))["weathertype"], "precipitation")

    def test_scattered_showers_are_not_enough(self):
        self.assertEqual(run(rain=rain(1.5, 0, 0, 0))["rule"], "årstid")

    def test_unusually_warm_for_october(self):
        found = run(temps=temps(16.2, 12))
        self.assertEqual(found["weathertype"], "warm")
        self.assertIn("16,2 grader", found["reason"])

    def test_same_temperature_is_normal_in_july(self):
        self.assertEqual(run(now=JULY, temps=temps(16.2, 12))["rule"], "årstid")

    def test_unusually_cold_in_january(self):
        self.assertEqual(run(now=JANUARY, temps=temps(-6, 1))["weathertype"], "cold")

    def test_season_defaults_never_pick_precipitation(self):
        for month in range(1, 13):
            now = OCTOBER.replace(month=month)
            self.assertIn(run(now=now, temps=temps(5, 5))["weathertype"], ("warm", "cold", "wind"))
        self.assertEqual(run(now=JULY)["weathertype"], "warm")
        self.assertEqual(run(now=JANUARY, temps=temps(2, 3))["weathertype"], "cold")
        self.assertEqual(run()["weathertype"], "wind")


class Hold(unittest.TestCase):
    def previous(self, rule, weathertype, hours_ago):
        since = (OCTOBER - timedelta(hours=hours_ago)).isoformat(timespec="minutes")
        return {"weathertype": weathertype, "rule": rule, "reason": "før", "since": since, "updated": since}

    def test_first_run(self):
        result = v.apply_hold(OCTOBER, v.candidate("vind", "wind", "x"), None)
        self.assertEqual(result["since"], OCTOBER.isoformat(timespec="minutes"))

    def test_same_type_keeps_since(self):
        prev = self.previous("vind", "wind", 5)
        result = v.apply_hold(OCTOBER, v.candidate("vind", "wind", "nå"), prev)
        self.assertEqual((result["since"], result["reason"]), (prev["since"], "nå"))

    def test_less_important_waits_three_hours(self):
        prev = self.previous("vind", "wind", 1)
        result = v.apply_hold(OCTOBER, v.candidate("årstid", "warm", "x"), prev)
        self.assertEqual((result["weathertype"], result["reason"]), ("wind", "før"))
        self.assertEqual(result["updated"], OCTOBER.isoformat(timespec="minutes"))

    def test_switches_after_three_hours(self):
        result = v.apply_hold(OCTOBER, v.candidate("årstid", "warm", "x"), self.previous("vind", "wind", 3))
        self.assertEqual(result["weathertype"], "warm")

    def test_more_important_switches_at_once(self):
        result = v.apply_hold(OCTOBER, v.candidate("farevarsel", "precipitation", "x"), self.previous("vind", "wind", 0.5))
        self.assertEqual(result["weathertype"], "precipitation")

    def test_broken_previous_file_is_ignored(self):
        result = v.apply_hold(OCTOBER, v.candidate("vind", "wind", "x"), {"weathertype": "wind"})
        self.assertEqual(result["since"], OCTOBER.isoformat(timespec="minutes"))

    def test_more_serious_alert_switches_at_once(self):
        for level in ("3; orange; Severe", "4; red; Extreme"):
            with self.subTest(level=level):
                previous = v.apply_hold(OCTOBER - timedelta(minutes=30), run(alerts=[alert("wind")]), None)
                found = run(alerts=[alert("wind"), alert("rain", level=level)])
                result = v.apply_hold(OCTOBER, found, previous)
                self.assertEqual(result["weathertype"], "precipitation")
                self.assertEqual(result["reason"], found["reason"])
                self.assertEqual(result["since"], OCTOBER.isoformat(timespec="minutes"))

    def test_equal_or_less_serious_alert_waits(self):
        previous = v.apply_hold(OCTOBER - timedelta(minutes=30), run(alerts=[alert("wind", level="3; orange; Severe")]), None)
        for level in ("2; yellow; Moderate", "3; orange; Severe"):
            with self.subTest(level=level):
                result = v.apply_hold(OCTOBER, run(alerts=[alert("rain", level=level)]), previous)
                self.assertEqual(result["weathertype"], "wind")
                self.assertEqual(result["alert_level"], 3)
                self.assertEqual(result["since"], previous["since"])

    def test_held_alert_keeps_severity_for_next_run(self):
        previous = v.apply_hold(OCTOBER - timedelta(minutes=30), run(alerts=[alert("rain", level="4; red; Extreme")]), None)
        held = v.apply_hold(OCTOBER, run(), previous)
        # Simulate saving and reading the JSON between runs.
        held = json.loads(json.dumps(held))
        result = v.apply_hold(OCTOBER + timedelta(minutes=30), run(alerts=[alert("wind")]), held)
        self.assertEqual(result["weathertype"], "precipitation")
        self.assertEqual(result["alert_level"], 4)

    def test_same_type_updates_severity_without_resetting_since(self):
        previous = v.apply_hold(OCTOBER - timedelta(minutes=30), run(alerts=[alert("wind")]), None)
        result = v.apply_hold(OCTOBER, run(alerts=[alert("wind", level="4; red; Extreme")]), previous)
        self.assertEqual(result["alert_level"], 4)
        self.assertEqual(result["since"], previous["since"])

    def test_legacy_alert_without_severity_does_not_block_new_alert(self):
        previous = self.previous("farevarsel", "wind", 0.5)
        result = v.apply_hold(OCTOBER, run(alerts=[alert("rain", level="4; red; Extreme")]), previous)
        self.assertEqual(result["weathertype"], "precipitation")

    def test_invalid_previous_state_is_replaced(self):
        previous = self.previous("vind", "wind", 0.5)
        broken = [None, [], "wind", 42]
        broken.extend({k: val for k, val in previous.items() if k != missing}
                      for missing in ("weathertype", "rule", "reason", "since"))
        broken.extend(previous | change for change in (
            {"since": "2026-10-09T13:00"}, {"since": "invalid"},
            {"since": (OCTOBER + timedelta(days=1)).isoformat()},
            {"rule": []}, {"rule": "unknown"}, {"reason": None},
            {"weathertype": "unknown"}, {"alert_level": "red"},
            {"alert_level": True}, {"alert_level": 99},
        ))
        for previous in broken:
            for weathertype in ("warm", "wind"):
                with self.subTest(previous=previous, weathertype=weathertype):
                    found = v.candidate("årstid", weathertype, "nå")
                    result = v.apply_hold(OCTOBER, found, previous)
                    self.assertEqual(result, found | {"since": OCTOBER.isoformat(timespec="minutes"),
                                                     "updated": OCTOBER.isoformat(timespec="minutes")})


class Job(unittest.TestCase):
    def test_broken_previous_file_does_not_stop_other_papers(self):
        with TemporaryDirectory() as tmp:
            public = Path(tmp) / "public"
            public.mkdir()
            (public / "first.no.json").write_text(json.dumps({
                "weathertype": "precipitation", "rule": "farevarsel",
                "since": datetime.now(v.OSLO).isoformat(),  # Missing reason.
            }))
            with (patch.object(v, "PUBLIC", public),
                  patch.object(v, "LOG_DIR", Path(tmp) / "logg"),
                  patch.object(v, "DOMAINS", ("first.no", "second.no")),
                  patch.object(v, "fetch", side_effect=[({"features": []}, None),
                                                        ({"data": LOCATIONS}, None),
                                                        ({"data": LOCATIONS}, None)]),
                  patch.object(v, "fetch_weather", return_value=(CALM["temps"], CALM["winds"], CALM["rain"])),
                  patch.object(sys, "argv", ["velg_type.py"]), redirect_stdout(StringIO())):
                self.assertEqual(v.main(), 0)
            for domain in ("first.no", "second.no"):
                result = json.loads((public / f"{domain}.json").read_text())
                self.assertIn(result["weathertype"], v.TYPES)
                self.assertIn("reason", result)


if __name__ == "__main__":
    unittest.main()
