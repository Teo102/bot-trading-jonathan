# STRAT-20261031-01, variante de robustesse R02 (entry_period = 30). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_R02(TrendDonchianV1):
    entry_period = 30
