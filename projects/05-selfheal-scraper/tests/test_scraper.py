"""Self-heal pipeline tests (demo mode, deterministic heuristic healer)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("SLACK_WEBHOOK_URL", None)

from fastapi.testclient import TestClient  # noqa: E402
from api import index  # noqa: E402

client = TestClient(index.app)


def setup_function(_):
    index.reset_state()


def test_v1_uses_css_fast_path():
    r = client.post("/api/scrape", json={"product_id": "p1", "force_layout": "v1"}).json()
    res = r["results"][0]
    assert res["status"] == "OK" and res["method"] == "css" and res["price"] == 549.00
    assert res["selector_version"] == 1 and not res["healed"]


def test_v2_breaks_selector_and_heals():
    r = client.post("/api/scrape", json={"product_id": "p1", "force_layout": "v2"}).json()
    res = r["results"][0]
    assert res["status"] == "OK" and res["healed"] is True
    assert res["price"] == 519.00
    assert "css_miss" in res["steps"] and "healed" in res["steps"]
    reg = client.get("/api/selectors").json()
    entry = next(e for e in reg["registry"] if e["product_id"] == "p1")
    assert entry["version"] == 2 and entry["method"].startswith("healed:")
    assert len(reg["heals"]) == 1 and reg["heals"][0]["validated"] is True


def test_healed_selector_works_on_next_run():
    client.post("/api/scrape", json={"product_id": "p1", "force_layout": "v2"})
    r2 = client.post("/api/scrape", json={"product_id": "p1", "force_layout": "v2"}).json()
    res = r2["results"][0]
    # second v2 run must hit the (healed) css fast path — no re-heal
    assert res["method"] == "css" and res["price"] == 519.00 and not res["healed"]
    reg = client.get("/api/selectors").json()
    entry = next(e for e in reg["registry"] if e["product_id"] == "p1")
    assert entry["version"] == 2  # no further bump


def test_cron_scrapes_all_products():
    r = client.get("/api/cron").json()
    assert r["cron"] is True and len(r["results"]) == len(index.CATALOG)
    assert all(x["status"] == "OK" for x in r["results"])
    prods = client.get("/api/products").json()["products"]
    assert all(p["current_price"] is not None for p in prods)


def test_price_drop_alert():
    client.post("/api/scrape", json={"product_id": "p3", "force_layout": "v1"})   # 429.00
    client.post("/api/scrape", json={"product_id": "p3", "force_layout": "v2"})   # 399.00 → -7%
    alerts = client.get("/api/products").json()["alerts"]
    assert any(a["product_id"] == "p3" and a["drop_pct"] >= 5 for a in alerts)


def test_all_products_heal_on_v2():
    r = client.post("/api/scrape", json={"force_layout": "v2"}).json()
    assert all(x["status"] == "OK" and x["healed"] for x in r["results"])
    expected = {p["id"]: p["price_v2"] for p in index.CATALOG}
    got = {x["product_id"]: x["price"] for x in r["results"]}
    assert got == expected


def test_mock_store_layouts_differ():
    v1 = client.get("/api/mock/store?layout=v1").text
    v2 = client.get("/api/mock/store?layout=v2").text
    assert "product-price" in v1 and "product-price" not in v2
    assert "pcard" in v2


def test_health_and_unknown_product():
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["mode"] == "demo"
    r = client.post("/api/scrape", json={"product_id": "nope"})
    assert r.status_code == 404
