import hashlib,csv
import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from common import *
pd.set_option('display.width',220); pd.set_option('display.max_rows',100)
# sha données vs csv de troncature
rows=[r for r in csv.reader(open(ROOT+"/resultats/brut/03_troncature_verrou.csv")) if len(r)==8 and r[0].endswith('.feather')]
ok=sum(hashlib.sha256(open(f"{DATA}/{r[0]}",'rb').read()).hexdigest()==r[7] for r in rows); print('sha fichiers identiques au csv de troncature',ok,'/',len(rows))
# exports : bornes de dates
for e in ["E00-ref","E01","E02","E03","E04","E05","E06","E07","E08","E09","R01","R02","R03"]:
    t,s=load_trades(e); print(e,s['backtest_end'],'max close',t.close_date.max().date(),'trades',len(t),'non nuls ff',int((t.funding_fees!=0).sum()),'paye',round(-t.funding_fees.clip(upper=0).sum()),'recu',round(t.funding_fees.clip(lower=0).sum()),'gain',round(t.profit_abs.sum()))
# registre
# gaps sur E00 et E02, flips
for e in ["E01","E02","E00-ref"]:
    t,s=load_trades(e); t=t.sort_values('open_date'); g=0;gb=0; flips=0; sameday=0
    for i,x in t.iterrows():
        o=raw(x.pair.split('/')[0]).set_index('date').loc[x.close_date]
        if x.exit_reason=='stop_loss':
            b=(o.open>x.stop_loss_abs) if x.is_short else (o.open<x.stop_loss_abs); g+=int(b)
            gb+=int(abs(x.close_rate/x.stop_loss_abs-1)>1e-9)
        pv=t[(t.pair==x.pair)&(t.close_date==x.open_date)&(t.is_short!=x.is_short)]
        flips+=int(len(pv)>0)
    print(e,'stops ouverture au-dela',g,'stops remplis hors prix du stop',gb,'retournements meme bougie',flips)
# qualité 1d
for x in WL:
    d=raw(x); print(x,'vol0',int((d.volume==0).sum()),'ohlc incoherent',int(((d.high<d[['open','close']].max(axis=1))|(d.low>d[['open','close']].min(axis=1))).sum()),'saut open/close veille >5%',int(((d.open/d.close.shift(1)-1).abs()>.05).sum()), 'max',round(float((d.open/d.close.shift(1)-1).abs().max()),4))
# DOGE : signaux perdus par la chauffe
o=indicators(raw('DOGE'))
w=o.loc['2021-01-25':'2021-02-15']
print('DOGE signaux 25/01-15/02/2021 L',int(w.sig_long.sum()),'S',int(w.sig_short.sum()),list(w[w.sig_long].index.strftime('%m-%d')))
print('DOGE premiere SMA',o.sma.first_valid_index())
# rang volume dec 2020 dans les données locales
print({x:round(float((lambda d:(d.volume*d.close)[(d.date>='2020-12-01')&(d.date<'2021-01-01')].sum())(raw(x))/1e9),2) for x in WL})
