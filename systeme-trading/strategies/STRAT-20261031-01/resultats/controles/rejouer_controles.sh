#!/bin/zsh
# Rejoue les contrôles locaux des contradicteurs. Aucun téléchargement, aucun backtest, lecture seule des exports et des données tronquées.
# t4 (doublon lent de t5) et t11 (appel réseau, interdit dans cette passe) ne sont pas rejoués ici.
C="${0:A:h}"; cd "$C" || exit 1
PY="${PYTHON_STRAT:-$C/../../../../.venv/bin/python}"
for s in "$@"; do
  o="sorties/${s%.py}.txt"
  { echo "debut $(date -u +%FT%TZ)"; echo "\$ python -B $s"; "$PY" -B "$s" 2>&1; echo "exit=$?"; echo "fin $(date -u +%FT%TZ)"; } > "$o"
  echo "$s $(tail -2 "$o" | head -1)"
done
