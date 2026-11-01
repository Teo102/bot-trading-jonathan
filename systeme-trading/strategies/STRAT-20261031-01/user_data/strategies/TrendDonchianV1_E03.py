# STRAT-20261031-01, variante de robustesse E03 (entry_period = 16). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_E03(TrendDonchianV1):
    entry_period = 16
