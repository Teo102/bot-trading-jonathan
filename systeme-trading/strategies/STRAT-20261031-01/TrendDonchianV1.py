# STRAT-20261031-01 — Suivi de tendance multi-actifs (cassure de canal de Donchian)
# Paramètres FIGÉS avant tout test : toute modification = nouvel essai au registre.
from datetime import datetime

from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, stoploss_from_absolute


class TrendDonchianV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1d"
    can_short = True
    startup_candle_count = 220
    process_only_new_candles = True

    # Sorties : canal opposé (signal) ou stop ATR (custom_stoploss). Pas de ROI.
    minimal_roi = {"0": 100}
    stoploss = -0.30            # filet de sécurité seulement
    use_custom_stoploss = True
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False

    # --- paramètres figés (5 paramètres libres) ---
    entry_period = 20           # cassure du plus haut / plus bas de 20 jours
    exit_period = 10            # sortie sur le canal opposé de 10 jours
    atr_period = 14
    atr_mult = 2.0              # stop initial à 2 ATR
    regime_period = 200         # long seulement au-dessus de la SMA 200, short seulement en dessous

    # --- risque (commun-trading § 8.2, valeur prudente) ---
    risk_per_trade = 0.005      # 0,5 % du capital à la perte stressée
    cost_buffer = 0.002         # frais taker aller-retour + glissement estimé, en fraction du prix
    max_stake_fraction = 0.20   # exposition maximale par actif (commun-trading § 3)

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        # shift(1) : le canal n'inclut jamais la bougie courante (pas d'anticipation)
        df["dc_high"] = df["high"].rolling(self.entry_period).max().shift(1)
        df["dc_low"] = df["low"].rolling(self.entry_period).min().shift(1)
        df["ex_high"] = df["high"].rolling(self.exit_period).max().shift(1)
        df["ex_low"] = df["low"].rolling(self.exit_period).min().shift(1)
        # ATR de Wilder et SMA en pandas pur (aucune dépendance à TA-Lib)
        prev_close = df["close"].shift(1)
        true_range = (df["high"] - df["low"]).combine((df["high"] - prev_close).abs(), max)
        true_range = true_range.combine((df["low"] - prev_close).abs(), max)
        df["atr"] = true_range.ewm(alpha=1 / self.atr_period, adjust=False,
                                   min_periods=self.atr_period).mean()
        df["sma_regime"] = df["close"].rolling(self.regime_period).mean()
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[
            (df["close"] > df["dc_high"]) & (df["close"] > df["sma_regime"]) & (df["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "breakout_long")
        df.loc[
            (df["close"] < df["dc_low"]) & (df["close"] < df["sma_regime"]) & (df["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "breakout_short")
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        df.loc[df["close"] < df["ex_low"], ["exit_long", "exit_tag"]] = (1, "channel_exit")
        df.loc[df["close"] > df["ex_high"], ["exit_short", "exit_tag"]] = (1, "channel_exit")
        return df

    def _atr_at_entry(self, pair: str, open_date: datetime) -> float | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return None
        before = df.loc[df["date"] < open_date]
        if before.empty:
            return None
        return float(before["atr"].iloc[-1])

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool,
                        **kwargs) -> float | None:
        atr = self._atr_at_entry(pair, trade.open_date_utc)
        if atr is None:
            return None
        if trade.is_short:
            stop_price = trade.open_rate + self.atr_mult * atr
        else:
            stop_price = trade.open_rate - self.atr_mult * atr
        return stoploss_from_absolute(stop_price, current_rate,
                                      is_short=trade.is_short, leverage=trade.leverage)

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float,
                            proposed_stake: float, min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None, side: str,
                            **kwargs) -> float:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return 0.0
        atr = float(df["atr"].iloc[-1])
        stop_fraction = self.atr_mult * atr / current_rate + self.cost_buffer   # perte stressée
        equity = self.wallets.get_total_stake_amount()
        stake = self.risk_per_trade * equity / stop_fraction
        stake = min(stake, self.max_stake_fraction * equity, max_stake)
        if min_stake is not None and stake < min_stake:
            return 0.0
        return stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str | None,
                 side: str, **kwargs) -> float:
        return 1.0
