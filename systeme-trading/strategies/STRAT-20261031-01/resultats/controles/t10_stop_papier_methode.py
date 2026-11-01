import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd, numpy as np
from datetime import datetime, timezone
from TrendDonchianV1 import TrendDonchianV1 as T
class DP:
    def __init__(s,df): s.df=df
    def get_analyzed_dataframe(s,p,tf): return s.df,None
class Tr: pass
d=pd.DataFrame({"date":pd.date_range("2024-01-01",periods=5,freq="D",tz="UTC"),"atr":[10.,11.,12.,5.,6.]})
s=T.__new__(T); s.atr_period=14; s.atr_mult=2.0
tr=Tr(); tr.open_date_utc=datetime(2024,1,4,0,0,5,tzinfo=timezone.utc); tr.is_short=False; tr.open_rate=100.; tr.leverage=1.
for lab,bar in (("live, entree 00:00:05, df jusqu au 03/01 (seule bougie close)",3),("live, le lendemain, df jusqu au 04/01",4),):
    s.dp=DP(d.iloc[:bar]); print(lab,'ATR lu',s._atr_at_entry("X",tr.open_date_utc))
tr2=Tr(); tr2.open_date_utc=datetime(2024,1,4,0,0,0,tzinfo=timezone.utc)
s.dp=DP(d.iloc[:4]); print('backtest, entree 00:00:00, df jusqu au 04/01','ATR lu',s._atr_at_entry("X",tr2.open_date_utc))
