#!/usr/bin/env python3
"""Rejeu hebdomadaire du papier de STRAT-06-bis sur les archives publiques (FICHE_STRAT-06-BIS.md § 4, point 2).

Une fois les archives de data.binance.vision publiées pour la période, on refait avec elles ce que le papier a fait avec
les données collectées en direct :
1. la sélection de chaque date de cohorte de la période, comparée au signal écrit (`signaux.csv`) ;
2. le prix d'entrée de chaque ligne close (ouverture de t + 1 h), comparé à celui des archives.
Tolérances lues dans `config_bis06.json` (proposées : sélection identique, prix d'entrée à 0,01 % près). Tout écart
est un incident consigné (`incidents.csv`, ajout seul) ; rien n'est corrigé rétroactivement.

Usage (serveur) : python3 -B rejeu_cohortes06.py --debut 2026-12-01 --fin 2026-12-08 --cache ~/cache_binance_vision
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "STRAT-20261031-03"))
sys.path.insert(0, str(ICI))
import paper_cohortes06 as pc6  # noqa: E402
import univers_cotations as uc  # noqa: E402

UNE_HEURE = pd.Timedelta(hours=1)


def prolonger_journalieres(source, wide: dict, syms, fin, nature: str) -> dict:
    """Prolonge chaque série par les archives journalières après sa dernière ligne mensuelle : le mois en cours n'a pas
    encore d'archive mensuelle, et `donnees_binance.combler` ne comble que l'intérieur d'une série (essai du 13/11/2026 :
    sans ce prolongement, novembre manquait et la médiane de volume de CTUSDT tombait sous 20 M USDT)."""
    import donnees_binance as db
    cles = {"1d": ("close", "volume"), "1h": ("open", "close"), "marque": ("mark_high", "mark_low")}[nature]
    src_cols = {"close": "close", "volume": "volume_usdt", "open": "open", "mark_high": "high", "mark_low": "low"}
    pas = pd.Timedelta(days=1) if nature == "1d" else pd.Timedelta(hours=1)
    ajouts = {k: {} for k in cles}
    for s in syms:
        ref = wide[cles[0]][s] if s in wide[cles[0]] else pd.Series(dtype=float)
        dernier = ref.last_valid_index()
        if dernier is None:
            continue
        for d in pd.date_range((dernier + pas).normalize(), pd.Timestamp(fin) - pd.Timedelta(days=1), freq="D"):
            z = source.lire(f"{db.RACINE_J}/" + db.CHEMINS_J[nature].format(s=s, d=d.date().isoformat()))
            if z is None:
                continue
            y = db.lire_klines(z)
            y = y[(y.index > dernier) & (y.index < db.naif(fin))]
            for k in cles:
                ajouts[k].setdefault(s, []).append(y[src_cols[k]])
    out = {}
    for k in cles:
        x = wide[k].copy()
        for s, morceaux in ajouts[k].items():
            serie = pd.concat(morceaux)
            idx = x.index.union(serie.index)
            x = x.reindex(idx)
            x.loc[serie.index, s] = serie.values
        out[k] = x.sort_index()
    return {**wide, **out}


def heures_journalieres(source, noms, debut, fin) -> dict:
    """Bougies 1 h du contrat et du prix de marque, lues dans les archives journalières seules. Le rejeu porte sur une
    semaine récente, dont l'archive mensuelle n'existe pas encore (`charger_heures` échoue alors, essai du 13/11/2026)."""
    import donnees_binance as db
    cols = {k: {} for k in ("open", "close", "mark_high", "mark_low")}
    for s in noms:
        for d in pd.date_range(pd.Timestamp(debut).normalize(), pd.Timestamp(fin) - pd.Timedelta(days=1), freq="D"):
            for nature, prises in (("1h", (("open", "open"), ("close", "close"))), ("marque", (("mark_high", "high"), ("mark_low", "low")))):
                z = source.lire(f"{db.RACINE_J}/" + db.CHEMINS_J[nature].format(s=s, d=d.date().isoformat()))
                if z is None:
                    continue
                y = db.lire_klines(z)
                for cle, src_col in prises:
                    cols[cle].setdefault(s, []).append(y[src_col])
    out = {}
    for k, par_sym in cols.items():
        out[k] = pd.DataFrame({s: pd.concat(v).sort_index()[lambda x: ~x.index.duplicated()] for s, v in par_sym.items()})
    return out


def symboles_jeunes(jours: dict, debut, marge_j: int = 61) -> list[str]:
    """Seuls les symboles cotés depuis moins de 61 jours au début de la période peuvent être éligibles (âge ≤ 60 j)."""
    v = jours["volume"].fillna(0) > 0
    prem = {s: v.index[v[s].to_numpy()][0] for s in v.columns if v[s].any()}
    return sorted(s for s, d in prem.items() if d >= pd.Timestamp(debut) - pd.Timedelta(days=marge_j))


def comparer_selections(jours_archives: dict, signaux: pd.DataFrame, p, pc, debut, fin) -> list[dict]:
    """Sélection recalculée sur les archives contre le signal écrit, pour chaque date de [debut, fin)."""
    cible = uc.fabrique_cible(pc, pc6.DEBUT_DONNEES)
    ecarts = []
    for r in signaux.itertuples(index=False):
        t = pd.Timestamp(str(r.date).rstrip("Z"))
        if not (pd.Timestamp(debut) <= t < pd.Timestamp(fin)):
            continue
        poids, _ = cible(jours_archives, t, p)
        a = ",".join(sorted(s for s, w in poids.items() if w < 0))
        ecrit = "" if pd.isna(r.shorts) else str(r.shorts)
        if a != ecrit:
            ecarts.append({"type": "rejeu_selection", "cohorte": int(r.cohorte), "date": pc6.iso(t), "papier": ecrit, "archives": a})
    return ecarts


def comparer_entrees(heures_archives: dict, lignes: pd.DataFrame, debut, fin, tolerance: float) -> list[dict]:
    """Prix d'entrée des lignes (ouverture de t + 1 h) contre l'ouverture de la même heure dans les archives."""
    ecarts = []
    o = heures_archives["open"]
    for r in lignes.itertuples(index=False):
        t = pd.Timestamp(str(r.lundi).rstrip("Z"))
        if not (pd.Timestamp(debut) <= t < pd.Timestamp(fin)) or r.statut == "absent" or r.serie != "base":
            continue
        t_in = t + UNE_HEURE
        a = o[r.symbole].get(t_in) if r.symbole in o else None
        if a is None or pd.isna(a):
            ecarts.append({"type": "rejeu_entree_absente", "cohorte": int(r.cohorte), "date": pc6.iso(t), "symbole": r.symbole})
            continue
        e = float(r.entree)
        if abs(e / float(a) - 1) > tolerance:
            ecarts.append({"type": "rejeu_entree", "cohorte": int(r.cohorte), "date": pc6.iso(t), "symbole": r.symbole,
                           "papier": e, "archives": float(a), "ecart_relatif": e / float(a) - 1})
    return ecarts


def main(argv=None) -> int:
    import donnees_binance as db
    import collecte_papier06 as cp
    ap = argparse.ArgumentParser()
    ap.add_argument("--debut", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--donnees", default=str(pc6.SORTIES / "donnees"))
    ap.add_argument("--sorties", default=str(pc6.SORTIES))
    a = ap.parse_args(argv)
    cb = pc6.charger_config_bis()
    mode = "compte" if cb["statut"] == "figee" else "a_blanc"
    dossier = Path(a.sorties) / mode
    p, pc = pc6.parametres()
    debut, fin = pd.Timestamp(a.debut), pd.Timestamp(a.fin)
    src = db.VisionHTTP(Path(a.cache).expanduser())
    collectes = cp.Collecteur(Path(a.donnees)).charger_jours()
    # Seuls les symboles cotés depuis moins de 61 jours peuvent être éligibles : on ne relit que ceux-là (et BTC, et l'actif
    # de base des contrats « 1000X »), sur 150 jours. La date de cotation collectée a été vérifiée égale à celle des
    # archives (essai du 13/11/2026). Relire tout l'univers depuis 2019 prenait 42 minutes.
    jeunes = symboles_jeunes(collectes, debut)
    import moteur_xsmom as m
    bases = {m.nom_de_base(s) + "USDT" for s in jeunes} - set(jeunes)
    syms = sorted(set(jeunes) | {s for s in bases if s in collectes["volume"].columns or s == "BTCUSDT"} | {"BTCUSDT"})
    syms = ["BTCUSDT" if s == "BTC" else s for s in syms]
    jours = db.charger_jours(src, syms, debut - pd.Timedelta(days=150), fin)
    jours = prolonger_journalieres(src, jours, syms, fin, "1d")
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    signaux = pd.read_csv(dossier / "signaux.csv", dtype=str, keep_default_na=False)
    ecarts = comparer_selections(jours, signaux, p, pc, debut, fin)
    lignes = pd.read_csv(dossier / "lignes.csv", dtype=str, keep_default_na=False) if (dossier / "lignes.csv").exists() else pd.DataFrame()
    if len(lignes):
        noms = sorted({"BTCUSDT" if s == "BTC" else s for s in lignes["symbole"]})
        heures = heures_journalieres(src, noms, debut, fin + pd.Timedelta(days=1))
        heures = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in heures.items()}
        ecarts += comparer_entrees(heures, lignes, debut, fin, float(cb["rejeu"]["tolerance_prix_entree_relative"]))
    h = pd.Timestamp(dt.datetime.now(dt.timezone.utc)).tz_localize(None).floor("s")
    if ecarts:
        pc6.JournalAjout(dossier / "incidents.csv", ["heure_utc", "type", "detail"], ["heure_utc", "type", "detail"]).ajouter(
            [{"heure_utc": pc6.iso(h), "type": e["type"], "detail": json.dumps(e, ensure_ascii=False)} for e in ecarts])
    rapport = (f"Rejeu du {pc6.iso(h)} sur [{debut.date()} ; {fin.date()}) : {len(signaux)} signaux écrits au total, "
               f"{len(ecarts)} écart(s) sur la période.\n")
    with (dossier / "REJEUX.md").open("a") as f:
        f.write(rapport)
    print(rapport + json.dumps(ecarts[:20], ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
