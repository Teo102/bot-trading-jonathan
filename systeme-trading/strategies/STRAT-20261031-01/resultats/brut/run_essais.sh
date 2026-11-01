#!/bin/zsh
# Lance E02 à E09, R01 à R03 et E00-ref. Chaque sortie brute va dans resultats/brut/.
cd "/Users/teobrondel/Bot Trading Jonathan/systeme-trading/strategies/STRAT-20261031-01/" || exit 1
FT="/Users/teobrondel/Bot Trading Jonathan/systeme-trading/.venv/bin/freqtrade"
PY="/Users/teobrondel/Bot Trading Jonathan/systeme-trading/.venv/bin/python"
# Sous-classes, une par fichier, jamais retenues à la place de la base
mk() { # id attr val
cat > "user_data/strategies/TrendDonchianV1_$1.py" <<PYEOF
# STRAT-20261031-01, variante de robustesse $1 ($2 = $3). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_$1(TrendDonchianV1):
    $2 = $3
PYEOF
}
mk E03 entry_period 16; mk E04 entry_period 24; mk E05 exit_period 8; mk E06 exit_period 12
mk E07 atr_mult 1.6; mk E08 atr_mult 2.4; mk R01 entry_period 15; mk R02 entry_period 30
run() { # id classe timerange fee debut fin
  id=$1; cls=$2; tr=$3; fee=$4; deb=$5; fin=$6
  dir="user_data/backtest_results/$id"; mkdir -p "$dir"
  out="resultats/brut/${id}_backtesting.txt"
  { date -u +%FT%TZ
    echo "\$ freqtrade backtesting -c config_strat01.json -s $cls --timerange $tr --fee $fee --export trades --backtest-directory $dir --userdir user_data"
    "$FT" backtesting -c config_strat01.json -s "$cls" --timerange "$tr" --fee "$fee" --export trades --backtest-directory "$dir" --userdir user_data 2>&1
    echo "exit=$?"; date -u +%FT%TZ; } > "$out"
  z=$(ls "$dir"/*.zip | tail -1)
  { date -u +%FT%TZ
    echo "\$ python analyse_strat.py $z --essai $id --start $deb --end $fin"
    "$PY" -B analyse_strat.py "$z" --essai "$id" --start "$deb" --end "$fin" 2>&1
    echo "exit=$?"; } > "resultats/brut/${id}_analyse.txt"
  echo "== $id ($cls $tr fee $fee)"; /usr/bin/grep -E "^(Trades|Espérance :|Drawdown|Sharpe|Erreur|AVERT)" "resultats/brut/${id}_analyse.txt"
}
run E02 TrendDonchianV1 20240701-20250731 0.0005 2024-07-01 2025-07-31
D=20210101-20250731; A=2021-01-01; B=2025-07-31
run E03 TrendDonchianV1_E03 $D 0.0005 $A $B
run E04 TrendDonchianV1_E04 $D 0.0005 $A $B
run E05 TrendDonchianV1_E05 $D 0.0005 $A $B
run E06 TrendDonchianV1_E06 $D 0.0005 $A $B
run E07 TrendDonchianV1_E07 $D 0.0005 $A $B
run E08 TrendDonchianV1_E08 $D 0.0005 $A $B
run E09 TrendDonchianV1 $D 0.0010 $A $B
run R01 TrendDonchianV1_R01 $D 0.0005 $A $B
run R02 TrendDonchianV1_R02 $D 0.0005 $A $B
run R03 TrendDonchianV1 $D 0.0015 $A $B
run E00-ref TrendDonchianV1 $D 0.0005 $A $B
