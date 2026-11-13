#!/bin/sh
# Tâche horaire du papier à blanc de STRAT-06-bis (installée le 13/11/2026 sur accord de Jonathan et Téo).
# Aucun ordre, aucune clé. Un seul passage à la fois (flock). Sorties et données hors du code déployé.
CODE=/root/papier06/systeme-trading/strategies/STRAT-20261102-06
DATA=/root/papier06_data
PY=/root/bot-trading-jonathan/systeme-trading/.venv/bin/python
mkdir -p "$DATA"
LIBRE=$(df -Pm / | awk 'NR==2 {print $4}')
if [ "$LIBRE" -lt 300 ]; then
  echo "$(date -u +%FT%TZ) arrêt : disque libre ${LIBRE} Mo < 300 Mo" >> "$DATA/cron.log"
  exit 1
fi
cd "$CODE" || exit 1
exec /usr/bin/flock -n "$DATA/verrou" "$PY" -B -W ignore paper_cohortes06.py --tout --donnees "$DATA/donnees" --sorties "$DATA/sorties" >> "$DATA/cron.log" 2>&1
