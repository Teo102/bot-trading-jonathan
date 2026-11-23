"""Tests synthétiques du moteur de STRAT-12 (aucune donnée réelle)."""
import math
import numpy as np
import pandas as pd
import moteur_bab12 as m

IDX = pd.date_range("2021-01-01", "2021-12-31", freq="D")


def marche(n=10, graine=2):
    rng = np.random.default_rng(graine)
    btc = rng.normal(0, 0.03, len(IDX))
    cl = {"BTCUSDT": 100 * np.exp(np.cumsum(btc))}
    for i in range(n):
        b = 0.3 + 0.25 * i
        cl[f"A{i:02d}USDT"] = 10 * np.exp(np.cumsum(b * btc + rng.normal(0, 0.01, len(IDX))))
    close = pd.DataFrame(cl, index=IDX)
    vol = pd.DataFrame(30e6, index=IDX, columns=close.columns)
    return close, vol


def test_exclusions():
    assert m.exclu("BTCDOMUSDT") and m.exclu("USDCUSDT") and m.exclu("DEFIUSDT") and not m.exclu("SOLUSDT")


def test_univers_age_et_liquidite():
    close, vol = marche()
    vol["A00USDT"] = 5e6
    close.loc[close.index < pd.Timestamp("2021-05-01"), "A01USDT"] = np.nan    # coté le 01/05
    d = pd.Timestamp("2021-06-06")
    u = m.univers(close, vol, d)
    assert "A00USDT" not in u and "A01USDT" not in u and "A02USDT" in u


def test_betas_classes_et_sans_anticipation():
    close, vol = marche()
    d = pd.Timestamp("2021-06-06")
    b = m.betas(close, d, [c for c in close.columns if c != "BTCUSDT"])
    assert b["A00USDT"] < b["A05USDT"] < b["A09USDT"]
    c2 = close.copy()
    c2.loc[c2.index > d] *= 3
    assert b == m.betas(c2, d, [c for c in close.columns if c != "BTCUSDT"])


def test_poids_neutres_au_beta_et_brut_100():
    b = {f"S{i}": 0.5 + 0.2 * i for i in range(15)}
    w = m.poids(b)
    assert abs(sum(abs(x) for x in w.values()) - 1) < 1e-12
    assert abs(sum(x * b[s] for s, x in w.items())) < 1e-12
    assert sum(1 for x in w.values() if x > 0) == 3 and min(w, key=w.get) in ("S12", "S13", "S14")
    assert m.poids({"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}) == {}         # moins de 2 × 3 contrats


def test_rendement_contrat_retire_et_financement():
    idx = pd.date_range("2021-03-07", periods=8, freq="D")
    close = pd.DataFrame({"X": [100, 101, 102, 110, np.nan, np.nan, np.nan, np.nan]}, index=idx)
    assert abs(m.rendement_contrat(close, "X", idx[0], idx[7]) - 0.10) < 1e-12
    f = pd.Series([0.001, 0.002, 0.004], index=pd.to_datetime(["2021-03-08 00:00", "2021-03-08 08:00", "2021-03-15 00:00"]))
    assert abs(m.financement_semaine({"X": f}, "X", idx[0], idx[7]) - 0.006) < 1e-15   # 08/03 00:00 exclu, 15/03 00:00 inclus


def test_simulation_couts_et_verrou():
    close, vol = marche(12)
    r, c = m.simuler(close, vol, {}, "2021-04-04", "2021-12-19")
    r2, _ = m.simuler(close, vol, {}, "2021-04-04", "2021-12-19", 0.002)
    assert (r["positions"] > 0).all() and r2["net"].sum() < r["net"].sum()
    assert abs((r["brut"] - r["couts"] - r["net"]).abs().max()) < 1e-12
    try:
        m.simuler(close, vol, {}, "2024-05-05", "2024-06-30")
        assert False
    except AssertionError as e:
        assert "verrouillé" in str(e)


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
