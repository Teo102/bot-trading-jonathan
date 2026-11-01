"""Repères chiffrés de AVENANT_AVANT_E10.md. Aucune donnée du hors échantillon : seuls T, N et V y entrent.
T = 457 jours (20250801-20261031). V réévaluée vient de sensibilite_dsr_meta.json, mise à l'échelle par 1673 / T."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
import analyse_strat as A
meta = json.loads((ROOT/"resultats/sensibilite_dsr_meta.json").read_text(encoding="utf-8"))
T = 457; V = meta["V_reevalue_11"]; Ve = V*1673/T; out = {"T": T, "V_reevalue_11": V, "V_echelle": Ve, "cas": []}
def sharpe_requis(sr0, t, seuil=0.95):
    # plus petit Sharpe quotidien tel que PSR(SR0) >= seuil, g3 = 0 et g4 = 3 (hypothèse normale)
    lo, hi = -1.0, 2.0
    for _ in range(200):
        mid = (lo+hi)/2
        if A.probabilistic_sharpe(mid, sr0, t, 0.0, 3.0) >= seuil: hi = mid
        else: lo = mid
    return hi
for n in (14, 15, 21, 28):
    for lab, v in (("V mise a l'echelle", Ve), ("V commune", V), ("V 1/T", 1.0/T)):
        s0 = A.expected_max_sharpe(v, n)
        out["cas"].append(dict(N=n, V=lab, v=v, sr0_annualise=A.annualize(s0), sharpe_annualise_requis_dsr_095=A.annualize(sharpe_requis(s0, T))))
from scipy import stats; import numpy as np
g = float(np.euler_gamma); emax = lambda n: (1-g)*stats.norm.ppf(1-1/n)+g*stats.norm.ppf(1-1/(n*math.e))
out["repere_sharpe_annuel"] = {str(n): float(emax(n)/math.sqrt(T/365)) for n in (14, 15, 21, 28)}
print(json.dumps(out, ensure_ascii=False, indent=1))
(Path(__file__).resolve().parent/"sorties/avenant_reperes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
