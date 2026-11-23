"""Tests synthétiques du papier de STRAT-20261119-09. Aucune donnée réelle, aucun réseau."""
import datetime as dt, json, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
import controle_week_end09 as ctl
import paper_week_end09 as pw

ICI = Path(__file__).resolve().parent
V = dt.date(2026, 11, 20)            # week-end synthétique (heure d'hiver)
CMP, CACT = ctl.calendrier(V, "mp"), ctl.calendrier(V, "act")


def cfg_test(**rempl):
    c = json.loads((ICI / "config_week_end09.json").read_text())
    c["statut"] = "figee"
    c["parametres_papier"]["premier_vendredi"] = str(V)
    d = c["decide_le_19_11_2026"]
    d["univers"]["matieres_premieres"], d["univers"]["actions"], d["temoins"] = ["AUSDT", "BUSDT"], ["CUSDT", "DUSDT", "EUSDT"], ["TUSDT"]
    d["K_positions_max_par_week_end"] = rempl.get("K", 6)
    tmp = Path(tempfile.mkdtemp())
    (tmp / "c.json").write_text(json.dumps(c))
    return pw.Config(tmp / "c.json"), tmp


class Faux:
    """Prix synthétiques : marche aléatoire horaire et minute ; un mouvement de week-end imposé par contrat."""

    def __init__(self, mouvements, apres=None, poison=False):
        self.h, self.m, self.demandes = {}, {}, []
        idx_h = pd.date_range("2026-08-15", "2026-11-25", freq="h")
        rng = np.random.default_rng(1)
        for i, (s, mv) in enumerate(mouvements.items()):
            p = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, len(idx_h))))
            df = pd.DataFrame({"open": p, "high": p * 1.001, "low": p * 0.999}, index=idx_h)
            cal = CMP if s in ("AUSDT", "BUSDT") else CACT
            if s == "TUSDT":
                cal = CMP
            cl = df.loc[cal["cloture"], "open"]
            apres_cl = df.index > cal["cloture"]
            df.loc[apres_cl, ["open", "high", "low"]] = cl * (1 + mv) * np.c_[np.ones(apres_cl.sum()), np.full(apres_cl.sum(), 1.001), np.full(apres_cl.sum(), 0.999)]
            for t, (o, hi, lo) in (apres or {}).get(s, {}).items():
                df.loc[t, ["open", "high", "low"]] = [o, hi, lo]
            if poison:
                d = cal["decision"]
                df.loc[df.index > d, ["open", "high", "low"]] = 1e9
            self.h[s] = df
            idx_m = pd.date_range(cal["decision"], cal["decision"] + dt.timedelta(minutes=59), freq="min")
            self.m[s] = pd.DataFrame({"open": df.loc[cal["decision"], "open"], "high": df.loc[cal["decision"], "open"] * 1.0005,
                                      "low": df.loc[cal["decision"], "open"] * 0.9995}, index=idx_m)

    def _tranche(self, df, a, b, quoi):
        self.demandes.append((quoi, a, b))
        return df[(df.index >= a) & (df.index <= b)]

    def contrat(self, s, iv, a, b):
        return self._tranche(self.h[s] if iv == "1h" else self.m[s], a, b, "contrat" + iv)

    def marque(self, s, iv, a, b):
        return self._tranche(self.h[s] if iv == "1h" else self.m[s], a, b, "marque" + iv)

    def financement(self, s, a, b):
        self.demandes.append(("financement", a, b))
        return [(dt.datetime(2026, 11, 23, 0), 0.0001)]


MOUV = {"AUSDT": 0.05, "BUSDT": 0.0, "CUSDT": -0.05, "DUSDT": 0.04, "EUSDT": 0.0, "TUSDT": 0.0}


def test_signaux_dans_la_fenetre_et_manque():
    cfg, tmp = cfg_test()
    f = Faux(MOUV)
    pw.passage(cfg, f, tmp, CMP["decision"] + dt.timedelta(minutes=2), True)
    J = pw.journaux(tmp)
    s = {(r["groupe"], r["symbole"]): r for r in J["signaux"].lire()}
    assert s[("mp", "AUSDT")]["signal"] == "1" and s[("mp", "AUSDT")]["sens"] == "-1" and s[("mp", "BUSDT")]["signal"] == "0"
    assert max(b for q, a, b in f.demandes) <= CMP["decision"]          # rien après la décision n'est demandé
    # passage suivant après la fenêtre du dimanche et avant la décision des actions : rien de neuf
    pw.passage(cfg, f, tmp, CMP["decision"] + dt.timedelta(minutes=40), True)
    assert {r["groupe"] for r in J["passages"].lire()} == {"mp", "temoin_mp"}
    # passage manqué pour les actions (après la fenêtre du lundi) : incident, groupe vide
    e = pw.passage(cfg, f, tmp, CACT["decision"] + dt.timedelta(minutes=45), True)
    st = {r["groupe"]: r["statut"] for r in J["passages"].lire()}
    assert st["act"] == "manque" and st["temoin_act"] == "manque" and len(e["incidents_du_passage"]) == 2


def test_non_anticipation_prix_empoisonnes():
    cfg, t1 = cfg_test()
    _, t2 = cfg_test()
    pw.passage(cfg, Faux(MOUV), t1, CMP["decision"] + dt.timedelta(minutes=2), True)
    pw.passage(cfg, Faux(MOUV, poison=True), t2, CMP["decision"] + dt.timedelta(minutes=2), True)
    cols = ["symbole", "M", "sigma", "signal", "sens", "retenu"]
    a = [[r[c] for c in cols] for r in pw.journaux(t1)["signaux"].lire()]
    b = [[r[c] for c in cols] for r in pw.journaux(t2)["signaux"].lire()]
    assert a == b and len(a) == 3


def test_plafond_matieres_d_abord():
    cfg, tmp = cfg_test(K=2)
    f = Faux({**MOUV, "BUSDT": -0.06})
    pw.passage(cfg, f, tmp, CMP["decision"] + dt.timedelta(minutes=2), True)
    pw.passage(cfg, f, tmp, CACT["decision"] + dt.timedelta(minutes=2), True)
    J = pw.journaux(tmp)
    ret = [(r["groupe"], r["symbole"]) for r in J["signaux"].lire() if r["retenu"] == "1"]
    assert ret == [("mp", "AUSDT"), ("mp", "BUSDT")]                    # aucune place pour les actions
    p = {r["groupe"]: r for r in J["passages"].lire()}
    assert p["act"]["places"] == "0" and p["act"]["signaux"] == "2"


def test_plafond_grappe():
    tri = [("G1", 3.0), ("G2", 2.9), ("G3", 2.5), ("G4", 2.4), ("H1", 1.0), ("G5", 0.9), ("H2", 0.8), ("H3", 0.7)]
    r = pw.choisir(tri, 6, {"G1", "G2", "G3", "G4", "G5"}, 3)
    assert r == {"G1": 1, "G2": 2, "G3": 3, "H1": 4, "H2": 5, "H3": 6}
    assert pw.choisir(tri, 2, {"G1", "G2", "G3", "G4", "G5"}, 3) == {"G1": 1, "G2": 2}
    assert len(pw.choisir(tri, 6, set(), 3)) == 6                           # témoin et matières premières : pas de grappe
    cfg, _ = cfg_test()
    assert cfg.max_grappe == 3 and "NVDAUSDT" in cfg.grappe


def test_position_sans_stop_et_couts():
    cfg, tmp = cfg_test()
    f = Faux(MOUV)
    t_ecrit = CMP["decision"] + dt.timedelta(minutes=2, seconds=30)
    pw.passage(cfg, f, tmp, t_ecrit, False)
    for t in (CACT["decision"] + dt.timedelta(minutes=2), CACT["sortie"] + dt.timedelta(minutes=70)):
        pw.passage(cfg, f, tmp, t, False)
    J = pw.journaux(tmp)
    p = {(r["groupe"], r["symbole"]): r for r in J["positions"].lire()}
    a = p[("mp", "AUSDT")]
    assert a["t_entree"] == (CMP["decision"] + dt.timedelta(minutes=3)).isoformat() and a["statut"] == "sortie"
    entree, sortie = float(a["entree"]), float(f.h["AUSDT"].loc[CMP["sortie"], "open"])
    brut = -1 * (sortie / entree - 1)
    fin = -(-1) * 0.0001                                                 # vendeur : reçoit le financement positif
    assert abs(float(a["net_base"]) - (brut - (2 * 0.0005 + 0.001 + 0.0005) + fin)) < 1e-12
    assert abs(float(a["net_couts_doubles"]) - (brut - 2 * (2 * 0.0005 + 0.001 + 0.0005) + fin)) < 1e-12
    sem = J["semaines"].lire()
    assert len(sem) == 1 and sem[0]["positions"] == str(len([k for k in p if not k[0].startswith("temoin")]))
    assert abs(float(sem[0]["base"]) - sum(float(r["net_base"]) for k, r in p.items() if not k[0].startswith("temoin")) / 6) < 1e-12


def test_stop_par_ecart_a_la_reouverture():
    cfg, tmp = cfg_test()
    # A vendu après +5 % ; à la réouverture (23:00 UTC) la marque ouvre 10 % plus haut : remplissage à l'ouverture
    f0 = Faux(MOUV)
    p_dec = f0.h["AUSDT"].loc[CMP["decision"], "open"]
    ouv = p_dec * 1.10
    f = Faux(MOUV, apres={"AUSDT": {CMP["reouverture"]: (ouv, ouv * 1.02, ouv * 0.99)}})
    pw.passage(cfg, f, tmp, CMP["decision"] + dt.timedelta(minutes=2), False)
    pw.passage(cfg, f, tmp, CMP["sortie"] + dt.timedelta(minutes=70), False)
    a = {r["symbole"]: r for r in pw.journaux(tmp)["positions"].lire()}["AUSDT"]
    assert a["statut"] == "stop" and a["t_sortie"] == CMP["reouverture"].isoformat()
    assert float(a["sortie_base"]) == ouv                                # écart compté en entier, pas le niveau
    assert float(a["sortie_stressee"]) == 0.5 * (ouv + ouv * 1.02)       # mode 1 : pire encore
    assert float(a["net_base"]) < -0.09


def test_issue_jamais_demandee_trop_tot():
    cfg, tmp = cfg_test()
    f = Faux(MOUV)
    pw.passage(cfg, f, tmp, CMP["decision"] + dt.timedelta(minutes=2), False)
    pw.passage(cfg, f, tmp, CMP["sortie"] + dt.timedelta(minutes=30), False)   # trop tôt : pas de position
    assert pw.journaux(tmp)["positions"].lire() == []
    assert all(q.startswith("contrat1h") for q, a, b in f.demandes)
    sig = pw.journaux(tmp)["signaux"].lire()[0]
    try:
        pw.jouer_position(cfg, f, sig, V, "mp", CMP["sortie"])
        assert False
    except AssertionError as e:
        assert "trop tôt" in str(e)


def test_mode_a_blanc_sans_issue():
    cfg, tmp = cfg_test()
    f = Faux(MOUV)
    for t in (CMP["decision"] + dt.timedelta(minutes=2), CACT["decision"] + dt.timedelta(minutes=2), CACT["sortie"] + dt.timedelta(hours=5)):
        pw.passage(cfg, f, tmp, t, True)
    assert pw.journaux(tmp)["positions"].lire() == [] and pw.journaux(tmp)["semaines"].lire() == []
    assert all(q == "contrat1h" for q, a, b in f.demandes)


def test_week_end_ferie_exclu():
    cfg, tmp = cfg_test()
    cfg.feries = {V}
    f = Faux(MOUV)
    pw.passage(cfg, f, tmp, CACT["sortie"] + dt.timedelta(hours=2), False)
    J = pw.journaux(tmp)
    assert J["signaux"].lire() == [] and J["semaines"].lire()[0]["exclu"] == "1" and f.demandes == []


def test_refus_si_configuration_non_figee():
    c = json.loads((ICI / "config_week_end09.json").read_text())
    c["statut"] = "en_preparation"
    tmp = Path(tempfile.mkdtemp())
    (tmp / "c.json").write_text(json.dumps(c))
    r = subprocess.run([sys.executable, "-B", str(ICI / "paper_week_end09.py"), "--config", str(tmp / "c.json"),
                        "--donnees", "/nonexistent", "--sorties", str(tmp / "s")], capture_output=True, text=True, cwd=ICI)
    assert r.returncode != 0 and "non figée" in r.stderr


def test_chercher_stop_ordre_du_temps():
    idx = pd.date_range("2026-11-22 22:03", periods=3, freq="min")
    b = pd.DataFrame({"open": [100, 100, 100], "high": [100.2, 103, 104], "low": [99.9, 99, 95]}, index=idx)
    t, base, st = pw.chercher_stop(b, 1, 98.0)
    assert t == idx[2] and base == 98.0 and st == 0.5 * (98 + 95)
    t, base, st = pw.chercher_stop(b, -1, 102.5)
    assert t == idx[1] and base == 102.5 and st == 0.5 * (102.5 + 103)


def test_seance_courte_exclue():
    cfg, tmp = cfg_test()
    cfg.feries, cfg.courtes = set(), {V}
    f = Faux(MOUV)
    pw.passage(cfg, f, tmp, CACT["sortie"] + dt.timedelta(hours=2), False)
    J = pw.journaux(tmp)
    assert J["signaux"].lire() == [] and J["semaines"].lire()[0]["exclu"] == "1" and f.demandes == []
    cfg2, _ = cfg_test()
    assert dt.date(2026, 11, 27) in cfg2.courtes and cfg2.exclu(dt.date(2026, 11, 27)) and not cfg2.exclu(dt.date(2026, 12, 4))


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
