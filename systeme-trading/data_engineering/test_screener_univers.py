#!/usr/bin/env python3
"""Tests sans réseau de l'entrée au classement et du signalement de troncature."""
from screener_univers import agreger_carnets, classer_par_volume, mesurer_carnet, volume_median_recent


def _x(sym, v24, med):
    return {"symbole": sym, "volume_24h": v24, "volume_median_30j": med}


def test_le_top_se_forme_sur_la_mediane_et_le_24h_reste_range():
    retenus = [_x("POINTE", 900.0, 1.0), _x("STABLE", 100.0, 80.0), _x("MOYEN", 50.0, 60.0), _x("JEUNE", 500.0, None)]
    top, top_24h, non_classables = classer_par_volume(retenus, 2)
    assert [x["symbole"] for x in top] == ["STABLE", "MOYEN"]
    assert [x["symbole"] for x in top_24h] == ["POINTE", "JEUNE"]
    assert [x["symbole"] for x in non_classables] == ["JEUNE"]
    assert top[0]["rang_volume_24h"] == 3 and top[0]["rang_volume_median"] == 1
    assert "rang_volume_median" not in non_classables[0]


def test_volume_median_exige_30_bougies_closes_et_ignore_la_bougie_ouverte():
    class Client:
        def __init__(self, n):
            self.n = n

        def get(self, url, params):
            lignes = [[i, 0, 0, 0, 0, 0, i * 1000, float(i)] for i in range(1, self.n + 1)]
            lignes.append([99, 0, 0, 0, 0, 0, 10_000_000, 1e12])  # bougie encore ouverte
            return lignes

    med, n = volume_median_recent(Client(30), "X", 1_000_000)
    assert (med, n) == (15.5, 30)
    med, n = volume_median_recent(Client(29), "X", 1_000_000)
    assert med is None and n == 29


def test_bande_tronquee_signalee_et_comptee():
    bids = [["99.99", "1"], ["99.95", "1"]]   # s'arrête à 5,5 bps environ sous le milieu
    asks = [["100.01", "1"], ["101.00", "1"]]  # couvre 100 bps
    m = mesurer_carnet(bids, asks)
    assert m["prof_10bps_bid_tronquee"] is True
    assert m["prof_50bps_bid_tronquee"] is True
    assert m["prof_10bps_ask_tronquee"] is False
    assert m["prof_50bps_ask_tronquee"] is False
    ag = agreger_carnets([{"binance": {"X": m}}, {"binance": {"X": m}}], "binance", "X")
    assert ag["prof_10bps_bid_tronquee_instantanes"] == 2
    assert ag["prof_10bps_ask_tronquee_instantanes"] == 0
    assert "prof_10bps_bid_tronquee_med" not in ag


if __name__ == "__main__":
    tests = [f for nom, f in sorted(globals().items()) if nom.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} tests OK")
