#!/usr/bin/env python3
"""Lance un essai préenregistré de STRAT-20261031-03 (E01 développement, E02 validation) et l'inscrit au registre.

Usage :
    python -B run_essai.py --essai E01 --cache CHEMIN_CACHE          # réseau data.binance.vision
    python -B run_essai.py --essai E01 --source-locale DOSSIER        # archives déjà copiées en local

Garde-fous (fiche § 1.8, `validation-edge`) :
- refus si `config_strat03.json` n'a pas `statut_regles = "figees"` ;
- refus si l'essai a déjà une date au registre (un essai ne se lance qu'une fois) ;
- refus de tout essai hors échantillon (E25, E26) : ce script ne lit jamais de donnée postérieure au bloc demandé ;
- verrou de bloc dans le chargeur : aucune ligne d'heure ≥ fin du bloc n'est lue.

Sorties : resultats/<essai>_metriques.json et .md, <essai>_semaines.csv, <essai>_lignes.csv, ligne du registre.
Résultat de recherche, aucun ordre.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees_binance as db  # noqa: E402
import moteur_xsmom as m  # noqa: E402

REGISTRE = ICI / "REGISTRE_ESSAIS.csv"
CONFIG = ICI / "config_strat03.json"
SORTIES = ICI / "resultats"
DISTANCE_R = 0.309  # stop de 30 % plus coûts doublés (fiche § 1.5)


class Refus(RuntimeError):
    pass


def horo() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def charger_config(chemin: Path = CONFIG) -> dict:
    return json.loads(chemin.read_text())


def params_depuis(config: dict) -> m.Params:
    ex = config["exclusions"]
    exclus = frozenset(ex["stablecoins_et_indexes"] + ex["indices"] + ex["memecoins_liste_close_2026-11-01"])
    return m.Params(**config["params_base"], exclus=exclus)


def controles(essai: str, config: dict, registre: Path = REGISTRE) -> dict:
    if config.get("statut_regles") != "figees":
        raise Refus("Règles D6 non figées (config_strat03.json, statut_regles). Aucun essai lancé.")
    bloc = next((b for b in config["blocs"].values() if b["essai"] == essai), None)
    if bloc is None:
        raise Refus(f"{essai} n'est pas un essai de ce script (seuls E01 et E02). Le hors échantillon reste fermé.")
    with registre.open() as f:
        ligne = next((r for r in csv.DictReader(f) if r["id_essai"] == essai), None)
    if ligne is None:
        raise Refus(f"{essai} absent du registre.")
    if ligne["date"].strip():
        raise Refus(f"{essai} déjà lancé le {ligne['date']}. Un essai ne se relance pas.")
    return bloc


def lundis_du_bloc(bloc: dict) -> list[pd.Timestamp]:
    lun = list(pd.date_range(bloc["premier_lundi"], bloc["dernier_lundi"], freq="W-MON"))
    return lun + [lun[-1] + pd.Timedelta(days=7)]  # le dernier sert d'heure de sortie


def bootstrap_blocs(x: np.ndarray, bloc: int, tirages: int, graine: int, niveau: float) -> list[float]:
    rng = np.random.default_rng(graine)
    n = len(x)
    nb = int(np.ceil(n / bloc))
    moy = np.empty(tirages)
    for i in range(tirages):
        debuts = rng.integers(0, n, nb)
        idx = (debuts[:, None] + np.arange(bloc)[None, :]).ravel()[:n] % n  # blocs circulaires
        moy[i] = x[idx].mean()
    a = (1 - niveau) / 2
    return [float(np.quantile(moy, a)), float(np.quantile(moy, 1 - a))]


def rendements_btc(heures: dict, lundis) -> pd.Series:
    o = heures["open"]["BTCUSDT"]
    r = {t: o.get(lundis[i + 1] + pd.Timedelta(hours=1)) / o.get(t + pd.Timedelta(hours=1)) - 1 for i, t in enumerate(lundis[:-1])}
    return pd.Series(r)


def metriques(sem: pd.DataFrame, lig: pd.DataFrame, btc: pd.Series, config: dict) -> dict:
    b = config["bootstrap"]
    r = sem["net"].to_numpy(float)
    st = m.statistiques(sem, btc.reindex(sem["lundi"]).reset_index(drop=True))
    x = btc.reindex(sem["lundi"]).to_numpy(float)
    xc = x - x.mean()
    beta = float((xc * (r - r.mean())).sum() / (xc * xc).sum())
    alpha = float(r.mean() - beta * x.mean())
    resid = r - beta * x
    cum = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], cum]))[1:] - cum)) if len(r) else 0.0
    actives = lig[lig["statut"] != "absent"]
    annees = sem.assign(annee=pd.to_datetime(sem["lundi"]).dt.year).groupby("annee")["net"].sum()
    gains_noms = actives.assign(g=actives["pnl_prix"] + actives["financement"]).groupby("symbole")["g"].sum()
    gain_total = float(sem["net"].sum())
    mois_ = sem.assign(mois=pd.to_datetime(sem["lundi"]).dt.to_period("M")).groupby("mois")["net"].sum()
    return {
        "semaines": int(len(r)), "semaines_vides": int((sem["longs"] == "").sum()),
        "lignes": int(len(actives)), "stops": int((actives["statut"] == "stop").sum()),
        "delistages": int((actives["statut"] == "delistage").sum()),
        "rendement_net_total_brut100": gain_total,
        "moyenne_hebdo_net": float(r.mean()),
        "ic90_moyenne_hebdo_blocs": bootstrap_blocs(r, b["bloc_semaines"], b["tirages"], b["graine"], b["niveau"]),
        "sharpe_net_annualise": st["sharpe_annualise"],
        "beta_btc_hebdo": beta,
        "alpha_hebdo_residuel": alpha,
        "alpha_annualise_residuel": alpha * 52,
        "sharpe_residuel_annualise": float(resid.mean() / resid.std(ddof=1) * np.sqrt(52)) if len(r) > 2 else float("nan"),
        "drawdown_max_brut100": dd,
        "esperance_par_ligne_R": float(gain_total / len(actives) / (DISTANCE_R / 6)) if len(actives) else float("nan"),
        "jambe_longue": float(sem["long"].sum()), "jambe_courte": float(sem["short"].sum()),
        "pnl_prix": float(sem["pnl_prix"].sum()), "financement": float(sem["financement"].sum()), "couts": float(sem["cout"].sum()),
        "par_annee": {str(k): float(v) for k, v in annees.items()},
        "annees_positives": int((annees > 0).sum()),
        "part_max_mois_du_gain": float(mois_.max() / gain_total) if gain_total > 0 else float("nan"),
        "part_max_nom_du_gain": float(gains_noms.max() / gain_total) if gain_total > 0 else float("nan"),
        "nom_max": str(gains_noms.idxmax()) if len(gains_noms) else None,
    }


def ecrire_registre(essai: str, mt: dict, horodatage: str, registre: Path = REGISTRE) -> None:
    lignes = list(csv.DictReader(registre.open()))
    champs = list(lignes[0].keys())
    for r in lignes:
        if r["id_essai"] == essai:
            r["date"] = horodatage
            r["trades"] = str(mt["lignes"])
            r["esperance_R"] = f"{mt['esperance_par_ligne_R']:.4f}"
            r["ic90_bas"], r["ic90_haut"] = (f"{v:.6f}" for v in mt["ic90_moyenne_hebdo_blocs"])
            r["dd_reel"] = f"{mt['drawdown_max_brut100']:.4f}"
            r["sharpe_net_brut100"] = f"{mt['sharpe_net_annualise']:.4f}"
            r["commentaire"] = (r["commentaire"] + " - IC90 sur la moyenne hebdo nette a brut 100 %").strip(" -")
    with registre.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)


def rapport_md(essai: str, mt: dict, meta: dict) -> str:
    p = lambda v: f"{100 * v:+.2f} %"
    ic = mt["ic90_moyenne_hebdo_blocs"]
    lignes = [
        f"# {essai} de STRAT-20261031-03 — métriques",
        "",
        f"Passage du {meta['horodatage']}. Bloc {meta['bloc']}, lundis {meta['premier_lundi']} à {meta['dernier_lundi']}. "
        f"Données data.binance.vision lues jusqu'à {meta['fin_donnees']} (verrou de bloc). Empreinte des données : `{meta['empreinte'][:16]}…`. "
        "Résultat de recherche, sans verdict : le verdict ne porte que sur E25 (fiche § 1.8).",
        "",
        "| Mesure | Valeur |", "|---|---:|",
        f"| Semaines, dont vides | {mt['semaines']}, {mt['semaines_vides']} |",
        f"| Lignes, stops, délistages | {mt['lignes']}, {mt['stops']}, {mt['delistages']} |",
        f"| Rendement net cumulé, brut 100 % | {p(mt['rendement_net_total_brut100'])} |",
        f"| Moyenne hebdomadaire nette | {p(mt['moyenne_hebdo_net'])} |",
        f"| IC 90 % par blocs de 4 semaines | [{p(ic[0])} ; {p(ic[1])}] |",
        f"| Sharpe net annualisé | {mt['sharpe_net_annualise']:.3f} |",
        f"| Bêta hebdomadaire sur BTC | {mt['beta_btc_hebdo']:.3f} |",
        f"| Rendement résiduel (alpha) annualisé | {p(mt['alpha_annualise_residuel'])} |",
        f"| Sharpe résiduel annualisé | {mt['sharpe_residuel_annualise']:.3f} |",
        f"| Drawdown maximal, brut 100 % | {p(-mt['drawdown_max_brut100'])} |",
        f"| Espérance par ligne (publiée, non éliminatoire) | {mt['esperance_par_ligne_R']:+.3f} R |",
        f"| Jambe longue, jambe courte | {p(mt['jambe_longue'])}, {p(mt['jambe_courte'])} |",
        f"| Prix, financement, coûts | {p(mt['pnl_prix'])}, {p(mt['financement'])}, {p(-mt['couts'])} |",
        f"| Années positives | {mt['annees_positives']} sur {len(mt['par_annee'])} |",
        f"| Part maximale d'un mois, d'un nom dans le gain | {mt['part_max_mois_du_gain']:.1%}, {mt['part_max_nom_du_gain']:.1%} ({mt['nom_max']}) |",
        "",
        "Par année : " + ", ".join(f"{k} {p(v)}" for k, v in mt["par_annee"].items()) + ".",
        "",
        f"Repli du prix de marque sur le contrat : {len(meta['qualite']['marque_repli_contrat'])} symboles. "
        f"Sans financement : {len(meta['qualite']['sans_financement'])}. Sans archive 1 h (lignes « absent ») : "
        f"{len(meta['qualite'].get('sans_archive_1h', []))}. Incidents réseau : {meta['incidents']}.",
    ]
    return "\n".join(lignes) + "\n"


def executer(essai: str, source, config: dict | None = None, registre: Path = REGISTRE, sorties: Path = SORTIES,
             symboles: list[str] | None = None) -> dict:
    config = config or charger_config()
    bloc = controles(essai, config, registre)
    p = params_depuis(config)
    lundis = lundis_du_bloc(bloc)
    fin = db.naif(bloc["fin_donnees_prix"])
    debut_jours = lundis[0] - pd.Timedelta(days=p.anciennete + p.fenetre_volume + 10)
    syms = symboles or db.symboles_usdt(source)
    jours = db.charger_jours(source, syms, debut_jours, fin)
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    jc, _, _, _ = m.couper_zombies(jours, {}, None)
    noms = set()
    for t in lundis[:-1]:
        noms |= set(m.univers(jc, t, p))
    noms = sorted(noms | {"BTCUSDT"})
    noms = [("BTCUSDT" if s == "BTC" else s) for s in noms]
    heures, fin_df, qualite = db.charger_heures(source, noms, lundis[0] - pd.Timedelta(days=1), fin)
    btc = rendements_btc(heures, lundis)
    ren = {"BTCUSDT": "BTC"}
    heures = {k: v.rename(columns=ren) for k, v in heures.items()}
    fin_df = fin_df.rename(columns=ren)
    # les jours ne gardent que les noms entrés au moins une fois dans l'univers et le facteur ; retirer les autres
    # ne change aucun classement. Un nom sans archive 1 h reste dans l'univers et sa ligne sort « absent ».
    utiles = ["BTC"] + [s for s in noms if s != "BTCUSDT"]
    jours = {k: v.reindex(columns=utiles) for k, v in jours.items()}
    heures = {k: v.reindex(columns=utiles) for k, v in heures.items()}
    qualite["sans_archive_1h"] = sorted(set(utiles) - set(heures["open"].dropna(axis=1, how="all").columns))
    sem, lig = m.backtest(jours, heures, fin_df, lundis, p, notionnel=1.0 / 6)
    mt = metriques(sem, lig, btc, config)
    h = horo()
    meta = {"horodatage": h, "essai": essai, "bloc": [k for k, b in config["blocs"].items() if b["essai"] == essai][0],
            "premier_lundi": bloc["premier_lundi"], "dernier_lundi": bloc["dernier_lundi"], "fin_donnees": bloc["fin_donnees_prix"],
            "empreinte": db.empreinte({**{f"j_{k}": v for k, v in jours.items()}, **{f"h_{k}": v for k, v in heures.items()}}),
            "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            "moteur_sha256": hashlib.sha256((ICI / "moteur_xsmom.py").read_bytes()).hexdigest(),
            "symboles_lus_1d": len(jours["close"].columns), "noms_univers": len(noms) - 1,
            "qualite": qualite, "incidents": len(getattr(source, "incidents", [])), "appels": getattr(source, "appels", None)}
    sorties.mkdir(exist_ok=True)
    (sorties / f"{essai}_metriques.json").write_text(json.dumps({"meta": meta, "metriques": mt}, ensure_ascii=False, indent=1, default=str))
    (sorties / f"{essai}_metriques.md").write_text(rapport_md(essai, mt, meta))
    sem.to_csv(sorties / f"{essai}_semaines.csv", index=False)
    lig.to_csv(sorties / f"{essai}_lignes.csv", index=False)
    ecrire_registre(essai, mt, h, registre)
    return {"meta": meta, "metriques": mt}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--essai", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cache")
    g.add_argument("--source-locale")
    a = ap.parse_args(argv)
    source = db.VisionLocale(Path(a.source_locale)) if a.source_locale else db.VisionHTTP(Path(a.cache))
    try:
        out = executer(a.essai, source)
    except Refus as e:
        print(f"REFUS : {e}", file=sys.stderr)
        return 2
    print(rapport_md(a.essai, out["metriques"], out["meta"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
