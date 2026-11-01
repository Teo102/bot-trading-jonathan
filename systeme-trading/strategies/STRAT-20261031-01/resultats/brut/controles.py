"""Contrôles complémentaires sur les exports réels. Lecture seule des exports et des données tronquées."""
import json, sys, zipfile, hashlib, re
from pathlib import Path
import numpy as np, pandas as pd
base = Path(sys.argv[1])
sys.path.insert(0, str(base))
import analyse_strat as A
BT = base/"user_data/backtest_results"; DATA = base/"user_data/data/binance/futures"
ESSAIS = ["E01","E02","E00-ref","E03","E04","E05","E06","E07","E08","E09","R01","R02","R03"]
def fname(p, k): return DATA/f"{p.split('/')[0]}_USDT_USDT-{k}.feather"
_c = {}
def ohlc(p):
    if p not in _c:
        df = pd.read_feather(fname(p,"1d-futures")); df["date"]=pd.to_datetime(df["date"],utc=True)
        pc=df["close"].shift(1)
        tr=(df["high"]-df["low"]).combine((df["high"]-pc).abs(),max).combine((df["low"]-pc).abs(),max)
        df["atr"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
        _c[p]=df.set_index("date")
    return _c[p]
_f={}
def fund(p):
    if p not in _f:
        fr=pd.read_feather(fname(p,"1h-funding_rate")); mk=pd.read_feather(fname(p,"1h-mark"))
        for d in (fr,mk): d["date"]=pd.to_datetime(d["date"],utc=True)
        _f[p]=fr[["date","funding_rate"]].rename(columns={"funding_rate":"open_f"}).merge(mk[["date","open"]].rename(columns={"open":"open_m"}),on="date")
    return _f[p]
out={}
loaded={}
for e in ESSAIS:
    z=next((BT/e).glob("*.zip")); data,member,sha,cfg=A.load_export(z)
    name,st=A.select_strategy(data); loaded[e]=(name,st,cfg,sha,z)
# 1. Traçabilité
print("## 1. Exports : stratégie, valeurs figées, frais, config, dernière clôture")
for e,(name,st,cfg,sha,z) in loaded.items():
    with zipfile.ZipFile(z) as zz:
        src=[n for n in zz.namelist() if n.endswith(".py")]; code=zz.read(src[0]).decode()
    over=re.findall(r"^\s{4}(\w+) = ([\d.]+)\s*$",code,flags=re.M)
    t=st["trades"]; last=max(x["close_date"] for x in t)
    print(e,name,"surcharge",over if e not in("E01","E02","E00-ref","E09","R03") else "aucune (base)", "fee",t[0]["fee_open"],"dry_run",cfg.get("dry_run"),"derniere_cloture",last,"trades",len(t),"sha256",sha[:16])
    assert pd.Timestamp(last)<pd.Timestamp("2025-08-01",tz="UTC")
# 2. financement recalculé
print("\n## 2. Financement recalculé depuis les fichiers (taux x mark x quantité, bornes incluses)")
for e in ["E01","E00-ref"]:
    tr=loaded[e][1]["trades"]; rows=[]
    for x in tr:
        f=fund(x["pair"]); o,c=pd.Timestamp(x["open_date"]),pd.Timestamp(x["close_date"])
        s=f[(f["date"]>=o)&(f["date"]<=c)]
        v=(s["open_f"]*s["open_m"]).sum()*x["amount"]; v= v if x["is_short"] else -v
        rows.append((x["funding_fees"],v))
    a=np.array(rows); print(e,"somme export",round(a[:,0].sum(),3),"somme recalculée",round(a[:,1].sum(),3),"écart abs moyen",round(np.abs(a[:,0]-a[:,1]).mean(),5),"écart abs max",round(np.abs(a[:,0]-a[:,1]).max(),4),"trades non nuls",int((a[:,0]!=0).sum()),"/",len(a))
# 3. Taille et stop : ATR de la bougie précédente ou courante
print("\n## 3. Rappels custom_stake_amount et custom_stoploss (non couverts par lookahead-analysis)")
for e,mult in [("E00-ref",2.0),("E07",1.6)]:
    df=A.prepare_trades(loaded[e][1]["trades"]); raw=sorted(loaded[e][1]["trades"],key=lambda x:(x["open_date"],x["close_date"],x["pair"]))
    ref=A.reference_equity(df,10000.0); R=[]
    for i,x in enumerate(raw):
        o=ohlc(x["pair"]); od=pd.Timestamp(x["open_date"]); idx=o.index.get_loc(od)
        ap,ac=o["atr"].iloc[idx-1],o["atr"].iloc[idx]; op=x["open_rate"]
        tg_p=0.005*ref[i]/(mult*ap/op+0.002); tg_c=0.005*ref[i]/(mult*ac/op+0.002)
        R.append(dict(pair=x["pair"],ratio_prev=x["stake_amount"]/tg_p,ratio_cur=x["stake_amount"]/tg_c,dist_ratio=abs(op-x["stop_loss_abs"])/(mult*ap),frac=x["stake_amount"]/ref[i],capped=min(tg_p,0.2*ref[i])<tg_p,atrpct=mult*ap/op,stop_ratio=x["stop_loss_ratio"]))
    r=pd.DataFrame(R); low=r[r.pair.isin(["DOGE/USDT:USDT","XRP/USDT:USDT","ADA/USDT:USDT","TRX/USDT:USDT"])]
    print(e,"mise/cible ATR précédent, paires à petit prix: médiane",round(low.ratio_prev.median(),4),"p5",round(low.ratio_prev.quantile(.05),4),"p95",round(low.ratio_prev.quantile(.95),4),"n",len(low))
    print(e,"mise/cible ATR courant, mêmes paires: médiane",round(low.ratio_cur.median(),4),"p5",round(low.ratio_cur.quantile(.05),4),"p95",round(low.ratio_cur.quantile(.95),4))
    print(e,"mise/cible toutes paires (ATR précédent): médiane",round(r.ratio_prev.median(),4),"min",round(r.ratio_prev.min(),4),"max",round(r.ratio_prev.max(),4))
    print(e,"distance de stop / (mult x ATR précédent): médiane",round(r.dist_ratio.median(),5),"min",round(r.dist_ratio.min(),4),"max",round(r.dist_ratio.max(),4),"trades hors 0,99-1,01:",int(((r.dist_ratio<.99)|(r.dist_ratio>1.01)).sum()))
    print(e,"plafond 20 % atteint:",int(r.capped.sum()),"distance prévue > 30 % (filet):",int((r.atrpct>0.3).sum()),"mise moyenne en part d'équité",round(r.frac.mean(),4),"max",round(r.frac.max(),4))
# 4. Risque réalisé
print("\n## 4. Risque réalisé par motif de sortie (R nominal)")
risk={}
for e in ["E01","E02","E00-ref","E07","E08"]:
    df=A.prepare_trades(loaded[e][1]["trades"]); r,fee_r,paid_r,ref=A.r_multiples(df,10000.0,0.005)
    df=df.assign(r=r,fee_r=fee_r,fund_r=df["funding_fees"].fillna(0)/(0.005*ref))
    for why,g in df.groupby("exit_reason"):
        print(e,why,"n",len(g),"moy",round(g.r.mean(),3),"med",round(g.r.median(),3),"min",round(g.r.min(),3),"max",round(g.r.max(),3))
    s=df[df.exit_reason=="stop_loss"]
    pl=s.r+s.fee_r-s.fund_r
    print(e,"stops: part frais",round(s.fee_r.mean(),3),"R, financement net",round(s.fund_r.mean(),3),"R, prix seul",round(pl.mean(),3),"R, part > 1 R:",round((s.r<-1).mean(),3),"> 1,5 R:",int((s.r<-1.5).sum()),"> 2 R:",int((s.r<-2).sum()))
    w=df.nsmallest(3,"r")[["pair","open_date","close_date","is_short","exit_reason","r","fund_r"]]
    b=df.nlargest(3,"r")[["pair","open_date","close_date","is_short","exit_reason","r","fund_r"]]
    print(" pires\n"+w.round(3).to_string(index=False)); print(" meilleurs\n"+b.round(3).to_string(index=False))
    risk[e]={"n_stop":len(s),"moy":float(s.r.mean()),"med":float(s.r.median()),"min":float(s.r.min()),"max":float(s.r.max())}
# 5. Par paire
print("\n## 5. Par paire")
perpair={}
for e in ["E01","E02","E00-ref"]:
    df=A.prepare_trades(loaded[e][1]["trades"]); r=A.r_multiples(df,10000.0,0.005)[0]; df=df.assign(r=r)
    g=df.groupby("pair").agg(trades=("r","size"),esp_R=("r","mean"),som_R=("r","sum"),pnl=("profit_abs","sum"),fin_net_paye=("funding_fees",lambda s:-s.sum()),reussite=("r",lambda s:(s>0).mean()),premier=("open_date","min")).sort_values("pnl",ascending=False)
    g["premier"]=g["premier"].dt.date
    print(e); print(g.round(3).to_string()); perpair[e]=g.assign(premier=g["premier"].astype(str)).round(4).reset_index().to_dict("records")
# 6. Concentration
print("\n## 6. Concentration")
conc={}
for e in ESSAIS:
    df=A.prepare_trades(loaded[e][1]["trades"]); r=A.r_multiples(df,10000.0,0.005)[0]; df=df.assign(r=r)
    s=np.sort(r)[::-1]; m=df.groupby(df["close_date"].dt.strftime("%Y-%m"))["profit_abs"].sum(); tot=df.profit_abs.sum()
    pnl=np.sort(df.profit_abs.to_numpy())[::-1]
    bt=df.loc[df.r.idxmax()]
    conc[e]=dict(esp=float(r.mean()),esp_sans_1=float(s[1:].mean()),esp_sans_3=float(s[3:].mean()),rmax=float(s[0]),meilleur=f"{bt.pair} {bt.open_date.date()} {'short' if bt.is_short else 'long'}",part_top1_pnl=float(pnl[0]/tot),part_top3_pnl=float(pnl[:3].sum()/tot),meilleur_mois=m.idxmax(),part_meilleur_mois=float(m.max()/tot),mois_pos=int((m>0).sum()),mois_avec_cloture=len(m),pnl_total=float(tot))
    print(e,{k:(round(v,3) if isinstance(v,float) else v) for k,v in conc[e].items()})
# 7. Drawdown réévalué à la clôture quotidienne
print("\n## 7. Drawdown réévalué chaque jour (prix de clôture 1d, frais et financement latents non inclus)")
mtm={}
for e,(a,b) in {"E01":("2021-01-01","2024-06-30"),"E02":("2024-07-01","2025-07-31"),"E00-ref":("2021-01-01","2025-07-31"),"E09":("2021-01-01","2025-07-31")}.items():
    tr=loaded[e][1]["trades"]; days=pd.date_range(a,b,freq="D",tz="UTC"); eq=pd.Series(10000.0,index=days)
    for x in tr:
        o,c=pd.Timestamp(x["open_date"]),pd.Timestamp(x["close_date"]); sign=-1 if x["is_short"] else 1
        eq[eq.index>=c.normalize()]+=x["profit_abs"]
        px=ohlc(x["pair"])["close"]
        d=days[(days>=o.normalize())&(days<c.normalize())]
        if len(d): eq.loc[d]+=sign*x["amount"]*(px.reindex(d).to_numpy()-x["open_rate"])
    real=A.max_drawdown(A.daily_series(A.prepare_trades(tr),10000.0,days[0],days[-1])["equity"].to_numpy(),10000.0)
    dd=A.max_drawdown(eq.to_numpy(),10000.0); rr=eq.pct_change().fillna(eq.iloc[0]/10000-1).to_numpy()
    pk=eq.cummax(); tr_day=((pk-eq)/pk).idxmax()
    mtm[e]=dict(dd_mtm=dd,dd_realise=real,date_creux=str(tr_day.date()),sharpe_mtm=float(rr.mean()/rr.std(ddof=1)*np.sqrt(365)))
    print(e,mtm[e])
# 8. Semestres
print("\n## 8. Semestres (depuis les métriques)")
for e in ["E01","E02","E00-ref"]:
    m=json.loads((base/"resultats"/f"{e}_metriques.json").read_text(encoding="utf-8"))["semestres"]
    print(e,m["n_positifs"],"/",m["n_semestres"]); print(pd.DataFrame(m["semestres"]).round(3).to_string(index=False))
json.dump({"risque_stops":risk,"par_paire":perpair,"concentration":conc,"drawdown_reevalue":mtm},open(base/"resultats/controles_complementaires.json","w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
