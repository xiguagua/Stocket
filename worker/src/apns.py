import base64
import json
import os
import time
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from . import db


def build_digest_payload(event_count: int) -> dict:
    body = "1 new Event in your Digest." if event_count == 1 else f"{event_count} new Events in your Digest."
    return {
        "aps": {
            "alert": {
                "title": "Stocket Digest",
                "body": body,
            },
            "sound": "default",
        },
        "type": "digest",
        "eventCount": event_count,
    }


def send_digest(event_count: int, client: httpx.Client | None = None) -> dict:
    devices = db.get_devices()
    if not devices or event_count <= 0:
        return {"attempted": 0, "sent": 0, "failed": 0}

    payload = build_digest_payload(event_count)
    return send_payload_to_devices(
        device_tokens=[device["device_token"] for device in devices],
        payload=payload,
        client=client,
    )


def send_payload_to_devices(
    device_tokens: list[str],
    payload: dict,
    client: httpx.Client | None = None,
) -> dict:
    if not device_tokens:
        return {"attempted": 0, "sent": 0, "failed": 0}

    owns_client = client is None
    client = client or httpx.Client(http2=True, timeout=10)
    attempted = sent = failed = 0

    try:
        for device_token in device_tokens:
            attempted += 1
            try:
                response = client.post(
                    _apns_url(device_token),
                    headers=_apns_headers(),
                    json=payload,
                )
            except httpx.HTTPError:
                failed += 1
                continue
            if 200 <= response.status_code < 300:
                sent += 1
            else:
                failed += 1
        return {"attempted": attempted, "sent": sent, "failed": failed}
    finally:
        if owns_client:
            client.close()


def _apns_headers() -> dict:
    topic = _required_env("APNS_TOPIC")
    return {
        "authorization": f"bearer {_apns_jwt()}",
        "apns-topic": topic,
        "apns-push-type": "alert",
        "apns-priority": "10",
    }


def _apns_url(device_token: str) -> str:
    host = "api.push.apple.com" if os.environ.get("APNS_ENV", "development") == "production" else "api.sandbox.push.apple.com"
    return f"https://{host}/3/device/{device_token}"


def _apns_jwt() -> str:
    key_id = _required_env("APNS_KEY_ID")
    team_id = _required_env("APNS_TEAM_ID")
    private_key = serialization.load_pem_private_key(_apns_private_key_pem(), password=None)

    header = {"alg": "ES256", "kid": key_id}
    claims = {"iss": team_id, "iat": int(time.time())}
    signing_input = f"{_base64url_json(header)}.{_base64url_json(claims)}"
    signature = private_key.sign(signing_input.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(signature)
    raw_signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{signing_input}.{_base64url(raw_signature)}"


def _apns_private_key_pem() -> bytes:
    key_inline = os.environ.get("APNS_PRIVATE_KEY")
    if key_inline:
        return key_inline.replace("\\n", "\n").encode("utf-8")

    key_path = os.environ.get("APNS_PRIVATE_KEY_PATH")
    if key_path:
        return Path(key_path).expanduser().read_bytes()

    raise RuntimeError("APNS_PRIVATE_KEY or APNS_PRIVATE_KEY_PATH is required")


def _base64url_json(data: dict) -> str:
    return _base64url(json.dumps(data, separators=(",", ":")).encode("utf-8"))


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for APNs")
    return value
