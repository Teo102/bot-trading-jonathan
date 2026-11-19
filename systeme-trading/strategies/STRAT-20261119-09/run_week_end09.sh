#!/bin/sh
# Passage du papier de STRAT-20261119-09. NON INSTALLÉ : la ligne de crontab ne sera posée qu'après le gel et l'accord
# de Jonathan et Téo. Ligne prévue : 2,12,22 * * * * /bin/sh /root/week_end09/systeme-trading/strategies/STRAT-20261119-09/run_week_end09.sh
# Aucun ordre, aucune clé. Un seul passage à la fois (flock). Sorties hors du code déployé.
CODE=/root/week_end09/systeme-trading/strategies/STRAT-20261119-09
DATA=/root/week_end09_data
PY=/root/bot-trading-jonathan/systeme-trading/.venv/bin/python
mkdir -p "$DATA/sorties"
LIBRE=$(df -Pm / | awk 'NR==2 {print $4}')
if [ "$LIBRE" -lt 300 ]; then
  echo "$(date -u +%FT%TZ) arrêt : disque libre ${LIBRE} Mo < 300 Mo" >> "$DATA/cron.log"
  exit 1
fi
cd "$CODE" || exit 1
exec /usr/bin/flock -n "$DATA/verrou" "$PY" -B -W ignore paper_week_end09.py --donnees "$DATA" --sorties "$DATA/sorties" >> "$DATA/cron.log" 2>&1
