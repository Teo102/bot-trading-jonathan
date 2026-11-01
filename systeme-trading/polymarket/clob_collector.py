#!/usr/bin/env python3
"""Collecteur public Polymarket et simulateur d'antisélection maker.

Recherche uniquement. Le script lit des points d'accès publics (Gamma, CLOB, Data API,
WebSocket marché). Il n'utilise aucune clé, aucune signature, et ne passe aucun ordre.

Usage :
    python clob_collector.py                       # collecte + simulateur
    python clob_collector.py --ws --ws-seconds 180 # ajoute une capture WebSocket
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import re
import sys
import time

import numpy as np
import requests

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
DOCS_FEES = "https://docs.polymarket.com/trading/fees.md"

# Filtre par catégorie : étiquettes éditoriales Gamma (slug). Ordre = priorité d'affectation.
CATEGORIES = {
    "macroeconomie": ["economy", "fed-rates", "macro-indicators", "economic-policy", "inflation",
                      "gdp", "jobs", "unemployment", "cpi", "fed", "economics"],
    "technologie": ["tech", "technology", "ai", "big-tech"],
    "politique": ["politics"],
}
# Pages de candidats par slug (100 marchés par page), pour chaque tri.
CAND_PAGES = {"politics": 15, "economy": 5, "tech": 5, "ai": 3, "fed-rates": 3, "finance": 3}
SORT_KEYS = ["liquidityNum", "volume24hr"]
# Étiquettes qui font sortir un marché du périmètre demandé.
EXCLUDE_TAGS = {
    "sports": "sport", "games": "sport", "crypto": "crypto", "crypto-prices": "crypto", "bitcoin": "crypto",
    "geopolitics": "geopolitique", "weather": "meteo", "mentions": "mentions", "mention-markets": "mentions",
    "tweet-markets": "comptage de publications", "tweets-markets": "comptage de publications",
}
EXCLUDE_RE = [
    (re.compile(r"\bpost\b.*\b(?:tweets?|posts?)\b", re.I), "comptage de publications"),
    (re.compile(r"\bwill .{1,60}\bsay\b", re.I), "mentions"),
]
MIDTERM_TAG_RE = re.compile(r"midterm|house-elections|senate-elections|nov-4-elections|governor|tossup", re.I)
MIDTERM_Q_RE = re.compile(r"midterm|\b2026 (house|senate|governor)|balance of power", re.I)
# Le scrutin visé est celui du 03/11/2026. Une autre année dans l'intitulé ou une date de fin lointaine exclut le marché.
MIDTERM_YEAR = 2026
MIDTERM_END_MAX = dt.datetime(2027, 3, 1, tzinfo=dt.timezone.utc).timestamp()
# Scrutins américains du même jour sans étiquette midterm (comté, mairie) : fin Gamma au lendemain du vote.
SAME_DAY_US_TAGS = {"us-presidential-election", "deprec-us-election", "mayoral-races"}
SAME_DAY_START = dt.datetime(2026, 11, 3, tzinfo=dt.timezone.utc).timestamp()
SAME_DAY_END = dt.datetime(2026, 11, 6, tzinfo=dt.timezone.utc).timestamp()

# Barème lu sur docs.polymarket.com/trading/fees et /market-makers/maker-rebates le 31/10/2026.
# Il ne sert que de scénario contrefactuel : le calcul réel utilise feeSchedule, marché par marché.
DOC_FEES = {
    "politique": {"rate": 0.04, "rebate": 0.25, "label": "Politics"},
    "macroeconomie": {"rate": 0.05, "rebate": 0.25, "label": "Economics"},
    "technologie": {"rate": 0.04, "rebate": 0.25, "label": "Tech"},
}
HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600, "derniere": None}
BLOCK_SECONDS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600, "derniere": 24 * 3600}
MAX_GAP_S = 1800  # écart maximal toléré entre l'instant visé et le point d'historique retenu


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(value) -> float | None:
    if not value:
        return None
    text = str(value).strip().replace(" ", "T").replace("Z", "+00:00")
    text = re.sub(r"\+00$", "+00:00", text)
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


class Http:
    """Client public avec bridage par hôte, reprises et journal d'incidents."""

    def __init__(self, min_interval: float = 0.07, retries: int = 5):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "recherche-clob-collector/1.0"
        self.min_interval = min_interval
        self.retries = retries
        self.last_call: dict[str, float] = {}
        self.incidents: list[dict] = []
        self.calls = collections.Counter()

    def _throttle(self, url: str) -> str:
        host = url.split("/")[2]
        wait = self.min_interval - (time.monotonic() - self.last_call.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last_call[host] = time.monotonic()
        return host

    def request(self, method: str, url: str, *, params=None, json_body=None, quiet_statuses=()):
        response = None
        for attempt in range(self.retries):
            host = self._throttle(url)
            self.calls[host] += 1
            try:
                response = self.session.request(method, url, params=params, json=json_body, timeout=30)
            except requests.RequestException as exc:
                self._note(url, params, f"exception {type(exc).__name__}", attempt)
                time.sleep(min(2 ** attempt, 20))
                continue
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    self._note(url, params, "réponse non JSON", attempt)
                    time.sleep(min(2 ** attempt, 20))
                    continue
            if response.status_code in quiet_statuses:
                return None
            if response.status_code == 429 or response.status_code >= 500:
                delay = float(response.headers.get("Retry-After") or min(2 ** attempt, 30))
                self._note(url, params, f"HTTP {response.status_code}", attempt)
                time.sleep(delay)
                continue
            self._note(url, params, f"HTTP {response.status_code} {response.text[:160]}", attempt)
            return None
        self._note(url, params, "abandon après reprises", self.retries)
        return None

    def get(self, url: str, params=None, quiet_statuses=()):
        return self.request("GET", url, params=params, quiet_statuses=quiet_statuses)

    def _note(self, url, params, message, attempt):
        self.incidents.append({"ts": iso(time.time()), "url": url, "params": str(params)[:160],
                               "message": message, "essai": attempt})


def load_json_field(value, default):
    if isinstance(value, (list, dict)):
        return value
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def market_tags(market: dict) -> set[str]:
    return {t.get("slug", "") for t in market.get("tags") or [] if isinstance(t, dict)}


def classify(market: dict, source_slugs: set[str]) -> tuple[str | None, list[str]]:
    tags = market_tags(market) | source_slugs
    matches = [cat for cat, slugs in CATEGORIES.items() if tags & set(slugs)]
    return (matches[0] if matches else None), matches


def is_midterm(market: dict) -> bool:
    tags = market_tags(market)
    question = market.get("question") or ""
    years = {int(y) for y in re.findall(r"\b(20\d\d)\b", question)}
    if years and MIDTERM_YEAR not in years:
        return False
    end_ts = parse_ts(market.get("endDate"))
    if any(MIDTERM_TAG_RE.search(t) for t in tags) or MIDTERM_Q_RE.search(question):
        return end_ts is None or end_ts <= MIDTERM_END_MAX
    same_day = end_ts is not None and SAME_DAY_START <= end_ts < SAME_DAY_END
    return bool(same_day and MIDTERM_YEAR in years and "elections" in tags and tags & SAME_DAY_US_TAGS)


def exclusion_reason(market: dict, now_ts: float) -> str | None:
    tags = market_tags(market)
    for slug, reason in EXCLUDE_TAGS.items():
        if slug in tags:
            return f"etiquette {slug} ({reason})"
    question = market.get("question") or ""
    for pattern, reason in EXCLUDE_RE:
        if pattern.search(question):
            return f"intitule ({reason})"
    if not market.get("enableOrderBook"):
        return "carnet non active"
    if not market.get("acceptingOrders"):
        return "ordres refuses (acceptingOrders faux)"
    if market.get("closed") or not market.get("active"):
        return "marche clos ou inactif"
    end_ts = parse_ts(market.get("endDate"))
    if end_ts is not None and end_ts <= now_ts:
        return "date de fin depassee"
    if load_json_field(market.get("umaResolutionStatuses"), []):
        return "resolution UMA en cours"
    tokens = load_json_field(market.get("clobTokenIds"), [])
    if len(tokens) != 2:
        return "jetons absents ou non binaires"
    return None


def fetch_candidates(http: Http) -> tuple[dict, dict]:
    """Candidats par étiquette, triés par liquidité déclarée puis par volume 24 h."""
    pool: dict[str, dict] = {}
    sources: dict[str, set[str]] = collections.defaultdict(set)
    tag_info = {}
    for slugs in CATEGORIES.values():
        for slug in slugs:
            tag = http.get(f"{GAMMA}/tags/slug/{slug}", quiet_statuses=(404,))
            if not tag:
                tag_info[slug] = {"id": None, "marches_lus": 0}
                continue
            count = 0
            for order in SORT_KEYS:
                for page in range(CAND_PAGES.get(slug, 2)):
                    rows = http.get(f"{GAMMA}/markets", params={
                        "active": "true", "closed": "false", "limit": 100, "offset": page * 100,
                        "tag_id": tag["id"], "order": order, "ascending": "false", "include_tag": "true"})
                    if not rows:
                        break
                    for market in rows:
                        cid = market.get("conditionId")
                        if not cid:
                            continue
                        pool[cid] = market
                        sources[cid].add(slug)
                        count += 1
                    if len(rows) < 100:
                        break
            tag_info[slug] = {"id": tag["id"], "marches_lus": count}
    return pool, {"sources": sources, "tags": tag_info}


def fetch_books(http: Http, token_ids: list[str]) -> dict[str, dict]:
    books: dict[str, dict] = {}
    for start in range(0, len(token_ids), 100):
        chunk = token_ids[start:start + 100]
        rows = http.request("POST", f"{CLOB}/books", json_body=[{"token_id": t} for t in chunk])
        if not isinstance(rows, list):
            continue
        for book in rows:
            books[str(book.get("asset_id"))] = book
    return books


def rel_depth(bids: list, asks: list, pct: float = 0.01) -> dict:
    """Profondeur à ±pct du milieu pour un jeton donné, en parts et en dollars de ce jeton."""
    mid = (bids[0][0] + asks[0][0]) / 2
    eps = 1e-9
    bid_lv = [(p, s) for p, s in bids if p >= mid * (1 - pct) - eps]
    ask_lv = [(p, s) for p, s in asks if p <= mid * (1 + pct) + eps]
    return {"bid_parts": sum(s for _, s in bid_lv), "bid_usd": sum(p * s for p, s in bid_lv),
            "ask_parts": sum(s for _, s in ask_lv), "ask_usd": sum(p * s for p, s in ask_lv)}


def book_metrics(book: dict) -> dict | None:
    bids = sorted(((float(l["price"]), float(l["size"])) for l in book.get("bids") or []), key=lambda x: -x[0])
    asks = sorted(((float(l["price"]), float(l["size"])) for l in book.get("asks") or []), key=lambda x: x[0])
    if not bids or not asks:
        return None
    best_bid, best_ask = bids[0][0], asks[0][0]
    if best_bid >= best_ask:
        return None
    mid = (best_bid + best_ask) / 2
    eps = 1e-9

    def depth(low: float, high: float) -> dict:
        bid_lv = [(p, s) for p, s in bids if p >= low - eps]
        ask_lv = [(p, s) for p, s in asks if p <= high + eps]
        return {
            "bid_parts": sum(s for _, s in bid_lv), "bid_usd": sum(p * s for p, s in bid_lv),
            "ask_parts": sum(s for _, s in ask_lv), "ask_usd": sum(p * s for p, s in ask_lv),
            # Capital minimal engagé, invariant au choix du jeton : le jeton le moins cher de chaque niveau.
            "bid_capital": sum(min(p, 1 - p) * s for p, s in bid_lv),
            "ask_capital": sum(min(p, 1 - p) * s for p, s in ask_lv),
        }

    # La bande à ±1 % se calcule sur le jeton le moins cher, sinon elle dépend du jeton lu. Le carnet du jeton 1
    # se déduit de celui du jeton 0 : un bid à p sur le jeton 0 est un ask à 1 - p sur le jeton 1.
    token_ref = 0 if mid <= 0.5 else 1
    if token_ref == 0:
        rel = rel_depth(bids, asks)
    else:
        rel = rel_depth([(round(1 - p, 6), s) for p, s in asks], [(round(1 - p, 6), s) for p, s in bids])
    abs1c = depth(mid - 0.01, mid + 0.01)
    return {
        "meilleur_bid": best_bid, "meilleur_ask": best_ask, "ecart_cents": round((best_ask - best_bid) * 100, 4),
        "milieu": round(mid, 5),
        "jeton_ref_1pct": token_ref,
        "bid_parts_1pct": rel["bid_parts"], "bid_usd_1pct": rel["bid_usd"],
        "ask_parts_1pct": rel["ask_parts"], "ask_usd_1pct": rel["ask_usd"],
        "bid_parts_1c": abs1c["bid_parts"], "bid_usd_1c": abs1c["bid_usd"],
        "ask_parts_1c": abs1c["ask_parts"], "ask_usd_1c": abs1c["ask_usd"],
        "score_liquidite_usd": min(abs1c["bid_capital"], abs1c["ask_capital"]),
        "score_rel_1pct_usd": min(rel["bid_usd"], rel["ask_usd"]),
        "pas_prix": float(book.get("tick_size") or 0) or None,
        "taille_min": float(book.get("min_order_size") or 0) or None,
        "carnet_ts_ms": int(book.get("timestamp") or 0),
        "_bids": bids, "_asks": asks,
    }


def fee_params(market: dict) -> dict:
    schedule = market.get("feeSchedule") or {}
    missing = not schedule
    return {
        "feesEnabled": market.get("feesEnabled"), "feeType": market.get("feeType"),
        "fee_rate": float(schedule.get("rate") or 0), "fee_exponent": float(schedule.get("exponent") or 1),
        "fee_taker_only": schedule.get("takerOnly"), "rebate_rate": float(schedule.get("rebateRate") or 0),
        "fee_schedule_absent": missing,
    }


def fee_per_share(price, rate, exponent):
    return rate * (price * (1 - price)) ** exponent


def rebate_per_1000(price: float, rate: float, rebate: float, exponent: float = 1.0) -> float:
    if price <= 0 or price >= 1:
        return 0.0
    return 1000.0 / price * fee_per_share(price, rate, exponent) * rebate


def reward_estimate(metrics: dict, market: dict) -> dict:
    """Récompense de liquidité brute pour 1 000 $ posés, borne haute [estimation]."""
    today = utcnow().strftime("%Y-%m-%d")
    rewards = [r for r in market.get("clobRewards") or []
               if (r.get("startDate") or "0000") <= today <= (r.get("endDate") or "9999")]
    daily = sum(float(r.get("rewardsDailyRate") or 0) for r in rewards)
    assets = sorted({r.get("assetAddress") for r in rewards if r.get("assetAddress")})
    out = {"recompense_jour_usd": daily, "recompense_actifs": assets,
           "recompense_taille_min": market.get("rewardsMinSize"), "recompense_ecart_max_cents": market.get("rewardsMaxSpread"),
           "recompense_estimee_1000usd_jour": None, "recompense_q_carnet": None}
    spread_max = float(market.get("rewardsMaxSpread") or 0)
    if daily <= 0 or spread_max <= 0:
        return out
    mid = metrics["milieu"]

    def score(price: float) -> float:
        distance = abs(price - mid) * 100
        return ((spread_max - distance) / spread_max) ** 2 if distance < spread_max else 0.0

    q_bid = sum(score(p) * s for p, s in metrics["_bids"])
    q_ask = sum(score(p) * s for p, s in metrics["_asks"])
    single_side = 0.10 <= mid <= 0.90

    def q_min(one: float, two: float) -> float:
        low, high = min(one, two), max(one, two)
        return max(low, high / 3.0) if single_side else low

    book_q = q_min(q_bid, q_ask)
    bid, ask = metrics["meilleur_bid"], metrics["meilleur_ask"]
    own_bid = score(bid) * 500.0 / bid
    own_ask = score(ask) * 500.0 / (1 - ask)  # vendre le jeton 0 revient à acheter le jeton 1 à (1 - prix)
    own_q = q_min(own_bid, own_ask)
    min_size = float(market.get("rewardsMinSize") or 0)
    if own_q <= 0 or 500.0 / bid < min_size or 500.0 / (1 - ask) < min_size:
        return out
    out["recompense_q_carnet"] = book_q
    out["recompense_estimee_1000usd_jour"] = daily * own_q / (own_q + book_q)
    return out


def fetch_trades(http: Http, condition_id: str, start_ts: float, end_ts: float, max_trades: int) -> dict:
    seen, rows, truncated, api_stop = set(), [], False, None
    offset = 0
    while True:
        batch = http.get(f"{DATA}/trades", params={"market": condition_id, "limit": 1000, "offset": offset, "takerOnly": "true"},
                         quiet_statuses=(400,))
        if batch is None:
            api_stop = f"offset {offset} refuse ou en erreur"
            truncated = True
            break
        if not batch:
            break
        for trade in batch:
            key = (trade.get("transactionHash"), trade.get("asset"), trade.get("side"), trade.get("price"), trade.get("size"), trade.get("timestamp"))
            if key in seen:
                continue
            seen.add(key)
            if trade.get("conditionId") == condition_id and float(trade.get("timestamp", 0)) <= end_ts:
                rows.append(trade)
        oldest = min(float(t.get("timestamp", 0)) for t in batch)
        if oldest < start_ts:
            break
        offset += len(batch)
        if len(batch) < 1000:
            break
        if offset > 10000 or len(rows) >= max_trades:
            truncated = True
            break
    rows = [t for t in rows if float(t.get("timestamp", 0)) >= start_ts]
    return {"rows": rows, "tronque": truncated, "arret_api": api_stop}


def fetch_history(http: Http, token: str, start_ts: float, end_ts: float, fidelity: int) -> dict:
    points: dict[int, float] = {}
    span, cursor, refusals = 3 * 86400, int(start_ts), 0
    end = int(end_ts)
    while cursor < end:
        upper = min(cursor + span, end)
        data = http.get(f"{CLOB}/prices-history", params={"market": token, "startTs": cursor, "endTs": upper, "fidelity": fidelity},
                        quiet_statuses=(400,))
        if data is None:
            refusals += 1
            if span > 6 * 3600:
                span //= 2
                continue
            cursor = upper
            continue
        for point in data.get("history") or []:
            points[int(point["t"])] = float(point["p"])
        cursor = upper
    fallback = False
    if not points:
        data = http.get(f"{CLOB}/prices-history", params={"market": token, "interval": "max", "fidelity": 60}, quiet_statuses=(400,))
        for point in (data or {}).get("history") or []:
            points[int(point["t"])] = float(point["p"])
        fallback = bool(points)
    times = np.array(sorted(points), dtype=np.int64)
    prices = np.array([points[t] for t in times], dtype=float)
    return {"t": times, "p": prices, "refus": refusals, "repli_horaire": fallback}


def price_asof(times, prices, targets):
    idx = np.searchsorted(times, targets, side="right") - 1
    values = np.full(len(targets), np.nan)
    ok = idx >= 0
    gaps = np.full(len(targets), np.inf)
    values[ok] = prices[idx[ok]]
    gaps[ok] = targets[ok] - times[idx[ok]]
    return values, gaps


def normalize_trades(rows: list[dict], token0: str, token1: str) -> dict:
    ts, prices0, traded, sizes, maker_dir, skipped = [], [], [], [], [], 0
    for trade in rows:
        try:
            price, size, stamp = float(trade["price"]), float(trade["size"]), float(trade["timestamp"])
        except (KeyError, TypeError, ValueError):
            skipped += 1
            continue
        if not 0 < price < 1 or size <= 0:
            skipped += 1
            continue
        side = trade.get("side")
        taker = 1 if side == "BUY" else -1 if side == "SELL" else 0
        if trade.get("asset") == token0:
            price0, direction = price, taker
        elif trade.get("asset") == token1:
            price0, direction = 1 - price, -taker
        else:
            skipped += 1
            continue
        if direction == 0:
            skipped += 1
            continue
        ts.append(stamp); prices0.append(price0); traded.append(price); sizes.append(size); maker_dir.append(-direction)
    return {"t": np.array(ts), "p0": np.array(prices0), "p_traded": np.array(traded), "size": np.array(sizes),
            "dir": np.array(maker_dir, dtype=float), "ignores": skipped}


def boot_block(buckets, markout, size, notional, rebate, rebate_doc, iterations, rng):
    unique, inverse = np.unique(buckets, return_inverse=True)
    n_blocks = len(unique)
    result = {"n_blocs": n_blocks}
    if n_blocks < 2:
        return result
    count = np.bincount(inverse, minlength=n_blocks).astype(float)
    sum_m = np.bincount(inverse, markout, n_blocks)
    sum_mz = np.bincount(inverse, markout * size, n_blocks)
    sum_n = np.bincount(inverse, notional, n_blocks)
    sum_rz = np.bincount(inverse, rebate * size, n_blocks)
    sum_z = np.bincount(inverse, size, n_blocks)
    draws = rng.multinomial(n_blocks, np.full(n_blocks, 1 / n_blocks), size=iterations).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        equal = draws @ sum_m / (draws @ count) * 100
        weighted = draws @ sum_mz / (draws @ sum_n) * 1000
        net = draws @ (sum_mz + sum_rz) / (draws @ sum_n) * 1000
        per_share = draws @ sum_mz / (draws @ sum_z) * 100
    for name, values in (("moy_cents", equal), ("vw_1000", weighted), ("net_1000", net), ("vw_cents", per_share)):
        low, high = np.nanpercentile(values, [2.5, 97.5])
        result[f"{name}_ic_bas"], result[f"{name}_ic_haut"] = float(low), float(high)
    return result


def simulate_market(info: dict, trades: dict, history: dict, *, terminal: float | None, iterations: int, rng, doc: dict | None) -> dict:
    """Markout d'un maker rempli à l'opposé de chaque trade taker, en termes du jeton 0."""
    times, prices = history["t"], history["p"]
    out = {"n_trades_bruts": len(trades["t"]), "horizons": {}, "_series": {}}
    if len(trades["t"]) == 0 or len(times) == 0:
        return out
    last_hist_t = float(times[-1])
    final_value = float(terminal) if terminal is not None else float(prices[-1])
    out["valeur_finale"] = final_value
    out["valeur_finale_ts"] = iso(last_hist_t)
    rate, rebate_rate, exponent = info["fee_rate"], info["rebate_rate"], info["fee_exponent"]
    rebate_share = fee_per_share(trades["p_traded"], rate, exponent) * rebate_rate
    doc_share = np.zeros_like(rebate_share)
    if doc:
        doc_share = fee_per_share(trades["p_traded"], doc["rate"], 1.0) * doc["rebate"]
    notional = trades["p_traded"] * trades["size"]
    p0_now, gap_now = price_asof(times, prices, trades["t"])
    ok_now = gap_now <= MAX_GAP_S
    half_spread = trades["dir"][ok_now] * (p0_now[ok_now] - trades["p0"][ok_now])
    out["demi_ecart_effectif_cents"] = float(np.mean(half_spread) * 100) if half_spread.size else None
    out["part_taker_achat_jeton0"] = float(np.mean(trades["dir"] < 0))
    # Contrôle du sens : un taker acheteur doit traiter au-dessus du milieu, donc le maker du bon côté du milieu.
    decided = half_spread[half_spread != 0]
    out["concordance_sens"] = float(np.mean(decided > 0)) if decided.size else None
    out["n_concordance"] = int(decided.size)
    for horizon, seconds in HORIZONS.items():
        if seconds is None:
            value = np.full(len(trades["t"]), final_value)
            usable = np.ones(len(trades["t"]), dtype=bool)
            censored = 0
        else:
            target = trades["t"] + seconds
            if terminal is not None:
                value, gaps = price_asof(times, prices, target)
                after_end = target >= last_hist_t
                value[after_end] = final_value
                gaps[after_end] = 0
                usable = (gaps <= MAX_GAP_S)
                censored = 0
            else:
                value, gaps = price_asof(times, prices, target)
                inside = target <= last_hist_t
                usable = inside & (gaps <= MAX_GAP_S)
                censored = int((~inside).sum())
        gap_dropped = int(len(trades["t"]) - censored - usable.sum())
        markout = trades["dir"][usable] * (value[usable] - trades["p0"][usable])
        size = trades["size"][usable]
        notion = notional[usable]
        reb = rebate_share[usable]
        reb_doc = doc_share[usable]
        stats = {"n": int(usable.sum()), "n_censures": censored, "n_ecartes_trou": gap_dropped}
        both = usable & ok_now
        hs_sum = float((trades["dir"][both] * (p0_now[both] - trades["p0"][both])).sum())
        mv_sum = float((trades["dir"][both] * (value[both] - p0_now[both])).sum())
        hs_count = int(both.sum())
        if hs_count:
            stats["demi_ecart_cents"] = hs_sum / hs_count * 100
            stats["mouvement_contre_maker_cents"] = -mv_sum / hs_count * 100
        if usable.sum() > 0:
            mean = float(markout.mean())
            total_notional = float(notion.sum())
            weighted = float((markout * size).sum() / total_notional * 1000)
            rebate_1000 = float((reb * size).sum() / total_notional * 1000)
            doc_1000 = float((reb_doc * size).sum() / total_notional * 1000)
            stats.update({
                "moy_cents": mean * 100, "cout_antiselection_cents": -mean * 100,
                "vw_cents": float((markout * size).sum() / size.sum() * 100),
                "vw_1000": weighted, "rebate_1000": rebate_1000, "net_1000": weighted + rebate_1000,
                "rebate_bareme_doc_1000": doc_1000, "net_bareme_doc_1000": weighted + doc_1000,
                "notionnel_usd": total_notional,
            })
            buckets = (trades["t"][usable] // BLOCK_SECONDS[horizon]).astype(np.int64)
            stats.update(boot_block(buckets, markout, size, notion, reb, reb_doc, iterations, rng))
        out["horizons"][horizon] = stats
        out["_series"][horizon] = {"m": markout, "z": size, "n": notion, "r": reb, "d": reb_doc, "hs": hs_sum, "mv": mv_sum, "hc": hs_count}
    # Prix moyen exécuté contre clôture (dernière valeur connue).
    buys, sells = trades["dir"] > 0, trades["dir"] < 0
    close = {}
    if buys.any():
        vwap = float((trades["p0"][buys] * trades["size"][buys]).sum() / trades["size"][buys].sum())
        close.update({"vwap_achats_maker": vwap, "gain_achats_cents": (final_value - vwap) * 100, "n_achats": int(buys.sum())})
    if sells.any():
        vwap = float((trades["p0"][sells] * trades["size"][sells]).sum() / trades["size"][sells].sum())
        close.update({"vwap_ventes_maker": vwap, "gain_ventes_cents": (vwap - final_value) * 100, "n_ventes": int(sells.sum())})
    close["derive_fenetre_cents"] = (final_value - float(trades["p0"][np.argmin(trades["t"])])) * 100
    out["cloture"] = close
    return out


def aggregate(results: list[dict], iterations: int, rng, min_n: int = 30) -> dict:
    """Agrégat par horizon. Le bootstrap rééchantillonne des événements entiers."""
    out = {}
    for horizon in HORIZONS:
        clusters: dict[str, dict] = {}
        total_markets = 0
        for res in results:
            series = res.get("sim", {}).get("_series", {}).get(horizon)
            if series is None or len(series["m"]) == 0:
                continue
            total_markets += 1
            cell = clusters.setdefault(res["groupe_evenement"], collections.Counter())
            markout, size, notion, reb, doc = series["m"], series["z"], series["n"], series["r"], series["d"]
            cell["m"] += float(markout.sum()); cell["c"] += len(markout)
            cell["mz"] += float((markout * size).sum()); cell["n"] += float(notion.sum()); cell["z"] += float(size.sum())
            cell["rz"] += float((reb * size).sum()); cell["dz"] += float((doc * size).sum())
            cell["hs"] += series["hs"]; cell["mv"] += series["mv"]; cell["hc"] += series["hc"]
            if len(markout) >= min_n:
                cell["mm"] += float(markout.mean()); cell["nm"] += 1
        if not clusters:
            out[horizon] = {"n": 0, "n_marches": 0, "n_evenements": 0}
            continue
        keys = list(clusters)
        arr = {k: np.array([clusters[c][k] for c in keys], dtype=float) for k in ("m", "c", "mz", "n", "z", "rz", "dz", "mm", "nm", "hs", "mv", "hc")}
        k_total = len(keys)
        stats = {
            "n": int(arr["c"].sum()), "n_marches": total_markets, "n_evenements": k_total,
            "moy_cents": float(arr["m"].sum() / arr["c"].sum() * 100),
            "cout_antiselection_cents": float(-arr["m"].sum() / arr["c"].sum() * 100),
            "moy_marches_cents": float(arr["mm"].sum() / arr["nm"].sum() * 100) if arr["nm"].sum() else None,
            "vw_cents": float(arr["mz"].sum() / arr["z"].sum() * 100),
            "vw_1000": float(arr["mz"].sum() / arr["n"].sum() * 1000),
            "rebate_1000": float(arr["rz"].sum() / arr["n"].sum() * 1000),
            "net_1000": float((arr["mz"].sum() + arr["rz"].sum()) / arr["n"].sum() * 1000),
            "rebate_bareme_doc_1000": float(arr["dz"].sum() / arr["n"].sum() * 1000),
            "net_bareme_doc_1000": float((arr["mz"].sum() + arr["dz"].sum()) / arr["n"].sum() * 1000),
            "notionnel_usd": float(arr["n"].sum()),
            "demi_ecart_cents": float(arr["hs"].sum() / arr["hc"].sum() * 100) if arr["hc"].sum() else None,
            "mouvement_contre_maker_cents": float(-arr["mv"].sum() / arr["hc"].sum() * 100) if arr["hc"].sum() else None,
        }
        if k_total >= 2:
            draws = rng.multinomial(k_total, np.full(k_total, 1 / k_total), size=iterations).astype(float)
            with np.errstate(invalid="ignore", divide="ignore"):
                series = {
                    "moy_cents": draws @ arr["m"] / (draws @ arr["c"]) * 100,
                    "moy_marches_cents": draws @ arr["mm"] / (draws @ arr["nm"]) * 100,
                    "vw_cents": draws @ arr["mz"] / (draws @ arr["z"]) * 100,
                    "vw_1000": draws @ arr["mz"] / (draws @ arr["n"]) * 1000,
                    "net_1000": draws @ (arr["mz"] + arr["rz"]) / (draws @ arr["n"]) * 1000,
                }
            for name, values in series.items():
                low, high = np.nanpercentile(values, [2.5, 97.5])
                stats[f"{name}_ic_bas"], stats[f"{name}_ic_haut"] = float(low), float(high)
        out[horizon] = stats
    return out


async def ws_capture(token_map: dict[str, dict], seconds: int, events_path: pathlib.Path) -> dict:
    import websockets

    counts = collections.Counter()
    per_market: dict[str, dict] = collections.defaultdict(lambda: {
        "evenements": 0, "trades": 0, "volume_parts": 0.0, "maj_prix": 0, "fee_rate_bps": collections.Counter(),
        "ecarts_cents": [], "dernier_bid": None, "dernier_ask": None})
    summary = {"url": WS_URL, "debut": iso(time.time()), "duree_demandee_s": seconds, "jetons_abonnes": len(token_map), "connexions": 0, "erreurs": []}
    deadline = time.monotonic() + seconds
    subscribe = json.dumps({"assets_ids": list(token_map), "type": "market", "custom_feature_enabled": True})

    def note_prices(asset, bid, ask) -> None:
        # Seul le jeton 0 alimente l'écart, pour ne pas compter deux fois le même carnet miroir.
        info = token_map.get(asset)
        if not info or not info["jeton0"]:
            return
        try:
            low, high = float(bid), float(ask)
        except (TypeError, ValueError):
            return
        if high > low:
            cell = per_market[info["question"]]
            cell["maj_prix"] += 1
            cell["dernier_bid"], cell["dernier_ask"] = low, high
            cell["ecarts_cents"].append((high - low) * 100)

    def handle(event: dict, stream) -> None:
        kind = event.get("event_type", "inconnu")
        counts[kind] += 1
        if kind not in ("book", "new_market"):
            stream.write(json.dumps(event) + "\n")
        if kind == "price_change":
            for change in event.get("price_changes") or []:
                info = token_map.get(change.get("asset_id"))
                if info:
                    per_market[info["question"]]["evenements"] += 1
                note_prices(change.get("asset_id"), change.get("best_bid"), change.get("best_ask"))
            return
        info = token_map.get(event.get("asset_id"))
        if not info:
            return
        cell = per_market[info["question"]]
        cell["evenements"] += 1
        if kind == "last_trade_price":
            cell["trades"] += 1
            cell["volume_parts"] += float(event.get("size") or 0)
            cell["fee_rate_bps"][str(event.get("fee_rate_bps"))] += 1
        elif kind == "best_bid_ask":
            note_prices(event.get("asset_id"), event.get("best_bid"), event.get("best_ask"))

    with gzip.open(events_path, "wt", encoding="utf-8") as stream:
        while time.monotonic() < deadline:
            try:
                async with websockets.connect(WS_URL, ping_interval=None, open_timeout=20, max_size=2 ** 24) as socket:
                    summary["connexions"] += 1
                    await socket.send(subscribe)
                    last_ping = time.monotonic()
                    while time.monotonic() < deadline:
                        if time.monotonic() - last_ping >= 10:
                            await socket.send("PING")
                            last_ping = time.monotonic()
                        try:
                            raw = await asyncio.wait_for(socket.recv(), timeout=2)
                        except asyncio.TimeoutError:
                            continue
                        if raw == "PONG":
                            counts["PONG"] += 1
                            continue
                        try:
                            payload = json.loads(raw)
                        except ValueError:
                            counts["non_json"] += 1
                            continue
                        for event in payload if isinstance(payload, list) else [payload]:
                            if isinstance(event, dict):
                                handle(event, stream)
            except Exception as exc:  # reconnexion sur toute coupure, avec trace
                summary["erreurs"].append({"ts": iso(time.time()), "erreur": f"{type(exc).__name__}: {str(exc)[:160]}"})
                await asyncio.sleep(3)
    summary["fin"] = iso(time.time())
    summary["compteurs"] = dict(counts)
    markets = {}
    for question, cell in per_market.items():
        spreads = cell.pop("ecarts_cents")
        cell["fee_rate_bps"] = dict(cell["fee_rate_bps"])
        cell["ecart_moyen_cents"] = float(np.mean(spreads)) if spreads else None
        cell["question"] = question
        markets[question] = cell
    summary["par_marche"] = markets
    return summary


def write_csv(path: pathlib.Path, rows: list[dict], columns: list[str] | None = None) -> None:
    if columns is None:
        columns = []
        for row in rows:
            for key in row:
                if key not in columns and not key.startswith("_"):
                    columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, set)) else v) for k, v in row.items() if k in columns})


def strip_private(obj):
    if isinstance(obj, dict):
        return {k: strip_private(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [strip_private(v) for v in obj]
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def fmt(value, digits=2, empty="n.d."):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return empty
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def ic(stats: dict, name: str, digits=2) -> str:
    low, high = stats.get(f"{name}_ic_bas"), stats.get(f"{name}_ic_haut")
    if low is None or high is None:
        return "n.d."
    return f"[{fmt(low, digits)} ; {fmt(high, digits)}]"


def short(text: str, width: int = 62) -> str:
    text = (text or "").replace("|", "/").strip()
    return text if len(text) <= width else text[:width - 1] + "…"


def check_docs(http: Http) -> dict:
    """Relecture automatique du barème publié, conservée telle quelle pour contrôle."""
    info = {"url": DOCS_FEES, "lu_a": iso(time.time())}
    try:
        response = http.session.get(DOCS_FEES, timeout=30)
        info["statut_http"] = response.status_code
        if response.status_code == 200:
            info["sha256"] = hashlib.sha256(response.content).hexdigest()
            info["lignes_tableau"] = [line.strip() for line in response.text.splitlines()
                                      if line.strip().startswith("|") and re.search(
                                          r"Politics|Economics|Tech|Finance|Geopolitic|Crypto|Sports|Category|Mentions", line)][:14]
    except requests.RequestException as exc:
        info["erreur"] = f"{type(exc).__name__}: {exc}"[:200]
    return info


def census_fees(rows: list[dict]) -> list[dict]:
    counter = collections.Counter()
    for row in rows:
        counter[(row["categorie"], row.get("feeType"), row.get("feesEnabled"), row.get("fee_rate"), row.get("rebate_rate"))] += 1
    return [{"categorie": k[0], "feeType": k[1], "feesEnabled": k[2], "rate": k[3], "rebateRate": k[4], "n_marches": v}
            for k, v in sorted(counter.items(), key=lambda item: (str(item[0][0]), -item[1]))]


def build_market_info(market: dict, category: str, categories: list[str], metrics: dict, rank_group: str | None = None) -> dict:
    tokens = load_json_field(market.get("clobTokenIds"), [])
    outcomes = load_json_field(market.get("outcomes"), [])
    fees = fee_params(market)
    mid = metrics["milieu"]
    doc = DOC_FEES.get(category)
    info = {
        "question": market.get("question"), "slug": market.get("slug"), "condition_id": market.get("conditionId"),
        "categorie": category, "categories_toutes": categories, "mi_mandat": is_midterm(market),
        "resultat_jeton0": outcomes[0] if outcomes else None, "token0": tokens[0], "token1": tokens[1],
        "date_fin": market.get("endDate"), "date_creation": market.get("createdAt"), "volume_24h_usd": market.get("volume24hrClob", market.get("volume24hr")),
        "liquidite_gamma_usd": market.get("liquidityNum"), "restricted": market.get("restricted"), "neg_risk": market.get("negRisk"),
        "holding_rewards": market.get("holdingRewardsEnabled"),
        "groupe_evenement": (market.get("negRiskMarketID") or ((market.get("events") or [{}])[0].get("id")) or market.get("conditionId")),
        "evenement": ((market.get("events") or [{}])[0].get("title")),
        "etiquettes": sorted(market_tags(market)),
        **{k: v for k, v in metrics.items()}, **fees,
    }
    info["rebate_1000_milieu"] = rebate_per_1000(mid, fees["fee_rate"], fees["rebate_rate"], fees["fee_exponent"])
    info["rebate_1000_bareme_doc"] = rebate_per_1000(mid, doc["rate"], doc["rebate"]) if doc else None
    info["frais_taker_cents_par_part"] = fee_per_share(mid, fees["fee_rate"], fees["fee_exponent"]) * 100
    info.update(reward_estimate(metrics, market))
    if rank_group:
        info["echantillon"] = rank_group
    return info


def run_simulation(http: Http, info: dict, args, rng, now_ts: float, *, start=None, end=None, terminal=None, doc=None, trade_sink=None) -> None:
    start_ts = start if start is not None else now_ts - args.window_days * 86400
    end_ts = end if end is not None else now_ts
    fetched = fetch_trades(http, info["condition_id"], start_ts, end_ts, args.max_trades)
    trades = normalize_trades(fetched["rows"], info["token0"], info["token1"])
    first = float(trades["t"].min()) if len(trades["t"]) else start_ts
    history = fetch_history(http, info["token0"], first - 3600, end_ts, args.fidelity)
    info["sim"] = simulate_market(info, trades, history, terminal=terminal, iterations=args.bootstrap, rng=rng, doc=doc)
    info["sim"].update({
        "trades_tronques": fetched["tronque"], "arret_api": fetched["arret_api"], "trades_ignores": trades["ignores"],
        "premier_trade": iso(first) if len(trades["t"]) else None,
        "dernier_trade": iso(float(trades["t"].max())) if len(trades["t"]) else None,
        "points_historique": int(len(history["t"])), "historique_refus": history["refus"], "historique_repli_horaire": history["repli_horaire"],
    })
    if len(history["t"]) and terminal is None:
        info["sim"]["ecart_hist_vs_milieu_cents"] = abs(float(history["p"][-1]) - info["milieu"]) * 100
    if trade_sink is not None and len(trades["t"]):
        for i in range(len(trades["t"])):
            trade_sink.writerow([info["condition_id"], int(trades["t"][i]), round(float(trades["p0"][i]), 5),
                                 round(float(trades["p_traded"][i]), 5), round(float(trades["size"][i]), 4), int(trades["dir"][i])])


def fetch_closed_control(http: Http, args, now_ts: float, trade_sink, rng) -> tuple[list[dict], dict]:
    """Témoin de marchés déjà résolus, pour mesurer en partie le biais de survivance."""
    min_end = dt.datetime.fromtimestamp(now_ts - args.closed_days * 86400, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pool, sources = {}, collections.defaultdict(set)
    for cat_slugs in CATEGORIES.values():
        for slug in cat_slugs[:4]:
            tag = http.get(f"{GAMMA}/tags/slug/{slug}", quiet_statuses=(404,))
            if not tag:
                continue
            for page in range(3):
                rows = http.get(f"{GAMMA}/markets", params={
                    "closed": "true", "limit": 100, "offset": page * 100, "tag_id": tag["id"], "order": "volumeNum",
                    "ascending": "false", "include_tag": "true", "end_date_min": min_end})
                if not rows:
                    break
                for market in rows:
                    pool[market.get("conditionId")] = market
                    sources[market.get("conditionId")].add(slug)
                if len(rows) < 100:
                    break
    selected, rejected, per_event = [], collections.Counter(), collections.Counter()
    ordered = sorted(pool.values(), key=lambda m: -(float(m.get("volumeNum") or 0)))
    for market in ordered:
        cid = market.get("conditionId")
        category, categories = classify(market, sources[cid])
        tags = market_tags(market)
        if any(slug in tags for slug in EXCLUDE_TAGS) or any(p.search(market.get("question") or "") for p, _ in EXCLUDE_RE):
            rejected["hors perimetre"] += 1
            continue
        prices = [float(x) for x in load_json_field(market.get("outcomePrices"), [])]
        if len(prices) != 2 or not (max(prices) == 1.0 and min(prices) == 0.0):
            rejected["resolution non binaire ou non finale"] += 1
            continue
        closed_ts = parse_ts(market.get("closedTime")) or parse_ts(market.get("endDate"))
        tokens = load_json_field(market.get("clobTokenIds"), [])
        if closed_ts is None or len(tokens) != 2 or closed_ts < now_ts - args.closed_days * 86400:
            rejected["date ou jetons absents, ou cloture trop ancienne"] += 1
            continue
        event_key = market.get("negRiskMarketID") or ((market.get("events") or [{}])[0].get("id")) or cid
        if per_event[event_key] >= 3:
            rejected["plafond de 3 marches par evenement"] += 1
            continue
        per_event[event_key] += 1
        metrics = {"milieu": 0.5, "meilleur_bid": None, "meilleur_ask": None}
        fees = fee_params(market)
        selected.append({
            "question": market.get("question"), "condition_id": cid, "categorie": category, "mi_mandat": is_midterm(market),
            "token0": tokens[0], "token1": tokens[1], "groupe_evenement": event_key, "date_cloture": iso(closed_ts),
            "resultat_final_jeton0": prices[0], "volume_total_usd": market.get("volumeNum"), "_closed_ts": closed_ts, **metrics, **fees,
        })
        if len(selected) >= args.closed_control:
            break
    for info in selected:
        print(f"  temoin {short(info['question'], 50)}", flush=True)
        run_simulation(http, info, args, rng, now_ts, start=info["_closed_ts"] - args.window_days * 86400,
                       end=info["_closed_ts"], terminal=info["resultat_final_jeton0"], doc=DOC_FEES.get(info["categorie"]), trade_sink=trade_sink)
    return selected, {"candidats_lus": len(pool), "ecartes": dict(rejected), "selectionnes": len(selected), "date_min": min_end}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--supplement", type=int, default=5, help="marchés témoins par catégorie hors du classement principal")
    parser.add_argument("--window-days", type=float, default=14)
    parser.add_argument("--max-trades", type=int, default=8000)
    parser.add_argument("--fidelity", type=int, default=1, help="minutes par point de prices-history")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--closed-control", type=int, default=15)
    parser.add_argument("--closed-days", type=int, default=30)
    parser.add_argument("--mid-min", type=float, default=0.03, help="milieu minimal retenu au classement (symétrique vers 1)")
    parser.add_argument("--ws", action="store_true")
    parser.add_argument("--ws-seconds", type=int, default=180)
    parser.add_argument("--outdir", default=str(pathlib.Path(__file__).resolve().parent / "resultats"))
    args = parser.parse_args()

    started = utcnow()
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    now_ts = started.timestamp()
    out_dir = pathlib.Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    http = Http()

    server_time = http.get(f"{CLOB}/time")
    print(f"[{iso(time.time())}] relecture du barème publié", flush=True)
    docs = check_docs(http)

    print(f"[{iso(time.time())}] candidats Gamma", flush=True)
    pool, meta = fetch_candidates(http)
    if not pool:
        print("Aucun candidat : Gamma indisponible.", file=sys.stderr)
        return 2

    excluded, kept = [], []
    for cid, market in pool.items():
        category, categories = classify(market, meta["sources"][cid])
        reason = exclusion_reason(market, now_ts)
        if reason:
            excluded.append({"condition_id": cid, "question": market.get("question"), "categorie_visee": category, "raison": reason,
                             "liquidite_gamma_usd": market.get("liquidityNum"), "volume_24h_usd": market.get("volume24hr"),
                             "etiquettes": sorted(market_tags(market))})
            continue
        kept.append((market, category, categories))

    print(f"[{iso(time.time())}] carnets de {len(kept)} marchés", flush=True)
    tokens = [load_json_field(m.get("clobTokenIds"), [])[0] for m, _, _ in kept]
    books = fetch_books(http, tokens)
    ranked = []
    for market, category, categories in kept:
        token = load_json_field(market.get("clobTokenIds"), [])[0]
        book = books.get(str(token))
        metrics = book_metrics(book) if book else None
        if metrics is None:
            excluded.append({"condition_id": market.get("conditionId"), "question": market.get("question"), "categorie_visee": category,
                             "raison": "carnet absent, vide ou croise", "liquidite_gamma_usd": market.get("liquidityNum"),
                             "volume_24h_usd": market.get("volume24hr"), "etiquettes": sorted(market_tags(market))})
            continue
        if not args.mid_min <= metrics["milieu"] <= 1 - args.mid_min:
            excluded.append({"condition_id": market.get("conditionId"), "question": market.get("question"), "categorie_visee": category,
                             "raison": f"prix extreme (milieu hors de {args.mid_min:g} a {1 - args.mid_min:g})", "liquidite_gamma_usd": market.get("liquidityNum"),
                             "volume_24h_usd": market.get("volume24hr"), "etiquettes": sorted(market_tags(market))})
            continue
        ranked.append(build_market_info(market, category, categories, metrics))
    ranked.sort(key=lambda r: (-r["score_liquidite_usd"], -(r["volume_24h_usd"] or 0)))
    for i, row in enumerate(ranked, 1):
        row["rang"] = i
    # Une mesure nulle ne classe rien : ces marchés restent sans rang relatif.
    for row in ranked:
        row["rang_rel_1pct"] = None
    for i, row in enumerate(sorted((r for r in ranked if r["score_rel_1pct_usd"] > 0), key=lambda r: -r["score_rel_1pct_usd"]), 1):
        row["rang_rel_1pct"] = i
    top = ranked[:args.top]
    for row in top:
        row["echantillon"] = "top"
    rest = ranked[args.top:]
    supplement = []
    for label, test in (("macroeconomie", lambda r: r["categorie"] == "macroeconomie"),
                        ("technologie", lambda r: r["categorie"] == "technologie"),
                        ("politique hors mi-mandat", lambda r: r["categorie"] == "politique" and not r["mi_mandat"]),
                        ("frais actifs", lambda r: r["fee_rate"] > 0)):
        picked = [r for r in rest if test(r) and "echantillon" not in r][:args.supplement]
        for row in picked:
            row["echantillon"] = f"supplement {label}"
        supplement += picked

    print(f"[{iso(time.time())}] contrôles frais et miroir sur {len(top) + len(supplement)} marchés", flush=True)
    for row in top + supplement:
        clob_info = http.get(f"{CLOB}/clob-markets/{row['condition_id']}", quiet_statuses=(404,)) or {}
        fd = clob_info.get("fd") or {}
        row["clob_fd_rate"] = fd.get("r")
        row["clob_fd_exposant"] = fd.get("e")
        row["clob_fd_taker_only"] = fd.get("to")
        row["clob_fd_coherent"] = (float(fd.get("r")) == row["fee_rate"]) if fd.get("r") is not None else None
        row["clob_maker_base_fee"] = clob_info.get("mbf")
        row["clob_taker_base_fee"] = clob_info.get("tbf")
        fee_rate = http.get(f"{CLOB}/fee-rate", params={"token_id": row["token0"]}, quiet_statuses=(404, 400)) or {}
        row["fee_rate_base_fee"] = fee_rate.get("base_fee")
        other = http.get(f"{CLOB}/book", params={"token_id": row["token1"]}, quiet_statuses=(404,))
        other_metrics = book_metrics(other) if other else None
        if other_metrics:
            row["miroir_ecart_cents"] = round(abs(other_metrics["meilleur_bid"] - (1 - row["meilleur_ask"])) * 100 +
                                              abs(other_metrics["meilleur_ask"] - (1 - row["meilleur_bid"])) * 100, 4)
            if row["jeton_ref_1pct"] == 1:
                direct = rel_depth(other_metrics["_bids"], other_metrics["_asks"])
                row["miroir_1pct_ecart_usd"] = abs(direct["bid_usd"] - row["bid_usd_1pct"]) + abs(direct["ask_usd"] - row["ask_usd_1pct"])
        else:
            row["miroir_ecart_cents"] = None

    ws_summary = None
    if args.ws:
        print(f"[{iso(time.time())}] WebSocket public, {args.ws_seconds} s", flush=True)
        token_map = {}
        for r in top:
            token_map[r["token0"]] = {"question": r["question"], "jeton0": True}
            token_map[r["token1"]] = {"question": r["question"], "jeton0": False}
        events_path = out_dir / f"{stamp}_ws_evenements.jsonl.gz"
        try:
            ws_summary = asyncio.run(ws_capture(token_map, args.ws_seconds, events_path))
            ws_summary["fichier"] = events_path.name
        except Exception as exc:
            ws_summary = {"echec": f"{type(exc).__name__}: {exc}"[:300]}

    trades_path = out_dir / f"{stamp}_trades_normalises.csv.gz"
    with gzip.open(trades_path, "wt", newline="", encoding="utf-8") as handle:
        sink = csv.writer(handle)
        sink.writerow(["condition_id", "ts", "prix_jeton0", "prix_trade", "taille_parts", "sens_maker_jeton0"])
        print(f"[{iso(time.time())}] simulateur sur {len(top) + len(supplement)} marchés", flush=True)
        for row in top + supplement:
            print(f"  {row.get('rang')} {short(row['question'], 60)}", flush=True)
            run_simulation(http, row, args, rng, now_ts, doc=DOC_FEES.get(row["categorie"]), trade_sink=sink)
        print(f"[{iso(time.time())}] témoin de marchés résolus", flush=True)
        closed, closed_meta = fetch_closed_control(http, args, now_ts, sink, rng) if args.closed_control else ([], {})

    groups = {
        "top": top,
        "top mi-mandat": [r for r in top if r["mi_mandat"]],
        "top hors mi-mandat": [r for r in top if not r["mi_mandat"]],
        "supplement macroeconomie": [r for r in supplement if r["echantillon"] == "supplement macroeconomie"],
        "supplement technologie": [r for r in supplement if r["echantillon"] == "supplement technologie"],
        "supplement politique hors mi-mandat": [r for r in supplement if r["echantillon"] == "supplement politique hors mi-mandat"],
        "supplement frais actifs": [r for r in supplement if r["echantillon"] == "supplement frais actifs"],
        "tous hors mi-mandat": [r for r in top + supplement if not r["mi_mandat"]],
        "temoin resolus": closed,
    }
    aggregates = {name: aggregate(items, args.bootstrap, rng) for name, items in groups.items() if items}

    finished = utcnow()
    prefix = out_dir / stamp
    columns_market = ["rang", "rang_rel_1pct", "echantillon", "question", "categorie", "categories_toutes", "mi_mandat", "evenement", "date_fin", "date_creation",
                      "meilleur_bid", "meilleur_ask", "ecart_cents", "milieu", "jeton_ref_1pct", "bid_parts_1pct", "bid_usd_1pct", "ask_parts_1pct", "ask_usd_1pct",
                      "bid_parts_1c", "bid_usd_1c", "ask_parts_1c", "ask_usd_1c", "score_liquidite_usd", "score_rel_1pct_usd", "volume_24h_usd",
                      "liquidite_gamma_usd", "pas_prix", "taille_min", "carnet_ts_ms", "feesEnabled", "feeType", "fee_rate", "fee_exponent", "fee_taker_only",
                      "rebate_rate", "clob_fd_rate", "clob_fd_coherent", "fee_rate_base_fee", "clob_maker_base_fee", "clob_taker_base_fee",
                      "rebate_1000_milieu", "rebate_1000_bareme_doc", "frais_taker_cents_par_part", "recompense_jour_usd", "recompense_taille_min",
                      "recompense_ecart_max_cents", "recompense_estimee_1000usd_jour", "holding_rewards", "restricted", "neg_risk",
                      "miroir_ecart_cents", "miroir_1pct_ecart_usd", "condition_id", "token0", "token1", "etiquettes"]
    write_csv(pathlib.Path(f"{prefix}_marches.csv"), top + supplement, columns_market)
    write_csv(pathlib.Path(f"{prefix}_candidats_classes.csv"), ranked, [c for c in columns_market if c not in ("clob_fd_rate", "clob_fd_coherent", "fee_rate_base_fee", "clob_maker_base_fee", "clob_taker_base_fee", "miroir_ecart_cents", "miroir_1pct_ecart_usd", "token0", "token1")])
    write_csv(pathlib.Path(f"{prefix}_ecartes.csv"), excluded)

    sim_rows = []
    for row in top + supplement + closed:
        sim = row.get("sim") or {}
        for horizon, stats in (sim.get("horizons") or {}).items():
            sim_rows.append({"echantillon": row.get("echantillon", "temoin resolu"), "rang": row.get("rang"), "question": row["question"], "categorie": row["categorie"],
                             "mi_mandat": row["mi_mandat"], "horizon": horizon, "feeType": row.get("feeType"), **stats,
                             "valeur_finale": sim.get("valeur_finale"), "premier_trade": sim.get("premier_trade"), "dernier_trade": sim.get("dernier_trade"),
                             "trades_tronques": sim.get("trades_tronques"), "demi_ecart_effectif_cents": sim.get("demi_ecart_effectif_cents"),
                             **(sim.get("cloture") or {}), "condition_id": row["condition_id"]})
    write_csv(pathlib.Path(f"{prefix}_simulateur_par_marche.csv"), sim_rows)
    agg_rows = [{"groupe": name, "horizon": horizon, **stats} for name, data in aggregates.items() for horizon, stats in data.items()]
    write_csv(pathlib.Path(f"{prefix}_simulateur_agrege.csv"), agg_rows)

    payload = {
        "genere_utc": iso(finished.timestamp()), "debut_utc": iso(now_ts), "heure_serveur_clob": server_time,
        "parametres": vars(args), "docs_frais": docs, "bareme_doc_scenario": DOC_FEES,
        "filtre": {"categories": CATEGORIES, "exclusions_etiquettes": EXCLUDE_TAGS, "exclusions_intitules": [p.pattern for p, _ in EXCLUDE_RE], "tags": meta["tags"],
                   "mi_mandat": {"etiquettes": MIDTERM_TAG_RE.pattern, "intitules": MIDTERM_Q_RE.pattern, "annee": MIDTERM_YEAR, "fin_max": iso(MIDTERM_END_MAX),
                                 "meme_jour_etiquettes": sorted(SAME_DAY_US_TAGS), "meme_jour_fin": [iso(SAME_DAY_START), iso(SAME_DAY_END)]}},
        "comptes": {"candidats": len(pool), "ecartes": len(excluded), "classes": len(ranked),
                    "candidats_avec_category": sum(1 for m in pool.values() if m.get("category")),
                    "classes_plusieurs_categories": sum(1 for r in ranked if len(r["categories_toutes"]) > 1)},
        "recensement_frais_candidats": census_fees(ranked),
        "top": top, "supplement": supplement, "temoin_resolus": closed, "temoin_meta": closed_meta,
        "agregats": aggregates, "websocket": ws_summary, "appels_http": dict(http.calls), "incidents": http.incidents,
    }
    with open(f"{prefix}_complet.json", "w", encoding="utf-8") as handle:
        json.dump(strip_private(payload), handle, ensure_ascii=False, indent=1, default=str)

    write_report(pathlib.Path(f"{prefix}_rapport.md"), payload, excluded, ranked, top, supplement, closed, closed_meta, aggregates, ws_summary, http, args, stamp)
    print(f"[{iso(time.time())}] terminé, préfixe {prefix}", flush=True)
    return 0


def counter_text(counter) -> str:
    return ", ".join(f"{key} {value}" for key, value in counter.items()) or "aucun"


def sign_of(stats: dict, name: str) -> str:
    low, high = stats.get(f"{name}_ic_bas"), stats.get(f"{name}_ic_haut")
    if low is None or high is None:
        return "sans intervalle"
    if stats.get("n_evenements", 99) < 5 or stats.get("n_blocs", 99) < 5:
        return "indicatif car trop peu de groupes"
    if low > 0:
        return "positif, hypothétique"
    if high < 0:
        return "négatif, hypothétique"
    return "indéterminé, zéro dans l'intervalle"


def ic_flag(stats: dict, name: str, digits=2) -> str:
    text = ic(stats, name, digits)
    few = stats.get("n_evenements", 99) < 5 or stats.get("n_blocs", 99) < 5
    return text + "*" if few and text != "n.d." else text


def jour(ts: float | None) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%d/%m/%Y") if ts is not None else "n.d."


def creation_range(rows: list[dict]) -> tuple[str, str]:
    stamps = [t for t in (parse_ts(r.get("date_creation")) for r in rows) if t is not None]
    return (jour(min(stamps)), jour(max(stamps))) if stamps else ("n.d.", "n.d.")


def creation_median(rows: list[dict]) -> str:
    stamps = [t for t in (parse_ts(r.get("date_creation")) for r in rows) if t is not None]
    return jour(float(np.median(stamps))) if stamps else "n.d."


def write_report(path, payload, excluded, ranked, top, supplement, closed, closed_meta, aggregates, ws, http, args, stamp) -> None:
    lines: list[str] = []
    add = lines.append
    generated = payload["genere_utc"]
    add(f"# Collecte CLOB Polymarket et simulateur d'antisélection, {generated}")
    add("")
    add(f"Résultat de recherche sans ordre ni clé. Collecte de {payload['debut_utc']} à {generated} (UTC) sur les points d'accès publics de Polymarket.")
    add("")
    add("## Alerte de contexte")
    add("")
    add("Le mi-mandat américain a lieu le 03/11/2026 et ces mesures sont prises juste avant le scrutin. "
        "Les marchés politiques sont atypiques en ce moment et des résolutions en masse approchent. "
        "Ces chiffres ne sont donc pas représentatifs d'une période ordinaire et ils ne se transposent pas à un autre régime.")
    add("")

    census = payload["recensement_frais_candidats"]
    total = sum(c["n_marches"] for c in census)
    zero = sum(c["n_marches"] for c in census if not c["rate"])
    top_zero = sum(1 for r in top if not r["fee_rate"])
    max_rebate = max((r["rebate_1000_milieu"] for r in top), default=0)
    cats = collections.Counter(r["categorie"] for r in top)
    mid_count = sum(1 for r in top if r["mi_mandat"])

    add("## Résumé")
    add("")
    add(f"Sur les {len(top)} marchés du classement, {mid_count} sont liés au mi-mandat et {top_zero} ont un taux de frais nul d'après l'API. "
        f"Le rebate API le plus élevé du classement vaut {fmt(max_rebate)} $ pour 1 000 $ exécutés.")
    active_rewards = [r["recompense_jour_usd"] for r in top if r.get("recompense_jour_usd")]
    if active_rewards:
        add(f"{len(active_rewards)} marchés du classement portent une récompense de liquidité publiée, de {fmt(min(active_rewards), 0)} à {fmt(max(active_rewards), 0)} $ par jour pour tout le marché. "
            "Sur ces marchés à frais nuls la récompense est donc la principale rémunération publiée du maker hors rendement de détention sur certains marchés.")
    add("")
    add("| Groupe | Horizon | Trades | Événements | Moy. ¢/part | IC 95 % | Pondéré taille ¢/part | IC 95 % | Rebate API $/1 000 | Net $/1 000 | IC 95 % | Lecture du net |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name in ("top", "tous hors mi-mandat", "supplement frais actifs", "temoin resolus"):
        for horizon, stats in (aggregates.get(name) or {}).items():
            if stats.get("n"):
                add(f"| {name} | {horizon} | {stats['n']} | {stats['n_evenements']} | {fmt(stats['moy_cents'], 3)} | {ic_flag(stats, 'moy_cents', 3)} | {fmt(stats['vw_cents'], 3)} | {ic_flag(stats, 'vw_cents', 3)} | {fmt(stats['rebate_1000'], 2)} | {fmt(stats['net_1000'], 2)} | {ic_flag(stats, 'net_1000', 2)} | {sign_of(stats, 'net_1000')} |")
    add("")
    add("Un astérisque signale un intervalle calculé sur moins de cinq groupes, donc seulement indicatif. "
        "Ce résumé ne mesure pas un gain atteignable car le simulateur suppose un remplissage sur chaque trade public. "
        "Un markout positif à 1 h vient surtout du demi-écart supposé capté et il peut disparaître si nos ordres ne sont remplis que dans les mauvais cas. "
        "La mesure en dollars dépend du prix du jeton traité et elle pèse lourd sur les prix bas, donc la lecture en ¢ par part reste la référence.")
    add("")
    fee_group = [r for r in supplement if r["echantillon"] == "supplement frais actifs"]
    if fee_group:
        low, high = creation_range(fee_group)
        add(f"Le groupe « supplement frais actifs » n'est pas un témoin du rebate. Ses {len(fee_group)} marchés ont été créés du {low} au {high} et ils sont peu traités. "
            "Il mesure donc des marchés très récents et il ne sépare pas un effet des frais d'un effet d'âge.")
        add("")

    add("## Frais et rebates vérifiés")
    add("")
    add("La documentation officielle a été relue le 31/10/2026 sur les pages fees et maker-rebates de docs.polymarket.com. "
        f"Le script a relu le barème à {payload['docs_frais'].get('lu_a')} avec le statut HTTP {payload['docs_frais'].get('statut_http')}.")
    add("")
    add("| Élément | Note de régime du 31/10 | Documentation officielle | Champs API par marché |")
    add("|---|---|---|---|")
    add("| Formule taker | parts × taux × p × (1 − p) | C × feeRate × p × (1 − p) | feeSchedule rate et exponent |")
    add("| Plafond à 50 ¢ | 1 à 1,75 ¢ par part | 1 à 1,75 ¢ selon la catégorie (0,04 à 0,07) | nul sur la plupart des marchés classés |")
    add("| Maker | 0 avec rebates de 15 à 25 % | 0 avec rebates de 15 à 25 % selon la catégorie | rebateRate par marché et nul si le taux est nul |")
    add(f"| Marchés sans frais | géopolitique | géopolitique, avec Politics listé à 0,04 | {zero} marchés classés sur {total} ont un taux nul dans les trois catégories |")
    add("")
    add(f"La note et la documentation concordent entre elles mais elles ne décrivent pas ce que renvoie l'API aujourd'hui. "
        f"Sur {total} marchés classés, {zero} ont un taux de frais nul dans feeSchedule. "
        "La documentation précise qu'un marché à frais nuls ne génère aucun rebate. "
        "Nous n'avons pas trouvé de texte officiel qui explique cet écart et sa cause reste [non vérifiée]. "
        "La ligne de frais de la note de régime demande donc une correction, car le potentiel de rebate se lit marché par marché.")
    add("")
    selected = top + supplement
    sel_on = [r for r in selected if r["fee_rate"] > 0]
    sel_off = [r for r in selected if not r["fee_rate"]]
    all_on = [r for r in ranked if r["fee_rate"] > 0]
    all_off = [r for r in ranked if not r["fee_rate"]]
    recent_limit = parse_ts(payload["debut_utc"]) - 3 * 86400
    recent = [r for r in ranked if (parse_ts(r.get("date_creation")) or 0) >= recent_limit]
    add(f"Nos propres données donnent un indice de date qui ne prouve rien. Sur les {len(selected)} marchés retenus, les {len(sel_on)} à frais actifs ont été créés du {creation_range(sel_on)[0]} au {creation_range(sel_on)[1]} "
        f"et les {len(sel_off)} à frais nuls du {creation_range(sel_off)[0]} au {creation_range(sel_off)[1]}. "
        f"Sur tous les marchés classés, la création médiane tombe le {creation_median(all_on)} pour les {len(all_on)} à frais actifs (du {creation_range(all_on)[0]} au {creation_range(all_on)[1]}) "
        f"et le {creation_median(all_off)} pour les {len(all_off)} à frais nuls. "
        f"Le lien n'est pas exclusif car, parmi les {len(recent)} marchés classés créés moins de 3 jours avant la collecte, {sum(1 for r in recent if not r['fee_rate'])} ont un taux nul. "
        "C'est une corrélation et non une cause établie.")
    add("")
    add("| Catégorie | feeType | feesEnabled | rate | rebateRate | Marchés classés |")
    add("|---|---|---|---|---|---|")
    for row in census:
        add(f"| {row['categorie']} | {row['feeType']} | {row['feesEnabled']} | {fmt(row['rate'], 2)} | {fmt(row['rebateRate'], 2)} | {row['n_marches']} |")
    add("")
    base = collections.Counter(str(r.get("fee_rate_base_fee")) for r in top)
    coherent = sum(1 for r in top if r.get("clob_fd_coherent") is True)
    ws_fee = collections.Counter()
    for cell in ((ws or {}).get("par_marche") or {}).values():
        ws_fee.update(cell.get("fee_rate_bps") or {})
    if ws_fee:
        add(f"Les trades captés par WebSocket sur le classement portent fee_rate_bps avec les valeurs {counter_text(ws_fee)} (valeur et nombre de trades). "
            "Ce petit échantillon va dans le sens des champs API sans le prouver.")
        add("")
    add(f"Sur le classement, le champ fd de /clob-markets concorde avec feeSchedule pour {coherent} marchés sur {len(top)}. "
        f"Le champ base_fee de /fee-rate donne {counter_text(base)} (valeur et nombre de marchés) et ne concorde pas avec un taux nul. "
        "La documentation le décrit en points de base sans dire qu'il est facturé et le journal des changements demande de calculer les frais avec feeSchedule. "
        "Nous l'ignorons donc dans le calcul et nous le signalons comme ambigu.")
    add("")

    add("## Méthode de filtrage par catégorie")
    add("")
    add("Le filtre repose sur les étiquettes éditoriales de Gamma (paramètre tag_id), lues par liquidité déclarée puis par volume sur 24 h. "
        "L'affectation suit l'ordre macroéconomie puis technologie puis politique quand un marché porte plusieurs étiquettes. "
        f"Le champ category est renseigné sur {payload['comptes']['candidats_avec_category']} candidats sur {payload['comptes']['candidats']} et feeType vaut zero_fees sur la plupart des marchés, donc aucun des deux ne permet de classer.")
    add("")
    add("| Catégorie | Étiquettes utilisées |")
    add("|---|---|")
    for cat, slugs in CATEGORIES.items():
        add(f"| {cat} | {' '.join(slugs)} |")
    add("")
    examples = [r for r in ranked if re.search(r"JetBlue|aliens exist", r["question"] or "")][:2]
    add("Ce filtre peut se tromper de plusieurs façons. "
        f"Les étiquettes sont posées à la main et {payload['comptes']['classes_plusieurs_categories']} marchés classés relèvent de plusieurs catégories. "
        + ("Nous avons relevé des étiquettes discutables comme " + " et ".join(f"« {short(e['question'], 60)} » ({e['categorie']})" for e in examples) + ". " if examples else "")
        + "Un marché géopolitique peut être politique par nature et il sort ici dès qu'il porte l'étiquette geopolitics. "
        "L'exclusion par intitulé repose sur des expressions régulières qui peuvent se tromper dans les deux sens. "
        "Le plafond de pages de Gamma (offset limité) peut enfin laisser de côté un marché peu visible mais bien coté.")
    add("")
    add("Les marchés de comptage sortent par l'étiquette tweets-markets ou par un intitulé du type « post … tweets » ou « post … posts ». "
        f"L'étiquette mi-mandat vise le scrutin du 03/11/{MIDTERM_YEAR}. Un intitulé qui cite une autre année ou une date de fin après le {jour(MIDTERM_END_MAX)} la retire, même avec une étiquette senate-elections. "
        f"Elle couvre aussi les scrutins américains locaux du même jour (comté, mairie) dont l'intitulé cite {MIDTERM_YEAR} et dont la fin Gamma tombe du {jour(SAME_DAY_START)} au 05/11/{MIDTERM_YEAR}. "
        f"Elle vaut vrai sur {sum(1 for r in ranked if r['mi_mandat'])} marchés classés. Elle reste large car elle suit les étiquettes Gamma, et elle garde des marchés voisins du scrutin comme « Fetterman out by December 31, 2026? » ou « Will Vivek Ramaswamy pull the Amy Acton mother ad? ». Un marché retenu ou écarté par ces filtres ne constitue pas une recommandation d'investissement.")
    add("")
    reasons = collections.Counter(re.sub(r"^etiquette ", "", e["raison"]) for e in excluded)
    add(f"Nous avons lu {payload['comptes']['candidats']} candidats. Nous en avons classé {payload['comptes']['classes']} et écarté {payload['comptes']['ecartes']}. Le détail est dans {stamp}_ecartes.csv.")
    add("")
    add("| Raison de l'écart | Marchés |")
    add("|---|---|")
    for reason, count in reasons.most_common():
        add(f"| {reason} | {count} |")
    add("")

    add(f"## Classement des {len(top)} marchés par liquidité réelle du carnet")
    add("")
    add("Le classement utilise la profondeur à ±1 ¢ du milieu, valorisée au coût du jeton le moins cher à chaque niveau, en retenant le côté le plus faible. "
        "Cette mesure ne dépend pas du choix entre Yes et No et elle ne gonfle pas les marchés proches de 0 ou de 1. "
        f"Les marchés dont le milieu sort de {args.mid_min:g} à {1 - args.mid_min:g} sont écartés car ±1 ¢ y représente un écart relatif sans rapport avec le reste. "
        "La profondeur à ±1 % relatif demandée figure aussi au tableau, en parts et en dollars du jeton le moins cher, car elle dépend sinon du jeton lu. La colonne Jeton 1 % indique ce jeton, et les côtés Bid et Ask de ces colonnes sont les siens. "
        f"Elle vaut 0 sur {sum(1 for r in top if not r['score_rel_1pct_usd'])} marchés du classement sur {len(top)} et sur {sum(1 for r in ranked if not r['score_rel_1pct_usd'])} marchés classés sur {len(ranked)}. "
        "Avec un écart de 1 ¢ le meilleur prix se trouve à 0,5 ¢ du milieu, et cela dépasse 1 % du prix dès que le jeton le moins cher vaut moins de 50 ¢. Le carnet peut donc être bien garni avec une mesure nulle, et la colonne ±1 ¢ reste la lecture principale. "
        "Le rang selon la mesure relative est dans le CSV (rang_rel_1pct) et il n'existe que pour une mesure positive.")
    add("")
    add("| # | Marché | Cat. | Mi-mandat | Bid | Ask | Écart ¢ | Milieu | Jeton 1 % | Bid 1 % parts | Bid 1 % $ | Ask 1 % parts | Ask 1 % $ | Bid 1 ¢ $ | Ask 1 ¢ $ | Score $ | Fin | Vol. 24 h $ |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in top:
        add(f"| {r['rang']} | {short(r['question'])} | {r['categorie'][:5]} | {'oui' if r['mi_mandat'] else 'non'} | {fmt(r['meilleur_bid'], 3)} | {fmt(r['meilleur_ask'], 3)} | {fmt(r['ecart_cents'], 2)} | {fmt(r['milieu'], 4)} | {r['jeton_ref_1pct']} | "
            f"{fmt(r['bid_parts_1pct'], 0)} | {fmt(r['bid_usd_1pct'], 0)} | {fmt(r['ask_parts_1pct'], 0)} | {fmt(r['ask_usd_1pct'], 0)} | {fmt(r['bid_usd_1c'], 0)} | {fmt(r['ask_usd_1c'], 0)} | {fmt(r['score_liquidite_usd'], 0)} | {(r['date_fin'] or '')[:10]} | {fmt(r['volume_24h_usd'], 0)} |")
    add("")
    thin = sum(1 for r in top if (r["volume_24h_usd"] or 0) < 1000)
    add(f"Ce classement mesure la profondeur posée et pas le flux. {thin} marchés du classement traitent moins de 1 000 $ sur 24 h et leur carnet tient sans doute en partie aux récompenses de liquidité [hypothèse].")
    add(f"Répartition du classement par catégorie {counter_text(cats)}. Carnets lus entre {iso(min(r['carnet_ts_ms'] for r in top) / 1000)} et {iso(max(r['carnet_ts_ms'] for r in top) / 1000)}.")
    mirror = [r.get("miroir_ecart_cents") for r in top if r.get("miroir_ecart_cents") is not None]
    add(f"Le contrôle de miroir compare les meilleurs prix du jeton 1 au complément du jeton 0. L'écart cumulé moyen vaut {fmt(float(np.mean(mirror)) if mirror else None, 3)} ¢ sur {len(mirror)} marchés et il justifie de lire le seul jeton 0.")
    mirror_rows = [r for r in top + supplement if r.get("miroir_1pct_ecart_usd") is not None]
    if mirror_rows:
        filled = [r["miroir_1pct_ecart_usd"] for r in mirror_rows if r["bid_usd_1pct"] + r["ask_usd_1pct"] > 0]
        add(f"La bande à 1 % déduite du jeton 0 a été comparée au carnet lu du jeton 1 sur {len(mirror_rows)} marchés, dont {len(filled)} à mesure non nulle. "
            + (f"Sur ceux-ci l'écart absolu moyen vaut {fmt(float(np.mean(filled)), 2)} $ et le maximum {fmt(float(np.max(filled)), 2)} $, avec des carnets lus à quelques secondes d'écart." if filled
               else "Ce contrôle ne teste donc rien dans cette exécution, et seul le miroir des meilleurs prix soutient la déduction."))
    add("")
    if supplement:
        add("## Supplément hors classement")
        add("")
        add("Ces marchés servent de témoins car le classement est dominé par le mi-mandat. Ils ne font pas partie des 20.")
        add("")
        add("| Rang global | Marché | Échantillon | Bid | Ask | Écart ¢ | Jeton 1 % | Bid 1 % $ | Ask 1 % $ | Bid 1 ¢ $ | Ask 1 ¢ $ | Score $ | Fin | Vol. 24 h $ |")
        add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in supplement:
            add(f"| {r['rang']} | {short(r['question'])} | {r['echantillon'].replace('supplement ', '')} | {fmt(r['meilleur_bid'], 3)} | {fmt(r['meilleur_ask'], 3)} | {fmt(r['ecart_cents'], 2)} | {r['jeton_ref_1pct']} | {fmt(r['bid_usd_1pct'], 0)} | {fmt(r['ask_usd_1pct'], 0)} | {fmt(r['bid_usd_1c'], 0)} | {fmt(r['ask_usd_1c'], 0)} | {fmt(r['score_liquidite_usd'], 0)} | {(r['date_fin'] or '')[:10]} | {fmt(r['volume_24h_usd'], 0)} |")
        add("")

    add("## Potentiel de capture des frais maker")
    add("")
    add("Le rebate théorique pour 1 000 $ exécutés au prix p vaut (1 000 / p) × rate × (p(1 − p))^exponent × rebateRate, et c'est une borne haute. "
        "Elle suppose que le pool du marché vaut exactement rebateRate fois les frais taker et que le seuil de versement de 1 pUSD est franchi. "
        "Polymarket garde la main sur le pourcentage. "
        "La colonne barème doc applique le tableau publié comme simple scénario et elle ne correspond pas aux champs actuels quand le taux API est nul.")
    add("")
    add("Les récompenses de liquidité viennent du champ public clobRewards. "
        "Le montant estimé suppose 1 000 $ de capital posés à moitié au meilleur bid et à moitié au meilleur ask, en permanence et sans jamais être rempli, face au carnet actuel. "
        "Il reprend la formule publiée sans les participants individuels ni la coupure de taille, donc c'est une borne haute [estimation] par jour et par capital posé, pas par dollar exécuté.")
    add("")
    add("| # | Marché | feeType | rate | rebateRate | Rebate API $/1 000 | Rebate barème doc $/1 000 | Récompense $/jour | Écart max ¢ | Taille min | Estimée $/jour pour 1 000 $ posés |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in top + supplement:
        add(f"| {r['rang']} | {short(r['question'], 48)} | {r['feeType']} | {fmt(r['fee_rate'], 2)} | {fmt(r['rebate_rate'], 2)} | {fmt(r['rebate_1000_milieu'], 2)} | {fmt(r['rebate_1000_bareme_doc'], 2)} | {fmt(r['recompense_jour_usd'], 0)} | {fmt(r['recompense_ecart_max_cents'], 1)} | {fmt(r['recompense_taille_min'], 0)} | {fmt(r['recompense_estimee_1000usd_jour'], 2)} |")
    add("")

    add("## Simulateur d'antisélection")
    add("")
    add(f"Pour chaque trade taker public de la fenêtre ({args.window_days:g} jours au plus), un maker hypothétique est rempli du côté opposé au prix du trade. "
        "Les trades sont ramenés au jeton 0, donc acheter le jeton 1 à q revient à vendre le jeton 0 à 1 − q. "
        "Le markout vaut sens × (prix à t + h − prix d'exécution) avec le prix de /prices-history. "
        "Le coût d'antisélection est l'opposé du markout moyen, donc un coût positif est une perte du maker. "
        "Ce markout contient le demi-écart gagné à l'exécution et le tableau agrégé le sépare du mouvement du prix contre le maker. "
        "Les trades dont l'horizon dépasse l'historique disponible sont retirés (censure), ce qui exclut les trades récents des horizons longs.")
    add("")
    sim_rows_all = [r for r in top + supplement if (r.get("sim") or {}).get("n_trades_bruts")]
    biggest = max(sim_rows_all, key=lambda r: r["sim"]["n_trades_bruts"]) if sim_rows_all else None
    cut = [r for r in sim_rows_all if r["sim"].get("trades_tronques")]
    span = lambda r: (parse_ts(r["sim"]["dernier_trade"]) - parse_ts(r["sim"]["premier_trade"])) / 86400
    add(f"La lecture des trades s'arrête quand {args.max_trades} trades sont lus. Ce contrôle se fait après chaque page de 1 000 lignes, donc un marché peut en garder jusqu'à {args.max_trades + 999}. "
        + (f"Dans cette exécution le maximum vaut {biggest['sim']['n_trades_bruts']} trades (#{biggest['rang']}). " if biggest else "")
        + (f"Les {len(cut)} marchés tronqués couvrent de {fmt(min(span(r) for r in cut), 1)} à {fmt(max(span(r) for r in cut), 1)} jours et non la fenêtre entière, donc le plus court ne donne que quelques blocs à 24 h." if cut else "Aucun marché n'a été tronqué."))
    add("")
    add("L'intervalle à 95 % par marché vient d'un bootstrap par blocs de la durée de l'horizon (un jour pour la dernière valeur). "
        f"L'intervalle agrégé rééchantillonne des événements entiers. Chaque intervalle utilise {args.bootstrap} tirages. "
        "Le résultat net ajoute le rebate théorique calculé avec les champs API. Un astérisque signale moins de cinq blocs ou événements. "
        "Les 1 000 $ sont comptés au prix du jeton traité par le taker (prix × parts), comme pour le rebate. "
        "Le capital réel du maker peut être différent car il peut être rempli par création du jeton opposé.")
    add("")
    add("### Agrégats")
    add("")
    add("| Groupe | Horizon | Trades | Marchés | Événements | Moy. ¢/part | IC 95 % | Coût ¢/part | Pondéré taille ¢/part | IC 95 % | Demi-écart ¢ | Mouvement contre maker ¢ | Moy. par marché ¢ | $/1 000 pondéré | IC 95 % | Rebate API $/1 000 | Net $/1 000 | IC 95 % | Net barème doc $/1 000 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, data in aggregates.items():
        for horizon, s in data.items():
            if not s.get("n"):
                continue
            add(f"| {name} | {horizon} | {s['n']} | {s['n_marches']} | {s['n_evenements']} | {fmt(s['moy_cents'], 3)} | {ic_flag(s, 'moy_cents', 3)} | {fmt(s['cout_antiselection_cents'], 3)} | {fmt(s['vw_cents'], 3)} | {ic_flag(s, 'vw_cents', 3)} | {fmt(s.get('demi_ecart_cents'), 3)} | {fmt(s.get('mouvement_contre_maker_cents'), 3)} | {fmt(s['moy_marches_cents'], 3)} | {fmt(s['vw_1000'], 2)} | {ic_flag(s, 'vw_1000', 2)} | {fmt(s['rebate_1000'], 2)} | {fmt(s['net_1000'], 2)} | {ic_flag(s, 'net_1000', 2)} | {fmt(s['net_bareme_doc_1000'], 2)} |")
    add("")
    add("### Par marché")
    add("")
    add("| # | Marché | Horizon | n | Censurés | Blocs | Moy. ¢/part | IC 95 % | Coût ¢ | Pondéré taille ¢/part | $/1 000 | Rebate API $/1 000 | Net $/1 000 | IC 95 % |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in top + supplement:
        for horizon, s in (r.get("sim", {}).get("horizons") or {}).items():
            if not s.get("n"):
                add(f"| {r['rang']} | {short(r['question'], 44)} | {horizon} | 0 | {s.get('n_censures')} | 0 | n.d. | n.d. | n.d. | n.d. | n.d. | n.d. | n.d. | n.d. |")
                continue
            add(f"| {r['rang']} | {short(r['question'], 44)} | {horizon} | {s['n']} | {s['n_censures']} | {s.get('n_blocs')} | {fmt(s['moy_cents'], 3)} | {ic_flag(s, 'moy_cents', 3)} | {fmt(s['cout_antiselection_cents'], 3)} | {fmt(s['vw_cents'], 3)} | {fmt(s['vw_1000'], 2)} | {fmt(s['rebate_1000'], 2)} | {fmt(s['net_1000'], 2)} | {ic_flag(s, 'net_1000', 2)} |")
    add("")
    add("### Prix moyen exécuté contre clôture")
    add("")
    add("La clôture est la dernière valeur connue de l'historique pour un marché actif, ce n'est donc pas une résolution. "
        "Le gain est positif quand le maker a acheté sous cette valeur ou vendu au-dessus. "
        "La dérive indique le mouvement du prix sur la fenêtre et elle pèse souvent plus que l'écart capté. "
        "La concordance est la part de trades où le prix d'exécution se place du côté attendu du milieu, elle contrôle l'hypothèse sur le sens du taker.")
    add("")
    add("| # | Marché | Valeur finale | Achats maker | Prix moyen achat | Gain achat ¢ | Ventes maker | Prix moyen vente | Gain vente ¢ | Dérive ¢ | Demi-écart ¢ | Part taker acheteur | Concordance | Premier trade | Tronqué |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in top + supplement:
        sim = r.get("sim") or {}
        c = sim.get("cloture") or {}
        add(f"| {r['rang']} | {short(r['question'], 44)} | {fmt(sim.get('valeur_finale'), 4)} | {c.get('n_achats', 0)} | {fmt(c.get('vwap_achats_maker'), 4)} | {fmt(c.get('gain_achats_cents'), 2)} | {c.get('n_ventes', 0)} | {fmt(c.get('vwap_ventes_maker'), 4)} | {fmt(c.get('gain_ventes_cents'), 2)} | {fmt(c.get('derive_fenetre_cents'), 2)} | {fmt(sim.get('demi_ecart_effectif_cents'), 3)} | {fmt(sim.get('part_taker_achat_jeton0'), 3)} | {fmt(sim.get('concordance_sens'), 3)} | {(sim.get('premier_trade') or '')[:16]} | {'oui' if sim.get('trades_tronques') else 'non'} |")
    add("")
    add("### Témoin de marchés déjà résolus")
    add("")
    if closed:
        ecartes = counter_text(closed_meta.get("ecartes") or {})
        add(f"Ce témoin réduit en partie le biais de survivance car la clôture y est une vraie résolution (0 ou 1). "
            f"La sélection se fait par volume total parmi les marchés clos depuis {closed_meta.get('date_min')}, avec trois marchés au plus par événement. "
            f"Nous avons lu {closed_meta.get('candidats_lus')} candidats et écarté ceux-ci avant d'atteindre le quota {ecartes}. "
            "Le choix par volume reste un biais.")
        add("")
        add("| Marché | Cat. | Clôture | Résultat jeton 0 | n | Moy. 1 h ¢ | Moy. 24 h ¢ | Moy. clôture ¢ | IC 95 % clôture | Net clôture $/1 000 | feeType |")
        add("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in closed:
            h = (r.get("sim") or {}).get("horizons") or {}
            one, day, end = h.get("1h", {}), h.get("24h", {}), h.get("derniere", {})
            add(f"| {short(r['question'], 48)} | {str(r['categorie'])[:5]} | {(r['date_cloture'] or '')[:10]} | {fmt(r['resultat_final_jeton0'], 0)} | {end.get('n', 0)} | {fmt(one.get('moy_cents'), 3)} | {fmt(day.get('moy_cents'), 3)} | {fmt(end.get('moy_cents'), 3)} | {ic_flag(end, 'moy_cents', 3)} | {fmt(end.get('net_1000'), 2)} | {r.get('feeType')} |")
    else:
        add("Aucun marché résolu n'a été simulé pendant cette exécution.")
    add("")

    add("## WebSocket public")
    add("")
    if ws is None:
        add("Le mode --ws n'a pas été activé pour cette exécution.")
    elif ws.get("echec"):
        add(f"La capture a échoué ({ws['echec']}).")
    else:
        add(f"Capture de {ws.get('debut')} à {ws.get('fin')} sur {ws.get('url')} pour {ws.get('jetons_abonnes')} jetons, avec {ws.get('connexions')} connexion(s) et {len(ws.get('erreurs') or [])} erreur(s). "
            f"Les événements bruts hors carnet complet sont dans {ws.get('fichier')}. Compteurs par type {counter_text(ws.get('compteurs') or {})}. "
            "Le champ fee_rate_bps vient des événements last_trade_price et sa signification exacte reste à confirmer.")
        add("")
        add("| Marché | Événements | Trades | Parts échangées | Mises à jour de prix | Écart moyen ¢ | fee_rate_bps observé |")
        add("|---|---|---|---|---|---|---|")
        for cell in sorted((ws.get("par_marche") or {}).values(), key=lambda c: -c["evenements"]):
            add(f"| {short(cell['question'], 56)} | {cell['evenements']} | {cell['trades']} | {fmt(cell['volume_parts'], 0)} | {cell['maj_prix']} | {fmt(cell['ecart_moyen_cents'], 2)} | {counter_text(cell['fee_rate_bps'])} |")
    add("")

    add("## Limites")
    add("")
    add("| Limite | Conséquence |")
    add("|---|---|")
    add("| Un trade public ne signifie pas que notre ordre aurait été rempli | Le simulateur ne prouve aucune exécution. Le remplissage réel est probablement plus fréquent quand le prix va contre le maker, donc ces chiffres peuvent sous-estimer l'antisélection |")
    add("| File d'attente ignorée | Sur un pas de 1 ¢ avec des centaines de milliers de parts au meilleur prix, un nouvel ordre passe après les autres et ne reçoit qu'une petite part du flux |")
    add("| Marchés non indépendants | Les marchés du mi-mandat réagissent aux mêmes nouvelles. Le bootstrap par événement ne corrige pas la corrélation entre événements, donc les intervalles agrégés restent trop étroits |")
    add(f"| Fenêtre courte | {args.window_days:g} jours au plus et moins pour les marchés très actifs, tronqués par le plafond de trades ou par l'API (offset limité à 10 000). L'horizon 24 h repose sur peu de blocs |")
    add("| Survivance des marchés encore actifs | Le classement exclut les marchés déjà résolus ou proches de 0 et 1. Le témoin résolu ne couvre que quelques marchés choisis par volume |")
    add("| Dernière valeur connue | Elle ne fournit qu'une réalisation par marché. L'intervalle par marché mesure surtout la dispersion des prix d'entrée et ne couvre pas l'incertitude du résultat final |")
    add("| Contexte | Mesures prises juste avant le scrutin du 03/11/2026 et donc non représentatives |")
    add("| Série de prix | /prices-history n'est pas documentée comme un milieu strict. Le pas demandé est de une minute avec un trou toléré de 30 minutes |")
    add("| Sens du taker | Le champ side de /trades avec takerOnly est lu comme le sens du taker. La colonne de concordance contrôle cette lecture sans la prouver |")
    add("| Coûts non modélisés | Gaz, immobilisation du capital et rendement de détention (holdingRewardsEnabled) ne figurent pas dans le résultat net. Les récompenses de liquidité sont présentées à part |")
    restricted = sum(1 for r in top if r.get("restricted"))
    add(f"| Accès | Gamma indique restricted vrai sur {restricted} marchés du classement. La documentation (market-details) le définit ainsi, « Market is geo-restricted for some jurisdictions ». Le champ ne nomme aucune juridiction et il ne dit donc rien d'un pays donné, et le statut d'accès se lit dans commun-trading |")
    add("| Groupe à frais actifs | Marchés créés quelques jours avant la collecte et peu traités. Ce groupe n'est pas un témoin du rebate et son résultat ne se transpose pas à un marché ancien |")
    add("| Frais à date | Les champs de frais sont lus au moment de la collecte et ils peuvent changer à tout moment |")
    add("| Nature du résultat | Résultat de recherche sans promesse de gain ni recommandation. Aucune stratégie ne change de statut |")
    add("")
    add("## Déroulement")
    add("")
    trunc = [r for r in top + supplement + closed if (r.get("sim") or {}).get("trades_tronques")]
    empty = sum(1 for r in top + supplement + closed if not (r.get("sim") or {}).get("horizons"))
    add(f"Appels HTTP par hôte {counter_text(payload['appels_http'])}. Incidents consignés {len(http.incidents)}, avec le détail dans le JSON.")
    add(f"Marchés aux trades tronqués {len(trunc)}. Marchés sans simulation exploitable {empty}.")
    gaps = [r["sim"].get("ecart_hist_vs_milieu_cents") for r in top + supplement if (r.get("sim") or {}).get("ecart_hist_vs_milieu_cents") is not None]
    if gaps:
        add(f"L'écart absolu moyen entre le dernier point d'historique et le milieu du carnet vaut {fmt(float(np.mean(gaps)), 3)} ¢ et le maximum {fmt(float(np.max(gaps)), 3)} ¢.")
    add("")
    add("Sources : gamma-api.polymarket.com, clob.polymarket.com, data-api.polymarket.com, docs.polymarket.com/trading/fees, docs.polymarket.com/market-makers/maker-rebates, docs.polymarket.com/market-makers/liquidity-rewards, docs.polymarket.com/market-data/market-details, docs.polymarket.com/changelog, docs.polymarket.com/api-reference/rate-limits.")
    add("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
