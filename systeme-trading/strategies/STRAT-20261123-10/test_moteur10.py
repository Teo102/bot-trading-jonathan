"""Tests synthétiques du moteur de STRAT-10 (aucune donnée réelle)."""
import datetime as dt, math
import pandas as pd
import moteur_condor10 as m

V = dt.date(2022, 3, 4)
ECH = "11MAR22"


def mk(k, S=40000.0):
    """Marque synthétique décroissante avec l'éloignement du prix d'exercice."""
    return 0.03 * math.exp(-abs(k - S) / 3000)


def trades(S=40000.0, iv=60.0, strikes=None):
    strikes = strikes or [30000, 34000, 36000, 38000, 40000, 42000, 44000, 46000, 50000]
    L, t = [], 1646380800000
    for k in strikes:
        for typ in ("P", "C"):
            L.append({"timestamp": t, "instrument_name": f"BTC-{ECH}-{k}-{typ}", "price": mk(k, S), "mark_price": mk(k, S),
                      "iv": iv, "index_price": S, "amount": 1, "direction": "buy", "trade_id": f"{k}{typ}"})
            t += 1000
    return pd.DataFrame(L)


def test_etiquette():
    assert m.etiquette(dt.date(2022, 3, 11)) == "11MAR22" and m.etiquette(dt.date(2021, 2, 5)) == "5FEB21"


def test_choix_des_prix_d_exercice():
    S, sig = 40000.0, 0.60
    r = sig * math.sqrt(7 / 365)
    w = m.semaine(trades(), V, 40000.0)
    assert w["position"]
    assert w["put_vendu"]["k"] == m.choisir([30000, 34000, 36000, 38000, 40000], S * math.exp(-r), -1) == 36000
    assert w["call_vendu"]["k"] == 44000 and w["put_achete"]["k"] == 30000   # cible 2σ : 33 880, donc 30 000 (34 000 est au-dessus) and w["call_achete"]["k"] == 50000


def test_paiement_dans_le_corridor_et_perte_max():
    w = m.semaine(trades(), V, 40000.0)                 # règlement entre les jambes vendues : on garde le crédit
    assert abs(w["pnl_usd"] - w["credit_usd"]) < 1e-9 and w["rendement"] > 0
    w2 = m.semaine(trades(), V, 20000.0)                # krach sous l'aile : perte maximale (plus les frais de livraison)
    assert abs(w2["paiement_usd"] - (-(36000 - 20000) + (30000 - 20000))) < 1e-9
    assert w2["rendement"] < -0.0199 and w2["rendement"] > -0.021


def test_couts():
    w = m.semaine(trades(), V, 40000.0)
    S, attendu = 40000.0, 0.0
    for k, sens in ((36000, -1), (44000, -1), (30000, 1), (50000, 1)):
        x = mk(k)
        g = max(0.0003, 0.08 * x)
        px = x + g if sens > 0 else x - g
        attendu += (-sens) * px * S - min(0.0003 * S, 0.125 * x * S)
    assert abs(w["credit_usd"] - attendu) < 1e-9 and w["credit_usd"] > 0
    w2 = m.semaine(trades(), V, 40000.0, cout=2.0)
    assert w2["credit_usd"] < w["credit_usd"]


def test_credit_non_positif_et_ailes():
    t = trades()
    t["mark_price"] = 0.002                              # marques égales : le crédit net est négatif
    w = m.semaine(t, V, 40000.0)
    assert not w["position"] and w["motif"] == "credit_non_positif"
    w3 = m.semaine(trades(strikes=[38000, 40000, 42000]), V, 40000.0)
    assert not w3["position"] and w3["motif"] == "jambes_absentes"


def test_verrou_hors_echantillon():
    try:
        m.semaine(trades(), dt.date(2025, 1, 3), 40000.0)
        assert False
    except AssertionError as e:
        assert "verrouillé" in str(e)


def test_evaluer_portes():
    base = [{"vendredi": str(dt.date(2021, 1, 1) + dt.timedelta(weeks=i)), "position": True, "rendement": 0.004 if i % 5 else -0.006} for i in range(200)]
    r, p = m.evaluer({"base": base, "couts_doubles": base})
    assert r["semaines_avec_position"] == 200 and p["au_moins_150_semaines"] and r["net_annualise"] > 0


if __name__ == "__main__":
    import traceback
    noms = [n for n in sorted(globals()) if n.startswith("test_")]
    e = 0
    for n in noms:
        try:
            globals()[n]()
        except Exception:
            e += 1
            print("ÉCHEC", n)
            traceback.print_exc()
    print(f"{len(noms) - e}/{len(noms)} tests verts")
    raise SystemExit(1 if e else 0)
