# STRAT-20261031-04 : localisation de la bascule d'horodatage de l'archive metrics (aucun rendement de trade).
# Usage : python -I mesure_bascule_horodatage.py <dossier contenant cache_vision et cache_5m>
# Compare, jour par jour, la correlation entre |variation d'OI| et |rendement 5 min| aux pas -1 et 0.

import zipfile,requests,pandas as pd,sys
from pathlib import Path
SC=Path(sys.argv[1]); cm=SC/"cache_vision"; c5=SC/"cache_5m"
res={}
for sym in ["BTCUSDT","ETHUSDT"]:
    months=pd.period_range("2021-12","2026-09",freq="M")
    out=[]
    for per in months:
        n=f"{sym}-5m-{per.year}-{per.month:02d}.zip"; c=c5/n
        if not c.exists():
            r=requests.get(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/5m/{n}",timeout=60); r.raise_for_status(); c.write_bytes(r.content)
        with zipfile.ZipFile(c) as z, z.open(z.namelist()[0]) as f:
            k=pd.read_csv(f,header=None,usecols=[0,1,4])
        if str(k.iloc[0,0])=="open_time": k=k.iloc[1:]
        k.columns=["t","o","c"]; k=k.astype(float)
        k.index=pd.to_datetime(k.t.astype("int64"),unit="ms",utc=True).astype("datetime64[ns, UTC]")
        ret=(k.c/k.o-1).abs()
        parts=[]
        for j in pd.date_range(per.start_time,per.end_time.floor("D"),freq="D"):
            z=cm/sym/f"{sym}-metrics-{j.date()}.zip"
            if z.exists():
                with zipfile.ZipFile(z) as zz, zz.open(zz.namelist()[0]) as f:
                    parts.append(pd.read_csv(f,usecols=["create_time","sum_open_interest"]))
        m=pd.concat(parts); m.index=pd.to_datetime(m.create_time,utc=True).astype("datetime64[ns, UTC]")
        oi=m[~m.index.duplicated()].sort_index().sum_open_interest.astype(float); d=oi.pct_change().abs()
        day=[]
        for dd,g in d.groupby(d.index.floor("D")):
            cs={}
            for p in (-1,0):
                r2=ret.copy(); r2.index=r2.index-pd.Timedelta(minutes=5*p)
                x=pd.concat([g.rename("d"),r2.rename("r")],axis=1,join="inner",sort=True).dropna()
                cs[p]=x.d.corr(x.r,method="spearman")
            day.append((dd.date(),cs[-1],cs[0]))
        D=pd.DataFrame(day,columns=["j","m1","z"]).set_index("j")
        out.append(D)
    A=pd.concat(out); res[sym]=A
    M=A.groupby(lambda x:x.strftime("%Y-%m")).mean().round(3)
    M["pic"]=(M.z>M.m1).map({True:0,False:-1})
    print(sym); print(M.to_string())
A=(res["BTCUSDT"]+res["ETHUSDT"])/2
A.to_csv(SC/"bascule_jours.csv")
