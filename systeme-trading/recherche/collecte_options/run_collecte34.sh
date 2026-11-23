#!/bin/sh
# Collecte horaire des cotations d'options BTC de Deribit pour H34 (installée le 23/11/2026 sur accord de Jonathan et Téo).
# Données seulement : aucun rendement, aucun ordre, aucune clé. Un seul passage à la fois (flock).
CODE=/root/options34
DATA=/root/options34_data
PY=/root/bot-trading-jonathan/systeme-trading/.venv/bin/python
mkdir -p "$DATA"
cd "$CODE" || exit 1
exec /usr/bin/flock -n "$DATA/verrou" "$PY" -I -B collecte_deribit34.py --sorties "$DATA" >> "$DATA/cron.log" 2>&1
