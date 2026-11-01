import sys; from pathlib import Path
SORTIE = str(Path(__file__).resolve().parent / "sorties")
from common import *
pd.set_option('display.width',240); pd.set_option('display.max_rows',100); pd.set_option('display.max_columns',40)
for e in ("E01","E02","E00-ref"):
    t,s=load_trades(e); rows=[]
    t=t.sort_values('open_date').reset_index(drop=True)
    for i,x in t.iterrows():
        sym=x.pair.split('/')[0]; f,m=fund(sym)
        col='funding_rate' if 'funding_rate' in f else 'open'
        j=f[['date',col]].rename(columns={col:'r'}).merge(m[['date','open']].rename(columns={'open':'mk'}),on='date').set_index('date')
        sign=1 if x.is_short else -1
        ent=(j.r*j.mk).get(x.open_date,0.0)*x.amount*sign   # financement compté à l'instant d'entrée
        ref=10000+t[(t.close_date<=x.open_date)&(t.open_date<x.open_date)].profit_abs.sum()
        row=dict(pair=sym,short=x.is_short,od=x.open_date,cd=x.close_date,reason=x.exit_reason,ent=ent,ref=ref,amount=x.amount,stop=x.stop_loss_abs,R=x.profit_abs/(0.005*ref),stake=x.stake_amount,ff=x.funding_fees,dur0=x.open_date==x.close_date)
        if x.exit_reason=="stop_loss":
            d=m[(m.date>=x.close_date)&(m.date<x.close_date+pd.Timedelta(days=1))].sort_values('date')
            if x.is_short: hit=d[d.high>=x.stop_loss_abs]
            else: hit=d[d.low<=x.stop_loss_abs]
            if len(hit):
                h=hit.iloc[0]; beyond=(h.open>x.stop_loss_abs) if x.is_short else (h.open<x.stop_loss_abs)
                # ecart adverse de l'ouverture de l'heure de franchissement
                slip=max(0.0,((h.open-x.stop_loss_abs) if x.is_short else (x.stop_loss_abs-h.open)))/x.stop_loss_abs
                row.update(hit_h=h.date.hour,beyond=bool(beyond),slip=slip,slip_R=slip*x.amount*x.stop_loss_abs/(0.005*ref))
                # financement omis : heures de financement après 00:00 jusqu'au franchissement
                om=j[(j.index>x.close_date)&(j.index<=h.date)]
                row['om']=float((om.r*om.mk).sum()*x.amount*sign)
                # pire hour low au-delà du stop dans l'heure de franchissement (borne pessimiste)
                worst=(h.high-x.stop_loss_abs if x.is_short else x.stop_loss_abs-h.low)/x.stop_loss_abs
                row['hr_ext_R']=max(worst,0)*x.amount*x.stop_loss_abs/(0.005*ref)
            else:
                row.update(hit_h=None,beyond=None,slip=0.0,slip_R=0.0,om=0.0,hr_ext_R=0.0)
        rows.append(row)
    D=pd.DataFrame(rows); st=D[D.reason=='stop_loss']
    print(e,'trades',len(D),'stops',len(st),'jour d entree stoppe',int(st.dur0.sum()))
    print(' stop non atteint sur le mark 1h le jour de sortie:',int(st.hit_h.isna().sum()),'| ouverture 1h au-dela du stop:',int((st.beyond==True).sum()),'| slip moyen R',round(st.slip_R.mean(),4),'max',round(st.slip_R.max(),3),'somme R',round(st.slip_R.sum(),2),'| extension moyenne dans l heure R',round(st.hr_ext_R.mean(),3),'max',round(st.hr_ext_R.max(),3))
    print(' pire slip'); print(st.sort_values('slip_R',ascending=False)[['pair','short','cd','hit_h','slip','slip_R','hr_ext_R','R']].head(5).to_string())
    print(' financement compte a l entree (USDT, negatif = paye):',round(D.ent.sum(),2),' moyenne R',round((D.ent/(0.005*D.ref)).mean(),4),' sur financement total',round(D.ff.sum(),2))
    print(' financement omis sur stops avant franchissement (USDT):',round(st.om.fillna(0).sum(),2))
    print(' stops R: moy',round(st.R.mean(),3),'min',round(st.R.min(),3),'max',round(st.R.max(),3),'part>1R',round((st.R<-1).mean(),3),'part>1.5',round((st.R<-1.5).mean(),3))
    print(' hors stops R min',round(D[D.reason!='stop_loss'].R.min(),3),'R max',round(D.R.max(),3),'mise/ref max',round((D.stake/D.ref).max(),4),'moy',round((D.stake/D.ref).mean(),4))
    # exposition simultanée
    days=pd.date_range(t.open_date.min(),t.close_date.max()); mx=0;mxn=0
    for dd in days:
        o=t[(t.open_date<=dd)&(t.close_date>dd)]
        mxn=max(mxn,len(o))
    print(' positions simultanées max (fin de journée)',mxn,'premiere entree DOGE',t[t.pair.str.startswith('DOGE')].open_date.min())
    if e=="E00-ref":
        w=t[abs(t.stop_loss_ratio)>0.3] if False else None
        t['dist']=(t.open_rate-t.stop_loss_abs).abs()/t.open_rate
        print(t[t.dist>0.30][['pair','open_date','close_date','is_short','open_rate','stop_loss_abs','dist','exit_reason','stake_amount','profit_abs']].to_string())
