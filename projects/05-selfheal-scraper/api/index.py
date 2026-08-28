"""
SelfHeal Scraper — LLM-adaptive selector repair for price monitoring
====================================================================

Scrapers die when sites redesign. This service monitors products with stored
CSS selectors (the fast path) and, on a selector MISS, runs a self-healing
pipeline:

  1. trim the DOM to a relevant snippet
  2. GROQ_API_KEY set → Llama 3 extracts the price and proposes a new selector
     else → deterministic heuristic healer (currency-regex DOM scan + candidate
            selector derivation from the matched node's classes/ids)
  3. validate the healed selector against the live DOM
  4. bump the selector registry version, log the heal, append price history

A bundled mock store serves layout v1; `?layout=v2` simulates a full site
redesign (renamed classes, restructured DOM, price moved into a data attr
span). Demo mode needs no keys and is fully deterministic.
"""
import os
import re
import time
import json as _json
import urllib.request

from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="SelfHeal Scraper",
    description="Price scraper whose CSS selectors repair themselves when site layouts change.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Mock store (two layouts = a simulated redesign)
# ---------------------------------------------------------------------------
CATALOG = [
    {"id": "p1", "name": "Aurora Standing Desk", "price_v1": 549.00, "price_v2": 519.00},
    {"id": "p2", "name": "Drift Ergonomic Chair", "price_v1": 899.00, "price_v2": 949.00},
    {"id": "p3", "name": "Pulse 4K Monitor", "price_v1": 429.00, "price_v2": 399.00},
]


def render_store(layout: str) -> str:
    if layout == "v2":  # post-redesign markup: new class names, price in nested span
        cards = "".join(f"""
        <article class="pcard" data-sku="{p['id']}">
          <h3 class="pcard__title">{p['name']}</h3>
          <div class="pcard__buy">
            <span class="amount" data-price="{p['price_v2']:.2f}">${p['price_v2']:,.2f}</span>
            <button class="pcard__btn">Add to cart</button>
          </div>
        </article>""" for p in CATALOG)
        return f"<!DOCTYPE html><html><head><title>MockStore v2</title></head><body><main class='catalog-grid'>{cards}</main></body></html>"
    cards = "".join(f"""
    <div class="product" id="{p['id']}">
      <h2 class="product-name">{p['name']}</h2>
      <div class="product-price">${p['price_v1']:,.2f}</div>
      <button>Buy</button>
    </div>""" for p in CATALOG)
    return f"<!DOCTYPE html><html><head><title>MockStore v1</title></head><body><div class='products'>{cards}</div></body></html>"


# ---------------------------------------------------------------------------
# Selector registry + price history (in-memory per instance)
# ---------------------------------------------------------------------------
def initial_state():
    return {
        "selectors": {
            p["id"]: {"product_id": p["id"], "selector": f"#{p['id']} .product-price",
                      "version": 1, "method": "seed", "healed_at": None}
            for p in CATALOG
        },
        "history": {p["id"]: [] for p in CATALOG},   # [{price, at, method, layout}]
        "heals": [],                                   # audit of heal events
        "alerts": [],                                  # price-drop alerts
    }


STATE = initial_state()


def reset_state():
    global STATE
    STATE = initial_state()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
PRICE_RE = re.compile(r"\$\s*([0-9][0-9,]*\.?[0-9]{0,2})")


def parse_price(text: str):
    m = PRICE_RE.search(text or "")
    if m:
        return float(m.group(1).replace(",", ""))
    m = re.search(r"([0-9][0-9,]*\.[0-9]{2})", text or "")
    return float(m.group(1).replace(",", "")) if m else None


def css_fast_path(soup: BeautifulSoup, selector: str):
    try:
        node = soup.select_one(selector)
    except Exception:
        return None
    if node is None:
        return None
    price = parse_price(node.get_text(" ", strip=True))
    if price is None and node.has_attr("data-price"):
        price = parse_price("$" + node["data-price"])
    return price


def product_scope(soup: BeautifulSoup, product):
    """Find the tightest DOM subtree containing ONLY this product's name."""
    all_names = [p["name"] for p in CATALOG]
    for tag in soup.find_all(True):
        if tag.string and product["name"] in tag.string:
            cur = tag
            # walk up while the parent still contains exactly one product name
            while cur.parent and cur.parent.name not in ("body", "html"):
                parent_text = cur.parent.get_text(" ", strip=True)
                if sum(1 for n in all_names if n in parent_text) > 1:
                    break
                cur = cur.parent
            return cur
    return soup


def derive_selector(node) -> str:
    """Derive a stable CSS selector for a matched price node."""
    parts = []
    cur = node
    while cur is not None and cur.name not in (None, "body", "html") and len(parts) < 3:
        seg = cur.name
        if cur.get("id"):
            parts.append(f"#{cur['id']}")
            break
        attrs = {k: v for k, v in cur.attrs.items()
                 if k.startswith("data-") and k != "data-price" and isinstance(v, str)}
        cls = cur.get("class") or []
        if attrs:  # data attrs (e.g. data-sku) are the most product-specific anchors
            k, v = next(iter(attrs.items()))
            seg += f"[{k}='{v}']"
            parts.append(seg)
            break
        if cls:
            seg += "." + ".".join(cls[:2])
        parts.append(seg)
        cur = cur.parent
    return " ".join(reversed(parts))


def heuristic_heal(soup: BeautifulSoup, product):
    """Deterministic healer: scan the product's DOM scope for currency text."""
    scope = product_scope(soup, product)
    candidates = []
    for tag in scope.find_all(True):
        txt = tag.get_text(" ", strip=True) if tag else ""
        direct = "".join(tag.find_all(string=True, recursive=False)).strip()
        p = parse_price(direct) or (parse_price("$" + tag["data-price"]) if tag.has_attr("data-price") else None)
        if p is None and len(txt) < 40:
            p = parse_price(txt)
        if p is not None:
            candidates.append((tag, p))
    if not candidates:
        return None, None
    # prefer the deepest/smallest node
    tag, price = min(candidates, key=lambda c: len(c[0].get_text()))
    return price, derive_selector(tag)


def llm_heal(html_snippet: str, product):
    """Real path: Multi-provider LLM selector repair (Groq -> Mistral Codestral -> NVIDIA NIM)."""
    sys_msg = (
        "You repair broken web scrapers. Given an HTML snippet and a product name, "
        'return JSON {"price": <number>, "selector": "<css selector for the price node>"}. JSON only.'
    )
    user_msg = f"Product: {product['name']}\nHTML:\n{html_snippet[:6000]}"

    # Provider 1: Groq Llama 3 70B
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            body = _json.dumps({
                "model": "llama3-70b-8192",
                "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}],
                "temperature": 0, "response_format": {"type": "json_object"},
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = _json.load(r)
            d = _json.loads(out["choices"][0]["message"]["content"])
            return float(d["price"]), str(d["selector"])
        except Exception:
            pass

    # Provider 2: Mistral Codestral
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    if mistral_key:
        try:
            body = _json.dumps({
                "model": "codestral-latest",
                "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}],
                "temperature": 0, "response_format": {"type": "json_object"},
            }).encode()
            req = urllib.request.Request(
                "https://api.mistral.ai/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {mistral_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = _json.load(r)
            d = _json.loads(out["choices"][0]["message"]["content"])
            return float(d["price"]), str(d["selector"])
        except Exception:
            pass

    # Provider 3: NVIDIA NIM
    nvidia_key = os.environ.get("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            body = _json.dumps({
                "model": "meta/llama-3.1-70b-instruct",
                "messages": [{"role": "system", "content": sys_msg}, {"role": "user", "content": user_msg}],
                "temperature": 0,
            }).encode()
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = _json.load(r)
            txt = out["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.DOTALL)
            if m:
                d = _json.loads(m.group(0))
                return float(d["price"]), str(d["selector"])
        except Exception:
            pass

    return None



# ---------------------------------------------------------------------------
# Scrape pipeline
# ---------------------------------------------------------------------------
def fetch_html(product, layout: str) -> str:
    url = product.get("url")
    if url and url.startswith("http"):
        try:
            import httpx  # optional; external URLs only
            return httpx.get(url, timeout=15, follow_redirects=True).text
        except Exception:
            pass
    return render_store(layout)


def scrape_product(product, layout: str) -> dict:
    t0 = time.time()
    reg = STATE["selectors"][product["id"]]
    html = fetch_html(product, layout)
    soup = BeautifulSoup(html, "html.parser")
    steps = ["fetched"]

    price = css_fast_path(soup, reg["selector"])
    method = "css"
    healed = False
    if price is not None:
        steps.append("css_fast_path_hit")
    else:
        steps.append("css_miss")
        # self-heal
        scope = product_scope(soup, product)
        result = llm_heal(str(scope), product)
        healer = "llama3 (groq)"
        if result is None:
            result = heuristic_heal(soup, product)
            healer = "heuristic"
        new_price, new_selector = (result if result and result[0] is not None else (None, None))
        if new_price is None:
            steps.append("heal_failed")
            return {"product_id": product["id"], "name": product["name"], "status": "FAILED",
                    "method": "none", "price": None, "selector": reg["selector"], "steps": steps,
                    "latency_ms": round((time.time() - t0) * 1000, 1)}
        # validate healed selector against the live DOM (must yield the same price)
        validated = bool(new_selector) and css_fast_path(soup, new_selector) == new_price
        if not validated:
            new_selector = reg["selector"]  # keep old; price still extracted
        old_selector = reg["selector"]
        if validated:
            reg.update({"selector": new_selector, "version": reg["version"] + 1,
                        "method": f"healed:{healer}",
                        "healed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        STATE["heals"].insert(0, {
            "product_id": product["id"], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "old_selector": old_selector, "new_selector": new_selector,
            "validated": bool(validated), "healer": healer, "price": new_price, "layout": layout,
        })
        price, method, healed = new_price, f"self-heal ({healer})", True
        steps += ["healed", "selector_validated" if validated else "selector_kept_old", "registry_updated"]

    # price history + drop alert
    hist = STATE["history"][product["id"]]
    prev = hist[-1]["price"] if hist else None
    hist.append({"price": price, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                 "method": method, "layout": layout})
    del hist[:-50]
    if prev and price < prev * 0.95:
        alert = {"product_id": product["id"], "name": product["name"], "from": prev, "to": price,
                 "drop_pct": round((1 - price / prev) * 100, 1),
                 "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        STATE["alerts"].insert(0, alert)
        _notify_slack(alert)
        steps.append("price_drop_alert")
    steps.append("price_logged")
    return {"product_id": product["id"], "name": product["name"], "status": "OK", "method": method,
            "healed": healed, "price": price, "selector": reg["selector"],
            "selector_version": reg["version"], "steps": steps,
            "latency_ms": round((time.time() - t0) * 1000, 1)}


def _notify_slack(alert: dict) -> None:
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    if not hook:
        return
    try:
        body = _json.dumps({"text": f"📉 {alert['name']}: ${alert['from']} → ${alert['to']} (-{alert['drop_pct']}%)"}).encode()
        urllib.request.urlopen(urllib.request.Request(
            hook, data=body, headers={"Content-Type": "application/json"}), timeout=10)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
class ScrapeIn(BaseModel):
    product_id: str | None = None
    force_layout: str = "v1"


@app.post("/api/scrape")
def api_scrape(body: ScrapeIn):
    layout = "v2" if body.force_layout == "v2" else "v1"
    targets = [p for p in CATALOG if body.product_id in (None, p["id"])]
    if not targets:
        return JSONResponse({"error": f"unknown product_id {body.product_id}"}, status_code=404)
    return {"layout": layout, "results": [scrape_product(p, layout) for p in targets]}


@app.get("/api/cron")
def api_cron(layout: str = Query("v1")):
    """Vercel Cron entrypoint — scrapes every monitored product."""
    layout = "v2" if layout == "v2" else "v1"
    return {"cron": True, "layout": layout,
            "results": [scrape_product(p, layout) for p in CATALOG]}


@app.get("/api/products")
def api_products():
    return {"products": [
        {**{k: p[k] for k in ("id", "name")},
         "current_price": (STATE["history"][p["id"]][-1]["price"] if STATE["history"][p["id"]] else None),
         "history": STATE["history"][p["id"]]}
        for p in CATALOG], "alerts": STATE["alerts"]}


@app.get("/api/selectors")
def api_selectors():
    return {"registry": list(STATE["selectors"].values()), "heals": STATE["heals"]}


@app.get("/api/mock/store")
def api_mock_store(layout: str = Query("v1")):
    return HTMLResponse(render_store("v2" if layout == "v2" else "v1"))


@app.get("/api/health")
def api_health():
    return {"service": "selfheal-scraper", "status": "ok",
            "mode": "live" if os.environ.get("GROQ_API_KEY") else "demo",
            "products_monitored": len(CATALOG),
            "heals_recorded": len(STATE["heals"])}


@app.post("/api/reset")
def api_reset():
    reset_state()
    return {"reset": True}


@app.get("/")
def root():
    path = os.path.join(os.path.dirname(__file__), "..", "public", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"service": "selfheal-scraper", "docs": "/docs"})
