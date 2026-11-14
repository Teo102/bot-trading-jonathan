#!/usr/bin/env python3
"""Papier aveugle de STRAT-06-bis : 7 cohortes quotidiennes (FICHE_STRAT-06-BIS.md § 1, PLAN_PAPIER_COHORTES.md).

Aucun ordre, aucune clé, `dry_run` permanent. Le moteur est celui qui a produit les résultats de la v1 :
`moteur_xsmom.jouer_ligne` et `cout_de_rotation`, avec la cible `univers_cotations.fabrique_cible` et la configuration
figée de la v1 (`config_strat06.json`, `run_essai06.params_cotation`). Seuls changent le calendrier et le poids :
- la cohorte c (0 à 6) se rééquilibre aux dates jour_0 + c + 7 k, signal lu sur les jours < t, exécution à t + 1 h ;
- chaque ligne pèse 1/84 du capital (6 shorts × 1/84 et BTC à n/84 par cohorte ; brut 100 % pour 7 cohortes pleines).

La boucle `jouer_cohorte` reprend celle de `moteur_xsmom.backtest` à deux différences près, testées :
1. la dernière semaine, encore ouverte, est valorisée à l'heure d'évaluation (ouverture de l'heure, sans coût de sortie) ;
2. aucun solde final n'est imputé : la stratégie continue.
Sur des semaines closes, elle rend exactement le backtest (test_cohortes06.py).

Série stressée (verdict, fiche § 1) : sortie de stop au mode 1 de `stress_stops.py`, à mi-chemin entre le remplissage de
base (pire du niveau et de l'ouverture) et le plus haut horaire du prix de marque, plus 0,30 %.

Signal manqué (fiche § 2, incidents) : une date dont le signal n'a pas été écrit avant son heure d'exécution (t + 1 h)
n'est ni rejouée ni remplacée. La cohorte reste vide cette semaine-là et ses lignes précédentes sont soldées à t + 1 h
(coût compté). C'est la lecture proposée de la règle, à confirmer au gel.

Usage (serveur, cron horaire) :
  python3 -B paper_cohortes06.py --tout                  # collecte, signaux, séries, journal
  python3 -B paper_cohortes06.py --tout --sans-reseau    # recalcul sur les données déjà collectées
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import moteur_xsmom as m  # noqa: E402
import univers_cotations as uc  # noqa: E402

UNE_HEURE = pd.Timedelta(hours=1)
UN_JOUR = pd.Timedelta(days=1)
COHORTES = 7
NOTIONNEL = 1.0 / 84
DEBUT_DONNEES = pd.Timestamp("2019-09-01")  # comme run_essai06 : un nom actif avant est « ancien »
CONFIG_BIS = ICI / "config_bis06.json"
SORTIES = ICI / "resultats" / "paper_cohortes"


class Refus(RuntimeError):
    pass


# ---------------------------------------------------------------- paramètres figés de la v1

def parametres(c6: dict | None = None, c3: dict | None = None):
    """(Params du moteur, ParamsCotation) exactement comme `run_essai06.executer`."""
    import run_essai as r3
    import run_essai06 as r6
    if c6 is None:
        c6, c3 = r6.charger_configs()
    if c6.get("statut_regles") != "figees" or c3.get("statut_regles") != "figees":
        raise Refus("Configuration de la v1 non figée : le papier de STRAT-06-bis ne tourne que sur les règles figées.")
    return r3.params_depuis(c3), r6.params_cotation(c6, c3)


def empreinte_fichier(chemin: Path) -> str:
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


# ---------------------------------------------------------------- données

def couper_zombies_vivants(jours: dict, heures: dict, fin: pd.DataFrame | None, dernier_jour_clos: pd.Timestamp):
    """`moteur_xsmom.couper_zombies`, sauf pour les symboles encore actifs au dernier jour clos : en direct, le jour en
    cours n'est pas clos, et la coupe d'origine effacerait ses heures (faux délistage de tous les noms)."""
    jc, hc, fc, dernier = m.couper_zombies(jours, heures, fin)
    for s, d in dernier.items():
        if d is not None and d >= dernier_jour_clos:
            for k in hc:
                if s in heures[k]:
                    hc[k][s] = heures[k][s]
            if fc is not None and fin is not None and s in fin:
                fc[s] = fin[s]
    return jc, hc, fc


# ---------------------------------------------------------------- calendrier

def dates_cohorte(jour0: pd.Timestamp, c: int, h_eval: pd.Timestamp) -> list[pd.Timestamp]:
    """Dates de rééquilibrage de la cohorte c dont l'exécution (t + 1 h) a eu lieu à l'heure d'évaluation."""
    out, t = [], pd.Timestamp(jour0).normalize() + c * UN_JOUR
    while t + UNE_HEURE <= h_eval:
        out.append(t)
        t += 7 * UN_JOUR
    return out


# ---------------------------------------------------------------- une ligne, version stressée

def stresser_stop(r: dict, heures: dict, p: m.Params, notionnel: float) -> dict:
    """Sortie de stop au mode 1 de stress_stops.py (mi-chemin entre le remplissage de base et le plus haut de marque)."""
    if r.get("statut") != "stop":
        return r
    s, h, sens, px_in = r["symbole"], r["t_sortie"], r["sens"], r["entree"]
    oh = heures["open"][s][h]
    niveau = px_in * (1 - sens * p.stop)
    if sens < 0:
        base = max(niveau, oh)
        brut = 0.5 * (base + max(base, heures["mark_high"][s][h]))
        sortie = brut * (1 + p.glissement_stop)
    else:
        base = min(niveau, oh)
        brut = 0.5 * (base + min(base, heures["mark_low"][s][h]))
        sortie = brut * (1 - p.glissement_stop)
    rend = sens * (sortie / px_in - 1)
    return {**r, "sortie": sortie, "pnl_prix": notionnel * rend, "cout_sortie_force": notionnel * (1 + rend) * p.frais,
            "valeur_fin": notionnel * (1 + rend) * sens}


# ---------------------------------------------------------------- une cohorte

def jouer_cohorte(jours: dict, heures: dict, fin, dates: list, p: m.Params, notionnel: float, fonction_cible,
                  h_eval: pd.Timestamp | None = None, stress: bool = False, manquees: set | None = None,
                  cohorte: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Boucle de `moteur_xsmom.backtest` (même ordre, mêmes fonctions), avec la dernière semaine valorisée à h_eval si
    elle est encore ouverte, sans solde final. `manquees` : dates dont le signal n'a pas été écrit à temps."""
    manquees = manquees or set()
    tenues: dict[str, float] = {}
    semaines, lignes = [], []
    for i, t in enumerate(dates):
        t_in = t + UNE_HEURE
        close = i + 1 < len(dates)
        t_out = dates[i + 1] + UNE_HEURE if close else h_eval
        if t_out is None or t_out < t_in:
            break
        if t in manquees:
            poids, n_univers = {}, 0
        else:
            poids, n_univers = fonction_cible(jours, t, p)
        cible = {s: w * notionnel for s, w in poids.items() if w}
        longs = [s for s, w in cible.items() if w > 0]
        shorts = [s for s, w in cible.items() if w < 0]
        cout_rotation = m.cout_de_rotation(tenues, cible, p)
        tenues = {}
        tot = {"pnl_prix": 0.0, "financement": 0.0, "cout": cout_rotation, "long": 0.0, "short": 0.0}
        for s, n in cible.items():
            sens = 1 if n > 0 else -1
            r = m.jouer_ligne(heures, fin, s, sens, t_in, t_out, abs(n), p)
            if stress:
                r = stresser_stop(r, heures, p, abs(n))
            r.update({"lundi": t, "cohorte": cohorte, "provisoire": not close, "notionnel": abs(n), "t_in": t_in})
            lignes.append(r)
            if r["statut"] == "absent":
                continue
            tot["pnl_prix"] += r["pnl_prix"]
            tot["financement"] += r["financement"]
            tot["cout"] += r["cout_sortie_force"]
            tot["long" if sens > 0 else "short"] += r["pnl_prix"] + r["financement"]
            if r["statut"] == "semaine":
                tenues[s] = r["valeur_fin"]
        net = tot["pnl_prix"] + tot["financement"] - tot["cout"]
        semaines.append({"cohorte": cohorte, "lundi": t, "t_in": t_in, "t_out": t_out, "provisoire": not close,
                         "manquee": t in manquees, "longs": ",".join(longs), "shorts": ",".join(shorts),
                         "univers": n_univers, **tot, "net": net})
    return pd.DataFrame(semaines), pd.DataFrame(lignes)


# ---------------------------------------------------------------- le portefeuille

@dataclass
class Resultat:
    semaines: pd.DataFrame          # semaines de cohortes (closes et ouvertes), base et stressée
    lignes: pd.DataFrame
    quotidien: pd.DataFrame         # valorisation à 01:00 UTC de chaque jour, base et stressée
    hebdo: pd.DataFrame             # semaines civiles : somme des semaines de cohortes closes dans la semaine


def calculer(jours: dict, heures: dict, fin, jour0, h_eval, p: m.Params, pc: uc.ParamsCotation,
             manquees: dict | None = None, notionnel: float = NOTIONNEL, dernier_jour_clos=None) -> Resultat:
    """Les 7 cohortes, en base et en stressé, et les séries du portefeuille."""
    jour0, h_eval = pd.Timestamp(jour0), pd.Timestamp(h_eval)
    dernier_jour_clos = pd.Timestamp(dernier_jour_clos) if dernier_jour_clos is not None else jours["volume"].index.max()
    jc, hc, fc = couper_zombies_vivants(jours, heures, fin, dernier_jour_clos)
    manquees = manquees or {}
    sem, lig = [], []
    for stress in (False, True):
        cible = uc.fabrique_cible(pc, DEBUT_DONNEES)
        for c in range(COHORTES):
            d = dates_cohorte(jour0, c, h_eval)
            s, l = jouer_cohorte(jc, hc, fc, d, p, notionnel, cible, h_eval, stress, manquees.get(c, set()), c)
            for x in (s, l):
                if len(x):
                    x["serie"] = "stressee" if stress else "base"
            sem.append(s); lig.append(l)
    semaines = pd.concat([x for x in sem if len(x)], ignore_index=True) if any(len(x) for x in sem) else pd.DataFrame()
    lignes = pd.concat([x for x in lig if len(x)], ignore_index=True) if any(len(x) for x in lig) else pd.DataFrame()
    quotidien = valorisation_quotidienne(jc, hc, fc, semaines, lignes, jour0, h_eval, p, notionnel)
    return Resultat(semaines, lignes, quotidien, hebdomadaire(semaines))


def valoriser_semaine_ouverte(heures, fin, lignes_sem: pd.DataFrame, h: pd.Timestamp, p: m.Params, stress: bool,
                              cout_rotation: float) -> float:
    """Valeur, à l'heure h, d'une semaine de cohorte entrée avant h : lignes rejouées jusqu'à h, coût d'entrée compris."""
    v = -cout_rotation
    for r in lignes_sem.itertuples(index=False):
        if r.statut == "absent":
            continue
        notionnel = float(r.notionnel)
        x = m.jouer_ligne(heures, fin, r.symbole, int(r.sens), r.t_in, h, notionnel, p)
        if stress:
            x = stresser_stop(x, heures, p, notionnel)
        if x["statut"] == "absent":
            continue
        v += x["pnl_prix"] + x["financement"] - x["cout_sortie_force"]
    return v


def valorisation_quotidienne(heures_jours, heures, fin, semaines: pd.DataFrame, lignes: pd.DataFrame, jour0, h_eval,
                             p: m.Params, notionnel: float) -> pd.DataFrame:
    """Cumul, à chaque jour D à 01:00 UTC, des semaines de cohortes closes avant D 01:00 et de la valeur des semaines
    ouvertes à cette heure (lignes rejouées jusqu'à D 01:00, coût d'entrée compris, sans coût de sortie). Équivalent
    brut 100 %, somme simple (convention de la v1)."""
    if semaines.empty:
        return pd.DataFrame(columns=["heure", "base", "stressee"])
    heures_eval = pd.date_range(pd.Timestamp(jour0).normalize() + UN_JOUR, pd.Timestamp(h_eval).normalize(), freq="D") + UNE_HEURE
    out = []
    for h in [x for x in heures_eval if x <= h_eval]:
        rang = {"heure": h}
        for serie in ("base", "stressee"):
            s = semaines[semaines["serie"] == serie]
            v = 0.0
            for w in s.itertuples(index=False):
                if w.t_in > h:
                    continue
                if (not w.provisoire and w.t_out <= h) or (w.provisoire and w.t_out == h):
                    v += w.net                      # semaine close avant h, ou ouverte et déjà valorisée à h
                    continue
                lw = lignes[(lignes["serie"] == serie) & (lignes["cohorte"] == w.cohorte) & (lignes["lundi"] == w.lundi)] if len(lignes) else lignes
                forces = lw.loc[lw["statut"] != "absent", "cout_sortie_force"].sum() if len(lw) else 0.0
                v += valoriser_semaine_ouverte(heures, fin, lw, h, p, serie == "stressee", w.cout - forces)
            rang[serie] = v
        out.append(rang)
    return pd.DataFrame(out)


def hebdomadaire(semaines: pd.DataFrame) -> pd.DataFrame:
    """Semaines civiles (lundi) : somme des semaines de cohortes closes dont la sortie tombe dans la semaine."""
    if semaines.empty:
        return pd.DataFrame(columns=["semaine", "base", "stressee", "cohortes"])
    s = semaines[~semaines["provisoire"]].copy()
    if s.empty:
        return pd.DataFrame(columns=["semaine", "base", "stressee", "cohortes"])
    jour = (s["t_out"] - UNE_HEURE).dt.normalize()
    s["semaine"] = jour - pd.to_timedelta(jour.dt.day_of_week, unit="D")
    t = s.pivot_table(index="semaine", columns="serie", values="net", aggfunc="sum").reset_index()
    n = s[s["serie"] == "base"].groupby("semaine").size().rename("cohortes")
    return t.merge(n, left_on="semaine", right_index=True, how="left")


# ---------------------------------------------------------------- journal en ajout seul

class JournalAjout:
    """Fichier CSV en ajout seul : une ligne écrite ne se réécrit pas. `verifier` signale toute ligne recalculée
    différente de celle déjà écrite (incident), sans jamais la corriger."""

    def __init__(self, chemin: Path, colonnes: list[str], cle: list[str]):
        self.chemin, self.colonnes, self.cle = Path(chemin), colonnes, cle

    def lire(self) -> pd.DataFrame:
        if not self.chemin.exists():
            return pd.DataFrame(columns=self.colonnes)
        return pd.read_csv(self.chemin, dtype=str, keep_default_na=False)

    def ajouter(self, lignes: list[dict], tolerance: float = 1e-10, comparer: list[str] | None = None) -> tuple[int, list[dict]]:
        """`comparer` : colonnes comparées pour une clé déjà écrite (toutes par défaut). Les métadonnées d'écriture
        (heure, drapeau « à l'heure ») ne se comparent pas : elles changent à chaque passage par construction."""
        deja = self.lire()
        connus = {tuple(r[k] for k in self.cle): r for r in deja.to_dict("records")}
        nouveaux, ecarts = [], []
        for l in lignes:
            l = {k: ("" if l.get(k) is None else str(l.get(k))) for k in self.colonnes}
            k = tuple(l[c] for c in self.cle)
            if k in connus:
                for c in (comparer or self.colonnes):
                    a, b = connus[k].get(c, ""), l[c]
                    if a != b and not _proches(a, b, tolerance):
                        ecarts.append({"cle": "|".join(k), "colonne": c, "ecrit": a, "recalcule": b})
                continue
            nouveaux.append(l)
            connus[k] = l
        if nouveaux:
            neuf = not self.chemin.exists()
            self.chemin.parent.mkdir(parents=True, exist_ok=True)
            with self.chemin.open("a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=self.colonnes)
                if neuf:
                    w.writeheader()
                w.writerows(nouveaux)
        return len(nouveaux), ecarts


def _proches(a: str, b: str, tol: float) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(a)))
    except ValueError:
        return False


def iso(t) -> str:
    return pd.Timestamp(t).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- écriture des sorties

def ecrire(res: Resultat, dossier: Path, maintenant: pd.Timestamp, capital_indicatif: float, notionnel: float) -> dict:
    """Sorties en ajout seul. Seuls les éléments définitifs s'écrivent (semaines closes, jours passés)."""
    dossier.mkdir(parents=True, exist_ok=True)
    incidents = []
    s = res.semaines
    closes = s[~s["provisoire"]] if len(s) else s
    js = JournalAjout(dossier / "semaines_cohortes.csv",
                      ["serie", "cohorte", "lundi", "t_in", "t_out", "manquee", "shorts", "longs", "univers", "pnl_prix", "financement", "cout", "net"],
                      ["serie", "cohorte", "lundi"])
    n_s, e_s = js.ajouter([{**r, "lundi": iso(r["lundi"]), "t_in": iso(r["t_in"]), "t_out": iso(r["t_out"])} for r in closes.to_dict("records")])
    l = res.lignes
    lc = l[~l["provisoire"]] if len(l) else l
    jl = JournalAjout(dossier / "lignes.csv",
                      ["serie", "cohorte", "lundi", "symbole", "sens", "statut", "entree", "sortie", "t_sortie", "pnl_prix", "financement", "cout_sortie_force"],
                      ["serie", "cohorte", "lundi", "symbole"])
    n_l, e_l = jl.ajouter([{**r, "lundi": iso(r["lundi"]), "t_sortie": iso(r["t_sortie"]) if isinstance(r.get("t_sortie"), pd.Timestamp) else r.get("t_sortie", "")}
                           for r in lc.to_dict("records")])
    jq = JournalAjout(dossier / "serie_quotidienne.csv", ["heure", "base", "stressee"], ["heure"])
    n_q, e_q = jq.ajouter([{"heure": iso(r["heure"]), "base": r["base"], "stressee": r["stressee"]} for r in res.quotidien.to_dict("records")])
    for nom, e in (("semaines", e_s), ("lignes", e_l), ("quotidien", e_q)):
        for x in e:
            incidents.append({"heure_utc": iso(maintenant), "type": f"ecart_recalcul_{nom}", "detail": json.dumps(x, ensure_ascii=False)})
    if incidents:
        JournalAjout(dossier / "incidents.csv", ["heure_utc", "type", "detail"], ["heure_utc", "type", "detail"]).ajouter(incidents)
    ouvertes = s[(s["provisoire"]) & (s["serie"] == "base")] if len(s) else s
    etat = {"heure_evaluation": iso(maintenant), "capital_indicatif_usdt": capital_indicatif, "notionnel_par_ligne": notionnel,
            "cohortes_ouvertes": [{"cohorte": int(r["cohorte"]), "date": iso(r["lundi"]), "shorts": r["shorts"].split(",") if r["shorts"] else [],
                                   "notionnel_short_usdt_indicatif": capital_indicatif * notionnel,
                                   "couverture_btc_usdt_indicative": capital_indicatif * notionnel * (len(r["shorts"].split(",")) if r["shorts"] else 0),
                                   "net_provisoire": r["net"]} for r in ouvertes.to_dict("records")],
            "cumul": res.quotidien.iloc[-1][["base", "stressee"]].to_dict() if len(res.quotidien) else {},
            "ajouts": {"semaines": n_s, "lignes": n_l, "jours": n_q}, "incidents_nouveaux": len(incidents)}
    (dossier / "etat.json").write_text(json.dumps(etat, indent=1, ensure_ascii=False, default=float))
    return etat


def ecrire_signaux(jours, pc: uc.ParamsCotation, p: m.Params, jour0, maintenant: pd.Timestamp, dossier: Path) -> dict:
    """Écrit, en ajout seul, le signal de chaque date de cohorte dont le jour est commencé (t ≤ maintenant), avec l'heure
    d'écriture. Un signal écrit après t + 1 h est marqué « en retard » : la date est manquée (ni rejouée ni remplacée)."""
    cible = uc.fabrique_cible(pc, DEBUT_DONNEES)
    j = JournalAjout(dossier / "signaux.csv", ["cohorte", "date", "ecrit_utc", "shorts", "a_l_heure"], ["cohorte", "date"])
    lignes = []
    for c in range(COHORTES):
        for t in dates_cohorte(jour0, c, maintenant + UNE_HEURE):
            if t > maintenant:
                continue
            poids, _ = cible(jours, t, p)
            shorts = ",".join(sorted(s for s, w in poids.items() if w < 0))
            lignes.append({"cohorte": c, "date": iso(t), "ecrit_utc": iso(maintenant), "shorts": shorts,
                           "a_l_heure": "oui" if maintenant <= t + UNE_HEURE else "non"})
    n, ecarts = j.ajouter(lignes, comparer=["shorts"])  # correctif du 14/11/2026 : seul le contenu du signal se compare
    if ecarts:
        JournalAjout(dossier / "incidents.csv", ["heure_utc", "type", "detail"], ["heure_utc", "type", "detail"]).ajouter(
            [{"heure_utc": iso(maintenant), "type": "signal_recalcule_different", "detail": json.dumps(e, ensure_ascii=False)} for e in ecarts])
    return {"ajoutes": n, "ecarts": len(ecarts)}


def lire_manquees(dossier: Path) -> dict:
    f = dossier / "signaux.csv"
    if not f.exists():
        return {}
    s = pd.read_csv(f, dtype=str)
    out: dict[int, set] = {}
    for r in s[s["a_l_heure"] != "oui"].itertuples(index=False):
        out.setdefault(int(r.cohorte), set()).add(pd.Timestamp(r.date.rstrip("Z")))
    return out


def journal_md(dossier: Path, etat: dict, signaux: dict, maintenant: pd.Timestamp, mode: str,
               h_eval: pd.Timestamp | None = None) -> None:
    """Une entrée par jour dans JOURNAL_COHORTES.md, en ajout seul, écrite au premier passage dont l'heure d'évaluation
    atteint 01:00 UTC du jour : l'entrée du jour sur le papier a alors eu lieu (correctif du 14/11/2026 : l'entrée
    s'écrivait à 00:05, avant l'exécution, et ne montrait pas la cohorte du jour)."""
    f = dossier / "JOURNAL_COHORTES.md"
    jour = maintenant.strftime("%Y-%m-%d")
    if h_eval is None or pd.Timestamp(h_eval) < maintenant.normalize() + UNE_HEURE:
        return
    if f.exists() and f"## {jour}" in f.read_text():
        return
    if not f.exists():
        f.write_text(f"# Journal du papier de STRAT-06-bis ({mode})\n\nEn ajout seul. Aucun ordre, `dry_run` permanent. Montants indicatifs, sans valeur de décision.\n")
    l = [f"\n## {jour} (écrit {iso(maintenant)})", "",
         f"Cumul à brut 100 % : base {etat['cumul'].get('base', 0):+.4%}, stressée {etat['cumul'].get('stressee', 0):+.4%}. "
         f"Incidents nouveaux : {etat['incidents_nouveaux']}.", ""]
    sig = dossier / "signaux.csv"
    if sig.exists():
        for r in pd.read_csv(sig, dtype=str, keep_default_na=False).itertuples(index=False):
            if r.date.startswith(jour):
                l.append(f"Signal du jour, cohorte {r.cohorte} : {r.shorts.replace(',', ', ') or 'aucun nom éligible, semaine vide'} "
                         f"(écrit {r.ecrit_utc}, à l'heure : {r.a_l_heure}).")
        l.append("")
    for c in etat["cohortes_ouvertes"]:
        l.append(f"- cohorte {c['cohorte']} ({c['date'][:10]}) : {', '.join(c['shorts']) or 'aucun nom'} ; "
                 f"{c['notionnel_short_usdt_indicatif']:.0f} USDT par short et {c['couverture_btc_usdt_indicative']:.0f} USDT de BTC (indicatif) ; "
                 f"net provisoire {c['net_provisoire']:+.4%}")
    with f.open("a") as x:
        x.write("\n".join(l) + "\n")


# ---------------------------------------------------------------- orchestration

def charger_config_bis() -> dict:
    c = json.loads(CONFIG_BIS.read_text())
    if c.get("statut") not in ("a_blanc", "figee"):
        raise Refus("config_bis06.json : statut inconnu.")
    return c


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tout", action="store_true")
    ap.add_argument("--sans-reseau", action="store_true")
    ap.add_argument("--donnees", default=str(SORTIES / "donnees"))
    ap.add_argument("--sorties", default=str(SORTIES), help="dossier des sorties, hors du code déployé")
    a = ap.parse_args(argv)
    import collecte_papier06 as cp
    cb = charger_config_bis()
    mode = "compte" if cb["statut"] == "figee" else "a_blanc"
    jour0 = pd.Timestamp(cb["jour_0"] if mode == "compte" else cb["jour_0_a_blanc"])
    dossier = Path(a.sorties) / mode
    p, pc = parametres()
    if cb.get("empreinte_config_v1") and empreinte_fichier(ICI / "config_strat06.json") != cb["empreinte_config_v1"]:
        raise Refus("config_strat06.json a changé depuis le gel du papier : refus.")
    col = cp.Collecteur(Path(a.donnees), http=None if a.sans_reseau else cp.Http())
    maintenant = pd.Timestamp(dt.datetime.now(dt.timezone.utc)).tz_localize(None).floor("min")
    if not a.sans_reseau:
        col.maj_jours(maintenant)
    jours = col.charger_jours()
    signaux = ecrire_signaux(jours, pc, p, jour0, maintenant, dossier)
    noms = cp.noms_a_suivre(dossier / "signaux.csv") | {"BTCUSDT"}
    if not a.sans_reseau:
        col.maj_heures(sorted(noms), jour0 - UN_JOUR, maintenant)
        col.maj_financement(sorted(noms), jour0 - UN_JOUR, maintenant)
    heures, fin = col.charger_heures(), col.charger_financement()
    if heures["open"].empty or maintenant + UNE_HEURE < jour0:
        (dossier / "battement.txt").parent.mkdir(parents=True, exist_ok=True)
        (dossier / "battement.txt").write_text(iso(maintenant) + "\n")
        print(json.dumps({"mode": mode, "jour_0": str(jour0.date()), "note": "avant le jour 0 ou aucune heure : collecte seule"}, ensure_ascii=False))
        return 0
    h_eval = heures["open"]["BTC"].dropna().index.max()
    res = calculer(jours, heures, fin, jour0, h_eval, p, pc, lire_manquees(dossier), NOTIONNEL, jours["volume"].index.max())
    etat = ecrire(res, dossier, h_eval, float(cb.get("capital_indicatif_usdt", 10000)), NOTIONNEL)
    etat["incidents_nouveaux"] += signaux["ecarts"]
    journal_md(dossier, etat, signaux, maintenant, mode, h_eval)
    (dossier / "battement.txt").write_text(iso(maintenant) + "\n")
    print(json.dumps({"mode": mode, "h_eval": iso(h_eval), **{k: etat[k] for k in ("cumul", "ajouts", "incidents_nouveaux")}}, ensure_ascii=False, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
