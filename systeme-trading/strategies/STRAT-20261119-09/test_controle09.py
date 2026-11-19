"""Tests synthétiques du contrôle de STRAT-20261119-09 : calendrier, heure d'été, σ, non-anticipation, plafond."""
import datetime as dt
import numpy as np, pandas as pd
import controle_week_end09 as c


def test_calendrier_hiver_et_ete():
    hiver = c.calendrier(dt.date(2026, 11, 13), "mp")
    assert hiver["cloture"] == dt.datetime(2026, 11, 13, 22) and hiver["decision"] == dt.datetime(2026, 11, 15, 22)
    assert hiver["reouverture"] == dt.datetime(2026, 11, 15, 23) and hiver["sortie"] == dt.datetime(2026, 11, 16, 1)
    ete = c.calendrier(dt.date(2026, 7, 10), "act")
    assert ete["cloture"] == dt.datetime(2026, 7, 10, 20) and ete["decision"] == dt.datetime(2026, 7, 13, 12)
    assert ete["reouverture"] == dt.datetime(2026, 7, 13, 13, 30) and ete["sortie"] == dt.datetime(2026, 7, 13, 16)


def test_changement_d_heure_pendant_le_week_end():
    # fin de l'heure d'été le dimanche 01/11/2026 : clôture en heure d'été, réouverture en heure d'hiver
    k = c.calendrier(dt.date(2026, 10, 30), "mp")
    assert k["cloture"] == dt.datetime(2026, 10, 30, 21) and k["decision"] == dt.datetime(2026, 11, 1, 22)


def test_exclusion_feries():
    assert c.exclu(dt.date(2026, 6, 19)) and c.exclu(dt.date(2026, 9, 4)) and not c.exclu(dt.date(2026, 9, 11))


def serie(vendredi, prix_lundi=1.0):
    idx = pd.date_range("2026-08-01", "2026-11-20", freq="h")
    rng = np.random.default_rng(0)
    p = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, len(idx))))
    return pd.DataFrame({"open": p, "qv": 1e6}, index=idx)


def test_sigma_ignore_le_futur():
    df = serie(None)
    v = dt.date(2026, 11, 13)
    s = c.sigma(df, v, "act")
    df3 = df.copy()
    df3.loc[df3.index > c.ny(v, 16), "open"] *= 50   # rien après la clôture du vendredi ne compte
    assert s is not None and s == c.sigma(df3, v, "act")


def test_lundi_exclu_du_sigma():
    v = dt.date(2026, 11, 13)
    jours = [d.date() for d in pd.date_range("2026-08-01", "2026-11-13") if d.weekday() < 5]
    prix = {}
    p = 100.0
    for j in jours:
        p *= 1.10 if j.weekday() == 0 else (1.01 if j.toordinal() % 2 else 0.99)   # lundi : +10 % (week-end)
        prix[c.ny(j, 16)] = p
    df = pd.DataFrame({"open": pd.Series(prix), "qv": 1.0})
    assert c.sigma(df, v, "act") < 0.02


def test_non_anticipation_evenement():
    v = dt.date(2026, 11, 13)
    df = serie(None)
    e1 = c.evenement(df, v, "mp")
    d = c.calendrier(v, "mp")["decision"]
    df2 = df.copy()
    df2.loc[df2.index > d, "open"] = np.nan          # prix empoisonnés après la décision
    df2.loc[df2.index > d + dt.timedelta(hours=1), "open"] = 1e9
    e2 = c.evenement(df2, v, "mp")
    assert e1 == e2 and e1 is not None


def test_signal_et_sens():
    v = dt.date(2026, 11, 13)
    df = serie(None)
    cal = c.calendrier(v, "act")
    s = c.sigma(df, v, "act")
    df.loc[cal["decision"], "open"] = df.loc[cal["cloture"], "open"] * (1 + 3 * s)
    e = c.evenement(df, v, "act")
    assert e["signal"] and e["sens"] == -1 and abs(e["rapport"] - 3) < 1e-9


def test_plafond_matieres_d_abord():
    mp = [("XAUUSDT", 1.2), ("CLUSDT", 2.0)]
    act = [(f"S{i}USDT", 1 + i / 10) for i in range(8)]
    a, b = c.plafonner(mp, act)
    assert [s for s, _ in a] == ["CLUSDT", "XAUUSDT"] and len(b) == 4 and b[0][0] == "S7USDT"
    a, b = c.plafonner([], [("AUSDT", 1.5), ("BUSDT", 1.5)], k=1)
    assert b == [("AUSDT", 1.5)]


def test_volume_week_end_heures_de_fermeture():
    idx = pd.date_range("2026-09-20", "2026-11-17", freq="h")
    df = pd.DataFrame({"open": 1.0, "qv": 0.0}, index=idx)
    for f in c.VENDREDIS_UNIVERS:
        k = c.calendrier(f, "act")
        df.loc[(df.index >= k["cloture"]) & (df.index < k["decision"]), "qv"] = 7e5
    assert c.volume_week_end(df, c.VENDREDIS_UNIVERS) == 7e5


if __name__ == "__main__":
    import traceback
    noms = [n for n in sorted(globals()) if n.startswith("test_")]
    echecs = 0
    for n in noms:
        try:
            globals()[n]()
        except Exception:
            echecs += 1
            print("ÉCHEC", n)
            traceback.print_exc()
    print(f"{len(noms) - echecs}/{len(noms)} tests verts")
    raise SystemExit(1 if echecs else 0)
