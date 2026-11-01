# STRAT-20261031-01, variante de robustesse R01 (entry_period = 15). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_R01(TrendDonchianV1):
    entry_period = 15
