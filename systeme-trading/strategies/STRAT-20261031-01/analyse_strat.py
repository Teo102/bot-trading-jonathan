"""Analyse d'un export de backtest freqtrade pour validation-edge.

Usage
    python analyse_strat.py <export .zip ou .json> --essai E01 --start 20210101 --end 20240630
        [--risk 0.005] [--wallet 10000] [--sims 5000] [--seed 0] [--out DOSSIER] [--strategy NOM]
        [--n-trials N --sr-var V --sr-var-reevalue VR | --registry-json REGISTRE.json]
        [--data-dir DOSSIER] [--sims-blocs 50000] [--seed-blocs 20261101] [--bloc-trades 10] [--bloc-jours 30]

Agrégation du registre pour le Sharpe déflaté (aucune analyse d'export dans ce mode)
    python analyse_strat.py --agreger-registre DOSSIER_METRIQUES --registre-csv REGISTRE_ESSAIS.csv
        --registry-json SORTIE.json

Sorties
    Console et exports <out>/<essai>_metriques.json et <out>/<essai>_metriques.md.
    --out vaut par défaut resultats/ à côté du script. Sans --essai, l'identifiant vaut SANS-ID,
    pour ne jamais écraser par erreur les métriques d'un essai du registre.
    --start et --end valent par défaut le champ timerange de l'export.

Conventions
    Équité de référence d'un trade. Wallet + profits des autres trades déjà clos à son ouverture.
    Un trade compte comme clos si close_date <= open_date du trade étudié et s'il a été ouvert
    strictement avant. Il est donc exclu de sa propre référence, même à durée nulle.
    R nominal. profit_abs / (risk x équité de référence). C'est un risque prévu, pas le risque
    effectif du trade (arrondi de quantité, plafond de 20 % par actif).
    Série réalisée. Une observation par jour civil UTC de --start à --end inclus, jours sans
    clôture à 0. Équité à la clôture des trades, non réévaluée quotidiennement.
    Série réévaluée (base principale). Mêmes jours. Chaque position ouverte en fin de jour est
    comptée à sa valeur latente au prix de clôture 1d (sens x quantité x (clôture - entrée)), hors
    frais et financement latents. Le jour de clôture du trade, profit_abs remplace le latent. Les
    bougies viennent de --data-dir et rien n'est lu au-delà de --end.
    Sharpe. moyenne / écart-type (ddof=1) x racine(365), taux sans risque 0 %.
    Sortino. moyenne / racine(moyenne(min(r, 0)^2)) sur toutes les observations x racine(365).
    Calmar. rendement annualisé composé (base 365 jours) / drawdown maximal.
    Semestres. Semestres civils de la plage, trades affectés à la date de clôture. La colonne
    réévaluée donne la variation de l'équité réévaluée sur le semestre.
    IC 90 % iid. Bootstrap historique des trades (--sims, --seed), conservé pour comparaison.
    IC 90 % par blocs. Bootstrap par blocs circulaires de --bloc-trades trades consécutifs dans
    l'ordre d'ouverture (--sims-blocs, --seed-blocs). Par épisodes et par mois. Tirage de grappes
    entières, estimateur somme des R sur nombre de trades. Un épisode est une chaîne de trades qui
    se chevauchent. Ces grappes sont peu nombreuses, donc ces deux bornes restent indicatives.
    Monte Carlo par blocs temporels. Blocs circulaires de --bloc-jours jours des rendements
    quotidiens réévalués (réalisés si les bougies manquent). Le drawdown 95e centile par
    permutation des trades (dd_95) reste affiché à titre de comparaison.
    Espérance hors force_exit. Retire les sorties forcées par la fin de plage, le R restant calculé
    sur la même équité de référence.
    DSR. Bailey et López de Prado (2014). --sr-var et les Sharpe du registre sont quotidiens et
    NON annualisés. Une variance annualisée se divise d'abord par 365. Le DSR principal porte sur
    la série réévaluée avec une V réévaluée. Le DSR sur série réalisée reste affiché en second.

Format du registre (--registry-json)
    {"essais": [{"id": "E01", "statut": "exporte", "sharpe_quotidien": 0.03,
                 "sharpe_quotidien_reevalue": 0.02, "timerange": "..."},
                {"id": "E12", "statut": "abandonne", "sharpe_quotidien": null}],
     "n_essais_declares": 12}
    N = max(nombre d'entrées, n_essais_declares si présent). V = variance transversale (ddof=1)
    des Sharpe connus, calculée à part pour chaque série.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import shlex
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

JOURS_PAR_AN = 365
DEFAULT_OUT = Path(__file__).resolve().parent / "resultats"
DEFAULT_DATA = Path(__file__).resolve().parent / "user_data" / "data" / "binance" / "futures"
SIMS_BLOCS = 50000
SEED_BLOCS = 20261101
BLOC_TRADES = 10
BLOC_JOURS = 30
TAILLE_LOT = 2000
JOURS_MIN_SHARPE_SEMESTRE = 90
LIBELLE_REALISE = "équité réalisée à la clôture des trades, sans les pertes latentes"
LIBELLE_REEVALUE = ("équité réévaluée chaque jour au prix de clôture 1d, "
                    "hors frais et financement latents")

NOTES_METHODE = [
    "Deux bases sont affichées. La base réalisée ne voit pas les pertes latentes des positions "
    "ouvertes, ce qui regroupe le P&L le jour de la clôture, flatte le Sortino et peut "
    "sous-estimer le drawdown. La base réévaluée, retenue comme principale, ajoute le latent au "
    "prix de clôture 1d, hors frais et financement latents. Elle ignore aussi les extrêmes "
    "intrajournaliers.",
    "Le R est nominal. Il rapporte le profit au risque prévu sur l'équité de référence, "
    "pas au risque effectif du trade.",
    "L'intervalle iid et le drawdown par permutation traitent les trades comme indépendants et "
    "successifs. Les positions se chevauchent et les actifs sont corrélés. Ces deux chiffres "
    "sont donc probablement trop optimistes et restent affichés pour comparaison. L'intervalle "
    "par blocs et le Monte Carlo par blocs temporels gardent une partie de la dépendance, sans "
    "capter l'instabilité due à l'ordre de la whitelist ni à l'attribution des places.",
    "Les espérances avec coûts doublés sont une approximation. Elles retirent une seconde fois "
    "les coûts à trajectoire inchangée, sans recalculer tailles, stops ni composition. Le "
    "glissement n'y figure que s'il est inclus dans le paramètre de frais. Seul un nouveau "
    "backtest avec --fee doublé (E09, E11) mesure réellement ce stress.",
    "Le DSR suppose des essais indépendants et comparables. Des variantes voisines ne sont pas "
    "indépendantes, et des essais sur des périodes différentes mesurent aussi un effet de régime "
    "dans V[SR]. N et V sont à lire avec cette limite. Sur la série réalisée, le regroupement du "
    "P&L à la clôture crée une forte asymétrie (g3) qui écrase le dénominateur du PSR. Le DSR "
    "réalisé n'est donc pas comparable d'un essai à l'autre, et le DSR réévalué sert de calcul "
    "principal.",
]


# ---------------------------------------------------------------------------- lecture de l'export
def _is_results(obj):
    """Vrai pour un JSON de résultats : 'strategy' est un dict de stratégies contenant 'trades'.
    Le _config.json du zip a aussi une clé 'strategy', mais c'est une chaîne."""
    strat = obj.get("strategy") if isinstance(obj, dict) else None
    return isinstance(strat, dict) and bool(strat) and all(
        isinstance(v, dict) and "trades" in v for v in strat.values())


def load_export(path):
    """Lit un export .zip (freqtrade 2026.10) ou .json. Aucune extraction sur disque.
    Renvoie (résultats, membre, sha256 du fichier analysé, config du zip ou None)."""
    path = Path(path)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not zipfile.is_zipfile(path):
        data = json.loads(raw)
        if not _is_results(data):
            raise ValueError(f"{path.name} n'est pas un JSON de résultats freqtrade.")
        return data, path.name, sha, None
    data, member, config = None, None, None
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json"):
                continue
            obj = json.loads(z.read(name))
            if _is_results(obj):
                data, member = obj, name
            elif name.endswith("_config.json"):
                config = obj
    if data is None:
        raise ValueError(f"Aucun JSON de résultats dans {path.name}.")
    return data, member, sha, config


def select_strategy(data, name=None):
    strategies = data["strategy"]
    if name:
        if name not in strategies:
            raise ValueError(f"Stratégie {name} absente de l'export : {sorted(strategies)}.")
        return name, strategies[name]
    if len(strategies) > 1:
        raise ValueError(f"Plusieurs stratégies dans l'export, préciser --strategy : {sorted(strategies)}.")
    return next(iter(strategies.items()))


def find_export_version(data, strat, config):
    """L'export de freqtrade 2026.10 ne contient pas la version (vérifié le 31/10/2026)."""
    for src in (strat, data.get("metadata") or {}, config or {}):
        for key in ("freqtrade_version", "version"):
            if isinstance(src, dict) and src.get(key):
                return str(src[key])
    return None


def find_env_version():
    try:
        return importlib.metadata.version("freqtrade")
    except importlib.metadata.PackageNotFoundError:
        return None


def prepare_trades(raw_trades):
    """DataFrame trié par ouverture. fee_abs est le coût réel en frais du trade.
    funding_fees (par trade, positif = reçu, négatif = payé) est déjà inclus dans profit_abs."""
    rows = []
    for t in raw_trades:
        fee_open = t.get("fee_open") or 0.0
        fee_close = t.get("fee_close") or 0.0
        amount, open_rate, close_rate = t.get("amount"), t.get("open_rate"), t.get("close_rate")
        if amount is not None and open_rate is not None and close_rate is not None:
            fee_abs = abs(amount) * (fee_open * open_rate + fee_close * close_rate)
        else:
            fee_abs = (fee_open + fee_close) * t["stake_amount"] * (t.get("leverage") or 1.0)
        rows.append({
            "pair": t.get("pair", ""),
            "open_date": t["open_date"],
            "close_date": t["close_date"],
            "is_short": bool(t.get("is_short")),
            "profit_abs": float(t["profit_abs"]),
            "fee_abs": float(fee_abs),
            "funding_fees": float(t["funding_fees"]) if t.get("funding_fees") is not None else np.nan,
            "exit_reason": t.get("exit_reason"),
            "is_open": bool(t.get("is_open")),
            "amount": float(amount) if amount is not None else np.nan,
            "open_rate": float(open_rate) if open_rate is not None else np.nan,
        })
    cols = ["pair", "open_date", "close_date", "is_short", "profit_abs", "fee_abs",
            "funding_fees", "exit_reason", "is_open", "amount", "open_rate"]
    df = pd.DataFrame(rows, columns=cols)
    df["open_date"] = pd.to_datetime(df["open_date"], utc=True)
    df["close_date"] = pd.to_datetime(df["close_date"], utc=True)
    df["profit_abs"] = df["profit_abs"].astype(float)
    df["fee_abs"] = df["fee_abs"].astype(float)
    df["funding_fees"] = df["funding_fees"].astype(float)
    df["amount"] = df["amount"].astype(float)
    df["open_rate"] = df["open_rate"].astype(float)
    df["is_short"] = df["is_short"].astype(bool)
    return df.sort_values(["open_date", "close_date", "pair"], kind="stable").reset_index(drop=True)


# ------------------------------------------------------------------------------------- calculs R
def reference_equity(df, wallet):
    """Wallet + profits des trades déjà clos à l'ouverture de chaque trade (voir l'en-tête)."""
    opens = df["open_date"].to_numpy()
    closes = df["close_date"].to_numpy()
    profits = df["profit_abs"].to_numpy()
    ref = np.empty(len(df))
    for i, opened in enumerate(opens):
        ref[i] = wallet + profits[(closes <= opened) & (opens < opened)].sum()
    if (ref <= 0).any():
        raise ValueError("Équité de référence négative ou nulle : R non défini.")
    return ref


def r_multiples(df, wallet, risk):
    ref = reference_equity(df, wallet)
    risk_amt = risk * ref
    r = df["profit_abs"].to_numpy() / risk_amt
    fee_r = df["fee_abs"].to_numpy() / risk_amt
    paid = np.clip(-df["funding_fees"].fillna(0.0).to_numpy(), 0.0, None)
    return r, fee_r, paid / risk_amt, ref


def max_dd_r(rs, risk):
    e = np.cumprod(1 + risk * rs)
    e = np.r_[1.0, e]
    pk = np.maximum.accumulate(e)
    return float(((pk - e) / pk).max())


def trade_statistics(df, wallet, risk, sims, seed):
    """Statistiques par trade, conservées de l'ancien script. Bootstrap puis permutations."""
    n = len(df)
    out = {"trades": n, "longs": int((~df["is_short"]).sum()), "shorts": int(df["is_short"].sum()),
           "capital_final": float(wallet + df["profit_abs"].sum())}
    if n == 0:
        out.update(dict.fromkeys([
            "taux_reussite", "gain_moyen_R", "perte_moyenne_R", "esperance_R", "ic90_bas", "ic90_haut",
            "esperance_frais_doubles_R_approx", "esperance_frais_et_financement_doubles_R_approx",
            "dd_95", "dd_sequentiel_R", "part_meilleur_trade_R", "part_meilleur_trade_pnl",
            "r_min", "r_max", "esperance_hors_force_exit_R", "pnl_force_exit"]))
        out["trades_force_exit"] = 0
        return out
    r, fee_r, paid_r, _ = r_multiples(df, wallet, risk)
    rng = np.random.default_rng(seed)
    boot = rng.choice(r, (sims, n)).mean(1)
    lo, hi = np.percentile(boot, [5, 95])
    dd_mc = np.array([max_dd_r(rng.permutation(r), risk) for _ in range(sims)])
    by_close = np.argsort(df["close_date"].to_numpy(), kind="stable")
    wins, losses = r[r > 0], r[r <= 0]
    pnl = df["profit_abs"].to_numpy()
    forced = (df["exit_reason"] == "force_exit").to_numpy()
    out.update({
        "taux_reussite": float(len(wins) / n),
        "gain_moyen_R": float(wins.mean()) if len(wins) else 0.0,
        "perte_moyenne_R": float(losses.mean()) if len(losses) else 0.0,
        "esperance_R": float(r.mean()),
        "esperance_hors_force_exit_R": float(r[~forced].mean()) if (~forced).any() else None,
        "trades_force_exit": int(forced.sum()),
        "pnl_force_exit": float(pnl[forced].sum()),
        "ic90_bas": float(lo),
        "ic90_haut": float(hi),
        "esperance_frais_doubles_R_approx": float((r - fee_r).mean()),
        "esperance_frais_et_financement_doubles_R_approx": float((r - fee_r - paid_r).mean()),
        "dd_95": float(np.percentile(dd_mc, 95)),
        "dd_sequentiel_R": max_dd_r(r[by_close], risk),
        "part_meilleur_trade_R": float(r.max() / r.sum()) if r.sum() > 0 else None,
        "part_meilleur_trade_pnl": float(pnl.max() / pnl.sum()) if pnl.sum() > 0 else None,
        "r_min": float(r.min()),
        "r_max": float(r.max()),
    })
    return out


def circular_block_indices(rng, n, block, sims):
    """Indices d'un bootstrap par blocs circulaires, n observations par tirage. La forme circulaire
    donne le même poids à chaque observation, contrairement aux blocs mobiles sans repli."""
    block = max(1, min(block, n))
    count = n // block + (1 if n % block else 0)
    starts = rng.integers(0, n, (sims, count))
    idx = (starts[:, :, None] + np.arange(block)) % n
    return idx.reshape(sims, -1)[:, :n]


def _by_batches(sims, size=TAILLE_LOT):
    done = 0
    while done < sims:
        step = min(size, sims - done)
        yield step
        done += step


def block_ci(values, block, sims, seed):
    """IC 90 % de la moyenne par blocs circulaires."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.concatenate([values[circular_block_indices(rng, len(values), block, step)].mean(1)
                            for step in _by_batches(sims)])
    lo, hi = np.percentile(means, [5, 95])
    return float(lo), float(hi)


def iid_ci(values, sims, seed):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.concatenate([values[rng.integers(0, len(values), (step, len(values)))].mean(1)
                            for step in _by_batches(sims)])
    lo, hi = np.percentile(means, [5, 95])
    return float(lo), float(hi)


def cluster_ci(values, labels, sims, seed):
    """IC 90 % par tirage de grappes entières, estimateur somme des R sur nombre de trades."""
    values, labels = np.asarray(values, dtype=float), np.asarray(labels)
    uniq = np.unique(labels)
    sums = np.array([values[labels == u].sum() for u in uniq])
    counts = np.array([(labels == u).sum() for u in uniq])
    rng = np.random.default_rng(seed)
    stats_ = []
    for step in _by_batches(sims):
        pick = rng.integers(0, len(uniq), (step, len(uniq)))
        stats_.append(sums[pick].sum(1) / counts[pick].sum(1))
    lo, hi = np.percentile(np.concatenate(stats_), [5, 95])
    return float(lo), float(hi), len(uniq)


def episode_labels(df):
    """Numéro d'épisode par trade, dans l'ordre d'ouverture. Un trade ouvert à ou après la fin de
    tous les précédents commence un nouvel épisode."""
    labels, current, end = [], -1, None
    for opened, closed in zip(df["open_date"], df["close_date"]):
        if end is None or opened >= end:
            current += 1
            end = closed
        else:
            end = max(end, closed)
        labels.append(current)
    return np.array(labels)


def dependence_intervals(df, wallet, risk, sims, seed, block):
    """Intervalles à 90 % de l'espérance, avec une graine dérivée par méthode. Ajouter une méthode
    ne change donc pas les bornes des autres."""
    base = {"tirages": sims, "graine": seed, "longueur_bloc_trades": block}
    if len(df) < 2:
        return {**base, "statut": "non_calculable", "motif": "Moins de 2 trades.",
                "iid": None, "blocs": None, "episodes": None, "mois": None}
    r = r_multiples(df, wallet, risk)[0]
    lo_i, hi_i = iid_ci(r, sims, [seed, 0])
    lo_b, hi_b = block_ci(r, block, sims, [seed, 1])
    lo_e, hi_e, n_e = cluster_ci(r, episode_labels(df), sims, [seed, 2])
    lo_m, hi_m, n_m = cluster_ci(r, df["open_date"].dt.strftime("%Y-%m").to_numpy(), sims, [seed, 3])
    return {**base, "statut": "calcule", "motif": None,
            "iid": {"bas": lo_i, "haut": hi_i},
            "blocs": {"bas": lo_b, "haut": hi_b},
            "episodes": {"bas": lo_e, "haut": hi_e, "grappes": n_e},
            "mois": {"bas": lo_m, "haut": hi_m, "grappes": n_m}}


def block_drawdown_quantiles(ret, block, sims, seed):
    """Drawdown maximal des séquences tirées par blocs temporels circulaires de rendements."""
    ret = np.asarray(ret, dtype=float)
    rng = np.random.default_rng(seed)
    out = []
    for step in _by_batches(sims):
        idx = circular_block_indices(rng, len(ret), block, step)
        curve = np.cumprod(1.0 + ret[idx], axis=1)
        curve = np.concatenate([np.ones((step, 1)), curve], axis=1)
        peak = np.maximum.accumulate(curve, axis=1)
        out.append(((peak - curve) / peak).max(axis=1))
    draws = np.concatenate(out)
    return {"dd_50": float(np.percentile(draws, 50)), "dd_95": float(np.percentile(draws, 95))}


def side_breakdown(df, wallet, risk):
    """Longs et shorts séparés, frais et financement compris."""
    r = r_multiples(df, wallet, risk)[0] if len(df) else np.array([])
    out = {}
    for label, mask in (("longs", ~df["is_short"]), ("shorts", df["is_short"]),
                        ("total", pd.Series(True, index=df.index))):
        sub = df[mask]
        rs = r[mask.to_numpy()] if len(df) else r
        out[label] = {
            "trades": len(sub),
            "taux_reussite": float((rs > 0).mean()) if len(rs) else None,
            "esperance_R": float(rs.mean()) if len(rs) else None,
            "pnl": float(sub["profit_abs"].sum()),
            "frais": float(sub["fee_abs"].sum()),
            **funding_summary(sub),
        }
    return out


def funding_summary(df):
    """Financement par trade : net payé = -somme. Le champ est net à l'échelle de chaque trade."""
    f = df["funding_fees"].dropna()
    if f.empty:
        return {"financement_paye": None, "financement_recu": None, "financement_net_paye": None}
    return {"financement_paye": float(-f[f < 0].sum()), "financement_recu": float(f[f > 0].sum()),
            "financement_net_paye": float(-f.sum())}


# --------------------------------------------------------------------------- série quotidienne
def parse_day(value):
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def daily_series(df, wallet, start, end):
    """Équité réalisée et rendements, une ligne par jour civil UTC de start à end inclus."""
    if start > end:
        raise ValueError(f"Plage invalide : {start.date()} après {end.date()}.")
    days = pd.date_range(start, end, freq="D")
    pnl = pd.Series(0.0, index=days)
    if len(df):
        close_day = df["close_date"].dt.normalize()
        outside = df[(close_day < days[0]) | (close_day > days[-1])]
        if len(outside):
            raise ValueError(f"{len(outside)} trade(s) clos hors de la plage "
                             f"{days[0].date()} - {days[-1].date()}. Vérifier --start et --end.")
        grouped = df.groupby(close_day)["profit_abs"].sum()
        pnl = grouped.reindex(days, fill_value=0.0).astype(float)
    equity = wallet + pnl.cumsum()
    previous = equity.shift(1, fill_value=wallet)
    if (previous <= 0).any():
        raise ValueError("Équité négative ou nulle pendant la plage : rendements non définis.")
    return pd.DataFrame({"pnl": pnl, "equity": equity, "ret": equity / previous - 1.0})


def candle_file(pair, data_dir):
    """BTC/USDT:USDT donne BTC_USDT_USDT-1d-futures.feather."""
    return Path(data_dir) / (pair.replace("/", "_").replace(":", "_") + "-1d-futures.feather")


def load_closes(pairs, data_dir, start, end):
    """Clôtures 1d par paire, coupées à la plage. Une donnée au-delà de end n'est jamais gardée."""
    closes = {}
    for pair in sorted(set(pairs)):
        frame = pd.read_feather(candle_file(pair, data_dir), columns=["date", "close"])
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
        frame = frame[(frame["date"] >= start) & (frame["date"] <= end)]
        closes[pair] = frame.set_index("date")["close"].astype(float)
    return closes


def marked_series(df, wallet, start, end, closes):
    """Équité réévaluée chaque jour et rendements, une ligne par jour civil UTC de start à end.
    Le trade pèse son P&L réalisé à partir de son jour de clôture et son latent avant ce jour."""
    if start > end:
        raise ValueError(f"Plage invalide : {start.date()} après {end.date()}.")
    days = pd.date_range(start, end, freq="D")
    equity = np.full(len(days), float(wallet))
    for row in df.itertuples():
        open_day, close_day = row.open_date.normalize(), row.close_date.normalize()
        if open_day < days[0] or close_day > days[-1]:
            raise ValueError(f"Trade {row.pair} du {open_day.date()} hors de la plage réévaluée.")
        first, last = days.get_loc(open_day), days.get_loc(close_day)
        equity[last:] += row.profit_abs
        if last > first:
            if np.isnan(row.amount) or np.isnan(row.open_rate):
                raise ValueError(f"Trade {row.pair} du {open_day.date()} sans quantité ni prix d'entrée.")
            prices = closes[row.pair].reindex(days[first:last]).to_numpy()
            if np.isnan(prices).any():
                raise ValueError(f"Bougie 1d manquante pour {row.pair} entre {open_day.date()} et {close_day.date()}.")
            sign = -1.0 if row.is_short else 1.0
            equity[first:last] += sign * row.amount * (prices - row.open_rate)
    previous = np.r_[float(wallet), equity[:-1]]
    if (previous <= 0).any():
        raise ValueError("Équité réévaluée négative ou nulle : rendements non définis.")
    return pd.DataFrame({"equity": equity, "ret": equity / previous - 1.0}, index=days)


def marked_metrics(series, wallet):
    ret = series["ret"].to_numpy()
    equity = series["equity"].to_numpy()
    final = float(equity[-1])
    dd = max_drawdown(equity, wallet)
    growth = cagr(final, wallet, len(series))
    sr = sharpe_daily(ret)
    with_start = np.r_[float(wallet), equity]
    depth = (np.maximum.accumulate(with_start) - with_start) / np.maximum.accumulate(with_start)
    trough = int(depth[1:].argmax()) if dd > 0 else None
    defined = sr is not None
    return {
        "statut": "calcule", "motif": None, "base": LIBELLE_REEVALUE,
        "T": len(series),
        "rendement_total": final / wallet - 1.0,
        "rendement_annualise": growth,
        "sharpe_quotidien": sr,
        "sharpe_annualise": annualize(sr),
        "sortino_annualise": sortino_annualized(ret),
        "calmar": growth / dd if (growth is not None and dd > 0) else None,
        "dd_reevalue": dd,
        "date_creux": str(series.index[trough].date()) if trough is not None else None,
        "g3_asymetrie": float(stats.skew(ret, bias=True)) if defined else None,
        "g4_kurtosis": float(stats.kurtosis(ret, fisher=False, bias=True)) if defined else None,
    }


def marked_unavailable(reason):
    return {"statut": "non_calculable", "motif": reason, "base": LIBELLE_REEVALUE, "T": None,
            "rendement_total": None, "rendement_annualise": None, "sharpe_quotidien": None,
            "sharpe_annualise": None, "sortino_annualise": None, "calmar": None, "dd_reevalue": None,
            "date_creux": None, "g3_asymetrie": None, "g4_kurtosis": None}


def sharpe_daily(ret):
    ret = np.asarray(ret, dtype=float)
    if len(ret) < 2:
        return None
    sd = ret.std(ddof=1)
    return float(ret.mean() / sd) if sd > 0 else None


def annualize(ratio):
    return None if ratio is None else ratio * math.sqrt(JOURS_PAR_AN)


def sortino_annualized(ret):
    ret = np.asarray(ret, dtype=float)
    if len(ret) == 0:
        return None
    downside = math.sqrt(float((np.minimum(ret, 0.0) ** 2).mean()))
    return annualize(float(ret.mean()) / downside) if downside > 0 else None


def max_drawdown(equity, initial):
    e = np.r_[float(initial), np.asarray(equity, dtype=float)]
    pk = np.maximum.accumulate(e)
    return float(((pk - e) / pk).max())


def cagr(final, initial, n_days):
    if final <= 0 or n_days <= 0:
        return None
    return float((final / initial) ** (JOURS_PAR_AN / n_days) - 1.0)


def daily_metrics(series, wallet):
    ret = series["ret"].to_numpy()
    final = float(series["equity"].iloc[-1])
    dd = max_drawdown(series["equity"].to_numpy(), wallet)
    growth = cagr(final, wallet, len(series))
    sr = sharpe_daily(ret)
    return {
        "base": LIBELLE_REALISE,
        "T": len(series),
        "jours_sans_cloture": int((series["pnl"] == 0).sum()),
        "rendement_total": final / wallet - 1.0,
        "rendement_annualise": growth,
        "sharpe_quotidien": sr,
        "sharpe_annualise": annualize(sr),
        "sortino_annualise": sortino_annualized(ret),
        "calmar": growth / dd if (growth is not None and dd > 0) else None,
        "dd_reel": dd,
    }


def semester_label(ts):
    return f"{ts.year}-S{1 if ts.month <= 6 else 2}"


def semester_breakdown(df, series, wallet, risk, marked=None):
    """Semestres civils de la plage, partiels signalés, trades affectés à la clôture. Avec la série
    réévaluée, ajoute la variation d'équité réévaluée et les décomptes hors semestre partiel."""
    r = r_multiples(df, wallet, risk)[0] if len(df) else np.array([])
    close_day = df["close_date"].dt.normalize() if len(df) else None
    labels = [semester_label(d) for d in series.index]
    rows, before, before_marked = [], float(wallet), float(wallet)
    for label in dict.fromkeys(labels):
        sub = series[[x == label for x in labels]]
        year, half = int(label[:4]), label[-1]
        first = pd.Timestamp(year=year, month=1 if half == "1" else 7, day=1, tz="UTC")
        last = pd.Timestamp(year=year, month=6 if half == "1" else 12, day=30 if half == "1" else 31, tz="UTC")
        if len(df):
            mask = ((close_day >= sub.index[0]) & (close_day <= sub.index[-1])).to_numpy()
        else:
            mask = np.array([], dtype=bool)
        pnl_marked = None
        if marked is not None:
            end_marked = float(marked.loc[sub.index[-1], "equity"])
            pnl_marked = end_marked - before_marked
            before_marked = end_marked
        rows.append({
            "semestre": label,
            "partiel": bool(sub.index[0] > first or sub.index[-1] < last),
            "sharpe_significatif": len(sub) >= JOURS_MIN_SHARPE_SEMESTRE,
            "pnl_reevalue": pnl_marked,
            "jours": len(sub),
            "trades": int(mask.sum()),
            "esperance_R": float(r[mask].mean()) if mask.any() else None,
            "sharpe_annualise": annualize(sharpe_daily(sub["ret"].to_numpy())),
            "dd": max_drawdown(sub["equity"].to_numpy(), before),
            "pnl": float(sub["pnl"].sum()),
        })
        before = float(sub["equity"].iloc[-1])
    n_pos = sum(1 for row in rows if row["pnl"] > 0)
    avec = sum(1 for row in rows if row["trades"] > 0)
    whole = [row for row in rows if not row["partiel"]]
    has_marked = marked is not None
    return {"semestres": rows, "n_semestres": len(rows), "n_positifs": n_pos,
            "n_avec_trades": avec, "part_positifs": n_pos / len(rows) if rows else None,
            "n_semestres_hors_partiel": len(whole),
            "n_positifs_hors_partiel": sum(1 for row in whole if row["pnl"] > 0),
            "n_positifs_reevalue": sum(1 for row in rows if row["pnl_reevalue"] > 0) if has_marked else None,
            "n_positifs_reevalue_hors_partiel": (
                sum(1 for row in whole if row["pnl_reevalue"] > 0) if has_marked else None)}


# ------------------------------------------------------------------------------- Sharpe déflaté
def probabilistic_sharpe(sr, sr0, t, g3, g4):
    """PSR(SR0), SR non annualisé, g3 asymétrie, g4 kurtosis non excédentaire, T observations."""
    if t < 2:
        return None
    variance = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2
    if variance <= 0:
        return None
    return float(stats.norm.cdf((sr - sr0) * math.sqrt(t - 1) / math.sqrt(variance)))


def expected_max_sharpe(sr_var, n_trials):
    """SR0 de Bailey et López de Prado (2014), dans l'unité de sr_var (ici quotidienne)."""
    gamma = float(np.euler_gamma)
    z1 = stats.norm.ppf(1.0 - 1.0 / n_trials)
    z2 = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return float(math.sqrt(sr_var) * ((1.0 - gamma) * z1 + gamma * z2))


def deflated_sharpe(sr, t, g3, g4, n_trials, sr_var):
    """Renvoie (sr0, dsr, motif). Motif renseigné et valeurs None si non calculable."""
    if sr is None:
        return None, None, "Sharpe quotidien non défini (variance nulle ou moins de 2 observations)."
    if n_trials is None:
        return None, None, "Nombre d'essais N inconnu."
    if n_trials < 2:
        return None, None, "N = 1. Aucune correction de tests multiples n'a de sens."
    if sr_var is None:
        return None, None, "V[SR] inconnue."
    if sr_var <= 0:
        return None, None, "V[SR] nulle ou négative."
    sr0 = expected_max_sharpe(sr_var, n_trials)
    dsr = probabilistic_sharpe(sr, sr0, t, g3, g4)
    if dsr is None:
        return sr0, None, "Dénominateur du PSR non défini."
    return sr0, dsr, None


def load_registry(path):
    """Renvoie (N, V, Sharpe connus, avertissements) depuis un registre JSON."""
    reg = json.loads(Path(path).read_text(encoding="utf-8"))
    essais = reg["essais"] if isinstance(reg, dict) else reg
    declared = reg.get("n_essais_declares") if isinstance(reg, dict) else None
    known = [float(e["sharpe_quotidien"]) for e in essais if e.get("sharpe_quotidien") is not None]
    n_trials = max(len(essais), int(declared or 0))
    sr_var = float(np.var(known, ddof=1)) if len(known) >= 2 else None
    warnings = []
    for key, label in (("timerange", "périodes"), ("frais", "frais")):
        values = {json.dumps(e[key]) for e in essais if e.get("sharpe_quotidien") is not None and e.get(key) is not None}
        if len(values) > 1:
            warnings.append(f"Registre hétérogène : {len(values)} {label} différent(e)s. "
                            "V[SR] mesure aussi cet effet, pas seulement la dispersion des variantes.")
    if len(known) < n_trials:
        warnings.append(f"Registre : {len(known)} Sharpe connus pour {n_trials} essais déclarés. "
                        "V[SR] n'utilise que les Sharpe connus.")
    return n_trials, sr_var, known, warnings


def load_registry_reevalue(path):
    """V[SR] de la série réévaluée depuis le même registre. None si moins de 2 Sharpe connus."""
    reg = json.loads(Path(path).read_text(encoding="utf-8"))
    essais = reg["essais"] if isinstance(reg, dict) else reg
    known = [float(e["sharpe_quotidien_reevalue"]) for e in essais
             if e.get("sharpe_quotidien_reevalue") is not None]
    return (float(np.var(known, ddof=1)) if len(known) >= 2 else None), known


def aggregate_registry(results_dir, declared_ids):
    """Construit le registre depuis les exports <id>_metriques.json et la liste des essais déclarés.
    Un essai déclaré sans export reste compté dans N (Sharpe null)."""
    results_dir = Path(results_dir)
    exports = {}
    for file in sorted(results_dir.glob("*_metriques.json")):
        content = json.loads(file.read_text(encoding="utf-8"))
        exports[content["essai"]] = content
    essais = []
    for essai in list(declared_ids) + [k for k in exports if k not in declared_ids]:
        content = exports.get(essai)
        if content is None:
            essais.append({"id": essai, "statut": "sans_export", "sharpe_quotidien": None})
            continue
        essais.append({
            "id": essai,
            "statut": "exporte" if essai in declared_ids else "exporte_non_declare",
            "sharpe_quotidien": content["metriques_quotidiennes"]["sharpe_quotidien"],
            "sharpe_quotidien_reevalue": (content.get("metriques_reevaluees") or {}).get("sharpe_quotidien"),
            "T": content["metriques_quotidiennes"]["T"],
            "timerange": content["plage"]["timerange_analyse"],
            "frais": content["execution"]["frais_par_cote"],
            "sha256_export": content["tracabilite"]["sha256_export"],
        })
    return {"essais": essais, "n_essais_declares": len(essais),
            "source": str(results_dir), "agrege_le_utc": now_utc()}


# ------------------------------------------------------------------------------ assemblage
def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_range(args_start, args_end, strat):
    """Plage de l'essai : options, sinon timerange de l'export, sinon dates du backtest."""
    tr_start, tr_end = None, None
    timerange = strat.get("timerange")
    if timerange and "-" in str(timerange):
        tr_start, tr_end = (str(timerange).split("-", 1) + [""])[:2]
    start = args_start or tr_start or strat.get("backtest_start")
    end = args_end or tr_end or strat.get("backtest_end")
    if not start or not end:
        raise ValueError("Plage inconnue : préciser --start et --end.")
    return parse_day(start).normalize(), parse_day(end).normalize()


def range_warnings(start, end, strat):
    warnings = []
    timerange = str(strat.get("timerange") or "")
    if timerange and "-" in timerange:
        tr_start, tr_end = timerange.split("-", 1)
        if tr_start and parse_day(tr_start).normalize() != start:
            warnings.append(f"--start ({start.date()}) diffère du timerange de l'export ({timerange}).")
        if tr_end and parse_day(tr_end).normalize() != end:
            warnings.append(f"--end ({end.date()}) diffère du timerange de l'export ({timerange}).")
    day = pd.Timedelta(days=1)
    if strat.get("backtest_start") and parse_day(strat["backtest_start"]).normalize() > start + day:
        warnings.append(f"Le backtest réel commence le {strat['backtest_start']}, après le début de plage "
                        f"{start.date()} (chauffe insuffisante probable). Ces jours comptent à 0.")
    if strat.get("backtest_end") and parse_day(strat["backtest_end"]).normalize() < end - day:
        warnings.append(f"Le backtest réel finit le {strat['backtest_end']}, avant la fin de plage "
                        f"{end.date()}. Ces jours comptent à 0.")
    return warnings


def consistency_warnings(df, wallet, strat):
    warnings = []
    if strat.get("final_balance") is not None:
        gap = wallet + df["profit_abs"].sum() - float(strat["final_balance"])
        if abs(gap) > 0.01:
            warnings.append(f"Capital final calculé différent de final_balance de l'export (écart {gap:+.2f}).")
    if strat.get("total_trades") is not None and int(strat["total_trades"]) != len(df):
        warnings.append(f"{len(df)} trades lus pour total_trades = {strat['total_trades']} dans l'export.")
    if df["is_open"].any():
        warnings.append(f"{int(df['is_open'].sum())} trade(s) marqué(s) ouverts dans l'export.")
    if strat.get("trading_mode") == "futures":
        if len(df) and df["funding_fees"].isna().all():
            warnings.append("Mode futures mais champ funding_fees absent : financement inconnu.")
        elif len(df) and (df["funding_fees"].fillna(0.0) == 0).all():
            warnings.append("Mode futures mais financement nul sur tous les trades : "
                            "données de financement à vérifier.")
    return warnings


def freqtrade_comparison(strat, wallet_final):
    """Chiffres propres à freqtrade, recopiés pour contrôle. Leurs formules diffèrent des nôtres :
    Sharpe 'trades' sans série calendaire, Sharpe 'wallet' en ddof=0 sur un solde décalé d'un jour,
    Sortino sur l'écart-type des seuls rendements négatifs."""
    wallet_stats = strat.get("wallet_stats") or {}
    return {
        "sharpe_trades": strat.get("sharpe"), "sortino_trades": strat.get("sortino"),
        "calmar_trades": strat.get("calmar"), "sharpe_wallet": wallet_stats.get("sharpe"),
        "sortino_wallet": wallet_stats.get("sortino"), "calmar_wallet": wallet_stats.get("calmar"),
        "dd_compte": strat.get("max_drawdown_account"),
        "dd_wallet": wallet_stats.get("max_drawdown_account"),
        "final_balance": strat.get("final_balance"), "capital_final_calcule": wallet_final,
        "taux_reussite": strat.get("winrate"), "total_trades": strat.get("total_trades"),
    }


def resolve_trials(args):
    """Source de N et V : options, registre, ou rien. Les deux ensemble sont refusés."""
    if args.registry_json and (args.n_trials is not None or args.sr_var is not None
                               or args.sr_var_reevalue is not None):
        raise ValueError("--registry-json exclut --n-trials, --sr-var et --sr-var-reevalue.")
    if args.registry_json:
        n_trials, sr_var, known, warnings = load_registry(args.registry_json)
        return n_trials, sr_var, f"registre {args.registry_json} ({len(known)} Sharpe connus)", warnings
    if args.n_trials is not None or args.sr_var is not None:
        return args.n_trials, args.sr_var, "options --n-trials et --sr-var", []
    return None, None, "aucune", []


def display_path(path):
    """Chemin relatif au dossier du script quand c'est possible, pour ne pas écrire de chemin local dans les exports."""
    try:
        return str(Path(path).resolve().relative_to(Path(__file__).resolve().parent))
    except ValueError:
        return str(path)


def deflated_block(source, n_trials, sr_var, sr, t, g3, g4):
    sr0, dsr, reason = deflated_sharpe(sr, t, g3, g4, n_trials, sr_var)
    return {
        "source": source,
        "n_essais": n_trials, "v_sr_quotidien": sr_var,
        "sr_quotidien": sr, "t": t, "g3_asymetrie": g3, "g4_kurtosis": g4,
        "psr_sr0_nul": probabilistic_sharpe(sr, 0.0, t, g3, g4) if sr is not None else None,
        "sr0_quotidien": sr0, "sr0_annualise": annualize(sr0),
        "dsr": dsr, "statut": "calcule" if dsr is not None else "non_calculable", "motif": reason,
    }


def build_marked(df, wallet, start, end, data_dir):
    """Série et métriques réévaluées. Renvoie (série ou None, métriques)."""
    try:
        closes = load_closes(df["pair"], data_dir, start, end) if len(df) else {}
        series = marked_series(df, wallet, start, end, closes)
    except (OSError, ValueError, KeyError) as exc:
        return None, marked_unavailable(str(exc))
    return series, marked_metrics(series, wallet)


def build_report(args, command):
    data, member, sha, config = load_export(args.path)
    strategy_name, strat = select_strategy(data, args.strategy)
    df = prepare_trades(strat["trades"])
    wallet = args.wallet if args.wallet is not None else float(strat.get("starting_balance") or 10000.0)
    start, end = resolve_range(args.start, args.end, strat)

    warnings = range_warnings(start, end, strat) + consistency_warnings(df, wallet, strat)
    if args.wallet is not None and strat.get("starting_balance") not in (None, args.wallet):
        warnings.append(f"--wallet {args.wallet} diffère de starting_balance {strat['starting_balance']}.")
    n_trials, sr_var, trials_source, trial_warnings = resolve_trials(args)
    warnings += trial_warnings

    series = daily_series(df, wallet, start, end)
    metrics = daily_metrics(series, wallet)
    ret = series["ret"].to_numpy()
    sr = metrics["sharpe_quotidien"]
    if sr is not None:
        g3 = float(stats.skew(ret, bias=True))
        g4 = float(stats.kurtosis(ret, fisher=False, bias=True))
    else:
        g3, g4 = None, None

    marked, marked_stats = build_marked(df, wallet, start, end, args.data_dir)
    if marked is None:
        warnings.append(f"Équité réévaluée non calculée : {marked_stats['motif']}")
    sr_var_marked = args.sr_var_reevalue
    source_marked = f"{trials_source}, V de la série réévaluée"
    if args.registry_json:
        sr_var_marked, known_marked = load_registry_reevalue(args.registry_json)
        source_marked = (f"registre {args.registry_json} ({len(known_marked)} Sharpe réévalués connus)")

    trade_stats = trade_statistics(df, wallet, args.risk, args.sims, args.seed)
    metrics["taux_reussite"] = trade_stats["taux_reussite"]
    intervals = dependence_intervals(df, wallet, args.risk, args.sims_blocs, args.seed_blocs, args.bloc_trades)
    mc_ret = marked["ret"].to_numpy() if marked is not None else ret
    monte_carlo = {
        "tirages": args.sims_blocs, "graine": args.seed_blocs, "longueur_bloc_jours": args.bloc_jours,
        "base": "reevaluee" if marked is not None else "realisee",
        **block_drawdown_quantiles(mc_ret, args.bloc_jours, args.sims_blocs, [args.seed_blocs, 4]),
    }
    fees = sorted({float(t.get("fee_open") or 0.0) for t in strat["trades"]})
    return {
        "essai": args.essai,
        "strategie": strategy_name,
        "statut_document": "Résultats de recherche. Aucune promesse de gain, aucune recommandation.",
        "tracabilite": {
            "commande": command,
            "horodatage_utc": now_utc(),
            "export": str(args.path),
            "donnees_bougies": display_path(args.data_dir),
            "membre_analyse": member,
            "sha256_export": sha,
            "freqtrade_version_export": find_export_version(data, strat, config),
            "freqtrade_version_environnement_analyse": find_env_version(),
            "backtest_execute_le_utc": (
                datetime.fromtimestamp(strat["backtest_run_start_ts"], timezone.utc).isoformat()
                if strat.get("backtest_run_start_ts") else None),
        },
        "plage": {
            "start": str(start.date()), "end": str(end.date()),
            "timerange_analyse": f"{start:%Y%m%d}-{end:%Y%m%d}",
            "timerange_export": strat.get("timerange"),
            "backtest_start": strat.get("backtest_start"), "backtest_end": strat.get("backtest_end"),
        },
        "execution": {
            "wallet": wallet, "risk": args.risk, "sims": args.sims, "seed": args.seed,
            "sims_blocs": args.sims_blocs, "seed_blocs": args.seed_blocs,
            "bloc_trades": args.bloc_trades, "bloc_jours": args.bloc_jours,
            "frais_par_cote": fees[0] if len(fees) == 1 else (fees or None),
            "trading_mode": strat.get("trading_mode"),
            "sorties_force_exit": int((df["exit_reason"] == "force_exit").sum()),
        },
        "trades": trade_stats,
        "intervalles_dependance": intervals,
        "monte_carlo_blocs": monte_carlo,
        "metriques_quotidiennes": metrics,
        "metriques_reevaluees": marked_stats,
        "par_sens": side_breakdown(df, wallet, args.risk),
        "semestres": semester_breakdown(df, series, wallet, args.risk, marked),
        "dsr": deflated_block(trials_source, n_trials, sr_var, sr, metrics["T"], g3, g4),
        "dsr_reevalue": deflated_block(source_marked, n_trials, sr_var_marked, marked_stats["sharpe_quotidien"],
                                       marked_stats["T"] if marked is not None else 0,
                                       marked_stats["g3_asymetrie"], marked_stats["g4_kurtosis"]),
        "comparaison_freqtrade": freqtrade_comparison(strat, trade_stats["capital_final"]),
        "avertissements": warnings,
        "notes_methode": NOTES_METHODE,
    }


# --------------------------------------------------------------------------------- restitution
def fmt(value, spec=".3f"):
    return "n/c" if value is None else format(value, spec)


def fr(text):
    """Nombre au format français : virgule décimale, espace fine pour les milliers, espace avant %."""
    return text.replace(",", "\u202f").replace(".", ",").replace("%", " %")


def fmt_fr(value, spec=".3f"):
    return fr(fmt(value, spec))


def console_summary(rep):
    t, m, d = rep["trades"], rep["metriques_quotidiennes"], rep["dsr"]
    mk, dk, iv, mc = rep["metriques_reevaluees"], rep["dsr_reevalue"], rep["intervalles_dependance"], rep["monte_carlo_blocs"]
    print(f"Trades : {t['trades']}  (longs {t['longs']}, shorts {t['shorts']})")
    if t["trades"]:
        print(f"Taux de réussite : {t['taux_reussite']:.1%}   gain moyen {t['gain_moyen_R']:.2f} R   "
              f"perte moyenne {t['perte_moyenne_R']:.2f} R")
        print(f"Espérance : {t['esperance_R']:+.3f} R   intervalle 90 % iid : [{t['ic90_bas']:+.3f} ; {t['ic90_haut']:+.3f}] R")
        print(f"Espérance hors force_exit : {fmt(t['esperance_hors_force_exit_R'], '+.3f')} R ({t['trades_force_exit']} sorties forcées)")
        if iv["statut"] == "calcule":
            print(f"Intervalle 90 % par blocs de {iv['longueur_bloc_trades']} trades ({iv['tirages']} tirages, graine {iv['graine']}) : "
                  f"[{iv['blocs']['bas']:+.3f} ; {iv['blocs']['haut']:+.3f}] R   par épisodes ({iv['episodes']['grappes']}) : "
                  f"[{iv['episodes']['bas']:+.3f} ; {iv['episodes']['haut']:+.3f}] R")
        print(f"Espérance avec frais doublés (approx.) : {t['esperance_frais_doubles_R_approx']:+.3f} R")
        print(f"Espérance avec frais et financement payé doublés (approx.) : "
              f"{t['esperance_frais_et_financement_doubles_R_approx']:+.3f} R")
        print(f"Drawdown réalisé : {m['dd_reel']:.1%}   réévalué : {fmt(mk['dd_reevalue'], '.1%')}   "
              f"95e centile par permutation : {t['dd_95']:.1%}   95e centile par blocs de {mc['longueur_bloc_jours']} jours : {mc['dd_95']:.1%}")
        share = t["part_meilleur_trade_R"]
        print(f"Part du gain portée par le meilleur trade : {share:.0%}" if share is not None
              else "Gain total négatif ou nul")
    else:
        print("Aucun trade.")
    print(f"Capital final : {t['capital_final']:,.0f} (départ {rep['execution']['wallet']:,.0f})")
    print(f"Base réévaluée (principale). Sharpe annualisé : {fmt(mk['sharpe_annualise'])}   Sortino : {fmt(mk['sortino_annualise'])}   "
          f"Calmar : {fmt(mk['calmar'])}   ({mk['statut']})")
    print(f"Base réalisée. Sharpe annualisé : {fmt(m['sharpe_annualise'])}   Sortino : {fmt(m['sortino_annualise'])}   "
          f"Calmar : {fmt(m['calmar'])}   ({m['T']} jours, base 365)")
    sem = rep["semestres"]
    print(f"Semestres positifs : {sem['n_positifs']} / {sem['n_semestres']} "
          f"({fmt(sem['part_positifs'], '.0%')}), hors partiel {sem['n_positifs_hors_partiel']} / {sem['n_semestres_hors_partiel']}, "
          f"réévalué {sem['n_positifs_reevalue'] if sem['n_positifs_reevalue'] is not None else 'n/c'}")
    tot = rep["par_sens"]["total"]
    print(f"Financement payé : {fmt(tot['financement_paye'], ',.2f')}   reçu : {fmt(tot['financement_recu'], ',.2f')}   "
          f"net payé : {fmt(tot['financement_net_paye'], ',.2f')}")
    if dk["dsr"] is not None:
        print(f"DSR principal (série réévaluée) : {dk['dsr']:.3f}   SR0 quotidien : {dk['sr0_quotidien']:.4f}   N = {dk['n_essais']}")
    else:
        print(f"DSR principal (série réévaluée) : non calculable. {dk['motif']}")
    if d["dsr"] is not None:
        print(f"DSR réalisé (second) : {d['dsr']:.3f}   SR0 quotidien : {d['sr0_quotidien']:.4f}   N = {d['n_essais']}")
    else:
        print(f"DSR réalisé (second) : non calculable. {d['motif']}")
    for warning in rep["avertissements"]:
        print(f"AVERTISSEMENT : {warning}")


def render_markdown(rep):
    tr, ex, pl = rep["tracabilite"], rep["execution"], rep["plage"]
    t, m, d = rep["trades"], rep["metriques_quotidiennes"], rep["dsr"]
    sem, cmp_ft = rep["semestres"], rep["comparaison_freqtrade"]
    mk, dk, iv, mc = rep["metriques_reevaluees"], rep["dsr_reevalue"], rep["intervalles_dependance"], rep["monte_carlo_blocs"]
    ic = lambda block: f"{f(block['bas'], '+.3f')} à {f(block['haut'], '+.3f')} R" if block else "n/c"
    pct = ".1%"
    f = fmt_fr
    absent = "absente de l'export (vérifié pour freqtrade 2026.10)"
    lines = [
        f"# Métriques de l'essai {rep['essai']} ({rep['strategie']})", "",
        rep["statut_document"], "",
        "## Traçabilité", "",
        "| Élément | Valeur |", "|---|---|",
        f"| Commande | `{tr['commande']}` |",
        f"| Horodatage de l'analyse (UTC) | {tr['horodatage_utc']} |",
        f"| Export analysé | `{tr['export']}` |",
        f"| Membre lu | `{tr['membre_analyse']}` |",
        f"| sha256 de l'export | `{tr['sha256_export']}` |",
        f"| Version freqtrade dans l'export | {tr['freqtrade_version_export'] or absent} |",
        f"| Version freqtrade de l'environnement d'analyse | {tr['freqtrade_version_environnement_analyse'] or 'inconnue'} |",
        f"| Backtest exécuté le (UTC) | {tr['backtest_execute_le_utc'] or 'inconnu'} |",
        f"| Plage analysée | {pl['start']} à {pl['end']} |",
        f"| Timerange de l'export | {pl['timerange_export']} |",
        f"| Backtest réel | {pl['backtest_start']} à {pl['backtest_end']} |",
        f"| Capital de départ, risque nominal, frais par côté | {f(ex['wallet'], ',.2f')}, {f(ex['risk'], '.2%')}, {fr(str(ex['frais_par_cote']))} |",
        f"| Simulations, graine | {ex['sims']}, {ex['seed']} |",
        f"| Tirages et graine des méthodes par blocs | {ex['sims_blocs']}, {ex['seed_blocs']} |",
        f"| Longueur des blocs | {ex['bloc_trades']} trades, {ex['bloc_jours']} jours |", "",
        "## Trades", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Trades (longs, shorts) | {t['trades']} ({t['longs']}, {t['shorts']}) |",
        f"| Sorties force_exit | {ex['sorties_force_exit']} |",
        f"| Taux de réussite | {f(t['taux_reussite'], pct)} |",
        f"| Gain moyen, perte moyenne | {f(t['gain_moyen_R'], '.2f')} R, {f(t['perte_moyenne_R'], '.2f')} R |",
        f"| Espérance | {f(t['esperance_R'], '+.3f')} R |",
        f"| Espérance hors force_exit | {f(t['esperance_hors_force_exit_R'], '+.3f')} R |",
        f"| Intervalle à 90 % iid ({ex['sims']} tirages, graine {ex['seed']}) | {f(t['ic90_bas'], '+.3f')} à {f(t['ic90_haut'], '+.3f')} R |",
        f"| Intervalle à 90 % iid ({iv['tirages']} tirages) | {ic(iv['iid'])} |",
        f"| Intervalle à 90 % par blocs de {iv['longueur_bloc_trades']} trades | {ic(iv['blocs'])} |",
        f"| Intervalle à 90 % par épisodes ({iv['episodes']['grappes'] if iv['episodes'] else 'n/c'}) | {ic(iv['episodes'])} |",
        f"| Intervalle à 90 % par mois d'ouverture ({iv['mois']['grappes'] if iv['mois'] else 'n/c'}) | {ic(iv['mois'])} |",
        f"| Espérance, frais doublés (approximation) | {f(t['esperance_frais_doubles_R_approx'], '+.3f')} R |",
        f"| Espérance, frais et financement payé doublés (approximation) | {f(t['esperance_frais_et_financement_doubles_R_approx'], '+.3f')} R |",
        f"| Drawdown 95e centile (permutation des trades, comparaison) | {f(t['dd_95'], pct)} |",
        f"| Drawdown 95e centile (blocs temporels de {mc['longueur_bloc_jours']} jours, base {mc['base']}) | {f(mc['dd_95'], pct)} |",
        f"| Part du gain du meilleur trade (en R) | {f(t['part_meilleur_trade_R'], '.0%')} |",
        f"| Part du gain du meilleur trade (en P&L) | {f(t['part_meilleur_trade_pnl'], '.0%')} |",
        f"| Capital final | {f(t['capital_final'], ',.2f')} |", "",
        "## Métriques sur l'équité réévaluée chaque jour (base principale)", "",
        (f"Série de {mk['T']} jours civils. Latent au prix de clôture 1d, hors frais et financement latents."
         if mk["statut"] == "calcule" else f"Non calculée. {mk['motif']}"), "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Rendement annualisé | {f(mk['rendement_annualise'], pct)} |",
        f"| Sharpe annualisé (base 365, sans risque 0 %) | {f(mk['sharpe_annualise'])} |",
        f"| Sharpe quotidien non annualisé | {f(mk['sharpe_quotidien'], '.5f')} |",
        f"| Sortino annualisé | {f(mk['sortino_annualise'])} |",
        f"| Calmar | {f(mk['calmar'])} |",
        f"| Drawdown maximal | {f(mk['dd_reevalue'], pct)} |",
        f"| Creux du drawdown | {mk['date_creux'] or 'n/c'} |", "",
        "## Métriques sur l'équité réalisée (base de comparaison)", "",
        f"Série de {m['T']} jours civils, dont {m['jours_sans_cloture']} sans clôture comptés à 0. "
        "Équité réalisée à la clôture des trades, non réévaluée chaque jour. "
        "Cela lisse la volatilité et peut flatter le Sharpe.", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Rendement total | {f(m['rendement_total'], pct)} |",
        f"| Rendement annualisé | {f(m['rendement_annualise'], pct)} |",
        f"| Sharpe annualisé (base 365, sans risque 0 %) | {f(m['sharpe_annualise'])} |",
        f"| Sharpe quotidien non annualisé | {f(m['sharpe_quotidien'], '.5f')} |",
        f"| Sortino annualisé | {f(m['sortino_annualise'])} |",
        f"| Calmar | {f(m['calmar'])} |",
        f"| Drawdown maximal | {f(m['dd_reel'], pct)} |",
        f"| Taux de réussite | {f(m['taux_reussite'], pct)} |", "",
        "## Par semestre civil (affectation à la clôture)", "",
        "| Semestre | Jours | Trades | Espérance R | Sharpe réalisé | Drawdown réalisé | P&L réalisé | P&L réévalué |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sem["semestres"]:
        name = row["semestre"] + (" (partiel)" if row["partiel"] else "")
        sharpe_txt = f(row["sharpe_annualise"], ".2f") if row["sharpe_significatif"] else "non significatif"
        lines.append(f"| {name} | {row['jours']} | {row['trades']} | {f(row['esperance_R'], '+.3f')} | "
                     f"{sharpe_txt} | {f(row['dd'], pct)} | {f(row['pnl'], '+,.2f')} | {f(row['pnl_reevalue'], '+,.2f')} |")
    lines += [
        "", f"Semestres positifs {sem['n_positifs']} sur {sem['n_semestres']} "
        f"({f(sem['part_positifs'], '.0%')}). Hors semestre partiel {sem['n_positifs_hors_partiel']} sur {sem['n_semestres_hors_partiel']}. "
        f"Réévalué {sem['n_positifs_reevalue'] if sem['n_positifs_reevalue'] is not None else 'n/c'} sur {sem['n_semestres']}, "
        f"hors semestre partiel {sem['n_positifs_reevalue_hors_partiel'] if sem['n_positifs_reevalue_hors_partiel'] is not None else 'n/c'} sur {sem['n_semestres_hors_partiel']}. "
        f"Semestres avec au moins un trade {sem['n_avec_trades']}.", "",
        "## Longs et shorts", "",
        "| Sens | Trades | Réussite | Espérance R | P&L | Frais | Financement payé | Financement reçu | Net payé |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ("longs", "shorts", "total"):
        s = rep["par_sens"][label]
        lines.append(f"| {label} | {s['trades']} | {f(s['taux_reussite'], pct)} | {f(s['esperance_R'], '+.3f')} | "
                     f"{f(s['pnl'], '+,.2f')} | {f(s['frais'], ',.2f')} | {f(s['financement_paye'], ',.2f')} | "
                     f"{f(s['financement_recu'], ',.2f')} | {f(s['financement_net_paye'], ',.2f')} |")
    lines += [
        "", "Le financement provient du champ funding_fees, net à l'échelle de chaque trade et déjà inclus dans le P&L.", "",
        "## Sharpe déflaté (Bailey et López de Prado, 2014)", "",
        "Calcul principal sur la série réévaluée, avec V réévaluée.", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Source de N et V | {dk['source']} |",
        f"| N | {dk['n_essais'] if dk['n_essais'] is not None else 'inconnu'} |",
        f"| V[SR] quotidien | {f(dk['v_sr_quotidien'], '.6f')} |",
        f"| Asymétrie g3, kurtosis g4 | {f(dk['g3_asymetrie'], '.3f')}, {f(dk['g4_kurtosis'], '.3f')} |",
        f"| PSR(0) | {f(dk['psr_sr0_nul'])} |",
        f"| SR0 quotidien, annualisé | {f(dk['sr0_quotidien'], '.4f')}, {f(dk['sr0_annualise'], '.3f')} |",
        f"| DSR | {f(dk['dsr']) if dk['dsr'] is not None else 'non calculable'} |",
    ]
    if dk["motif"]:
        lines.append(f"| Motif | {dk['motif']} |")
    lines += [
        "", "Calcul second sur la série réalisée, non comparable d'un essai à l'autre.", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Source de N et V | {d['source']} |",
        f"| N | {d['n_essais'] if d['n_essais'] is not None else 'inconnu'} |",
        f"| V[SR] quotidien | {f(d['v_sr_quotidien'], '.6f')} |",
        f"| Asymétrie g3, kurtosis g4 | {f(d['g3_asymetrie'], '.3f')}, {f(d['g4_kurtosis'], '.3f')} |",
        f"| PSR(0) | {f(d['psr_sr0_nul'])} |",
        f"| SR0 quotidien, annualisé | {f(d['sr0_quotidien'], '.4f')}, {f(d['sr0_annualise'], '.3f')} |",
        f"| DSR | {f(d['dsr']) if d['dsr'] is not None else 'non calculable'} |",
    ]
    if d["motif"]:
        lines.append(f"| Motif | {d['motif']} |")
    lines += [
        "", "## Contrôle face aux chiffres de freqtrade", "",
        "Ces chiffres viennent de l'export. Leurs formules diffèrent de celles de ce document.", "",
        "| Mesure | Freqtrade |", "|---|---:|",
        f"| Sharpe (trades) | {f(cmp_ft['sharpe_trades'])} |",
        f"| Sharpe (solde quotidien) | {f(cmp_ft['sharpe_wallet'])} |",
        f"| Sortino (trades) | {f(cmp_ft['sortino_trades'])} |",
        f"| Sortino (solde quotidien) | {f(cmp_ft['sortino_wallet'])} |",
        f"| Calmar (trades) | {f(cmp_ft['calmar_trades'])} |",
        f"| Calmar (solde quotidien) | {f(cmp_ft['calmar_wallet'])} |",
        f"| Drawdown du compte | {f(cmp_ft['dd_compte'], pct)} |",
        f"| Capital final | {f(cmp_ft['final_balance'], ',.2f')} |", "",
    ]
    if rep["avertissements"]:
        lines += ["## Avertissements", ""]
        for warning in rep["avertissements"]:
            lines += [warning, ""]
    lines += ["## Notes de méthode", ""]
    for note in rep["notes_methode"]:
        lines += [note, ""]
    lines.append(f"Sources : export freqtrade `{Path(tr['export']).name}`, analyse du {tr['horodatage_utc']}.")
    return "\n".join(lines) + "\n"


def write_exports(rep, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{rep['essai']}_metriques.json"
    md_path = out_dir / f"{rep['essai']}_metriques.md"
    json_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(rep), encoding="utf-8")
    return json_path, md_path


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Analyse d'un export freqtrade pour validation-edge.")
    ap.add_argument("path", nargs="?", help="Export .zip ou .json de freqtrade.")
    ap.add_argument("--risk", type=float, default=0.005, help="Risque nominal par trade (R).")
    ap.add_argument("--wallet", type=float, default=None, help="Capital de départ. Défaut : starting_balance de l'export.")
    ap.add_argument("--sims", type=int, default=5000, help="Tirages du bootstrap et du Monte Carlo.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--start", help="Début de plage de l'essai (AAAAMMJJ). Défaut : timerange de l'export.")
    ap.add_argument("--end", help="Fin de plage incluse (AAAAMMJJ). Défaut : timerange de l'export.")
    ap.add_argument("--essai", default="SANS-ID", help="Identifiant de l'essai (E01...).")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Dossier des exports. Défaut : resultats/ à côté du script.")
    ap.add_argument("--strategy", help="Nom de la stratégie si l'export en contient plusieurs.")
    ap.add_argument("--n-trials", type=int, help="N, nombre d'essais déclarés, abandonnés compris.")
    ap.add_argument("--sr-var", type=float, help="V[SR], variance transversale des Sharpe QUOTIDIENS non annualisés.")
    ap.add_argument("--sr-var-reevalue", type=float, help="V[SR] des Sharpe quotidiens de la série réévaluée.")
    ap.add_argument("--data-dir", default=str(DEFAULT_DATA), help="Dossier des bougies 1d pour l'équité réévaluée.")
    ap.add_argument("--sims-blocs", type=int, default=SIMS_BLOCS, help="Tirages de l'IC par blocs et du Monte Carlo par blocs.")
    ap.add_argument("--seed-blocs", type=int, default=SEED_BLOCS, help="Graine fixe des méthodes par blocs.")
    ap.add_argument("--bloc-trades", type=int, default=BLOC_TRADES, help="Longueur des blocs de l'IC, en trades.")
    ap.add_argument("--bloc-jours", type=int, default=BLOC_JOURS, help="Longueur des blocs du Monte Carlo, en jours.")
    ap.add_argument("--registry-json", help="Registre JSON pour N et V. En mode --agreger-registre, fichier écrit.")
    ap.add_argument("--agreger-registre", metavar="DOSSIER", help="Agrège les *_metriques.json de DOSSIER vers --registry-json.")
    ap.add_argument("--registre-csv", help="REGISTRE_ESSAIS.csv, lu seulement, pour la liste des essais déclarés.")
    return ap, ap.parse_args(argv)


def run_aggregation(args):
    if not args.registry_json or not args.registre_csv:
        raise ValueError("--agreger-registre demande --registry-json (sortie) et --registre-csv.")
    with open(args.registre_csv, encoding="utf-8", newline="") as handle:
        declared = [row["id_essai"] for row in csv.DictReader(handle)
                    if not (row.get("statut") or "").startswith("hors N")]
    registry = aggregate_registry(args.agreger_registre, declared)
    target = Path(args.registry_json)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    known = sum(1 for e in registry["essais"] if e["sharpe_quotidien"] is not None)
    print(f"Registre écrit : {target} ({len(registry['essais'])} essais, {known} Sharpe connus)")
    return registry


def main(argv=None):
    raw = list(sys.argv[1:] if argv is None else argv)
    ap, args = parse_args(raw)
    try:
        if args.agreger_registre:
            return run_aggregation(args)
        if not args.path:
            ap.error("chemin de l'export manquant.")
        report = build_report(args, shlex.join(["python", Path(__file__).name] + raw))
    except (ValueError, KeyError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        sys.exit(f"Erreur : {exc}")
    console_summary(report)
    json_path, md_path = write_exports(report, args.out)
    print(f"Exports : {json_path} ; {md_path}")
    return report


if __name__ == "__main__":
    main()
