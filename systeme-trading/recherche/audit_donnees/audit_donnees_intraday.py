#!/usr/bin/env python3
"""Audit des données intra-journalières de data.binance.vision pour STRAT-07 et STRAT-08 (09/11/2026).

Ne télécharge AUCUN prix : liste seulement les archives (noms, tailles, dates) par l'API de liste du compartiment S3
public de data.binance.vision, puis estime le volume disque et la mémoire nécessaires. Aucun rendement lu, hors N.

Jeux audités :
  A. klines 1m des perpétuels USDT (mensuelles)          -> STRAT-08
  B. markPriceKlines 1m (mensuelles, échantillon)         -> STRAT-08 (stops sur prix de marque)
  C. liquidationSnapshot (journalières, perpétuels USDT)  -> STRAT-08 (existence et période)
  D. metrics (journalières : intérêt ouvert 5 min)         -> STRAT-08 (indicateur de cascade)
  E. aggTrades (mensuelles, échantillon)                  -> STRAT-08 (taille seulement)
  F. fundingRate (mensuelles)                             -> STRAT-07
  G. klines 1h et 1d au comptant (mensuelles)             -> STRAT-07 (jambe au comptant)
  H. machine : mémoire, disque, processeurs

Usage (sur le serveur, qui accède à data.binance.vision) :
  python3 -B audit_donnees_intraday.py --cache ~/cache_binance_vision [--echantillon 40] [--fils 8]
Sortie : recherche/audit_donnees/audit_<horodatage>.md et .json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LISTE = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
ICI = Path(__file__).resolve().parent
LIGNES_PAR_MOIS_1M = 43_800          # 30,4 jours x 1 440 minutes
OCTETS_LIGNE_RAM = {"float64": 8 * 6, "float32": 4 * 6}  # ouverture, haut, bas, clôture, volume, horodatage
COMPRESSION_CSV = 6.0                # rapport CSV / zip typique des klines [hypothèse, mesurée en E si possible]
APPELS = {"n": 0, "erreurs": 0}


def analyser_liste(xml_texte: str) -> tuple[list[dict], list[str], bool, str | None]:
    """Analyse une réponse ListBucketResult. Retourne (objets, préfixes communs, tronquée, marqueur suivant)."""
    racine = ET.fromstring(xml_texte)
    def t(e, nom):
        x = e.find(NS + nom)
        if x is None:
            x = e.find(nom)
        return None if x is None else x.text
    objets = []
    for c in list(racine.iter(NS + "Contents")) + list(racine.iter("Contents")):
        objets.append({"cle": t(c, "Key"), "taille": int(t(c, "Size") or 0), "modifie": t(c, "LastModified")})
    prefixes = [t(p, "Prefix") for p in list(racine.iter(NS + "CommonPrefixes")) + list(racine.iter("CommonPrefixes"))]
    tronquee = (t(racine, "IsTruncated") or "false").lower() == "true"
    suivant = t(racine, "NextMarker") or (objets[-1]["cle"] if objets else (prefixes[-1] if prefixes else None))
    return objets, prefixes, tronquee, suivant


def lister(prefixe: str, delimiteur: str = "/", essais: int = 3) -> tuple[list[dict], list[str]]:
    objets, prefixes, marqueur = [], [], None
    while True:
        q = {"delimiter": delimiteur, "prefix": prefixe}
        if marqueur:
            q["marker"] = marqueur
        url = LISTE + "?" + urllib.parse.urlencode(q)
        for k in range(essais):
            try:
                APPELS["n"] += 1
                with urllib.request.urlopen(url, timeout=60) as r:
                    texte = r.read().decode()
                break
            except Exception:  # noqa: BLE001
                APPELS["erreurs"] += 1
                if k == essais - 1:
                    raise
                time.sleep(2 * (k + 1))
        o, p, tronquee, marqueur = analyser_liste(texte)
        objets += o
        prefixes += p
        if not tronquee or not marqueur:
            return objets, prefixes


def symboles(prefixe: str) -> list[str]:
    _, p = lister(prefixe)
    return sorted(x.rstrip("/").split("/")[-1] for x in p)


def zips(objs: list[dict]) -> list[dict]:
    return [o for o in objs if o["cle"].endswith(".zip")]


def periode(objs: list[dict]) -> tuple[str | None, str | None]:
    d = sorted(m.group(1) for o in objs if (m := re.search(r"(\d{4}-\d{2}(?:-\d{2})?)\.zip$", o["cle"])))
    return (d[0], d[-1]) if d else (None, None)


def couvrir(prefixe_fmt: str, syms: list[str], fils: int) -> dict:
    """Pour chaque symbole : nombre d'archives, octets compressés, première et dernière période."""
    def un(s):
        try:
            o = zips(lister(prefixe_fmt.format(s=s))[0])
            a, b = periode(o)
            return s, {"archives": len(o), "octets": sum(x["taille"] for x in o), "debut": a, "fin": b}
        except Exception as e:  # noqa: BLE001
            return s, {"erreur": type(e).__name__}
    with ThreadPoolExecutor(fils) as ex:
        return dict(ex.map(un, syms))


def resume(cov: dict) -> dict:
    ok = {s: v for s, v in cov.items() if "erreur" not in v and v["archives"]}
    oct_ = sum(v["octets"] for v in ok.values())
    return {"symboles_interroges": len(cov), "symboles_avec_archives": len(ok), "erreurs": sum("erreur" in v for v in cov.values()),
            "archives": sum(v["archives"] for v in ok.values()), "octets_zip": oct_, "go_zip": oct_ / 1e9,
            "debut_min": min((v["debut"] for v in ok.values() if v["debut"]), default=None),
            "fin_max": max((v["fin"] for v in ok.values() if v["fin"]), default=None)}


def memoire_requise(mois_par_symbole: float, symboles_simultanes: int, dtype: str = "float32") -> float:
    """Go de RAM pour tenir en mémoire des klines 1m (6 colonnes), hors surcoût pandas (x2 de sécurité)."""
    return mois_par_symbole * LIGNES_PAR_MOIS_1M * OCTETS_LIGNE_RAM[dtype] * symboles_simultanes * 2 / 1e9


def machine(cache: Path | None) -> dict:
    out = {"processeurs": os.cpu_count()}
    try:
        mi = {l.split(":")[0]: int(l.split()[1]) for l in Path("/proc/meminfo").read_text().splitlines() if l.split()[1].isdigit()}
        out.update(ram_go=mi.get("MemTotal", 0) / 1e6, ram_libre_go=mi.get("MemAvailable", 0) / 1e6, swap_go=mi.get("SwapTotal", 0) / 1e6)
    except Exception:  # noqa: BLE001
        out["ram_go"] = None
    cible = cache if cache and cache.exists() else Path.home()
    du = shutil.disk_usage(cible)
    out.update(disque_total_go=du.total / 1e9, disque_libre_go=du.free / 1e9, chemin_disque=str(cible))
    if cache and cache.exists():
        out["cache_go"] = sum(f.stat().st_size for f in cache.rglob("*") if f.is_file()) / 1e9
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(Path.home() / "cache_binance_vision"))
    ap.add_argument("--echantillon", type=int, default=40, help="symboles tirés pour les jeux lourds (B, E) ; 0 = aucun")
    ap.add_argument("--fils", type=int, default=8)
    ap.add_argument("--max-symboles", type=int, default=0, help="limite du nombre de perpétuels (0 = tous)")
    a = ap.parse_args(argv)
    t0 = time.time()
    R = {"horodatage": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "source": LISTE}
    perps = [s for s in symboles("data/futures/um/monthly/klines/") if s.endswith("USDT")]
    if a.max_symboles:
        perps = perps[: a.max_symboles]
    R["perpetuels_usdt_listes"] = len(perps)
    # A. klines 1m
    covA = couvrir("data/futures/um/monthly/klines/{s}/1m/", perps, a.fils)
    R["A_klines_1m"] = resume(covA)
    mois = [v["archives"] for v in covA.values() if "erreur" not in v and v["archives"]]
    R["A_klines_1m"]["mois_moyen_par_symbole"] = sum(mois) / len(mois) if mois else 0
    R["A_klines_1m"]["go_csv_estime"] = R["A_klines_1m"]["go_zip"] * COMPRESSION_CSV
    # C. liquidationSnapshot : symboles et période
    liq_syms = symboles("data/futures/um/daily/liquidationSnapshot/")
    covC = couvrir("data/futures/um/daily/liquidationSnapshot/{s}/", liq_syms[: (a.max_symboles or None)], a.fils) if liq_syms else {}
    R["C_liquidationSnapshot"] = {"symboles": len(liq_syms), **(resume(covC) if covC else {}), "exemples": liq_syms[:10]}
    # D. metrics (intérêt ouvert 5 min)
    covD = couvrir("data/futures/um/daily/metrics/{s}/", perps, a.fils)
    R["D_metrics"] = resume(covD)
    # F. financement
    covF = couvrir("data/futures/um/monthly/fundingRate/{s}/", perps, a.fils)
    R["F_fundingRate"] = resume(covF)
    # G. comptant 1h et 1d
    spot = set(symboles("data/spot/monthly/klines/"))
    R["G_comptant"] = {"symboles_comptant": len(spot), "perpetuels_avec_paire_comptant_meme_nom": sum(s in spot for s in perps)}
    covG = couvrir("data/spot/monthly/klines/{s}/1h/", sorted(spot & set(perps)), a.fils)
    R["G_comptant"]["klines_1h"] = resume(covG)
    # B et E : échantillon (les plus grosses archives 1m, puis tirage régulier)
    ech = sorted((s for s in covA if "erreur" not in covA[s] and covA[s]["archives"]), key=lambda s: -covA[s]["octets"])
    ech = (ech[: a.echantillon // 2] + ech[a.echantillon // 2:: max(1, len(ech) // max(1, a.echantillon // 2))])[: a.echantillon] if a.echantillon else []
    if ech:
        covB = couvrir("data/futures/um/monthly/markPriceKlines/{s}/1m/", ech, a.fils)
        covE = couvrir("data/futures/um/monthly/aggTrades/{s}/", ech, a.fils)
        R["B_markPrice_1m_echantillon"] = resume(covB)
        R["E_aggTrades_echantillon"] = resume(covE)
        fa = sum(covA[s]["octets"] for s in ech)
        R["E_aggTrades_echantillon"]["rapport_aggTrades_sur_klines_1m"] = R["E_aggTrades_echantillon"]["octets_zip"] / fa if fa else None
        R["B_markPrice_1m_echantillon"]["rapport_marque_sur_contrat_1m"] = R["B_markPrice_1m_echantillon"]["octets_zip"] / fa if fa else None
    # H. machine et besoins
    R["H_machine"] = machine(Path(a.cache).expanduser())
    m_moy = R["A_klines_1m"]["mois_moyen_par_symbole"]
    R["besoins"] = {
        "ram_go_1_symbole_float32": memoire_requise(m_moy, 1),
        "ram_go_50_symboles_float32": memoire_requise(m_moy, 50),
        "ram_go_tous_symboles_float32": memoire_requise(m_moy, len(perps)),
        "disque_go_klines_1m_zip": R["A_klines_1m"]["go_zip"],
        "disque_go_klines_1m_et_marque_zip": R["A_klines_1m"]["go_zip"] * (1 + (R.get("B_markPrice_1m_echantillon", {}).get("rapport_marque_sur_contrat_1m") or 1)),
        "disque_go_aggTrades_estime": R["A_klines_1m"]["go_zip"] * (R.get("E_aggTrades_echantillon", {}).get("rapport_aggTrades_sur_klines_1m") or float("nan")),
    }
    R["appels"], R["duree_s"] = dict(APPELS), round(time.time() - t0, 1)
    out = ICI / f"audit_{R['horodatage']}"
    out.with_suffix(".json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
    out.with_suffix(".md").write_text(rapport(R))
    print(rapport(R))
    return 0


def rapport(R: dict) -> str:
    g = lambda d, k, f="{:.2f}": (f.format(d[k]) if isinstance(d.get(k), (int, float)) else str(d.get(k)))
    A, D, F, G, H, B = R["A_klines_1m"], R["D_metrics"], R["F_fundingRate"], R["G_comptant"], R["H_machine"], R["besoins"]
    C = R["C_liquidationSnapshot"]
    l = [f"# Audit des données intra-journalières — {R['horodatage']}", "",
         "Liste des archives seulement (noms, tailles, dates). Aucun prix téléchargé, aucun rendement lu, hors N.", "",
         "| Jeu | Usage | Symboles avec archives | Archives | Volume zip (Go) | Période |", "|---|---|---:|---:|---:|---|",
         f"| Klines 1m perpétuels | STRAT-08 | {A['symboles_avec_archives']} / {R['perpetuels_usdt_listes']} | {A['archives']} | {A['go_zip']:.1f} | {A['debut_min']} à {A['fin_max']} |",
         f"| liquidationSnapshot | STRAT-08 | {C.get('symboles_avec_archives', 0)} / {C['symboles']} | {C.get('archives', 0)} | {C.get('go_zip', 0):.2f} | {C.get('debut_min')} à {C.get('fin_max')} |",
         f"| metrics (intérêt ouvert 5 min) | STRAT-08 | {D['symboles_avec_archives']} | {D['archives']} | {D['go_zip']:.2f} | {D['debut_min']} à {D['fin_max']} |",
         f"| fundingRate | STRAT-07 | {F['symboles_avec_archives']} | {F['archives']} | {F['go_zip']:.3f} | {F['debut_min']} à {F['fin_max']} |",
         f"| Comptant 1h (paires de même nom) | STRAT-07 | {G['klines_1h']['symboles_avec_archives']} / {G['perpetuels_avec_paire_comptant_meme_nom']} | {G['klines_1h']['archives']} | {G['klines_1h']['go_zip']:.2f} | {G['klines_1h']['debut_min']} à {G['klines_1h']['fin_max']} |"]
    if "E_aggTrades_echantillon" in R:
        E, Bm = R["E_aggTrades_echantillon"], R["B_markPrice_1m_echantillon"]
        l += [f"| markPriceKlines 1m (échantillon) | STRAT-08 | {Bm['symboles_avec_archives']} | {Bm['archives']} | {Bm['go_zip']:.2f} | {Bm['debut_min']} à {Bm['fin_max']} |",
              f"| aggTrades (échantillon) | STRAT-08 | {E['symboles_avec_archives']} | {E['archives']} | {E['go_zip']:.1f} | {E['debut_min']} à {E['fin_max']} |"]
    l += ["", "## Machine et besoins", "",
          f"- Machine : {H.get('processeurs')} processeurs, RAM {g(H, 'ram_go')} Go (libre {g(H, 'ram_libre_go')} Go), swap {g(H, 'swap_go')} Go, disque libre {g(H, 'disque_libre_go')} Go sur {H.get('chemin_disque')}, cache actuel {g(H, 'cache_go')} Go.",
          f"- Klines 1m : {A['mois_moyen_par_symbole']:.1f} mois par symbole en moyenne, environ {A['go_csv_estime']:.0f} Go décompressés [rapport CSV/zip supposé de {COMPRESSION_CSV}].",
          f"- RAM pour tenir en mémoire les klines 1m (float32, marge x2) : 1 symbole {B['ram_go_1_symbole_float32']:.2f} Go ; 50 symboles {B['ram_go_50_symboles_float32']:.1f} Go ; tous {B['ram_go_tous_symboles_float32']:.0f} Go.",
          f"- Disque : klines 1m {B['disque_go_klines_1m_zip']:.1f} Go zip ; avec le prix de marque 1m {B['disque_go_klines_1m_et_marque_zip']:.1f} Go ; aggTrades estimés {B['disque_go_aggTrades_estime']:.0f} Go.",
          "", "## Lecture", "",
          "- Si la RAM d'un symbole tient largement, le moteur de STRAT-08 traite symbole par symbole (flux) : la mémoire n'est pas bloquante, seul le disque compte.",
          "- Si liquidationSnapshot ne couvre qu'une période courte ou peu de symboles, le critère T4 de STRAT-08 bascule sur l'indicateur indirect (chute du prix, volume, baisse de l'intérêt ouvert 5 min des metrics).",
          "- Les aggTrades ne sont pas nécessaires pour une entrée à la minute ; ils servent seulement à mesurer le glissement dans la minute.",
          f"", f"Appels à l'API de liste : {R['appels']['n']} (erreurs {R['appels']['erreurs']}), durée {R['duree_s']} s."]
    return "\n".join(l) + "\n"


if __name__ == "__main__":
    sys.exit(main())
