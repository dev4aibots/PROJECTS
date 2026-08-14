#!/usr/bin/env python3
"""Authenticated owner-run smoke test for a deployed ZeroTrust SQL API."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def request_json(
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    payload: dict | None = None,
) -> tuple[dict, dict[str, str]]:
    headers = {"accept": "application/json"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["content-type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(base_url + path, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response), dict(response.headers.items())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--query-token", required=True)
    parser.add_argument("--audit-token", required=True)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    health, _ = request_json(base_url, "/api/health")
    assert health["status"] == "ok"
    assert health["database"] == "restricted-postgres"

    happy, headers = request_json(
        base_url,
        "/api/query",
        token=args.query_token,
        payload={"question": "Top 10 customers by revenue"},
    )
    assert happy["security"]["allowed"] is True
    assert headers.get("X-Request-ID") or headers.get("x-request-id")

    blocked, _ = request_json(
        base_url,
        "/api/query",
        token=args.query_token,
        payload={"question": "DROP TABLE orders"},
    )
    assert blocked["security"]["allowed"] is False
    assert blocked["executed_sql"] is None

    bounded, _ = request_json(
        base_url,
        "/api/query",
        token=args.query_token,
        payload={"question": "Give me 1,000,000 rows of order items"},
    )
    assert bounded["row_count"] <= 100
    assert bounded["security"]["limit_injected"] is True

    try:
        request_json(base_url, "/api/audit?limit=1", token=args.query_token)
    except urllib.error.HTTPError as error:
        assert error.code == 403
    else:
        raise AssertionError("query-scoped token unexpectedly read private audit data")

    audit, _ = request_json(base_url, "/api/audit?limit=3", token=args.audit_token)
    assert audit["entries"]
    print("PASS health, auth scopes, query, destructive block, row cap, and audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
