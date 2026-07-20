"""
Combined implementation + pytest tests for date / timedelta / timezone JSON encode-decode.

Save this file as tests/test_report_json.py and run:
    pytest -q
"""
from __future__ import annotations
import json
import datetime
from datetime import date, timedelta, timezone
from typing import Any
import pytest


# -------------------------
# Implementation under test
# -------------------------
class Obj1:
    def __init__(self, report: Any):
        self.report = report

    def __repr__(self) -> str:
        return f"Obj1(report={self.report})"


class Obj2:
    def __init__(self, created: date, duration: timedelta, tz: timezone):
        self.created = created
        self.duration = duration
        self.timezone = tz

    def __repr__(self) -> str:
        return (
            f"Obj2(created={self.created}, "
            f"duration={self.duration}, "
            f"timezone={self.timezone})"
        )


class Convert(json.JSONDecoder):
    """
    Decoder: converts dicts with "__class" markers into date/timedelta/timezone,
    and converts the nested "created"/"report" dicts into Obj2/Obj1 instances.
    """

    def __init__(self):
        super().__init__(object_hook=self.object_hook)

    def object_hook(self, obj: dict) -> Any:
        cls = obj.get("__class")
        if cls == "date":
            # expect keys: y, month, d
            return date(obj["y"], obj["month"], obj["d"])
        if cls == "timedelta":
            # expected keys: days, seconds, microseconds
            return timedelta(days=obj["days"], seconds=obj["seconds"], microseconds=obj["microseconds"])
        if cls == "timezone":
            # expected key: offset (hours)
            return timezone(timedelta(hours=obj["offset"]))
        # Higher-level conversions
        if "created" in obj and "duration" in obj and "timezone" in obj:
            return Obj2(obj["created"], obj["duration"], obj["timezone"])
        if "report" in obj:
            return Obj1(obj["report"])
        return obj


class Convert2(json.JSONEncoder):
    """
    Encoder: turns Obj1/Obj2/date/timedelta/timezone instances into JSON-serializable dicts
    with markers so Convert can decode them back.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Obj1):
            return {"report": obj.report}
        if isinstance(obj, Obj2):
            return {"created": obj.created, "duration": obj.duration, "timezone": obj.timezone}
        if isinstance(obj, date) and not isinstance(obj, datetime.datetime):
            return {"__class": "date", "y": obj.year, "month": obj.month, "d": obj.day}
        if isinstance(obj, timedelta):
            return {"__class": "timedelta", "days": obj.days, "seconds": obj.seconds, "microseconds": obj.microseconds}
        if isinstance(obj, timezone):
            # timezone.utcoffset requires a datetime; pass a naive datetime to obtain offset
            offset = obj.utcoffset(datetime.datetime(1970, 1, 1))
            hours = int(offset.total_seconds() // 3600)
            return {"__class": "timezone", "offset": hours}
        return super().default(obj)


# -------------------------
# Sample JSON used in tests
# -------------------------
SAMPLE_JSON = """{
    "report": {
        "created": {
            "__class": "date",
            "y": 2025,
            "month": 4,
            "d": 27
        },
        "duration": {
            "__class": "timedelta",
            "days": 2,
            "seconds": 3600,
            "microseconds": 4
        },
        "timezone": {
            "__class": "timezone",
            "offset": 2
        }
    }
}"""


# -------------------------
# Pytest test suite
# -------------------------
def test_decode_creates_obj_structure_and_types():
    """json.loads with Convert should produce Obj1 containing Obj2 with proper types."""
    obj = json.loads(SAMPLE_JSON, cls=Convert)
    assert isinstance(obj, Obj1)
    assert isinstance(obj.report, Obj2)

    created = obj.report.created
    duration = obj.report.duration
    tz = obj.report.timezone

    assert isinstance(created, date) and not isinstance(created, datetime.datetime)
    assert created == date(2025, 4, 27)

    assert isinstance(duration, timedelta)
    assert duration.days == 2
    assert duration.seconds == 3600
    assert duration.microseconds == 4

    assert isinstance(tz, timezone)
    # utcoffset should be 2 hours
    assert tz.utcoffset(datetime.datetime(2025, 1, 1)) == timedelta(hours=2)


def test_encode_produces_expected_markers_after_dump():
    """Encoding an Obj1/Obj2 structure should produce JSON with __class markers for primitives."""
    original = json.loads(SAMPLE_JSON, cls=Convert)  # Obj1 instance
    dumped = json.dumps(original, cls=Convert2)
    assert isinstance(dumped, str)
    # Ensure the encoded JSON contains markers for date, timedelta, timezone
    assert '"__class": "date"' in dumped or '"__class":"date"' in dumped
    assert '"__class": "timedelta"' in dumped or '"__class":"timedelta"' in dumped
    assert '"__class": "timezone"' in dumped or '"__class":"timezone"' in dumped


def test_round_trip_encode_decode_preserves_values():
    """Round-trip: SAMPLE_JSON -> Obj1 -> JSON -> Obj1 should preserve values."""
    obj1 = json.loads(SAMPLE_JSON, cls=Convert)
    dumped = json.dumps(obj1, cls=Convert2)
    obj2 = json.loads(dumped, cls=Convert)

    # obj2 should be Obj1 with nested Obj2 and matching values
    assert isinstance(obj2, Obj1)
    assert isinstance(obj2.report, Obj2)

    assert obj1.report.created == obj2.report.created
    assert obj1.report.duration == obj2.report.duration
    assert obj1.report.timezone.utcoffset(datetime.datetime(2025, 1, 1)) == obj2.report.timezone.utcoffset(datetime.datetime(2025, 1, 1))


def test_decoder_missing_fields_raises_key_error():
    """Missing expected keys for date/timedelta/timezone should raise KeyError during decode."""
    # missing 'd' for date
    bad_date = '{"__class":"date","y":2025,"month":4}'
    with pytest.raises(KeyError):
        json.loads(bad_date, cls=Convert)

    # missing 'seconds' for timedelta
    bad_td = '{"__class":"timedelta","days":1,"microseconds":0}'
    with pytest.raises(KeyError):
        json.loads(bad_td, cls=Convert)

    # missing 'offset' for timezone
    bad_tz = '{"__class":"timezone"}'
    with pytest.raises(KeyError):
        json.loads(bad_tz, cls=Convert)


def test_encoder_unsupported_object_raises_type_error():
    """Convert2 should raise TypeError for objects it doesn't know how to encode."""
    class Dummy:
        pass

    with pytest.raises(TypeError):
        json.dumps(Dummy(), cls=Convert2)


def test_obj_repr_contains_key_words():
    """Basic sanity for __repr__ implementations."""
    obj = json.loads(SAMPLE_JSON, cls=Convert)
    r = repr(obj)
    assert "Obj1" in r and "report" in r
    r2 = repr(obj.report)
    assert "Obj2" in r2 and "created" in r2