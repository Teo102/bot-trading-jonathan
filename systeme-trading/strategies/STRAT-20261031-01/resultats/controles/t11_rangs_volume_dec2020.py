import requests, time, json, datetime as dt
print('horodatage UTC',dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
cut=int(dt.datetime(2021,1,1,tzinfo=dt.timezone.utc).timestamp()*1000); st=int(dt.datetime(2020,12,1,tzinfo=dt.timezone.utc).timestamp()*1000)
r=requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo",timeout=30); print('exchangeInfo',r.status_code)
if r.status_code!=200: print(r.text[:300]); raise SystemExit
sy=[s for s in r.json()["symbols"] if s.get("contractType")=="PERPETUAL" and s.get("quoteAsset")=="USDT" and s.get("onboardDate",9e15)<cut]
print('perps USDT presentes dans exchangeInfo et cotees avant 2021',len(sy))
out=[]
for s in sy:
    k=requests.get("https://fapi.binance.com/fapi/v1/klines",params=dict(symbol=s["symbol"],interval="1d",startTime=st,endTime=cut-1,limit=31),timeout=30)
    if k.status_code!=200: out.append((s["symbol"],None)); continue
    out.append((s["symbol"],sum(float(c[7]) for c in k.json()))); time.sleep(0.05)
out=[o for o in out if o[1] is not None]; out.sort(key=lambda x:-x[1])
U={"BTCUSDT","ETHUSDT","XRPUSDT","LTCUSDT","BCHUSDT","LINKUSDT","ADAUSDT","BNBUSDT","DOGEUSDT","TRXUSDT"}
for i,(a,b) in enumerate(out[:30],1): print(i,a,round(b/1e9,2),'*' if a in U else '')
print('rangs',{a:i for i,(a,b) in enumerate(out,1) if a in U})
