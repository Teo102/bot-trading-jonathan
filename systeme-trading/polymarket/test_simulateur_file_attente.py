"""Tests synthétiques de la mécanique de file (aucune donnée de marché)."""
import numpy as np
import pytest

import simulateur_file_attente as s


def ordre(sens=1, prix=0.50, taille=100.0, devant=300.0):
    return s.Ordre(sens, prix, taille, devant, 0.0)


def test_file_consommee_exactement():
    o = ordre()
    assert s.consommer(o, 0.50, 300.0, 1) == 0.0        # la file devant est mangée, rien pour nous
    assert o.devant == 0.0 and o.restant == 100.0
    assert s.consommer(o, 0.50, 100.0, 1) == 100.0      # puis notre ordre en entier
    assert o.restant == 0.0


def test_remplissage_partiel():
    o = ordre()
    assert s.consommer(o, 0.50, 340.0, 1) == pytest.approx(40.0)
    assert o.restant == pytest.approx(60.0) and o.rempli == pytest.approx(40.0)


def test_annulation_devant_au_prorata():
    o = ordre(devant=300.0)
    # niveau de 600 parts hors nous, 300 devant et 300 derrière ; 200 annulées au prorata
    s.annuler_devant(o, 200.0, 600.0)
    assert o.devant == pytest.approx(200.0)
    assert s.consommer(o, 0.50, 250.0, 1) == pytest.approx(50.0)


def test_mauvais_cote_et_prix_qui_s_eloigne():
    o = ordre(sens=1, prix=0.50)
    assert s.consommer(o, 0.51, 1000.0, 1) == 0.0       # trade au-dessus de notre bid : il ne nous touche pas
    assert s.consommer(o, 0.50, 1000.0, -1) == 0.0      # taker acheteur : côté ask, pas le nôtre
    assert o.devant == 300.0


def test_niveau_traverse_remplit_tout():
    o = ordre(sens=1, prix=0.50, devant=1e9)
    assert s.consommer(o, 0.49, 30.0, 1) == 30.0        # trade sous notre bid : il nous sert d'abord
    assert o.devant == 0.0
    assert s.consommer(o, 0.48, 500.0, 1) == 70.0       # plafonné à notre reste
    a = ordre(sens=-1, prix=0.50, devant=1e9)
    assert s.consommer(a, 0.51, 1000.0, -1) == 100.0


def test_cible_milieu_un_cent():
    assert s.cible("milieu_1c", 1, 0.94, 0.95, 0.01) == pytest.approx(0.93)
    assert s.cible("milieu_1c", -1, 0.94, 0.95, 0.01) == pytest.approx(0.96)
    assert s.cible("milieu_1c", 1, 0.45, 0.47, 0.01) == pytest.approx(0.45)
    assert s.cible("meilleur", -1, 0.45, 0.47, 0.01) == pytest.approx(0.47)


def _tr(rows):
    a = np.array(rows, dtype=float)
    return {"t": a[:, 0], "p": a[:, 1], "z": a[:, 2], "dir": a[:, 3].astype(int)}


def _marche(**kw):
    m = {"tick": 0.01, "ecart": 0.01, "taille_min": 5.0, "milieu": 0.505, "bb": 0.50, "ba": 0.51,
         "bid_parts_1c": 200.0, "ask_parts_1c": 200.0, "fee_rate": 0.0, "fee_exponent": 1.0, "rebate_rate": 0.0}
    m.update(kw)
    return m


def test_rest_reposte_quand_le_prix_bouge():
    # Bid posé à 0,50 derrière 200 parts. Le prix monte à 0,52 : l'ordre est annulé sans remplissage.
    tr = _tr([(0, 0.50, 10, 1), (10, 0.52, 10, 1), (20, 0.52, 150, 1)])
    sim = s.simuler_rest(_marche(), tr, variante="meilleur", alpha=1.0)
    assert sim["fills"] == []
    motifs = [e["motif"] for e in sim["episodes"] if e["sens"] == 1]
    assert motifs[0] == "annule"


def test_rest_remplissage_apres_file():
    # 200 parts devant, taille d'ordre 198 (100 $ / 0,505). 250 traités à 0,50 : 50 parts pour nous.
    tr = _tr([(0, 0.50, 1, 1), (10, 0.50, 250, 1)])
    sim = s.simuler_rest(_marche(), tr, variante="meilleur", alpha=1.0)
    assert len(sim["fills"]) == 1 and sim["fills"][0][3] == pytest.approx(50.0)


def test_rest_naif_remplit_chaque_trade():
    tr = _tr([(0, 0.50, 1, 1), (10, 0.51, 7, -1)])
    sim = s.simuler_rest(_marche(), tr, variante="meilleur", alpha=1.0, naif=True)
    assert [f[3] for f in sim["fills"]] == [1, 7]


def test_ws_appariement_trade_contre_annulation():
    flux = [
        {"ts": 0, "type": "niveau", "sens": 1, "prix": 0.50, "taille": 300.0, "bb": 0.50, "ba": 0.51},
        {"ts": 1000, "type": "niveau", "sens": 1, "prix": 0.50, "taille": 200.0, "bb": 0.50, "ba": 0.51},   # 100 annulées
        {"ts": 5000, "type": "trade", "prix": 0.50, "taille": 150.0, "sens_maker": 1},
        {"ts": 5100, "type": "niveau", "sens": 1, "prix": 0.50, "taille": 50.0, "bb": 0.50, "ba": 0.51},     # baisse due au trade
    ]
    s.apparier(flux)
    assert flux[1]["annule"] == pytest.approx(100.0)
    assert flux[3]["annule"] == pytest.approx(0.0)


def test_ws_rejeu_complet():
    # Ordre posé derrière 300 parts. 100 annulées au prorata : 200 devant. Trade de 250 : 50 remplies.
    flux = [
        {"ts": 0, "type": "niveau", "sens": 1, "prix": 0.50, "taille": 300.0, "bb": 0.50, "ba": 0.51},
        {"ts": 0, "type": "niveau", "sens": -1, "prix": 0.51, "taille": 300.0, "bb": 0.50, "ba": 0.51},
        {"ts": 1000, "type": "niveau", "sens": 1, "prix": 0.50, "taille": 200.0, "bb": 0.50, "ba": 0.51},
        {"ts": 5000, "type": "trade", "prix": 0.50, "taille": 250.0, "sens_maker": 1},
    ]
    sim = s.simuler_ws(_marche(), flux, "meilleur")
    assert len(sim["fills"]) == 1 and sim["fills"][0][3] == pytest.approx(50.0)
