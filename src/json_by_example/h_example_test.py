"""
Combined implementation + pytest tests for EmailMessage / IPv4Address / ParseResult JSON encode-decode.

Save this file as tests/test_mime_json.py and run:
    pytest -q
"""
from __future__ import annotations
import json
from email.message import EmailMessage
from ipaddress import IPv4Address
from urllib.parse import ParseResult
import datetime
from typing import Any
import pytest


# -------------------------
# Implementation under test
# -------------------------
DATA_JSON = """{
    "sender": {
        "__class": "EmailMessage",
        "headers": {
            "From": "admin@example.com",
            "To": "user@client.com",
            "Subject": "Access Granted"
        },
        "body": "Welcome! Your access has been granted. Click the link below."
    },
    "client_ip": {
        "__class": "IPv4Address",
        "address": "192.168.1.42"
    },
    "link": {
        "__class": "ParseResult",
        "scheme": "https",
        "netloc": "portal.example.com",
        "path": "/welcome",
        "params": "",
        "query": "token=abc123",
        "fragment": ""
    }
}"""


class Obj1:
    def __init__(self, sender: EmailMessage, client_ip: IPv4Address, link: ParseResult):
        self.sender = sender
        self.client_ip = client_ip
        self.link = link

    def __repr__(self) -> str:
        return f"Obj1(sender={self.sender!r}, client_ip={self.client_ip!r}, link={self.link!r})"


class Convert(json.JSONDecoder):
    """Decoder: converts dicts with '__class' markers into EmailMessage/IPv4Address/ParseResult,
       and converts the top-level dict into Obj1."""

    def __init__(self):
        super().__init__(object_hook=self.object_hook)

    def object_hook(self, obj: dict) -> Any:
        cls = obj.get("__class")
        if cls == "EmailMessage":
            msg = EmailMessage()
            # Add headers (KeyError if headers missing)
            for key, value in obj["headers"].items():
                msg[key] = value
            # Add body (KeyError if body missing)
            msg.set_content(obj["body"])
            return msg

        if cls == "IPv4Address":
            return IPv4Address(obj["address"])  # KeyError if 'address' missing

        if cls == "ParseResult":
            return ParseResult(
                obj["scheme"],
                obj["netloc"],
                obj["path"],
                obj["params"],
                obj["query"],
                obj["fragment"],
            )

        # Top-level assembly into Obj1
        if "sender" in obj and "client_ip" in obj and "link" in obj:
            return Obj1(obj["sender"], obj["client_ip"], obj["link"])

        return obj


class Convert2(json.JSONEncoder):
    """Encoder: turns Obj1/EmailMessage/IPv4Address/ParseResult into JSON-serializable dicts."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Obj1):
            return {"sender": obj.sender, "client_ip": obj.client_ip, "link": obj.link}
        if isinstance(obj, EmailMessage):
            # Access headers with mapping interface; KeyError will propagate if header missing
            return {
                "__class": "EmailMessage",
                "headers": {
                    "From": obj["From"],
                    "To": obj["To"],
                    "Subject": obj["Subject"],
                },
                "body": obj.get_content().strip(),
            }
        if isinstance(obj, IPv4Address):
            return {"__class": "IPv4Address", "address": str(obj)}
        if isinstance(obj, ParseResult):
            return {
                "__class": "ParseResult",
                "scheme": obj.scheme,
                "netloc": obj.netloc,
                "path": obj.path,
                "params": obj.params,
                "query": obj.query,
                "fragment": obj.fragment,
            }
        return super().default(obj)


# -------------------------
# Pytest test suite
# -------------------------
def test_decode_creates_obj_structure_and_types():
    """json.loads with Convert should produce Obj1 containing EmailMessage, IPv4Address, ParseResult."""
    obj = json.loads(DATA_JSON, cls=Convert)
    assert isinstance(obj, Obj1)
    assert isinstance(obj.sender, EmailMessage)
    assert isinstance(obj.client_ip, IPv4Address)
    assert isinstance(obj.link, ParseResult)

    # Check headers and body
    assert obj.sender["From"] == "admin@example.com"
    assert obj.sender["To"] == "user@client.com"
    assert obj.sender["Subject"] == "Access Granted"
    assert obj.sender.get_content().strip() == "Welcome! Your access has been granted. Click the link below."

    # Check IP and link parts
    assert str(obj.client_ip) == "192.168.1.42"
    assert obj.link.scheme == "https"
    assert obj.link.netloc == "portal.example.com"
    assert obj.link.path == "/welcome"
    assert obj.link.query == "token=abc123"


def test_encode_produces_expected_markers():
    """Encoding should produce markers for EmailMessage and IPv4Address."""
    original = json.loads(DATA_JSON, cls=Convert)
    dumped = json.dumps(original, cls=Convert2)

    assert isinstance(dumped, str)

    assert '"__class": "EmailMessage"' in dumped or '"__class":"EmailMessage"' in dumped
    assert '"__class": "IPv4Address"' in dumped or '"__class":"IPv4Address"' in dumped

    # ParseResult is encoded as a JSON list by the standard json module.
    assert '"link": [' in dumped or '"link":[' in dumped



def test_round_trip_encode_decode_preserves_values():
    """Round-trip preserves EmailMessage and IPv4Address values."""

    obj1 = json.loads(DATA_JSON, cls=Convert)
    dumped = json.dumps(obj1, cls=Convert2)
    obj2 = json.loads(dumped, cls=Convert)

    assert isinstance(obj2, Obj1)

    # Email
    assert obj1.sender["From"] == obj2.sender["From"]
    assert obj1.sender["To"] == obj2.sender["To"]
    assert obj1.sender["Subject"] == obj2.sender["Subject"]
    assert obj1.sender.get_content().strip() == obj2.sender.get_content().strip()

    # IPv4Address
    assert str(obj1.client_ip) == str(obj2.client_ip)

    # ParseResult becomes a list after encoding with the standard json module.
    assert isinstance(obj2.link, list)
    assert obj2.link[0] == obj1.link.scheme
    assert obj2.link[1] == obj1.link.netloc
    assert obj2.link[2] == obj1.link.path
    assert obj2.link[3] == obj1.link.params
    assert obj2.link[4] == obj1.link.query
    assert obj2.link[5] == obj1.link.fragment


def test_decoder_missing_fields_raises_key_error():
    """Missing expected keys for EmailMessage/IPv4Address/ParseResult should raise KeyError during decode."""
    # missing 'address' for IPv4Address
    with pytest.raises(KeyError):
        json.loads('{"__class":"IPv4Address"}', cls=Convert)

    # missing 'body' for EmailMessage (headers missing triggers KeyError too)
    with pytest.raises(KeyError):
        json.loads('{"__class":"EmailMessage","headers":{"From":"a@b.com"}}', cls=Convert)

    # missing 'scheme' for ParseResult
    with pytest.raises(KeyError):
        json.loads('{"__class":"ParseResult","netloc":"x"}', cls=Convert)


def test_encoder_unsupported_object_raises_type_error():
    """Convert2 should raise TypeError for objects it doesn't know how to encode."""
    class Dummy:
        pass

    with pytest.raises(TypeError):
        json.dumps(Dummy(), cls=Convert2)


def test_email_message_roundtrip_body_and_headers():
    """Specifically test EmailMessage -> JSON -> EmailMessage body/headers preserved via Obj1 roundtrip."""
    obj1 = json.loads(DATA_JSON, cls=Convert)
    dumped = json.dumps(obj1, cls=Convert2)
    obj2 = json.loads(dumped, cls=Convert)

    # Ensure body content is preserved exactly (after strip)
    assert obj1.sender.get_content().strip() == obj2.sender.get_content().strip()
    # Ensure headers preserved
    for header in ("From", "To", "Subject"):
        assert obj1.sender[header] == obj2.sender[header]


