import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from common import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',500)
t,s=load_trades("E01")
print(len(t), list(t.columns))
print(t.exit_reason.value_counts(), t.enter_tag.value_counts(dropna=False), t.exit_reason.groupby(t.is_short).value_counts(), t.leverage.unique(), t.fee_open.unique(), t.fee_close.unique(), t.liquidation_price.describe() if 'liquidation_price' in t else '')
print({k:s[k] for k in s if k in ('backtest_start','backtest_end','max_open_trades','stake_amount','rejected_signals','timedout_entry_orders','starting_balance','final_balance','canceled_trade_entries','canceled_entry_orders')})
I={x:indicators(raw(x)) for x in WL}
rows=[];bad=[]
eqref=[]
for idx,x in t.sort_values("open_date").iterrows():
    sym=x.pair.split('/')[0]; o=I[sym]
    od=x.open_date; cd=x.close_date; sd=od-pd.Timedelta(days=1)
    sg=o.loc[sd]; ec=o.loc[od]; xc=o.loc[cd]
    # signal en clôture de la veille
    ok_sig=bool(sg.sig_short if x.is_short else sg.sig_long)
    ok_open=abs(x.open_rate/ec.open-1)<1e-9
    stop=x.open_rate+(1 if x.is_short else -1)*2*sg.atr
    d_stop=abs(x.stop_loss_abs/stop-1)
    d_stop_i=abs(x.initial_stop_loss_abs/stop-1)
    prevx=o.loc[cd-pd.Timedelta(days=1)]
    if x.exit_reason=="stop_loss":
        ok_exit= (xc.high>=x.stop_loss_abs if x.is_short else xc.low<=x.stop_loss_abs)
        fill="stop" if abs(x.close_rate/x.stop_loss_abs-1)<1e-9 else ("open" if abs(x.close_rate/xc.open-1)<1e-9 else "??")
        # open au-delà du stop = gap
        gap=(xc.open>x.stop_loss_abs) if x.is_short else (xc.open<x.stop_loss_abs)
    elif x.exit_reason=="channel_exit":
        ok_exit=bool(prevx.ex_short if x.is_short else prevx.ex_long) and abs(x.close_rate/xc.open-1)<1e-9
        fill="open"; gap=False
    else:
        ok_exit=True; fill="force@%s"%("open" if abs(x.close_rate/xc.open-1)<1e-9 else "?"); gap=False
    # stop non touché entre entrée et sortie (hors dernière bougie)
    between=o.loc[od:cd-pd.Timedelta(days=1)]
    missed=((between.high>=x.stop_loss_abs).any() if x.is_short else (between.low<=x.stop_loss_abs).any())
    # sortie de canal manquée
    bw=o.loc[od:cd-pd.Timedelta(days=2)]
    missed_ex=(bw.ex_short.any() if x.is_short else bw.ex_long.any())
    rows.append(dict(pair=sym,s='S' if x.is_short else 'L',sig=str(sd.date()),cl=sg.close,lvl=(sg.dcl if x.is_short else sg.dch),sma=sg.sma,ok_sig=ok_sig,entry=str(od.date()),opn=x.open_rate,ok_open=ok_open,atr=sg.atr,stop_calc=stop,stop_x=x.stop_loss_abs,d_stop=d_stop,d_init=d_stop_i,exit=x.exit_reason,cd=str(cd.date()),close_rate=x.close_rate,fill=fill,gap=gap,ok_exit=ok_exit,missed_stop=missed,missed_ex=missed_ex,stake=x.stake_amount,amt=x.amount,lev=x.leverage,pa=x.profit_abs,ff=x.funding_fees,tag=x.enter_tag))
R=pd.DataFrame(rows)
R.to_csv(SORTIE+"/t1_E01_check.csv")
print(R[['ok_sig','ok_open','ok_exit','missed_stop','missed_ex','gap']].agg(['sum','count']))
print('d_stop max',R.d_stop.max(),'d_init max',R.d_init.max())
print(R.fill.value_counts())
print(R[~R.ok_sig|~R.ok_open|~R.ok_exit|R.missed_stop|R.missed_ex|R.gap])
print('tag coherent', ((R.tag=="breakout_short")==(R.s=='S')).all())
print(R.groupby(['s','exit']).size())
