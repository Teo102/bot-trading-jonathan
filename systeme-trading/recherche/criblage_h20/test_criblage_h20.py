"""Tests synthétiques du criblage de H20 : fenêtres, absence d'anticipation, univers, coûts, plafond, trimestres."""
import numpy as np
import pandas as pd
import criblage_h20 as c


def grille(n, debut="2022-01-01 08:00"):
    return pd.date_range(debut, periods=n, freq="8h")


def test_fenetres_8h_et_4h():
    b = pd.Series([0.0001, 0.0002], index=pd.to_datetime(["2022-01-01 08:00", "2022-01-01 16:00"]))
    assert list(c.fenetres(b).index) == list(pd.to_datetime(["2022-01-01 08:00", "2022-01-01 16:00"]))
    y = pd.Series([0.0001, 0.0001, 0.0003], index=pd.to_datetime(["2022-01-01 04:00", "2022-01-01 08:00", "2022-01-01 12:00"]))
    f = c.fenetres(y)
    assert abs(f[pd.Timestamp("2022-01-01 08:00")] - 0.0002) < 1e-15 and abs(f[pd.Timestamp("2022-01-01 16:00")] - 0.0003) < 1e-15


def test_univers_age_et_classement():
    q = pd.Timestamp("2022-04-01")
    vol = pd.Series({"A": 5, "B": 9, "C": 7, "D": 1})
    pb = {"A": pd.Timestamp("2021-01-01"), "B": pd.Timestamp("2022-03-01"), "C": pd.Timestamp("2021-06-01"), "D": pd.Timestamp("2021-01-01")}
    py = {"A": pd.Timestamp("2021-01-01"), "B": pd.Timestamp("2021-01-01"), "C": pd.Timestamp("2021-06-01")}
    assert c.choisir_univers(vol, pb, py, q, 2) == ["C", "A"]          # B trop récent sur Binance, D absent de Bybit


def test_revenu_seulement_apres_la_decision_et_couts():
    t = grille(12)
    x = [0.0, 0.0, 0.0003, 0.0003, 0.0003, 0.0001, 0.0001, 0.0001, 0.0, 0.0, 0.0, 0.0]
    diff = pd.DataFrame({"AUSDT": x}, index=t)
    u = {pd.Timestamp("2022-01-01"): ["AUSDT"]}
    p, f = c.simuler(diff, u, pd.Timestamp("2022-01-01"), t[-1])
    assert len(p) == 1
    r = p.iloc[0]
    # D atteint 0,0002 à la 4e fenêtre (moyenne des 3e, 4e et... : 0,0001, 0,0002, 0,0003) ; entrée à la fin de t[3]
    D = diff["AUSDT"].rolling(3).mean()
    entree = D[D >= 0.0002].index[0]
    assert r["entree"] == entree and r["signe"] == 1
    attendu = diff["AUSDT"][(diff.index > entree) & (diff.index <= r["sortie"])].sum()
    assert abs(r["brut"] - attendu) < 1e-15                          # jamais la fenêtre qui a déclenché l'entrée
    assert abs(r["couts"] - 2 * (0.0005 + 0.00055 + 2 * 0.0002)) < 1e-15   # rang 1 : glissement des 10 premiers
    assert abs(r["couts_teneur"] - 4 * 0.0002) < 1e-15


def test_signe_negatif_et_sortie_au_changement_de_signe():
    t = grille(8)
    diff = pd.DataFrame({"AUSDT": [-0.0003, -0.0003, -0.0003, -0.0003, 0.0004, 0.0004, 0.0, 0.0]}, index=t)
    p, _ = c.simuler(diff, {pd.Timestamp("2022-01-01"): ["AUSDT"]}, pd.Timestamp("2022-01-01"), t[-1])
    r = p.iloc[0]
    assert r["signe"] == -1 and r["entree"] == t[2]
    # t3 : +0,0003 ; t4 : −0,0004 (D encore négatif, −0,0000667) ; t5 : −0,0004 puis D devient positif → sortie
    assert abs(r["brut"] - (0.0003 - 0.0008)) < 1e-15 and r["motif"] == "seuil" and r["sortie"] == t[5]


def test_plafond_dix_paires():
    t = grille(6)
    cols = {f"S{i:02d}USDT": [0.0005 + i * 1e-6] * 6 for i in range(12)}
    diff = pd.DataFrame(cols, index=t)
    u = {pd.Timestamp("2022-01-01"): sorted(cols)}
    p, f = c.simuler(diff, u, pd.Timestamp("2022-01-01"), t[-1])
    assert len(p) == 10 and set(p["symbole"]) == {f"S{i:02d}USDT" for i in range(2, 12)}


def test_fermeture_hors_univers_au_trimestre():
    t = pd.date_range("2022-03-30 00:00", periods=9, freq="8h")
    diff = pd.DataFrame({"AUSDT": [0.0003] * 9}, index=t)
    u = {pd.Timestamp("2022-01-01"): ["AUSDT"], pd.Timestamp("2022-04-01"): []}
    p, _ = c.simuler(diff, u, pd.Timestamp("2022-01-01"), t[-1])
    r = p.iloc[0]
    assert r["sortie"] == pd.Timestamp("2022-04-01") and r["motif"] == "hors_univers"


def test_fenetre_manquante_ferme():
    t = grille(8)
    diff = pd.DataFrame({"AUSDT": [0.0003, 0.0003, 0.0003, 0.0003, np.nan, 0.0003, 0.0003, 0.0003]}, index=t)
    p, _ = c.simuler(diff, {pd.Timestamp("2022-01-01"): ["AUSDT"]}, pd.Timestamp("2022-01-01"), t[-1])
    assert p.iloc[0]["motif"] == "fenetre_manquante" and p.iloc[0]["sortie"] == t[4]


def test_capital_et_blocs():
    assert abs(c.au_capital(0.01) - 0.01 / 10 / 2) < 1e-15
    t = pd.to_datetime(["2022-06-01", "2023-06-01"])
    f = pd.DataFrame({"t": t, "symbole": ["A", "B"], "nature": ["financement", "financement"], "preneur": [0.2, 0.2], "teneur": [0.2, 0.2]})
    p = pd.DataFrame({"entree": t})
    blocs, crit, ok, tot = c.blocs_et_criteres(f, p, pd.Timestamp("2022-01-01"), pd.Timestamp("2024-01-01"))
    assert abs(blocs["2022"]["net"] - 0.01) < 1e-12 and crit["4_concentration"]["part_max_paire"] == 0.5 and not ok["5"]


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
