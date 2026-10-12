import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
