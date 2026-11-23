"""Tests synthétiques du moteur de STRAT-11 (aucune donnée réelle)."""
import math
import numpy as np
import pandas as pd
import moteur_vol11 as m

IDX = pd.date_range("2018-01-01", "2018-06-30", freq="D")


def prix(vol_btc=0.8, vol_eth=0.4, graine=1):
    rng = np.random.default_rng(graine)
    b = 100 * np.exp(np.cumsum(rng.normal(0, vol_btc / math.sqrt(365), len(IDX))))
    e = 100 * np.exp(np.cumsum(rng.normal(0, vol_eth / math.sqrt(365), len(IDX))))
    return pd.DataFrame({"BTCUSDT": b, "ETHUSDT": e}, index=IDX)


def test_poids_et_plafond():
    p = prix(1.0, 0.2)
    w = m.poids_cibles(p, IDX[60])
    assert 0.3 < w["BTCUSDT"] < 0.8 and w["ETHUSDT"] == 1.0          # cible 50 % : BTC réduit, ETH plafonné à 1


def test_poids_sans_anticipation():
    p = prix()
    t = IDX[80]
    w1 = m.poids_cibles(p, t)
    p2 = p.copy()
    p2.loc[p2.index > t] *= 10
    assert w1 == m.poids_cibles(p2, t)


def test_detention_sans_cout_suit_les_prix():
    p = prix()
    v, _ = m.simuler(p[["BTCUSDT"]], "2018-01-01", "2018-06-30", "detention", cout=0.0)
    assert abs(v.iloc[-1] - p["BTCUSDT"].iloc[-2] / p["BTCUSDT"].iloc[0]) < 1e-9


def test_couts_et_rotation():
    p = prix()
    v0, _ = m.simuler(p, "2018-01-01", "2018-06-30", "pilote", cout=0.0)
    v1, rot = m.simuler(p, "2018-01-01", "2018-06-30", "pilote", cout=0.0015)
    assert v1.iloc[-1] < v0.iloc[-1] and rot > 0


def test_liquidites_ne_rapportent_rien():
    idx = pd.date_range("2018-01-01", periods=80, freq="D")
    p = pd.DataFrame({"BTCUSDT": np.r_[100 * np.exp(np.cumsum(np.tile([0.1, -0.1], 25))), np.full(30, 100.0)]}, index=idx)
    v, _ = m.simuler(p, idx[50], idx[-1], "pilote", cout=0.0)
    assert abs(v.iloc[-1] - 1.0) < 1e-12                              # prix plats : valeur inchangée, même en partie liquide


def test_verrou():
    try:
        m.simuler(prix(), "2023-06-01", "2024-02-01")
        assert False
    except AssertionError as e:
        assert "verrouillé" in str(e)


def test_mesures():
    v = pd.Series([1.0, 1.1, 0.99, 1.2], index=pd.date_range("2018-01-01", periods=4))
    r = m.mesures(v)
    assert abs(r["baisse_max"] - 0.1) < 1e-12 and abs(r["rendement_total"] - 0.2) < 1e-12


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
