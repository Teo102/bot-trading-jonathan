#!/bin/bash
echo "[Sun Nov  1 20:56:55 UTC 2026] Surveillance de PID 9762 lancee..." >> /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX/donnees/enchainer.log
while ps aux | grep -v grep | grep -q "analyse_cohorte.py tout"; do
    sleep 30
done
echo "[Sun Nov  1 20:56:55 UTC 2026] analyse_cohorte.py termine ! Lancement des controles de robustesse..." >> /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX/donnees/enchainer.log
cd /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX
/root/bot-trading-jonathan/systeme-trading/.venv/bin/python controles_robustesse.py >> /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX/donnees/robustesse.log 2>&1
echo "[Sun Nov  1 20:56:55 UTC 2026] Controles de robustesse termines ! Commit et push sur git..." >> /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX/donnees/enchainer.log
cd /root/bot-trading-jonathan
git add systeme-trading/strategies/STRAT-DEX/resultats/
git commit -m "resultats: cohorte pilote et controles de robustesse DEX (analyse de nuit terminee)"
git push origin main
echo "[Sun Nov  1 20:56:55 UTC 2026] Tout est committe et en ligne sur GitHub !" >> /root/bot-trading-jonathan/systeme-trading/strategies/STRAT-DEX/donnees/enchainer.log
