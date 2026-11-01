# STRAT-20261031-01, variante de robustesse E08 (atr_mult = 2.4). Sous-classe, base inchangée.
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from TrendDonchianV1 import TrendDonchianV1


class TrendDonchianV1_E08(TrendDonchianV1):
    atr_mult = 2.4
