# STRAT-20261031-01, variante de robustesse E06 (exit_period = 12). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_E06(TrendDonchianV1):
    exit_period = 12
