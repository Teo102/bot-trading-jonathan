import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from common import *
pd.set_option('display.width',260); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',500)
t,s=load_trades("E01"); t=t.sort_values(["open_date"]).reset_index(drop=True)
I={x:indicators(raw(x)) for x in WL}
F={x:fund(x) for x in WL}
# recompute sizes, equity by order of close
tt=t.copy()
res=[]
for i,x in tt.iterrows():
    sym=x.pair.split('/')[0]; o=I[sym]; sg=o.loc[x.open_date-pd.Timedelta(days=1)]; cur=o.loc[x.open_date]
    # equity: all trades closed <= open date, excluding those opened same day (R-def) -> two variants
    closed_strict=tt[(tt.close_date<x.open_date)].profit_abs.sum()
    closed_incl=tt[(tt.close_date<=x.open_date)&(tt.open_date<x.open_date)].profit_abs.sum()
    best=None
    for lab,eq in (("strict",10000+closed_strict),("incl",10000+closed_incl)):
        tgt=0.005*0.99*eq/(2*sg.atr/x.open_rate+0.002)
        cap=0.2*0.99*eq
        res_t=min(tgt,cap)
        if lab=="strict": s1=x.stake_amount/res_t
        else: s2=x.stake_amount/res_t; eqi=eq
    tgt_cur=0.005*0.99*eqi/(2*cur.atr/x.open_rate+0.002)
    dist=abs(x.open_rate-x.stop_loss_abs)/x.open_rate
    risk_nom=x.stake_amount*dist/eqi
    risk_str=x.stake_amount*(dist+0.002)/eqi
    # funding independent
    f,m=F[sym]
    ff=f[(f.date>=x.open_date)&(f.date<=x.close_date)][['date','funding_rate' if 'funding_rate' in f else 'open']].rename(columns={'open':'funding_rate'})
    mm=m[['date','open']].rename(columns={'open':'mark'})
    jn=ff.merge(mm,on='date',how='inner')
    fee_calc=(jn.funding_rate*jn.mark*x.amount).sum()
    fee_calc=fee_calc if x.is_short else -fee_calc
    # P&L reconstruction
    fo=x.fee_open; fc=x.fee_close
    if x.is_short:
        pa=x.amount*x.open_rate*(1-fo)-x.amount*x.close_rate*(1+fc)
    else:
        pa=x.amount*x.close_rate*(1-fc)-x.amount*x.open_rate*(1+fo)
    res.append(dict(pair=sym,s='S' if x.is_short else 'L',od=x.open_date.date(),cd=x.close_date.date(),exit=x.exit_reason,n_fund=len(jn),s_strict=s1,s_incl=s2,s_cur=x.stake_amount/min(tgt_cur,0.2*0.99*eqi),stake=x.stake_amount,stake_pct=x.stake_amount/eqi,dist=dist,risk_nom=risk_nom,risk_str=risk_str,ff=x.funding_fees,ff_calc=fee_calc,pa=x.profit_abs,pa_calc_noff=pa,pa_calc=pa+fee_calc,amt=x.amount,lev=x.leverage,open=x.open_rate,close=x.close_rate,stop=x.stop_loss_abs,atr=sg.atr,stop_calc=x.open_rate+(1 if x.is_short else -1)*2*sg.atr,lvl=(sg.dcl if x.is_short else sg.dch),sgc=sg.close,sma=sg.sma,R=x.profit_abs/(0.005*eqi),init_pct=x.initial_stop_loss_ratio))
R=pd.DataFrame(res); R.to_pickle(SORTIE+"/t2_E01_size.csv")
print("ecart pnl max", (R.pa-R.pa_calc).abs().max(), "ecart ff max",(R.ff-R.ff_calc).abs().max(),"somme ff",R.ff.sum(),R.ff_calc.sum())
print("somme pa",R.pa.sum(),"sans ff",R.pa_calc_noff.sum())
print("lev",R.lev.unique())
print("mise/cible ATR veille strict",R.s_strict.describe()[['min','50%','max']].to_dict())
print("mise/cible ATR veille incl",R.s_incl.describe()[['min','50%','max']].to_dict())
print("mise/cible ATR courant",R.s_cur.describe()[['min','50%','max']].to_dict())
print("hors BTC/ETH/BCH mise/cible incl",R[~R.pair.isin(['BTC','ETH','BCH','LTC','BNB'])].s_incl.describe()[['min','50%','max']].to_dict())
print(R.groupby('pair').s_incl.agg(['min','median','max','count']))
print("stake pct",R.stake_pct.max(),R.stake_pct.mean()," risk nominal (dist) max",R.risk_nom.max(),"min",R.risk_nom.min()," risk stress",R.risk_str.min(),R.risk_str.max())
print("init ratio",R.init_pct.unique())
print("stops",R[R.exit=='stop_loss'].R.describe().to_dict())
sample=pd.concat([R[(R.s=='L')&(R.exit=='stop_loss')].iloc[[0,5,15,25,33]],R[(R.s=='S')&(R.exit=='stop_loss')].iloc[[0,7,14,21]],R[(R.s=='L')&(R.exit=='channel_exit')].iloc[[0,12,24,35]],R[(R.s=='S')&(R.exit=='channel_exit')].iloc[[0,20,40]],R[R.exit=='force_exit']])
print(sample[['pair','s','od','cd','exit','sgc','lvl','sma','open','atr','stop','stop_calc','close','stake','stake_pct','amt','risk_str','ff','pa','R']].to_string(float_format=lambda v:f"{v:.5g}"))
