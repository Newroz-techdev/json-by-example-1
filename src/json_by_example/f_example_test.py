"""
Combined implementation + pytest tests for Signal, Convert, and Convert2.

Save this file as tests/test_signal_json.py and run:
    pytest -q
"""
from __future__ import annotations
import datetime
import json
from typing import Any
import pytest


# -------------------------
# Implementation under test
# -------------------------
class Signal:
    def __init__(self, _place: str, _stamp: datetime.datetime, _samples: list[complex]):
        self._place = _place
        self._stamp = _stamp
        self._samples = _samples

    @property
    def place(self) -> str:
        return self._place

    @property
    def stamp(self) -> datetime.datetime:
        return self._stamp

    @property
    def samples(self) -> list[complex]:
        return self._samples

    def __repr__(self) -> str:
        return f"Signal(place={self._place!r}, stamp={self._stamp!r}, samples={self._samples!r})"


class Convert(json.JSONEncoder):
    """Custom JSONEncoder: encode datetime.datetime and complex objects."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return {
                "__class": "datetime",
                "y": obj.year,
                "month": obj.month,
                "d": obj.day,
                "h": obj.hour,
                "minute": obj.minute,
                "s": obj.second,
            }
        if isinstance(obj, complex):
            return {"__class": "complex", "real": obj.real, "imag": obj.imag}
        return super().default(obj)


class Convert2(json.JSONDecoder):
    """Custom JSONDecoder: rebuild complex and datetime objects from dict markers."""

    def __init__(self):
        super().__init__(object_hook=self.object_hook)

    def object_hook(self, obj: dict) -> Any:
        cls_name = obj.get("__class")
        if cls_name == "complex":
            return complex(obj["real"], obj["imag"])  # KeyError if missing keys
        if cls_name == "datetime":
            return datetime.datetime(
                obj["y"], obj["month"], obj["d"], obj["h"], obj["minute"], obj["s"]
            )
        return obj


# -------------------------
# Pytest test suite
# -------------------------
@pytest.fixture
def sample_text():
    return {
        "signal": {
            "place": "Uppsala",
            "stamp": {
                "__class": "datetime",
                "y": 2025,
                "month": 4,
                "d": 19,
                "h": 16,
                "minute": 23,
                "s": 51,
            },
            "samples": [
                {"__class": "complex", "real": -2.0, "imag": 5.0},
                {"__class": "complex", "real": 3.0, "imag": 1.0},
                {"__class": "complex", "real": 2.0, "imag": 5.0},
            ],
        }
    }


def test_encode_produces_json_string(sample_text):
    """json.dumps with Convert should produce a JSON string containing class markers."""
    s = json.dumps(sample_text, cls=Convert)
    assert isinstance(s, str)
    assert '"__class": "datetime"' in s or '"__class":"datetime"' in s
    assert '"__class": "complex"' in s or '"__class":"complex"' in s


def test_decode_round_trip_and_construct_signal(sample_text):
    """
    Encode sample_text to JSON, decode back to python objects with Convert2,
    assert types are restored, and construct a Signal instance.
    """
    dumped = json.dumps(sample_text, cls=Convert)
    loaded = json.loads(dumped, cls=Convert2)

    assert "signal" in loaded
    sig = loaded["signal"]

    assert isinstance(sig["stamp"], datetime.datetime)
    assert isinstance(sig["samples"], list)
    assert all(isinstance(x, complex) for x in sig["samples"])

    signal = Signal(sig["place"], sig["stamp"], sig["samples"])
    assert signal.place == "Uppsala"
    assert signal.stamp == sig["stamp"]
    assert signal.samples == sig["samples"]


def test_signal_properties_are_read_only():
    """Properties have only getters; attempting to assign should raise AttributeError."""
    stamp = datetime.datetime.now()
    samples = [1 + 2j]
    s = Signal("Loc", stamp, samples)

    with pytest.raises(AttributeError):
        s.place = "New"

    with pytest.raises(AttributeError):
        s.stamp = datetime.datetime.now()

    with pytest.raises(AttributeError):
        s.samples = []


def test_encoder_unsupported_object_raises_type_error():
    """Convert should defer to super().default and raise TypeError for unsupported objects."""
    class Dummy:
        pass

    with pytest.raises(TypeError):
        json.dumps(Dummy(), cls=Convert)


def test_object_hook_returns_dict_when_no_class():
    """If the dict doesn't contain __class, the object_hook should return the dict unchanged."""
    obj = json.loads('{"foo": "bar"}', cls=Convert2)
    assert isinstance(obj, dict)
    assert obj["foo"] == "bar"


def test_decoder_missing_complex_fields_raises_key_error():
    """Missing 'imag' for complex should raise KeyError inside object_hook."""
    with pytest.raises(KeyError):
        json.loads('{"__class":"complex","real": 1}', cls=Convert2)


def test_decoder_missing_datetime_fields_raises_key_error():
    """Missing datetime fields should raise KeyError inside object_hook."""
    with pytest.raises(KeyError):
        json.loads('{"__class":"datetime","y":2020}', cls=Convert2)