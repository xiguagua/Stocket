from datetime import datetime, timezone

import httpx

from src import apns, db


def test_build_digest_payload_uses_event_count():
    payload = apns.build_digest_payload(2)

    assert payload["aps"]["alert"] == {
        "title": "Stocket Digest",
        "body": "2 new Events in your Digest.",
    }
    assert payload["aps"]["sound"] == "default"
    assert payload["type"] == "digest"
    assert payload["eventCount"] == 2


def test_send_digest_skips_when_no_devices():
    assert apns.send_digest(event_count=1, client=FakeAPNsClient()) == {
        "attempted": 0,
        "sent": 0,
        "failed": 0,
    }


def test_send_digest_skips_when_no_events():
    db.upsert_device(
        user_id="local-user",
        device_token="token-1",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    assert apns.send_digest(event_count=0, client=FakeAPNsClient()) == {
        "attempted": 0,
        "sent": 0,
        "failed": 0,
    }


def test_send_digest_posts_payload_to_registered_devices(monkeypatch):
    client = FakeAPNsClient(status_codes=[200, 410])
    monkeypatch.setattr(apns, "_apns_jwt", lambda: "jwt-token")
    monkeypatch.setenv("APNS_TOPIC", "com.flhcc.Stocket")
    db.upsert_device(
        user_id="local-user",
        device_token="token-1",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    db.upsert_device(
        user_id="local-user",
        device_token="token-2",
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    result = apns.send_digest(event_count=3, client=client)

    assert result == {"attempted": 2, "sent": 1, "failed": 1}
    assert [request["url"] for request in client.requests] == [
        "https://api.sandbox.push.apple.com/3/device/token-1",
        "https://api.sandbox.push.apple.com/3/device/token-2",
    ]
    assert client.requests[0]["headers"]["authorization"] == "bearer jwt-token"
    assert client.requests[0]["headers"]["apns-topic"] == "com.flhcc.Stocket"
    assert client.requests[0]["json"]["eventCount"] == 3


def test_apns_url_uses_production_host(monkeypatch):
    monkeypatch.setenv("APNS_ENV", "production")

    assert apns._apns_url("token") == "https://api.push.apple.com/3/device/token"


class FakeAPNsClient:
    def __init__(self, status_codes=None):
        self.status_codes = status_codes or []
        self.requests = []

    def post(self, url, headers, json):
        self.requests.append({"url": url, "headers": headers, "json": json})
        status_code = self.status_codes[len(self.requests) - 1] if len(self.requests) <= len(self.status_codes) else 200
        return httpx.Response(status_code=status_code)

    def close(self):
        pass
