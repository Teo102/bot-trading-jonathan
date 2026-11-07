#!/usr/bin/env python3
"""Module de Paper Trading & Détection en Direct — STRAT-20261102-06
Dérive des perpétuels nouvellement cotés : short de jeunes cotations, couverture BTC.

Conforme à :
- FICHE_STRAT-20261102-06 § 3 et § 7 (Condition suspensive CS7)
- AUDIT_STRAT-06 § 11 (Consensus méthodologique v1 gelée + shadow v2)
- commun-trading § 7 et § 8 (Exécution publique, dry_run permanent, zéro clé privée)

Usage :
  python3 paper_trading_strat06.py --check-now
  python3 paper_trading_strat06.py --capital 10000 --risque 0.005
  python3 paper_trading_strat06.py --cron  # boucle attendant chaque lundi 00:05 UTC
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

# Chemins relatifs au module
STRAT_DIR = Path(__file__).resolve().parent
RESULTATS_PAPER_DIR = STRAT_DIR / "resultats" / "paper"
CONFIG_FILE = STRAT_DIR / "config_strat06.json"
EXCLUSIONS_FILE = STRAT_DIR / "exclusions_non_coin.json"
JOURNAL_PAPER_MD = RESULTATS_PAPER_DIR / "JOURNAL_PAPER.md"

BINANCE_FAPI_URL = "https://fapi.binance.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("STRAT-06-Paper")


@dataclass
class SignalLigne:
    symbole: str
    sens: str  # "SHORT" ou "LONG"
    age_jours: int
    date_cotation_utc: str
    volume_median_usdt: float
    prix_repere: float
    stop_loss_30pct: float | None
    notionnel_usdt: float
    quantite: float
    funding_rate_8h: float
    funding_rate_annualise_pct: float
    alerte_anti_funding_v2: bool
    tranche_age: str  # "7-13j", "14-27j", "28-60j"


@dataclass
class SignalHebdo:
    horodatage_utc: str
    capital_compte_usdt: float
    risque_par_ligne_pct: float
    exposition_brute_pct: float
    nombre_shorts: int
    lignes_shorts: list[SignalLigne]
    couverture_btc: SignalLigne | None
    shadow_v2_filtres: dict[str, Any]
    statut: str


def charger_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def charger_exclusions_non_coin() -> set[str]:
    if EXCLUSIONS_FILE.exists():
        try:
            data = json.loads(EXCLUSIONS_FILE.read_text(encoding="utf-8"))
            return set(data.get("symboles", []))
        except Exception as e:
            logger.warning("Impossible de lire %s: %s", EXCLUSIONS_FILE, e)
    return set()


def appeler_binance_fapi(path: str, params: dict | None = None) -> Any:
    url = f"{BINANCE_FAPI_URL}{path}"
    headers = {"User-Agent": "Antigravity-STRAT06-Paper/1.0"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Tentative %d/3 échouée pour %s: %s", attempt + 1, url, e)
            time.sleep(1 + attempt)
    raise RuntimeError(f"Échec répété appel Binance {url}")


def scanner_univers_live(config: dict) -> list[dict]:
    """Scanne tous les symboles de Binance Futures et applique les filtres statut, COIN et faux nouveaux."""
    exchange_info = appeler_binance_fapi("/fapi/v1/exchangeInfo")
    symbols = exchange_info.get("symbols", [])
    
    cfg_univ = config.get("univers", {})
    faux_nouveaux = set(cfg_univ.get("faux_nouveaux_noms", [
        "RENDERUSDT", "1000LUNCUSDT", "FRAXUSDT", "MANTRAUSDT", "DODOXUSDT"
    ]))
    exclusions_non_coin = charger_exclusions_non_coin()
    
    candidats = []
    now = dt.datetime.now(dt.timezone.utc)
    
    for s in symbols:
        sym = s.get("symbol", "")
        if s.get("quoteAsset") != "USDT" or s.get("status") != "TRADING":
            continue
        if s.get("contractType") not in ["PERPETUAL", "PREMARKET"]:
            continue
        if s.get("underlyingType", "COIN") != "COIN" or "TRADIFI" in str(s.get("contractType", "")):
            continue
        if sym in faux_nouveaux or sym in exclusions_non_coin or sym == "BTCUSDT":
            continue
        
        onboard_ms = s.get("onboardDate")
        if not onboard_ms:
            continue
        
        date_onboard = dt.datetime.fromtimestamp(onboard_ms / 1000, tz=dt.timezone.utc)
        age_jours = (now - date_onboard).days
        
        # Filtre d'âge figé STRAT-06 v1 (7 à 60 jours)
        age_min = cfg_univ.get("age_min_j", 7)
        age_max = cfg_univ.get("age_max_j", 60)
        if age_min <= age_jours <= age_max:
            candidats.append({
                "symbol": sym,
                "age_jours": age_jours,
                "date_onboard": date_onboard.isoformat(),
            })
            
    logger.info("Scan initial : %d symboles perpétuels âgés de %d à %d jours.", len(candidats), age_min, age_max)
    return candidats


def analyser_volumes_et_financement(candidats: list[dict], liquidite_min: float = 20e6) -> list[dict]:
    """Pour chaque candidat, télécharge les klines journalières récentes et le funding rate."""
    valides = []
    
    # Récupérer les funding rates actuels de tous les perpétuels en un seul appel
    premium_data = appeler_binance_fapi("/fapi/v1/premiumIndex")
    funding_map = {x["symbol"]: float(x.get("lastFundingRate", 0.0)) for x in premium_data if "symbol" in x}
    mark_prices = {x["symbol"]: float(x.get("markPrice", 0.0)) for x in premium_data if "symbol" in x}
    
    for c in candidats:
        sym = c["symbol"]
        try:
            # 35 dernières bougies journalières pour avoir la fenêtre de 30 jours jusqu'à veille
            klines = appeler_binance_fapi("/fapi/v1/klines", {"symbol": sym, "interval": "1d", "limit": 35})
            if len(klines) < 2:
                continue
            
            # Klines format : [openTime, open, high, low, close, volume, closeTime, quoteVolume, ...]
            # On exclut la dernière bougie en cours (d'aujourd'hui) pour éviter tout biais d'anticipation
            bougies_closes = klines[:-1]
            if not bougies_closes:
                continue
            
            # Volumes en USDT (quoteVolume, index 7)
            volumes_quote = [float(k[7]) for k in bougies_closes[-30:]]
            if not volumes_quote:
                continue
            
            mediane_vol = float(np.median(volumes_quote))
            veille_vol = volumes_quote[-1]
            
            # Filtre : vivant (volume veille > 0) et médiane >= 20M USDT
            if veille_vol > 0 and mediane_vol >= liquidite_min:
                prix_actuel = mark_prices.get(sym, float(bougies_closes[-1][4]))
                fr_8h = funding_map.get(sym, 0.0)
                fr_ann = fr_8h * 3 * 365 * 100  # annualisé en %
                
                age_j = c["age_jours"]
                if age_j <= 13:
                    tranche = "7-13j"
                elif age_j <= 27:
                    tranche = "14-27j"
                else:
                    tranche = "28-60j"
                
                valides.append({
                    "symbol": sym,
                    "age_jours": age_j,
                    "date_onboard": c["date_onboard"],
                    "volume_median_usdt": mediane_vol,
                    "prix_repere": prix_actuel,
                    "funding_rate_8h": fr_8h,
                    "funding_rate_ann_pct": fr_ann,
                    "alerte_anti_funding_v2": fr_ann < -50.0,
                    "tranche_age": tranche,
                })
        except Exception as e:
            logger.warning("Erreur analyse %s: %s", sym, e)
            
    # Tri par liquidité médiane décroissante
    valides.sort(key=lambda x: -x["volume_median_usdt"])
    return valides


def generer_signal(
    capital_compte: float = 10000.0,
    risque_par_ligne: float = 0.005,
    stop_pct: float = 0.30,
    noms_max: int = 6,
) -> SignalHebdo:
    """Génère le signal complet de rééquilibrage pour le portefeuille STRAT-06."""
    config = charger_config()
    cfg_univ = config.get("univers", {})
    liquidite_min = float(cfg_univ.get("liquidite_min_usdt", 20e6))
    
    maintenant_utc = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    candidats = scanner_univers_live(config)
    valides = analyser_volumes_et_financement(candidats, liquidite_min=liquidite_min)
    
    retenus = valides[:noms_max]
    n_shorts = len(retenus)
    
    # Prix de référence du Bitcoin pour la couverture
    try:
        btc_info = appeler_binance_fapi("/fapi/v1/premiumIndex", {"symbol": "BTCUSDT"})
        prix_btc = float(btc_info.get("markPrice", 0.0))
        fr_btc = float(btc_info.get("lastFundingRate", 0.0))
    except Exception:
        prix_btc = 100000.0
        fr_btc = 0.0001
        
    lignes_shorts: list[SignalLigne] = []
    
    if n_shorts == 0:
        logger.info("Aucun candidat éligible cette semaine : semaine blanche (0 position).")
        return SignalHebdo(
            horodatage_utc=maintenant_utc,
            capital_compte_usdt=capital_compte,
            risque_par_ligne_pct=risque_par_ligne,
            exposition_brute_pct=0.0,
            nombre_shorts=0,
            lignes_shorts=[],
            couverture_btc=None,
            shadow_v2_filtres={"anti_funding_exclus": [], "demi_tailles": []},
            statut="SEMAINE_BLANCHE",
        )
        
    # Calcul du notionnel par ligne :
    # Perte maximale acceptée au stop = Capital * risque_par_ligne
    # Stop = 30% -> Notionnel = Perte / 0.30
    perte_max_ligne = capital_compte * risque_par_ligne
    notionnel_par_short = perte_max_ligne / stop_pct
    
    notionnel_total_shorts = notionnel_par_short * n_shorts
    notionnel_couverture_btc = notionnel_total_shorts * 1.0  # ratio 1x dollar-neutral
    
    exposition_brute_totale = (notionnel_total_shorts + notionnel_couverture_btc) / capital_compte * 100
    
    anti_funding_exclus = []
    demi_tailles = []
    
    for r in retenus:
        prix = r["prix_repere"]
        stop_prix = prix * (1.0 + stop_pct)
        qty = notionnel_par_short / prix if prix > 0 else 0.0
        
        if r["alerte_anti_funding_v2"]:
            anti_funding_exclus.append(r["symbol"])
        if r["tranche_age"] in ["7-13j", "14-27j"]:
            demi_tailles.append(r["symbol"])
            
        lignes_shorts.append(
            SignalLigne(
                symbole=r["symbol"],
                sens="SHORT",
                age_jours=r["age_jours"],
                date_cotation_utc=r["date_onboard"],
                volume_median_usdt=r["volume_median_usdt"],
                prix_repere=prix,
                stop_loss_30pct=stop_prix,
                notionnel_usdt=notionnel_par_short,
                quantite=qty,
                funding_rate_8h=r["funding_rate_8h"],
                funding_rate_annualise_pct=r["funding_rate_ann_pct"],
                alerte_anti_funding_v2=r["alerte_anti_funding_v2"],
                tranche_age=r["tranche_age"],
            )
        )
        
    couverture_btc = SignalLigne(
        symbole="BTCUSDT",
        sens="LONG",
        age_jours=9999,
        date_cotation_utc="2019-09-08T17:55:00Z",
        volume_median_usdt=1e9,
        prix_repere=prix_btc,
        stop_loss_30pct=None,
        notionnel_usdt=notionnel_couverture_btc,
        quantite=notionnel_couverture_btc / prix_btc if prix_btc > 0 else 0.0,
        funding_rate_8h=fr_btc,
        funding_rate_annualise_pct=fr_btc * 3 * 365 * 100,
        alerte_anti_funding_v2=False,
        tranche_age="couverture",
    )
    
    return SignalHebdo(
        horodatage_utc=maintenant_utc,
        capital_compte_usdt=capital_compte,
        risque_par_ligne_pct=risque_par_ligne,
        exposition_brute_pct=exposition_brute_totale,
        nombre_shorts=n_shorts,
        lignes_shorts=lignes_shorts,
        couverture_btc=couverture_btc,
        shadow_v2_filtres={
            "anti_funding_exclus": anti_funding_exclus,
            "demi_tailles_recommandees": demi_tailles,
        },
        statut="SIGNAL_ACTIF",
    )


def enregistrer_rapport(signal: SignalHebdo) -> Path:
    """Enregistre le rapport JSON et met à jour le journal Markdown du paper trading."""
    RESULTATS_PAPER_DIR.mkdir(parents=True, exist_ok=True)
    
    horod = signal.horodatage_utc.replace(":", "").replace("-", "")
    fichier_json = RESULTATS_PAPER_DIR / f"signal_{horod}.json"
    
    data = asdict(signal)
    fichier_json.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("Signal JSON enregistré : %s", fichier_json)
    
    # Formatage de l'entrée Markdown pour JOURNAL_PAPER.md
    lignes_md = [
        f"\n## Signal Paper Trading — {signal.horodatage_utc}",
        f"- **Statut** : `{signal.statut}`",
        f"- **Capital référence** : {signal.capital_compte_usdt:,.2f} USDT | **Risque/ligne** : {signal.risque_par_ligne_pct*100:.2f}% | **Exposition brute** : {signal.exposition_brute_pct:.1f}%",
        f"- **Positions Short** : {signal.nombre_shorts} noms",
    ]
    
    if signal.lignes_shorts:
        lignes_md.append("\n| Symbole | Sens | Âge | Prix repère | Stop 30% | Notionnel (USDT) | Qté | Funding 8h | Tranche | Shadow v2 |")
        lignes_md.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|")
        for s in signal.lignes_shorts:
            v2_flag = "⚠️ Anti-Funding" if s.alerte_anti_funding_v2 else "Normal"
            lignes_md.append(
                f"| `{s.symbole}` | **{s.sens}** | {s.age_jours} j | {s.prix_repere:.4f} | {s.stop_loss_30pct:.4f} | {s.notionnel_usdt:.1f} | {s.quantite:.3f} | {s.funding_rate_annualise_pct:+.1f}%/an | {s.tranche_age} | {v2_flag} |"
            )
        if signal.couverture_btc:
            btc = signal.couverture_btc
            lignes_md.append(
                f"| `{btc.symbole}` | **{btc.sens}** | — | {btc.prix_repere:.1f} | — | {btc.notionnel_usdt:.1f} | {btc.quantite:.5f} | {btc.funding_rate_annualise_pct:+.1f}%/an | Couverture | 1x Dollar-Neutral |"
            )
    else:
        lignes_md.append("\n*Aucune ligne éligible cette semaine (semaine blanche).*")
        
    entree_md = "\n".join(lignes_md) + "\n"
    
    if not JOURNAL_PAPER_MD.exists():
        JOURNAL_PAPER_MD.write_text(
            "# Journal Paper Trading — STRAT-20261102-06\n\nSuivi hebdomadaire des signaux en direct (Binance Futures dry_run).\n",
            encoding="utf-8",
        )
    with JOURNAL_PAPER_MD.open("a", encoding="utf-8") as f:
        f.write(entree_md)
        
    return fichier_json


def afficher_recapitulatif(signal: SignalHebdo) -> None:
    """Affiche le signal sous une forme claire et lisible dans la console."""
    print("\n" + "=" * 80)
    print(f"📊 RAPPORT STRAT-06 PAPER TRADING — {signal.horodatage_utc}")
    print("=" * 80)
    print(f"Capital portefeuille : {signal.capital_compte_usdt:,.2f} USDT")
    print(f"Risque unitaire / ligne : {signal.risque_par_ligne_pct*100:.2f}% (Stop 30%)")
    print(f"Exposition totale brute : {signal.exposition_brute_pct:.1f}%")
    print(f"Statut : {signal.statut}")
    print("-" * 80)
    
    if not signal.lignes_shorts:
        print("⚠️  AUCUNE POSITION ÉLIGIBLE : Semaine blanche (zéro risque engagé).")
        print("=" * 80 + "\n")
        return
        
    print("🔻 POSITIONS SHORTS (Jeunes perpétuels Binance) :")
    for s in signal.lignes_shorts:
        alerte = " [⚠️ ANTI-FUNDING V2]" if s.alerte_anti_funding_v2 else ""
        print(f"  • {s.symbole:<12} | Âge: {s.age_jours:>2}j ({s.tranche_age}) | Prix: {s.prix_repere:>10.4f} | Stop: {s.stop_loss_30pct:>10.4f} (+30%) | Notionnel: {s.notionnel_usdt:>6.1f} USDT | Funding: {s.funding_rate_annualise_pct:>+6.1f}%/an{alerte}")
        
    if signal.couverture_btc:
        btc = signal.couverture_btc
        print("\n🛡️ COUVERTURE HEDGE DOLLAR-NEUTRAL :")
        print(f"  • {btc.symbole:<12} | Sens: LONG  | Prix: {btc.prix_repere:>10.1f} | Notionnel: {btc.notionnel_usdt:>6.1f} USDT | Qté: {btc.quantite:.5f} BTC")
        
    print("-" * 80)
    print("💡 PIPELINE SHADOW V2 (Pour comparaison d'audit) :")
    print(f"  • Noms exclus par filtre anti-funding (<-50%/an) : {signal.shadow_v2_filtres['anti_funding_exclus'] or 'Aucun'}")
    print(f"  • Noms recommandés en demi-taille (7-27j)        : {signal.shadow_v2_filtres['demi_tailles_recommandees'] or 'Aucun'}")
    print("=" * 80 + "\n")


def boucle_cron(capital: float, risque: float) -> None:
    """Boucle infinie exécutant le scan chaque lundi matin à 00:05:00 UTC."""
    logger.info("Démarrage du démon Paper Trading en attente du prochain lundi 00:05 UTC...")
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        # 0 = lundi
        if now.weekday() == 0 and now.hour == 0 and 5 <= now.minute <= 10:
            logger.info("Déclenchement du scan hebdomadaire automatique du lundi !")
            try:
                signal = generer_signal(capital_compte=capital, risque_par_ligne=risque)
                enregistrer_rapport(signal)
                afficher_recapitulatif(signal)
            except Exception as e:
                logger.error("Erreur exécution scan lundi: %s", e)
            # Attendre 1 heure pour ne pas re-déclencher immédiatement
            time.sleep(3600)
        else:
            time.sleep(30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper Trading automatique pour STRAT-20261102-06")
    parser.add_argument("--check-now", action="store_true", help="Exécute un scan complet immédiatement")
    parser.add_argument("--cron", action="store_true", help="Tourne en démon en attendant chaque lundi 00:05 UTC")
    parser.add_argument("--capital", type=float, default=10000.0, help="Capital du portefeuille en USDT (défaut: 10000)")
    parser.add_argument("--risque", type=float, default=0.005, help="Risque par ligne (défaut: 0.005 soit 0.50%%)")
    
    args = parser.parse_args()
    
    if args.cron:
        boucle_cron(capital=args.capital, risque=args.risque)
        return 0
        
    signal = generer_signal(capital_compte=args.capital, risque_par_ligne=args.risque)
    enregistrer_rapport(signal)
    afficher_recapitulatif(signal)
    return 0


if __name__ == "__main__":
    sys.exit(main())
