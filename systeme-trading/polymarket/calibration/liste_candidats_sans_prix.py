#!/usr/bin/env python3
"""Liste des marchés candidats à une prévision, SANS AUCUN PRIX (protocole de la mission du 09/11/2026).

Le prévisionniste ne doit pas voir le prix avant d'écrire sa probabilité. Ce script lit l'API publique Gamma et
n'écrit que des champs d'une liste blanche : question, règles, dates, identifiants, étiquettes, volume et liquidité.
Aucun champ de prix (outcomePrices, bestBid, bestAsk, lastTradePrice, spread, variations) n'est écrit ni affiché.

Sélection, fixée avant toute lecture :
- marché actif, non clos, carnet ouvert, fin Gamma dans [aujourd'hui + 2 j, aujourd'hui + horizon_max j] ;
- hors mi-mandat (`clob_collector.is_midterm`), hors marchés « Up or Down » (résolus par Chainlink, hors registre UMA) ;
- liquidité Gamma ≥ seuil et volume 24 h ≥ seuil ;
- un seul marché par événement Gamma : celui dont le volume 24 h est le plus grand (règle aveugle au prix).

Usage : python3 -B liste_candidats_sans_prix.py --horizon-max 45 --sortie <fichier.json>
"""
import argparse, datetime as dt, json, re, sys, time
from pathlib import Path
import requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import clob_collector as cc  # noqa: E402

GAMMA = "https://gamma-api.polymarket.com"
BLANCHE = ["id", "conditionId", "slug", "question", "description", "endDate", "startDate", "outcomes", "negRisk",
           "resolutionSource", "umaBond", "customLiveness", "clobTokenIds", "groupItemTitle"]
INTERDITS = re.compile(r"price|bid|ask|spread|change|lastTrade", re.I)


def get(url, params):
    for essai in range(6):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 422):  # décalage trop grand : fin de la pagination simple
                return []
        except requests.exceptions.RequestException:
            pass
        time.sleep(2 + essai)
    raise RuntimeError(url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon-min", type=int, default=2)
    ap.add_argument("--horizon-max", type=int, default=45)
    ap.add_argument("--liquidite-min", type=float, default=10000)
    ap.add_argument("--volume24-min", type=float, default=5000)
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    lo, hi = now + dt.timedelta(days=a.horizon_min), now + dt.timedelta(days=a.horizon_max)
    par_evenement, lus = {}, 0
    for page in range(a.pages):
        rows = get(f"{GAMMA}/markets", {"active": "true", "closed": "false", "limit": 100, "offset": page * 100,
                                        "order": "volume24hr", "ascending": "false", "include_tag": "true",
                                        "end_date_min": lo.strftime("%Y-%m-%dT%H:%M:%SZ"), "end_date_max": hi.strftime("%Y-%m-%dT%H:%M:%SZ")})
        if not rows:
            break
        lus += len(rows)
        for m in rows:
            q = m.get("question") or ""
            if not m.get("conditionId") or not m.get("enableOrderBook", True) or m.get("acceptingOrders") is False:
                continue
            if re.search(r"up or down", q, re.I) or cc.is_midterm(m):
                continue
            liq, v24 = float(m.get("liquidityNum") or 0), float(m.get("volume24hr") or 0)
            if liq < a.liquidite_min or v24 < a.volume24_min:
                continue
            ev = (m.get("events") or [{}])[0]
            x = {k: m.get(k) for k in BLANCHE}
            x.update({"evenement_id": ev.get("id"), "evenement_slug": ev.get("slug"), "evenement_titre": ev.get("title"),
                      "etiquettes": sorted(cc.market_tags(m)), "volume24h": round(v24), "liquidite": round(liq),
                      "nb_marches_evenement": None})
            assert not any(INTERDITS.search(k) for k in x), "champ de prix dans la sortie"
            cle = ev.get("id") or m["conditionId"]
            par_evenement.setdefault(cle, []).append(x)
        if len(rows) < 100:
            break
    sortie = []
    for cle, lst in par_evenement.items():
        lst.sort(key=lambda z: -z["volume24h"])
        lst[0]["nb_marches_evenement"] = len(lst)
        sortie.append(lst[0])
    sortie.sort(key=lambda z: z["endDate"] or "")
    Path(a.sortie).write_text(json.dumps({"genere_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "parametres": vars(a), "marches_lus": lus,
                                          "candidats": sortie}, indent=1, ensure_ascii=False))
    print(f"{lus} marchés lus, {len(sortie)} événements candidats, écrits dans {a.sortie} (aucun prix lu ni écrit)")


if __name__ == "__main__":
    main()
