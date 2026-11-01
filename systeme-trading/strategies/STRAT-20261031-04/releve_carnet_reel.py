#!/usr/bin/env python3
"""STRAT-20261031-04 : instantané réel de carnets publics pour contrôler la formule de glissement.

Point d'accès public /fapi/v1/depth, limite 1000, sans clé. Chaque actif dont le carnet couvre 1 %
est conservé jusqu'à 1 % du milieu. Le parcours réel est comparé à la formule corrigée et à
l'ancienne formule fautive. Sortie : resultats/carnet_reel_<horodatage UTC>.json, lu par le test.
Marché calme : cela valide le calcul, pas le niveau de glissement pendant une cascade.
"""
import json
from datetime import datetime, timezone

import requests

from mesure_carnet_signaux import FAPI, P, RES, SES, glissement_moyen_pct, parcours_carnet_pct


def main():
    debut = datetime.now(timezone.utc)
    stamp = debut.strftime("%Y%m%dT%H%M%SZ")
    rap = {"debut_utc": debut.isoformat(timespec="seconds"), "source": "/fapi/v1/depth limite 1000", "actifs": {}, "ecartes": {}}
    for s in P["univers"]:
        b = SES.get(f"{FAPI}/fapi/v1/depth", params={"symbol": s, "limit": 1000}, timeout=30).json()
        asks = [(float(p), float(q)) for p, q in b["asks"]]
        bids = [(float(p), float(q)) for p, q in b["bids"]]
        mid = (asks[0][0] + bids[0][0]) / 2
        if asks[-1][0] < mid * 1.01:
            rap["ecartes"][s] = f"carnet couvert jusqu'à {round((asks[-1][0] / mid - 1) * 100, 3)} % seulement"
            continue
        dans = [x for x in asks if x[0] <= mid * 1.01]
        D = sum(p * q for p, q in dans)
        h = (asks[0][0] - bids[0][0]) / 2 / mid * 100
        e = {"milieu": mid, "meilleur_achat": bids[0][0], "meilleur_vendeur": asks[0][0], "demi_ecart_pct": round(h, 5),
             "profondeur_1pct_usd": round(D), "asks_jusqu_a_1pct": dans, "comparaison": {}}
        for n in [10_000, 100_000]:
            e["comparaison"][str(n)] = {
                "parcours_reel_pct": round(parcours_carnet_pct(dans, mid, n), 5),
                "formule_corrigee_avec_demi_ecart_pct": round(glissement_moyen_pct(n, D, h), 5),
                "ancienne_formule_fautive_pct": round(n / (2 * D) * 100, 5),
            }
        rap["actifs"][s] = e
    RES.mkdir(exist_ok=True)
    (RES / f"carnet_reel_{stamp}.json").write_text(json.dumps(rap, ensure_ascii=False))
    print(stamp)
    print(json.dumps({"ecartes": rap["ecartes"], "actifs": {k: {a: b for a, b in v.items() if a != "asks_jusqu_a_1pct"} for k, v in rap["actifs"].items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
