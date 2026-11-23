#!/usr/bin/env python3
"""Papier aveugle en avant de STRAT-20261119-09 (fiche § 3, § 4 et § 6). Aucun ordre, aucune clé, capital nul.

Passage prévu toutes les 10 minutes de chaque heure (minutes 2, 12 et 22). À chaque passage :
1. signaux : dans les 30 minutes qui suivent l'heure de décision d'un groupe (matières premières le dimanche, actions
   le lundi, et les mêmes heures pour le témoin BTC et ETH), calcul de M, σ et du signal avec les seules bougies
   ≤ décision, puis écriture en ajout seul. Un signal non écrit dans la fenêtre est un incident : le groupe compte
   comme vide ce week-end, sans rejeu ni remplacement (fiche § 6) ;
2. positions : une fois l'heure de sortie passée d'au moins 65 minutes, entrée à l'ouverture de la première minute
   qui suit l'écriture du signal, stop sur le prix de marque (minutes de l'heure d'entrée, puis heures), sortie à
   l'ouverture de l'heure de sortie. Trois versions : base, stressée (stop au mode 1 de STRAT-06) et coûts doublés ;
3. semaines : quand les quatre groupes d'un week-end sont réglés, une ligne par week-end (somme des positions à 1/K).

Garde-fous : le papier ne tourne que si la configuration est « figee ». Avec --maintenant (essai à blanc sur une date
passée), seuls les signaux sont calculés : aucune position, aucune issue, jamais.

Usage : python -I -B paper_week_end09.py --donnees DIR --sorties DIR [--maintenant 2026-11-16T13:02:00] [--config FICHIER]
"""
import argparse, csv, datetime as dt, hashlib, json, math, time
from pathlib import Path
import numpy as np, pandas as pd, requests
import controle_week_end09 as ctl

ICI = Path(__file__).resolve().parent
UTC = dt.timezone.utc
FAPI = "https://fapi.binance.com"
CAL = {"mp": "mp", "act": "act", "temoin_mp": "mp", "temoin_act": "act"}      # groupe → calendrier
ORDRE = ["mp", "act", "temoin_mp", "temoin_act"]
PRECEDENT = {"act": "mp", "temoin_act": "temoin_mp"}                          # places du plafond déjà prises
DELAI_POSITIONS = dt.timedelta(minutes=65)

C_SIGNAUX = ["vendredi", "groupe", "symbole", "ecrit_utc", "p_cloture", "p_decision", "M", "sigma", "rapport", "signal",
             "sens", "retenu", "rang"]
C_PASSAGES = ["vendredi", "groupe", "statut", "ecrit_utc", "eligibles", "signaux", "retenus", "places", "empreinte"]
C_POSITIONS = ["vendredi", "groupe", "symbole", "sens", "sigma", "t_entree", "entree", "niveau_stop", "statut", "t_sortie",
               "sortie_base", "sortie_stressee", "brut_base", "brut_stressee", "financement", "net_base", "net_stressee",
               "net_couts_doubles", "calcule_utc"]
C_SEMAINES = ["vendredi", "exclu", "positions", "base", "stressee", "couts_doubles", "temoin_positions", "temoin",
              "incidents", "calcule_utc"]


def _r(x):
    """Nombre écrit en entier, sans perte (float Python, jamais np.float64)."""
    return repr(float(x))


# ---------------------------------------------------------------- configuration et calendrier

class Config:
    def __init__(self, chemin):
        c = json.loads(Path(chemin).read_text())
        d, p = c["decide_le_19_11_2026"], c["parametres_papier"]
        self.brut = c
        self.statut = c["statut"]
        self.k, self.m, self.K = float(d["k_sigma"]), float(d["m"]), int(d["K_positions_max_par_week_end"])
        assert int(d["H_heures"]) == 2 and int(d["N_sigma_rendements"]) == ctl.N_SIGMA, "H et N sont fixés dans le calendrier du contrôle"
        self.univers = {"mp": d["univers"]["matieres_premieres"], "act": d["univers"]["actions"],
                        "temoin_mp": d["temoins"], "temoin_act": d["temoins"]}
        pr = c["precisions_de_regles_a_valider_au_gel"]
        self.feries = {dt.date.fromisoformat(x) for x in pr["feries_proposes_vendredi_ou_lundi"]}
        self.courtes = {dt.date.fromisoformat(x) for x in pr.get("seances_courtes_exclues", [])}   # vendredis à clôture avancée
        self.frais, self.g_entree, self.g_sortie, self.g_stop = (float(p[x]) for x in ("frais", "glissement_entree", "glissement_sortie", "glissement_stop"))
        self.fenetre = dt.timedelta(minutes=int(p["fenetre_signal_minutes"]))
        self.premier = dt.date.fromisoformat(p["premier_vendredi"]) if p.get("premier_vendredi") else None
        pg = d.get("plafond_grappe") or {}
        self.grappe, self.max_grappe = set(pg.get("symboles", [])), int(pg.get("max_positions", self.K))

    def exclu(self, v):
        """Week-end exclu d'avance : vendredi ou lundi férié, ou vendredi à séance courte (clôture avancée)."""
        return v in self.feries or (v + dt.timedelta(days=3)) in self.feries or v in self.courtes


def vendredis(premier, maintenant):
    """Vendredis du papier dont la clôture est passée, du premier jusqu'à maintenant."""
    out, v = [], premier
    while ctl.calendrier(v, "act")["cloture"] <= maintenant:
        out.append(v)
        v += dt.timedelta(weeks=1)
    return out


# ---------------------------------------------------------------- source de données (remplacée par un faux dans les tests)

class Source:
    def __init__(self):
        self.s = requests.Session()

    def _get(self, chemin, params):
        for essai in range(5):
            try:
                r = self.s.get(FAPI + chemin, params=params, timeout=30)
                if r.status_code == 200:
                    time.sleep(0.2)
                    return r.json()
                if r.status_code in (400, 404):
                    return []
            except requests.exceptions.RequestException:
                pass
            time.sleep(3 + 3 * essai)
        raise RuntimeError(f"échec {chemin} {params}")

    @staticmethod
    def _ms(t):
        return int(t.replace(tzinfo=UTC).timestamp() * 1000)

    def _bougies(self, chemin, cle, sym, intervalle, debut, fin):
        pas = {"1m": 60_000, "1h": 3_600_000}[intervalle]
        lignes, t, f = [], self._ms(debut), self._ms(fin)
        while t <= f:
            k = self._get(chemin, {cle: sym, "interval": intervalle, "startTime": t, "endTime": f, "limit": 1500})
            if not k:
                break
            lignes += k
            t = int(k[-1][0]) + pas
            if len(k) < 1500:
                break
        df = pd.DataFrame({"open": [float(x[1]) for x in lignes], "high": [float(x[2]) for x in lignes],
                           "low": [float(x[3]) for x in lignes]}, index=pd.to_datetime([int(x[0]) for x in lignes], unit="ms"))
        return df[~df.index.duplicated()].sort_index()

    def contrat(self, sym, intervalle, debut, fin):
        return self._bougies("/fapi/v1/klines", "symbol", sym, intervalle, debut, fin)

    def marque(self, sym, intervalle, debut, fin):
        return self._bougies("/fapi/v1/markPriceKlines", "symbol", sym, intervalle, debut, fin)

    def financement(self, sym, debut, fin):
        f = self._get("/fapi/v1/fundingRate", {"symbol": sym, "startTime": self._ms(debut), "endTime": self._ms(fin), "limit": 1000})
        return [(pd.Timestamp(int(x["fundingTime"]), unit="ms").to_pydatetime(), float(x["fundingRate"])) for x in f]


# ---------------------------------------------------------------- journaux en ajout seul

class Ajout:
    def __init__(self, chemin, colonnes, cle):
        self.chemin, self.colonnes, self.cle = Path(chemin), colonnes, cle

    def lire(self):
        if not self.chemin.exists():
            return []
        with self.chemin.open(newline="") as f:
            return list(csv.DictReader(f))

    def cles(self):
        return {tuple(r[c] for c in self.cle) for r in self.lire()}

    def ajouter(self, lignes):
        connus, nouveaux = self.cles(), []
        for l in lignes:
            l = {c: ("" if l.get(c) is None else str(l[c])) for c in self.colonnes}
            k = tuple(l[c] for c in self.cle)
            if k not in connus:
                nouveaux.append(l)
                connus.add(k)
        if nouveaux:
            neuf = not self.chemin.exists()
            self.chemin.parent.mkdir(parents=True, exist_ok=True)
            with self.chemin.open("a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=self.colonnes)
                if neuf:
                    w.writeheader()
                w.writerows(nouveaux)
        return len(nouveaux)


def journaux(sorties):
    s = Path(sorties)
    return {"signaux": Ajout(s / "signaux.csv", C_SIGNAUX, ["vendredi", "groupe", "symbole"]),
            "passages": Ajout(s / "passages.csv", C_PASSAGES, ["vendredi", "groupe"]),
            "positions": Ajout(s / "positions.csv", C_POSITIONS, ["vendredi", "groupe", "symbole"]),
            "semaines": Ajout(s / "semaines.csv", C_SEMAINES, ["vendredi"])}


# ---------------------------------------------------------------- 1. signaux

def evenement(df, v, cal, k):
    """M, σ et signal d'un contrat avec les seules bougies ≤ décision (même calcul que le contrôle, seuil k)."""
    c = ctl.calendrier(v, cal)
    df = ctl.couper(df, c["decision"])
    p0, p1 = df["open"].get(c["cloture"]), df["open"].get(c["decision"])
    s = ctl.sigma(df, v, cal)
    if p0 is None or p1 is None or s is None or s <= 0 or not np.isfinite(p0) or not np.isfinite(p1):
        return None
    m = p1 / p0 - 1
    return {"p_cloture": p0, "p_decision": p1, "M": m, "sigma": s, "rapport": abs(m) / s, "signal": abs(m) >= k * s,
            "sens": -1 if m > 0 else 1}


def places_libres(cfg, J, v, g):
    if g not in PRECEDENT:
        return cfg.K
    pris = sum(1 for r in J["signaux"].lire() if r["vendredi"] == str(v) and r["groupe"] == PRECEDENT[g] and r["retenu"] == "1")
    return cfg.K - pris


def choisir(tri, places, grappe, max_grappe):
    """Signaux retenus dans l'ordre de |M|/σ décroissant : au plus `places`, dont au plus `max_grappe` de la grappe.
    Un signal de la grappe au-delà de son plafond est écarté et la place va au signal suivant hors grappe."""
    retenus, n_grappe = {}, 0
    for s, _ in tri:
        if len(retenus) >= max(places, 0):
            break
        if s in grappe:
            if n_grappe >= max_grappe:
                continue
            n_grappe += 1
        retenus[s] = len(retenus) + 1
    return retenus


def ecrire_signaux(cfg, src, J, v, g, maintenant):
    cal = CAL[g]
    c = ctl.calendrier(v, cal)
    debut = ctl.ny(v - dt.timedelta(days=75), 0)
    ev = {}
    for s in cfg.univers[g]:
        e = evenement(src.contrat(s, "1h", debut, c["decision"]), v, cal, cfg.k)
        if e is not None:
            ev[s] = e
    places = places_libres(cfg, J, v, g)
    tri = sorted(((s, e["rapport"]) for s, e in ev.items() if e["signal"]), key=lambda x: (-x[1], x[0]))
    retenus = choisir(tri, places, cfg.grappe if g == "act" else set(), cfg.max_grappe)
    ecrit = maintenant.strftime("%Y-%m-%dT%H:%M:%SZ")
    lignes = [{"vendredi": v, "groupe": g, "symbole": s, "ecrit_utc": ecrit, "p_cloture": _r(e["p_cloture"]),
               "p_decision": _r(e["p_decision"]), "M": _r(e["M"]), "sigma": _r(e["sigma"]), "rapport": _r(e["rapport"]),
               "signal": int(e["signal"]), "sens": e["sens"], "retenu": int(s in retenus), "rang": retenus.get(s, "")}
              for s, e in sorted(ev.items())]
    J["signaux"].ajouter(lignes)
    emp = hashlib.sha256(json.dumps(lignes, default=str, sort_keys=True).encode()).hexdigest()[:16]
    J["passages"].ajouter([{"vendredi": v, "groupe": g, "statut": "ecrit", "ecrit_utc": ecrit, "eligibles": len(ev),
                            "signaux": len(tri), "retenus": len(retenus), "places": places, "empreinte": emp}])
    return len(retenus)


def etape_signaux(cfg, src, J, liste, maintenant):
    faits, incidents = J["passages"].cles(), []
    for v in liste:
        if cfg.exclu(v):
            continue
        for g in ORDRE:
            if (str(v), g) in faits:
                continue
            d = ctl.calendrier(v, CAL[g])["decision"]
            if d <= maintenant < d + cfg.fenetre:
                ecrire_signaux(cfg, src, J, v, g, maintenant)
            elif maintenant >= d + cfg.fenetre:
                J["passages"].ajouter([{"vendredi": v, "groupe": g, "statut": "manque",
                                        "ecrit_utc": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ")}])
                incidents.append(f"{v} {g} : signal non écrit dans la fenêtre")
    return incidents


# ---------------------------------------------------------------- 2. positions

def premiere_minute_apres(t):
    return t.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)


def chercher_stop(barres, sens, niveau):
    """Première barre (dans l'ordre du temps) où la marque touche le niveau. Renvoie (t, base, stressée) ou None.
    Base : pire du niveau et de l'ouverture (écart compté en entier). Stressée : mi-chemin entre la base et l'extrême
    de la barre (mode 1 de STRAT-06)."""
    for t, b in barres.iterrows():
        if sens > 0 and b["low"] <= niveau:
            base = min(niveau, b["open"])
            return t.to_pydatetime(), base, 0.5 * (base + min(base, b["low"]))
        if sens < 0 and b["high"] >= niveau:
            base = max(niveau, b["open"])
            return t.to_pydatetime(), base, 0.5 * (base + max(base, b["high"]))
    return None


def jouer_position(cfg, src, sig, v, g, maintenant):
    c = ctl.calendrier(v, CAL[g])
    assert maintenant >= c["sortie"] + DELAI_POSITIONS, "issue demandée trop tôt"
    s, sens, sigma = sig["symbole"], int(sig["sens"]), float(sig["sigma"])
    t_e = premiere_minute_apres(dt.datetime.strptime(sig["ecrit_utc"], "%Y-%m-%dT%H:%M:%SZ"))
    k1 = src.contrat(s, "1m", t_e, t_e)
    if t_e not in k1.index:
        return None
    entree = float(k1.loc[t_e, "open"])
    niveau = entree * (1 - sens * cfg.m * cfg.k * sigma)
    fin_heure = c["decision"] + dt.timedelta(minutes=59)
    barres = pd.concat([src.marque(s, "1m", t_e, fin_heure),
                        src.marque(s, "1h", c["decision"] + dt.timedelta(hours=1), c["sortie"] - dt.timedelta(hours=1))])
    barres = barres[(barres.index >= t_e) & (barres.index < c["sortie"])].sort_index()
    stop = chercher_stop(barres, sens, niveau)
    if stop:
        t_s, sortie_b, sortie_s = stop
        g_sortie, statut = cfg.g_stop, "stop"
    else:
        kh = src.contrat(s, "1h", c["sortie"], c["sortie"])
        if c["sortie"] not in kh.index:
            return None
        t_s, sortie_b, statut = c["sortie"], float(kh.loc[c["sortie"], "open"]), "sortie"
        sortie_s, g_sortie = sortie_b, cfg.g_sortie
    fin_fin = max(t_s, t_e)
    fin_ = sum(-sens * r for t, r in src.financement(s, t_e, fin_fin) if t_e < t <= fin_fin)
    brut_b, brut_s = sens * (sortie_b / entree - 1), sens * (sortie_s / entree - 1)
    couts = 2 * cfg.frais + cfg.g_entree + g_sortie
    return {"vendredi": v, "groupe": g, "symbole": s, "sens": sens, "sigma": _r(sigma), "t_entree": t_e.isoformat(),
            "entree": _r(entree), "niveau_stop": _r(niveau), "statut": statut, "t_sortie": t_s.isoformat(),
            "sortie_base": _r(sortie_b), "sortie_stressee": _r(sortie_s), "brut_base": _r(brut_b), "brut_stressee": _r(brut_s),
            "financement": _r(fin_), "net_base": _r(brut_b - couts + fin_), "net_stressee": _r(brut_s - couts + fin_),
            "net_couts_doubles": _r(brut_b - 2 * couts + fin_), "calcule_utc": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ")}


def etape_positions(cfg, src, J, maintenant):
    faits, incidents, n = J["positions"].cles(), [], 0
    ecrits = {(r["vendredi"], r["groupe"]) for r in J["passages"].lire() if r["statut"] == "ecrit"}
    for sig in J["signaux"].lire():
        if sig["retenu"] != "1" or (sig["vendredi"], sig["groupe"]) not in ecrits:
            continue
        if (sig["vendredi"], sig["groupe"], sig["symbole"]) in faits:
            continue
        v, g = dt.date.fromisoformat(sig["vendredi"]), sig["groupe"]
        if maintenant < ctl.calendrier(v, CAL[g])["sortie"] + DELAI_POSITIONS:
            continue
        p = jouer_position(cfg, src, sig, v, g, maintenant)
        if p is None:
            incidents.append(f"{v} {g} {sig['symbole']} : prix d'entrée ou de sortie absent, nouvel essai au passage suivant")
            continue
        n += J["positions"].ajouter([p])
    return n, incidents


# ---------------------------------------------------------------- 3. semaines et état

def etape_semaines(cfg, J, liste, maintenant):
    deja = J["semaines"].cles()
    passages = {(r["vendredi"], r["groupe"]): r["statut"] for r in J["passages"].lire()}
    retenus = [r for r in J["signaux"].lire() if r["retenu"] == "1"]
    pos = {(r["vendredi"], r["groupe"], r["symbole"]): r for r in J["positions"].lire()}
    ecrit = maintenant.strftime("%Y-%m-%dT%H:%M:%SZ")
    for v in liste:
        sv = str(v)
        if (sv,) in deja:
            continue
        if cfg.exclu(v):
            J["semaines"].ajouter([{"vendredi": sv, "exclu": 1, "calcule_utc": ecrit}])
            continue
        if any((sv, g) not in passages for g in ORDRE):
            continue
        attendus = [r for r in retenus if r["vendredi"] == sv and passages[(sv, r["groupe"])] == "ecrit"]
        if any((sv, r["groupe"], r["symbole"]) not in pos for r in attendus):
            continue
        p = [pos[(sv, r["groupe"], r["symbole"])] for r in attendus]
        pr = [x for x in p if not x["groupe"].startswith("temoin")]
        pt = [x for x in p if x["groupe"].startswith("temoin")]
        somme = lambda L, c: sum(float(x[c]) for x in L) / cfg.K
        J["semaines"].ajouter([{"vendredi": sv, "exclu": 0, "positions": len(pr), "base": _r(somme(pr, "net_base")),
                                "stressee": _r(somme(pr, "net_stressee")), "couts_doubles": _r(somme(pr, "net_couts_doubles")),
                                "temoin_positions": len(pt), "temoin": _r(somme(pt, "net_base")),
                                "incidents": sum(1 for g in ORDRE if passages[(sv, g)] == "manque"), "calcule_utc": ecrit}])


def etat(J, maintenant, incidents):
    s = [r for r in J["semaines"].lire() if r["exclu"] == "0"]
    res = {"maintenant_utc": maintenant.strftime("%Y-%m-%dT%H:%M:%SZ"), "week_ends_comptes": len(s),
           "week_ends_actifs": sum(1 for r in s if int(r["positions"]) > 0), "positions": sum(int(r["positions"]) for r in s),
           "incidents_du_passage": incidents}
    for c in ("base", "stressee", "couts_doubles", "temoin"):
        r = np.array([float(x[c]) for x in s]) if s else np.array([])
        cap = np.cumprod(1 + r) if len(r) else np.array([1.0])
        res[c] = {"net_cumule": float(cap[-1] - 1), "drawdown_max": float(np.max(1 - cap / np.maximum.accumulate(np.r_[1.0, cap])[1:])) if len(r) else 0.0,
                  "sharpe_annualise": float(r.mean() / r.std(ddof=1) * math.sqrt(52)) if len(r) > 2 and r.std(ddof=1) > 0 else None}
    return res


def passage(cfg, src, sorties, maintenant, signaux_seulement):
    J = journaux(sorties)
    liste = vendredis(cfg.premier, maintenant)
    inc = etape_signaux(cfg, src, J, liste, maintenant)
    if not signaux_seulement:
        n, inc2 = etape_positions(cfg, src, J, maintenant)
        inc += inc2
        etape_semaines(cfg, J, liste, maintenant)
    e = etat(J, maintenant, inc)
    e["signaux_seulement"] = signaux_seulement
    Path(sorties, "etat.json").write_text(json.dumps(e, indent=1, ensure_ascii=False))
    if inc:
        with Path(sorties, "incidents.csv").open("a") as f:
            for x in inc:
                f.write(f"{e['maintenant_utc']},{x}\n")
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ICI / "config_week_end09.json"))
    ap.add_argument("--donnees", required=True, help="réservé (les prix sont relus à Binance et consignés dans les journaux)")
    ap.add_argument("--sorties", required=True)
    ap.add_argument("--maintenant", help="essai à blanc sur une date passée : signaux seulement")
    ap.add_argument("--premier-vendredi", help="essai à blanc seulement")
    a = ap.parse_args()
    cfg = Config(a.config)
    if a.maintenant:
        maintenant = dt.datetime.fromisoformat(a.maintenant)
        if a.premier_vendredi:
            cfg.premier = dt.date.fromisoformat(a.premier_vendredi)
        signaux_seulement = True                     # jamais d'issue sur une date passée
    else:
        if cfg.statut != "figee" or cfg.premier is None:
            raise SystemExit("configuration non figée ou premier vendredi absent : le papier ne tourne pas")
        maintenant = dt.datetime.now(UTC).replace(tzinfo=None)
        signaux_seulement = False
    Path(a.sorties).mkdir(parents=True, exist_ok=True)
    e = passage(cfg, Source(), a.sorties, maintenant, signaux_seulement)
    print(json.dumps({k: e[k] for k in ("maintenant_utc", "week_ends_comptes", "positions", "incidents_du_passage", "signaux_seulement")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
