#!/usr/bin/env python3
"""Smoke-test a deployed StateGraph API using one owner bearer token."""
from __future__ import annotations

import argparse
import os
import sys
import uuid

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a deployed StateGraph API")
    parser.add_argument("base_url")
    parser.add_argument("--token", default=os.getenv("STATEGRAPH_SMOKE_TOKEN"))
    args = parser.parse_args()
    if not args.token:
        parser.error("provide --token or STATEGRAPH_SMOKE_TOKEN for a disposable test user")

    base = args.base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {args.token}"}
    with httpx.Client(timeout=45, headers=headers) as client:
        health = client.get(f"{base}/api/health")
        health.raise_for_status()
        readiness = client.get(f"{base}/api/readiness")
        readiness.raise_for_status()
        if not readiness.json().get("ready"):
            raise RuntimeError("deployed dependencies are not ready")

        created = client.post(
            f"{base}/api/tasks",
            headers={**headers, "X-Request-ID": str(uuid.uuid4())},
            json={
                "title": "Deployment smoke",
                "input": "Analyze sensitive financial risk and summarize the evidence",
                "remember": False,
            },
        )
        created.raise_for_status()
        task = created.json()
        if task.get("status") != "awaiting_approval":
            raise RuntimeError("risk policy did not interrupt the smoke task")

        detail = client.get(f"{base}/api/tasks/{task['id']}")
        detail.raise_for_status()
        approval = detail.json().get("approval")
        if not approval or not detail.json().get("sources"):
            raise RuntimeError("interrupted task lacks approval or evidence")

        resumed = client.post(
            f"{base}/api/approvals/{approval['id']}/approve",
            json={"note": "deployment smoke approval"},
        )
        resumed.raise_for_status()
        if resumed.json().get("status") != "completed":
            raise RuntimeError("approved task did not complete")

        persisted = client.get(f"{base}/api/tasks/{task['id']}")
        persisted.raise_for_status()
        if persisted.json().get("status") != "completed" or not persisted.json().get("result"):
            raise RuntimeError("completed task was not queryable after resume")

    print("PASS: health, readiness, interrupt, approval, completion, and projection read")
    return 0


if __name__ == "__main__":
    sys.exit(main())
