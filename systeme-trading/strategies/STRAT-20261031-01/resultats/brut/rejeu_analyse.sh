#!/bin/zsh
# Rejoue analyse_strat.py sur les exports .zip existants, sans backtest ni téléchargement.
# Première passe pour les Sharpe, puis registre, puis passe finale avec N et V (série réalisée et série réévaluée).
cd "${0:A:h}/../.." || exit 1
PY="${PYTHON_STRAT:-../../.venv/bin/python}"
per() { case "$1" in E01) echo "2021-01-01 2024-06-30";; E02) echo "2024-07-01 2025-07-31";; *) echo "2021-01-01 2025-07-31";; esac; }
ESSAIS=(E01 E02 E03 E04 E05 E06 E07 E08 E09 R01 R02 R03 E00-ref)
for id in $ESSAIS; do
  z=$(ls user_data/backtest_results/$id/*.zip | tail -1); p=($(per $id))
  "$PY" -B analyse_strat.py "$z" --essai "$id" --start "$p[1]" --end "$p[2]" > /dev/null 2>&1 || { echo "échec passe 1 $id"; exit 1; }
done
"$PY" -B resultats/brut/registre_dsr.py resultats || exit 1
for id in $ESSAIS; do
  z=$(ls user_data/backtest_results/$id/*.zip | tail -1); p=($(per $id))
  { date -u +%FT%TZ
    echo "\$ python analyse_strat.py $z --essai $id --start $p[1] --end $p[2] --registry-json resultats/registre_dsr.json"
    "$PY" -B analyse_strat.py "$z" --essai "$id" --start "$p[1]" --end "$p[2]" --registry-json resultats/registre_dsr.json 2>&1
    echo "exit=$?"; date -u +%FT%TZ; } > "resultats/brut/${id}_analyse_reevalue.txt"
  echo "== $id"; /usr/bin/grep -E "^(Trades|Espérance hors|Intervalle|Drawdown|Base|DSR|Erreur|AVERT)" "resultats/brut/${id}_analyse_reevalue.txt" | cut -c1-170
done
