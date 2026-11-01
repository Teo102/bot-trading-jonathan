from common import *
I={x:indicators(raw(x)) for x in WL}
FUND={}
for x in WL:
    f,m=fund(x)
    col='funding_rate' if 'funding_rate' in f.columns else 'open'
    j=f[['date',col]].rename(columns={col:'r'}).merge(m[['date','open']].rename(columns={'open':'mk'}),on='date')
    FUND[x]=j.set_index('date').assign(u=lambda d:d.r*d.mk)['u']
LD=pd.Timestamp("2020-05-26",tz='UTC')
def sim(start,end,order=WL,fee=0.0005,strict_slots=False,strict_equity=False,mult=2.0,startup=220,max_open=3):
    start=pd.Timestamp(start,tz='UTC'); end=pd.Timestamp(end,tz='UTC')
    load=start-pd.Timedelta(days=startup)
    days=pd.date_range(start+pd.Timedelta(days=1),end,freq='D')
    first={}
    for x in order:
        d=I[x]; dates=d.index[d.index>=load]
        first[x]=dates[startup+1] if len(dates)>startup+1 else None
    op=[];done=[];rej=0;closed=0.0;closed_prev=0.0
    for day in days:
        last=(day==end)
        pwo=[t['pair'] for t in op]
        seq=list(dict.fromkeys(pwo+list(order)))
        n_open_at_start=len(op)
        # sorties intrajournalières (stops) vues depuis le début du jour
        n_stops_today=0
        closed_at_open=0
        eq_open=10000+closed
        for x in seq:
            d=I[x]
            if first[x] is None or day<first[x] or day not in d.index: continue
            cur=d.loc[day]; prev=d.loc[day-pd.Timedelta(days=1)]
            has=[t for t in op if t['pair']==x]
            if x in pwo and not has: continue
            tdir=None
            if prev.sig_long and not prev.ex_long and not prev.sig_short: tdir='L'
            elif prev.sig_short and not prev.ex_short and not prev.sig_long: tdir='S'
            for _pass in (0,1):
                has=[t for t in op if t['pair']==x]
                exiting=has[0]['dir'] if has else None
                if tdir and not has and not last:
                    # places
                    if strict_slots:
                        used=n_open_at_start-closed_at_open+sum(1 for t in op if t['od']==day)
                    else:
                        used=len(op)
                    if used<max_open:
                        eq=(eq_open if strict_equity else 10000+closed)
                        st=0.005*0.99*eq/(mult*prev.atr/cur.open+0.002)
                        st=min(st,0.2*0.99*eq)
                        sp=cur.open+(1 if tdir=='S' else -1)*mult*prev.atr
                        t=dict(pair=x,dir=tdir,od=day,o=cur.open,stake=st,amt=st/cur.open,stop=sp)
                        op.append(t)
                    else: rej+=1
                has=[t for t in op if t['pair']==x]
                closed_flag=False
                for t in has:
                    is_s=t['dir']=='S'
                    ex_sig=(prev.ex_short if is_s else prev.ex_long)
                    ent_same=(prev.sig_short if is_s else prev.sig_long)
                    reason=None
                    if ex_sig and not ent_same:
                        reason='channel_exit'; px=cur.open
                    else:
                        hit=(cur.high>=t['stop']) if is_s else (cur.low<=t['stop'])
                        if hit:
                            reason='stop_loss'
                            beyond=(t['stop']<cur.low) if is_s else (t['stop']>cur.high)
                            px=cur.open if beyond else t['stop']
                    if reason:
                        u=FUND[x]; ffu=u[(u.index>=t['od'])&(u.index<=day)].sum()*t['amt']
                        ff=ffu if is_s else -ffu
                        pnl=(t['amt']*t['o']*(1-fee)-t['amt']*px*(1+fee) if is_s else t['amt']*px*(1-fee)-t['amt']*t['o']*(1+fee))+ff
                        closed+=pnl
                        t.update(cd=day,c=px,reason=reason,ff=ff,pnl=pnl,eq_ref=10000+closed-pnl)
                        done.append(t); op.remove(t); closed_flag=True
                        if reason=='channel_exit': closed_at_open+=1
                if not (closed_flag and tdir and exiting and exiting!=tdir): break
    # fin : sortie forcée à l'ouverture de la dernière bougie
    for t in list(op):
        x=t['pair']; cur=I[x].loc[end]; is_s=t['dir']=='S'; px=cur.open
        u=FUND[x]; ffu=u[(u.index>=t['od'])&(u.index<=end)].sum()*t['amt']; ff=ffu if is_s else -ffu
        pnl=(t['amt']*t['o']*(1-fee)-t['amt']*px*(1+fee) if is_s else t['amt']*px*(1-fee)-t['amt']*t['o']*(1+fee))+ff
        closed+=pnl
        t.update(cd=end,c=px,reason='force_exit',ff=ff,pnl=pnl,eq_ref=10000+closed-pnl); done.append(t); op.remove(t)
    D=pd.DataFrame(done)
    return D,rej
def stats(D):
    D=D.copy(); D['r']=D.pnl/(0.005*D.eq_ref)
    return dict(n=len(D),exp=round(D.r.mean(),3),pnl=round(D.pnl.sum(),1),L=round(D[D.dir=='L'].r.mean(),3),S=round(D[D.dir=='S'].r.mean(),3))
