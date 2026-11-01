import sys, json
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1
LOG=Path(__file__).parent.parent/"inst_log.jsonl"
class Inst(TrendDonchianV1):
    def custom_stake_amount(self,pair,current_time,current_rate,proposed_stake,min_stake,max_stake,leverage,entry_tag,side,**kw):
        df,_=self.dp.get_analyzed_dataframe(pair,self.timeframe)
        s=super().custom_stake_amount(pair,current_time,current_rate,proposed_stake,min_stake,max_stake,leverage,entry_tag,side,**kw)
        with LOG.open("a") as f: f.write(json.dumps(dict(k="stake",pair=pair,now=str(current_time),rate=current_rate,last=str(df.date.iloc[-1]),eq=self.wallets.get_total_stake_amount(),max_stake=max_stake,tag=entry_tag,side=side,stake=s,lev=leverage,uses=self._ft_stop_uses_after_fill))+"\n")
        return s
    def custom_stoploss(self,pair,trade,current_time,current_rate,current_profit,after_fill,**kw):
        df,_=self.dp.get_analyzed_dataframe(pair,self.timeframe)
        v=super().custom_stoploss(pair,trade,current_time,current_rate,current_profit,after_fill,**kw)
        with LOG.open("a") as f: f.write(json.dumps(dict(k="sl",pair=pair,now=str(current_time),rate=current_rate,af=after_fill,last=str(df.date.iloc[-1]),open_date=str(trade.open_date_utc),v=v,sl=trade.stop_loss))+"\n")
        return v
