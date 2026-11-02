#!/usr/bin/env python3
"""Orchestrateur autonome de nuit pour STRAT-20261031-03.
1. Complete le prechargement des symboles manquants de l'univers (1h, marque, financement).
2. Lance l'essai E01 (developpement 2021-2024).
3. Verifie la porte eliminatoire : Rendement Net > 0.
4. Si valide, enchaine E02 (validation 2024-2025).
5. Commite et push chaque etape sur GitHub.
6. Redige le rapport de synthese final.
"""
import csv
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time
import pandas as pd

RACINE_STRAT = Path(__file__).resolve().parent
REPO = RACINE_STRAT.parents[2]
CACHE = Path("/root/cache_binance_vision")
PYTHON = sys.executable

sys.path.insert(0, str(RACINE_STRAT))
import donnees_binance as db
import moteur_xsmom as m
import run_essai as re

def log(msg: str):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ligne = f"[{now}] {msg}"
    print(ligne, flush=True)
    with open(RACINE_STRAT / "orchestrateur_nuit.log", "a") as f:
        f.write(ligne + "\n")

def git_commit_push(message: str):
    log(f"Git commit & push : {message}")
    try:
        subprocess.run(["git", "add", "."], cwd=REPO, check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", message], cwd=REPO, check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=True)
            log("Git push reussi !")
        else:
            log("Aucune modification a committer.")
    except Exception as e:
        log(f"Erreur Git : {e}")

def precharger_univers():
    log("=== Etape 1 : Verification et prechargement de l'univers E01 ===")
    config = re.charger_config()
    bloc = re.controles("E01", config, re.REGISTRE)
    p = re.params_depuis(config)
    lundis = re.lundis_du_bloc(bloc)
    fin = db.naif(bloc["fin_donnees_prix"])
    debut_jours = lundis[0] - pd.Timedelta(days=p.anciennete + p.fenetre_volume + 10)
    
    source_locale = db.VisionLocale(CACHE)
    syms = db.symboles_usdt(source_locale)
    log(f"Calcul de l'univers local sur {len(syms)} symboles...")
    comblement = {}
    jours = db.charger_jours(source_locale, syms, debut_jours, fin, journal=comblement)
    jours = {k: v.rename(columns={"BTCUSDT": "BTC"}) for k, v in jours.items()}
    jc, _, _, _ = m.couper_zombies(jours, {}, None)
    
    noms = set()
    for t in lundis[:-1]:
        noms |= set(m.univers(jc, t, p))
    noms = sorted(noms | {"BTCUSDT"})
    noms = [("BTCUSDT" if s == "BTC" else s) for s in noms]
    log(f"Univers E01 determine : {len(noms)} symboles au total.")
    
    p_1h = CACHE / "data" / "futures" / "um" / "monthly" / "klines"
    manquants = []
    for s in noms:
        d = p_1h / s / "1h"
        if not d.exists() or not any(d.glob("*.zip")):
            manquants.append(s)
            
    log(f"Symboles deja en cache 1h : {len(noms) - len(manquants)} / {len(noms)}")
    log(f"Symboles a telecharger : {len(manquants)} ({manquants})")
    
    if manquants:
        v_http = db.VisionHTTP(CACHE)
        debut_heures = lundis[0] - pd.Timedelta(days=1)
        for i, s in enumerate(manquants, 1):
            t0 = time.time()
            log(f"[{i}/{len(manquants)}] Telechargement 1h/marque/financement : {s}...")
            try:
                db.charger_heures(v_http, [s], debut_heures, fin)
                log(f"[{i}/{len(manquants)}] {s} termine en {time.time()-t0:.1f}s")
            except Exception as e:
                log(f"Erreur sur {s} : {e}")
    log("=== Prechargement de l'univers E01 termine avec succes ===")

def executer_e01():
    log("=== Etape 2 : Execution de l'essai E01 (Developpement) ===")
    cmd = [PYTHON, "-B", "run_essai.py", "--essai", "E01", "--cache", str(CACHE)]
    t0 = time.time()
    res = subprocess.run(cmd, cwd=RACINE_STRAT, capture_output=True, text=True)
    log(f"Fin de run_essai.py E01 en {time.time()-t0:.1f}s (code {res.returncode})")
    if res.returncode != 0:
        log(f"STDOUT: {res.stdout}")
        log(f"STDERR: {res.stderr}")
        raise RuntimeError("Echec de run_essai.py E01")
    
    git_commit_push("resultats: execution E01 STRAT-03 (nuit cloud)")
    
    p_json = RACINE_STRAT / "resultats" / "E01_metriques.json"
    data = json.loads(p_json.read_text())
    mt = data["metriques"]
    rdt_net = mt.get("rendement_net_total_brut100", 0.0)
    sharpe = mt.get("sharpe_net_annualise", 0.0)
    dd = mt.get("drawdown_max_brut100", 0.0)
    log(f"=== Verdict E01 : Rendement Net = {rdt_net:.4f} (Sharpe annualise = {sharpe:.2f}, Max DD = {dd:.2%}) ===")
    return rdt_net > 0, mt

def executer_e02():
    log("=== Etape 3 : Execution de l'essai E02 (Validation 2024-2025) ===")
    cmd = [PYTHON, "-B", "run_essai.py", "--essai", "E02", "--cache", str(CACHE)]
    t0 = time.time()
    res = subprocess.run(cmd, cwd=RACINE_STRAT, capture_output=True, text=True)
    log(f"Fin de run_essai.py E02 en {time.time()-t0:.1f}s (code {res.returncode})")
    if res.returncode != 0:
        log(f"STDOUT: {res.stdout}")
        log(f"STDERR: {res.stderr}")
        raise RuntimeError("Echec de run_essai.py E02")
    
    git_commit_push("resultats: execution E02 validation STRAT-03 (nuit cloud)")
    
    p_json = RACINE_STRAT / "resultats" / "E02_metriques.json"
    data = json.loads(p_json.read_text())
    mt = data["metriques"]
    rdt_net = mt.get("rendement_net_total_brut100", 0.0)
    sharpe = mt.get("sharpe_net_annualise", 0.0)
    log(f"=== Verdict E02 : Rendement Net Validation = {rdt_net:.4f} (Sharpe = {sharpe:.2f}) ===")
    return mt

def rediger_synthese(e01_valide: bool, mt_e01: dict, mt_e02: dict | None):
    log("=== Etape 4 : Redaction du rapport de synthese global ===")
    rapport = []
    rapport.append("# Synthèse Nocturne d'Exécution — STRAT-20261031-03")
    rapport.append(f"\n*Généré automatiquement le {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d à %H:%M:%S UTC')} sur l'instance cloud Scaleway.*\n")
    
    rapport.append("## 1. Porte 1 : Essai E01 (Développement 2021-01 à 2024-06)")
    rdt1 = mt_e01.get('rendement_net_total_brut100', 0.0)
    statut1 = "FRANCHIE (VALIDE)" if e01_valide else "ECHEC (REJET DE LA STRATEGIE)"
    rapport.append(f"- **Statut de la porte** : **{statut1}** (Seuil : Rendement net > 0)")
    rapport.append(f"- **Rendement net total (exposition 100%)** : `{rdt1:+.2%}`")
    rapport.append(f"- **Sharpe net annualisé** : `{mt_e01.get('sharpe_net_annualise', 0.0):.2f}`")
    rapport.append(f"- **Drawdown maximal** : `{mt_e01.get('drawdown_max_brut100', 0.0):.2%}`")
    rapport.append(f"- **Nombre de semaines actives** : {mt_e01.get('semaines', 0)}")
    rapport.append(f"- **Nombre de lignes traitées** : {mt_e01.get('lignes', 0)} (dont {mt_e01.get('stops', 0)} stops exécutés)")
    rapport.append(f"- **Détail par année** : {mt_e01.get('par_annee', {})}")
    
    if mt_e02 is not None:
        rapport.append("\n## 2. Porte 2 : Essai E02 (Validation 2024-07 à 2025-07)")
        rdt2 = mt_e02.get('rendement_net_total_brut100', 0.0)
        statut2 = "FRANCHIE (VALIDE)" if rdt2 > 0 else "ECHEC"
        rapport.append(f"- **Statut de la porte** : **{statut2}** (Seuil : Rendement net > 0)")
        rapport.append(f"- **Rendement net total (exposition 100%)** : `{rdt2:+.2%}`")
        rapport.append(f"- **Sharpe net annualisé** : `{mt_e02.get('sharpe_net_annualise', 0.0):.2f}`")
        rapport.append(f"- **Drawdown maximal** : `{mt_e02.get('drawdown_max_brut100', 0.0):.2%}`")
        rapport.append(f"- **Nombre de semaines actives** : {mt_e02.get('semaines', 0)}")
        rapport.append(f"- **Détail par année** : {mt_e02.get('par_annee', {})}")
    
    p_synthese = RACINE_STRAT / "SYNTHESE_PORTES_STRAT03.md"
    p_synthese.write_text("\n".join(rapport) + "\n")
    git_commit_push("rapport: synthese nocturne STRAT-03 (E01/E02)")
    log("=== Processus nocturne STRAT-03 termine avec succes ! ===")

def main():
    log("Demarrage de l'orchestrateur nocturne STRAT-03...")
    precharger_univers()
    e01_valide, mt_e01 = executer_e01()
    mt_e02 = None
    if e01_valide:
        log("E01 valide ! Enchainement immediat vers E02 (Validation)...")
        try:
            mt_e02 = executer_e02()
        except Exception as e:
            log(f"Erreur lors de E02 : {e}")
    else:
        log("E01 non valide (rendement <= 0). Selon le protocole, STRAT-03 est rejetee et E02 ne se lance pas.")
    rediger_synthese(e01_valide, mt_e01, mt_e02)

if __name__ == "__main__":
    main()
