"""Variantes E03 à E18 de STRAT-20261102-06 (fiche § 6, registre au commit ebcb777, décision du 03/11/2026 sur le notionnel).

Lecture et contrôle de `variantes_strat06.json`, paramètres de chaque variante, calendrier (lundi ou jeudi), cible avec
le filtre anticipé de E16, découpe en sous-blocs. Sans réseau, sans clé, sans ordre.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import run_essai as r3  # noqa: E402
import univers_cotations as uc  # noqa: E402

VARIANTES = ICI / "variantes_strat06.json"
UN_JOUR = pd.Timedelta(days=1)
UNE_HEURE = pd.Timedelta(hours=1)
CLES_COTATION = {"age_min_j", "age_max_j", "liquidite_min", "fenetre_liquidite_max_j", "noms_max",
                 "multiple_couverture", "couverture", "inverse"}
CLES_MOTEUR = {"stop", "frais", "glissement", "glissement_stop"}
SPECIAL_BASE = {"calendrier": "lundi", "memecoins_exclus": False, "filtre_anticipe_delistage_j": 0}
CALENDRIERS = {"lundi": "W-MON", "jeudi": "W-THU"}
Refus = r3.Refus


def sha256_fichier(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def charger_variantes(chemin: Path = VARIANTES) -> dict:
    """Refuse si l'empreinte enregistrée (fichier .sha256 commité avec le JSON) ne correspond plus."""
    temoin = chemin.with_name(chemin.name + ".sha256")
    if not temoin.exists():
        raise Refus(f"{temoin.name} absent : empreinte des variantes non enregistrée.")
    if temoin.read_text().split()[0] != sha256_fichier(chemin):
        raise Refus("variantes_strat06.json modifié après l'enregistrement de son empreinte : refus.")
    return json.loads(chemin.read_text())


def ligne_registre(essai: str, registre: Path) -> dict:
    with registre.open() as f:
        ligne = next((r for r in csv.DictReader(f) if r["id_essai"] == essai), None)
    if ligne is None:
        raise Refus(f"{essai} absent du registre.")
    return ligne


def valider(essai: str, d: dict, registre: Path, pc_base: uc.ParamsCotation, p_base) -> dict:
    """Contrôles avant tout calcul. Retourne la définition de la variante."""
    if essai not in d.get("essais", {}):
        raise Refus(f"{essai} n'est pas une variante de développement et validation. Le hors échantillon reste fermé.")
    v = d["essais"][essai]
    inconnues = set(v) - {"variante", "commentaire_registre", "cotation", "moteur", "special"}
    inconnues |= set(v.get("cotation", {})) - CLES_COTATION
    inconnues |= set(v.get("moteur", {})) - CLES_MOTEUR
    inconnues |= set(v.get("special", {})) - set(SPECIAL_BASE)
    if inconnues:
        raise Refus(f"{essai} : clés inconnues {sorted(inconnues)}.")
    n = 0
    for k, x in v.get("cotation", {}).items():
        if getattr(pc_base, k) == x:
            raise Refus(f"{essai} : {k} = {x} égale la base, erreur de transcription probable.")
        n += 1
    for k, x in v.get("moteur", {}).items():
        if getattr(p_base, k) == x:
            raise Refus(f"{essai} : {k} = {x} égale la base, erreur de transcription probable.")
        n += 1
    for k, x in v.get("special", {}).items():
        if SPECIAL_BASE[k] == x:
            raise Refus(f"{essai} : {k} = {x} égale la base.")
        if k == "calendrier" and x not in CALENDRIERS:
            raise Refus(f"{essai} : calendrier {x} inconnu.")
        n += 1
    if n == 0:
        raise Refus(f"{essai} : aucune surcharge, la variante égale la base.")
    r = ligne_registre(essai, registre)
    if r["date"].strip():
        raise Refus(f"{essai} déjà lancé le {r['date']}. Un essai ne se relance pas.")
    if not r["bloc"].startswith("dev+val"):
        raise Refus(f"{essai} : bloc du registre « {r['bloc']} », pas dev+val.")
    if r["variante"] != v["variante"]:
        raise Refus(f"{essai} : libellé du registre « {r['variante']} » différent du JSON « {v['variante']} ».")
    return v


def params_variante(v: dict, pc_base: uc.ParamsCotation, p_base, memecoins) -> tuple:
    sp = {**SPECIAL_BASE, **v.get("special", {})}
    pc = replace(pc_base, **v.get("cotation", {}))
    if sp["memecoins_exclus"]:
        pc = replace(pc, exclus=pc.exclus | frozenset(memecoins))
    p = replace(p_base, **v.get("moteur", {}))
    return pc, p, sp


def verifier_couts_registre(essai: str, registre: Path, p) -> None:
    r = ligne_registre(essai, registre)
    if abs(float(r["frais"]) - p.frais) > 1e-12 or abs(float(r["glissement"]) - p.glissement) > 1e-12:
        raise Refus(f"{essai} : frais ou glissement du registre ({r['frais']}, {r['glissement']}) différents des paramètres.")


def notionnel(pc: uc.ParamsCotation) -> float:
    """Décision du 03/11/2026 : 1/(2 × noms_max). Base : 1/12."""
    return 1.0 / (2 * pc.noms_max)


def dates_bloc(bloc: dict, calendrier: str = "lundi") -> list[pd.Timestamp]:
    d = list(pd.date_range(bloc["premier_jour"], bloc["dernier_jour"], freq=CALENDRIERS[calendrier]))
    d.append(d[-1] + pd.Timedelta(days=7))  # la dernière date sert d'heure de sortie
    fin = r3.db.naif(bloc["fin_donnees_prix"])
    if d[-1] + UNE_HEURE > fin:
        raise Refus(f"Sortie {d[-1] + UNE_HEURE} au-delà du verrou de bloc {fin}.")
    return d


def a_exclure_e16(dernier: dict, t: pd.Timestamp, horizon_j: int, fin_donnees: pd.Timestamp) -> set:
    """Noms dont les données s'arrêtent définitivement entre t − 1 j et t + horizon. La fin due au verrou de bloc
    n'est pas un délistage. Filtre anticipé : il lit l'avenir, volontairement (E16 seulement)."""
    limite = fin_donnees.normalize() - UN_JOUR
    return {s for s, D in dernier.items()
            if D is not None and D < limite and t - UN_JOUR <= D <= t + pd.Timedelta(days=horizon_j)}


def fabrique_cible_variante(pc: uc.ParamsCotation, debut_donnees: pd.Timestamp, dernier: dict | None = None,
                            horizon_j: int = 0, fin_donnees: pd.Timestamp | None = None, journal: dict | None = None):
    """Même cible que uc.fabrique_cible ; si horizon_j > 0 (E16), les noms délistés sous horizon_j sortent de
    l'univers avant le classement."""
    cache = {}

    def f(jours, t, p):
        cle = id(jours["volume"])
        if cle not in cache:
            cache.clear()
            cache[cle] = uc.premiers_volumes(jours["volume"])
        pc_t = pc
        if horizon_j:
            ex = a_exclure_e16(dernier or {}, t, horizon_j, fin_donnees)
            if ex:
                pc_t = replace(pc, faux_nouveaux=pc.faux_nouveaux | frozenset(ex))
                if journal is not None:
                    journal[str(t)] = sorted(ex)
        noms = [s for s, _ in uc.eligibles(jours, t, pc_t, debut_donnees, cache[cle])]
        signe = 1 if pc.inverse else -1
        poids = {s: float(signe) for s in noms}
        if noms and pc.couverture:
            poids[pc.facteur] = -signe * pc.multiple_couverture * len(noms)
        return poids, len(noms)
    return f


def decouper(sem: pd.DataFrame, lig: pd.DataFrame, coupure: str) -> dict:
    c = pd.Timestamp(coupure)
    ds, dl = pd.to_datetime(sem["lundi"]), pd.to_datetime(lig["lundi"])
    return {"developpement": (sem[ds < c].reset_index(drop=True), lig[dl < c].reset_index(drop=True)),
            "validation": (sem[ds >= c].reset_index(drop=True), lig[dl >= c].reset_index(drop=True))}
