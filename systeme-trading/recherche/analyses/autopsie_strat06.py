#!/usr/bin/env python3
"""Autopsie empirique de STRAT-20261102-06 (05/11/2026). Lit seulement les sorties déjà publiées des essais
(base continue CDV, E11 sans stop) et les diagnostics. Aucune donnée de marché nouvelle, aucun réseau, hors N.
Usage : python3 -B autopsie_strat06.py"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
RES = ICI.parent.parent / "strategies" / "STRAT-20261102-06" / "resultats"
OUT = ICI / "sorties_strat06"
OUT.mkdir(exist_ok=True)
NT = 1 / 12
H = pd.Timedelta(hours=1)
pd.set_option("display.width", 200)


def charger(nom):
    l = pd.read_csv(RES / f"{nom}_lignes.csv", parse_dates=["t_sortie", "lundi"])
    l = l[l.statut != "absent"].copy()
    l["entree_t"] = l["lundi"] + H
    l["jours"] = (l["t_sortie"] - l["entree_t"]).dt.total_seconds() / 86400
    l["r_px"] = l["sortie"] / l["entree"] - 1
    l["g"] = l["pnl_prix"] + l["financement"]
    return l


base, e11 = charger("CDV_controle_reproduction"), charger("E11")
cot = pd.concat([pd.read_csv(RES / f"DIAG_{e}_classement_noms.csv") for e in ("E01", "E02")]).drop_duplicates("symbole")
cot["cotation_perp"] = pd.to_datetime(cot["cotation_perp"])
cl = cot.set_index("symbole")
fac = pd.concat([pd.read_csv(RES / f"DIAG_{e}_facteurs.csv", index_col=0, parse_dates=True) for e in ("E01", "E02")])
fac = fac[~fac.index.duplicated()]
sem = pd.read_csv(RES / "CDV_controle_reproduction_semaines.csv", parse_dates=["lundi"])
R = {}

def ajouter_age(x):
    x = x.copy()
    x["age_j"] = [(t - cl.loc[s, "cotation_perp"]).days if s in cl.index else np.nan for s, t in zip(x.symbole, x.lundi)]
    x["classe"] = [cl.loc[s, "classe"] if s in cl.index else "n.d." for s in x.symbole]
    return x

sh = ajouter_age(base[base.symbole != "BTC"])
sh11 = ajouter_age(e11[e11.symbole != "BTC"])

# ---- A. stops
st = sh[sh.statut == "stop"].copy()
st["heures_apres_entree"] = (st["t_sortie"] - st["entree_t"]).dt.total_seconds() / 3600
st["jour_semaine"] = st["t_sortie"].dt.day_name()
st["heure_utc"] = st["t_sortie"].dt.hour
st["jour_de_tenue"] = np.floor(st["heures_apres_entree"] / 24).astype(int) + 1
A = {"stops_shorts": len(st), "stops_btc": int(((base.symbole == "BTC") & (base.statut == "stop")).sum()),
     "taux_stop": len(st) / len(sh),
     "quantiles_heures": st["heures_apres_entree"].quantile([.1, .25, .5, .75, .9]).round(1).to_dict(),
     "part_24h": float((st.heures_apres_entree < 24).mean()), "part_48h": float((st.heures_apres_entree < 48).mean()),
     "par_jour_de_tenue": st["jour_de_tenue"].value_counts().sort_index().to_dict(),
     "par_jour_semaine": st["jour_semaine"].value_counts().to_dict(),
     "par_tranche_horaire_utc": pd.cut(st.heure_utc, [-1, 5, 11, 17, 23], labels=["00-05", "06-11", "12-17", "18-23"]).value_counts().sort_index().to_dict(),
     "taux_stop_par_tranche_age": sh.assign(t=pd.cut(sh.age_j, [6, 13, 27, 60])).groupby("t", observed=True).apply(lambda g: round((g.statut == "stop").mean(), 3)).astype(str).to_dict(),
     "taux_stop_par_annee": sh.groupby(sh.lundi.dt.year).apply(lambda g: round((g.statut == "stop").mean(), 3)).to_dict(),
     "perte_moyenne_stop_brut": float(st.g.mean()), "perte_totale_stops_prix": float(st.pnl_prix.sum()),
     "gain_total_non_stop_prix": float(sh[sh.statut != "stop"].pnl_prix.sum())}
# chi2 d'uniformité sur les 7 jours de tenue
obs = np.array([A["par_jour_de_tenue"].get(k, 0) for k in range(1, 8)])
A["chi2_uniformite_7_jours"] = float(((obs - obs.mean()) ** 2 / obs.mean()).sum())
R["A_stops"] = A
st[["symbole", "lundi", "t_sortie", "heures_apres_entree", "age_j", "classe", "g"]].to_csv(OUT / "stops_base.csv", index=False)

# ---- B. top 20 gains et pertes (lignes de shorts)
vol = sh11.groupby("symbole")["r_px"].std().rename("vol_hebdo_nom_sans_stop")
sh = sh.join(vol, on="symbole")
cols = ["symbole", "lundi", "statut", "r_px", "g", "financement", "age_j", "classe", "vol_hebdo_nom_sans_stop"]
top_g, top_p = sh.nlargest(20, "g")[cols], sh.nsmallest(20, "g")[cols]
top_g.to_csv(OUT / "top20_gains.csv", index=False); top_p.to_csv(OUT / "top20_pertes.csv", index=False)
def resume(x):
    return {"gain_total": float(x.g.sum()), "r_px_median": float(x.r_px.median()), "age_median_j": float(x.age_j.median()),
            "vol_hebdo_mediane": float(x.vol_hebdo_nom_sans_stop.median()), "stops": int((x.statut == "stop").sum()),
            "classes": x.classe.value_counts().to_dict(), "annees": x.lundi.dt.year.value_counts().sort_index().to_dict(),
            "noms_distincts": int(x.symbole.nunique())}
R["B_top20"] = {"gains": resume(top_g), "pertes": resume(top_p), "part_gain_net_top20_gains": float(top_g.g.sum() / sh.g.sum()),
                "vol_hebdo_mediane_tous": float(sh.vol_hebdo_nom_sans_stop.median())}

# ---- C. persistance
def runs(x):
    out = []
    for s, g in x.sort_values("lundi").groupby("symbole"):
        d = g.lundi.tolist(); gg = g.g.tolist(); deb, k, acc = d[0], 1, gg[0]
        for i in range(1, len(d)):
            if (d[i] - d[i - 1]).days == 7:
                k += 1; acc += gg[i]
            else:
                out.append((s, deb, k, acc)); deb, k, acc = d[i], 1, gg[i]
        out.append((s, deb, k, acc))
    return pd.DataFrame(out, columns=["symbole", "debut", "semaines", "gain"])
ru = runs(sh)
parnom = sh.groupby("symbole").agg(lignes=("g", "size"), gain=("g", "sum"), stops=("statut", lambda s: int((s == "stop").sum())))
parnom = parnom.join(cl["classe"]).sort_values("gain", ascending=False)
parnom.to_csv(OUT / "gain_par_nom.csv"); ru.to_csv(OUT / "series_de_detention.csv", index=False)
R["C_persistance"] = {"noms": int(len(parnom)), "series": int(len(ru)),
    "semaines_par_serie_distribution": ru.semaines.value_counts().sort_index().to_dict(),
    "semaines_par_serie_moyenne": float(ru.semaines.mean()), "lignes_par_nom_moyenne": float(parnom.lignes.mean()),
    "gain_moyen_par_serie_selon_longueur": ru.groupby(ru.semaines.clip(upper=6)).gain.mean().round(4).to_dict(),
    "noms_perdants": int((parnom.gain < 0).sum()), "part_noms_perdants": float((parnom.gain < 0).mean()),
    "top10": parnom.head(10).gain.round(4).to_dict(), "bottom10": parnom.tail(10).gain.round(4).to_dict(),
    "part_gain_top10_noms": float(parnom.head(10).gain.sum() / parnom.gain.sum()),
    "part_gain_top30_noms": float(parnom.head(30).gain.sum() / parnom.gain.sum()),
    "gain_median_par_nom": float(parnom.gain.median())}

# ---- D. financement
sh["f_annualise_short"] = sh.financement / NT / sh.jours.clip(lower=1 / 24) * 365  # >0 : le short reçoit
d = sh.f_annualise_short
bt = base[base.symbole == "BTC"].copy(); bt["f_ann_long"] = -bt.financement / (bt.valeur_fin.abs() / (1 + bt.pnl_prix / bt.valeur_fin.abs()).clip(lower=0.01)) # approx, non utilisé
D = {"lignes": int(len(d)), "quantiles_ann": d.quantile([.01, .05, .1, .25, .5, .75, .9, .95, .99]).round(3).to_dict(),
     "part_short_paie_plus_10pct": float((d < -0.10).mean()), "part_short_paie_plus_50pct": float((d < -0.50).mean()),
     "part_short_paie_plus_100pct": float((d < -1.00).mean()), "part_short_recoit_plus_10pct": float((d > 0.10).mean()),
     "financement_total_shorts": float(sh.financement.sum()), "par_annee_total": sh.groupby(sh.lundi.dt.year).financement.sum().round(4).to_dict(),
     "par_annee_part_paie_10pct": sh.groupby(sh.lundi.dt.year).f_annualise_short.apply(lambda s: round(float((s < -0.10).mean()), 3)).to_dict(),
     "par_tranche_age_median": sh.assign(t=pd.cut(sh.age_j, [6, 13, 27, 60])).groupby("t", observed=True).f_annualise_short.median().round(3).astype(str).to_dict(),
     "taux_stop_si_paie_50pct": float((sh[d < -0.5].statut == "stop").mean()), "taux_stop_sinon": float((sh[d >= -0.5].statut == "stop").mean()),
     "financement_btc_total": float(base[base.symbole == "BTC"].financement.sum())}
pires = sh.nsmallest(10, "f_annualise_short")[["symbole", "lundi", "statut", "jours", "f_annualise_short", "r_px", "g"]]
pires.to_csv(OUT / "pires_financements.csv", index=False)
D["pires_10"] = [f"{r.symbole} {r.lundi.date()} {r.statut} {r.f_annualise_short:+.1%}/an r_px {r.r_px:+.1%}" for r in pires.itertuples()]
R["D_financement"] = D

# ---- E. corrélation interne (rendements hebdomadaires non tronqués de E11, même sélection que la base)
x = sh11[["symbole", "lundi", "r_px"]].copy()
mu, s2 = x.r_px.mean(), x.r_px.var()
num = den = 0.0
corr_sem = []
for t, g in x.groupby("lundi"):
    n = len(g)
    if n < 2:
        continue
    dv = g.r_px.to_numpy() - mu
    num += dv.sum() ** 2 - (dv ** 2).sum(); den += n * (n - 1)
    corr_sem.append((t, n, g.r_px.mean(), g.r_px.std(ddof=1)))
rho = num / den / s2
cs = pd.DataFrame(corr_sem, columns=["lundi", "n", "moy", "ecart_type"]).set_index("lundi")
cs = cs.join(fac[["btc", "alts"]]).join(sem.set_index("lundi")["net"])
crise = cs.nsmallest(int(len(cs) * 0.1), "net")
def rho_sur(idx):
    nu = de = 0.0
    for t, g in x[x.lundi.isin(idx)].groupby("lundi"):
        if len(g) < 2: continue
        dv = g.r_px.to_numpy() - mu; nu += dv.sum() ** 2 - (dv ** 2).sum(); de += len(g) * (len(g) - 1)
    return nu / de / s2 if de else np.nan
x2 = x.join(fac[["btc", "alts"]], on="lundi").dropna()
b_btc = np.polyfit(x2.btc, x2.r_px, 1)[0]; b_alt = np.polyfit(x2.alts, x2.r_px, 1)[0]
r2_alt = np.corrcoef(x2.alts, x2.r_px)[0, 1] ** 2
x2["resid"] = x2.r_px - np.polyval(np.polyfit(x2.alts, x2.r_px, 1), x2.alts)
nu = de = 0.0
for t, g in x2.groupby("lundi"):
    if len(g) < 2: continue
    dv = g.resid.to_numpy() - g.resid.mean() * 0 - x2.resid.mean(); nu += dv.sum() ** 2 - (dv ** 2).sum(); de += len(g) * (len(g) - 1)
rho_resid = nu / de / x2.resid.var()
R["E_correlation"] = {"lignes": int(len(x)), "semaines_2_noms_ou_plus": int(len(cs)), "rho_moyen_toutes_semaines": float(rho),
    "rho_10pct_pires_semaines": float(rho_sur(crise.index)), "rho_semaines_btc_sup_10pct": float(rho_sur(cs[cs.btc > 0.10].index)),
    "rho_semaines_alts_sup_15pct": float(rho_sur(cs[cs.alts > 0.15].index)), "rho_residuel_apres_facteur_alts": float(rho_resid),
    "beta_nom_sur_btc": float(b_btc), "beta_nom_sur_panier_alts": float(b_alt), "r2_nom_sur_panier_alts": float(r2_alt),
    "pires_semaines_moyenne_shorts_r_px": float(crise.moy.mean()), "pires_semaines_alts": float(crise.alts.mean()), "pires_semaines_btc": float(crise.btc.mean()),
    "ecart_type_hebdo_nom": float(np.sqrt(s2))}
# n effectif : N / (1 + (N-1) rho) pour 6 noms
R["E_correlation"]["n_effectif_6_noms"] = float(6 / (1 + 5 * rho))
crise.to_csv(OUT / "semaines_de_crise.csv")

# ---- F. queue droite (E11, rendements non tronqués)
F = {}
for seuil in (0.3, 0.5, 1.0):
    q = sh11[sh11.r_px >= seuil]
    F[f"r_px_sup_{int(seuil*100)}pct"] = {"lignes": int(len(q)), "part": float(len(q) / len(sh11)), "noms": int(q.symbole.nunique()),
        "annees": q.lundi.dt.year.value_counts().sort_index().to_dict(), "age_median_j": float(q.age_j.median()),
        "classes": q.classe.value_counts().to_dict(), "perte_totale_sans_stop": float(q.g.sum())}
gauche = sh11[sh11.r_px <= -0.3]
F["r_px_inf_moins30pct"] = {"lignes": int(len(gauche)), "part": float(len(gauche) / len(sh11)), "gain_total_sans_stop": float(gauche.g.sum())}
F["asymetrie_skew_r_px"] = float(sh11.r_px.skew()); F["kurtosis_r_px"] = float(sh11.r_px.kurt())
F["quantiles_r_px"] = sh11.r_px.quantile([.01, .05, .25, .5, .75, .95, .99]).round(3).to_dict()
F["part_lignes_baissieres"] = float((sh11.r_px < 0).mean())
ext = sh11.nlargest(15, "r_px")[["symbole", "lundi", "r_px", "age_j", "classe"]]
ext.to_csv(OUT / "queue_droite_top15.csv", index=False)
F["top15"] = [f"{r.symbole} {r.lundi.date()} {r.r_px:+.0%} age {r.age_j:.0f} j" for r in ext.itertuples()]
# série suivante : le nom poursuit-il sa hausse la semaine d'après ?
nxt = []
for r in sh11[sh11.r_px >= 0.5].itertuples():
    n2 = sh11[(sh11.symbole == r.symbole) & (sh11.lundi == r.lundi + pd.Timedelta(days=7))]
    if len(n2): nxt.append(float(n2.r_px.iloc[0]))
F["semaine_suivante_apres_hausse_50pct"] = {"cas": len(nxt), "moyenne": float(np.mean(nxt)) if nxt else None, "mediane": float(np.median(nxt)) if nxt else None,
    "part_baisse": float(np.mean(np.array(nxt) < 0)) if nxt else None}
R["F_queue"] = F

def cles(o):
    if isinstance(o, dict):
        return {str(k): cles(v) for k, v in o.items()}
    if isinstance(o, list):
        return [cles(v) for v in o]
    return o
R = cles(R)
(OUT / "autopsie_strat06.json").write_text(json.dumps(R, indent=1, default=str, ensure_ascii=False))
print(json.dumps(R, indent=1, default=str, ensure_ascii=False))
