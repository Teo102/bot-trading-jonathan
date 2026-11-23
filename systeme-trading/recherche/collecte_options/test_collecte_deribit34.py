"""Tests synthétiques de la collecte Deribit (aucun réseau)."""
import csv, datetime as dt, gzip, tempfile
from pathlib import Path
import collecte_deribit34 as c

M = dt.datetime(2026, 11, 23, 19, 1, tzinfo=dt.timezone.utc)


def opt(nom, **kw):
    return {"instrument_name": nom, "bid_price": 0.01, "ask_price": 0.012, "mark_price": 0.011, "mark_iv": 50.0,
            "underlying_price": 61000, "underlying_index": "SYN", "open_interest": 1, "volume": 0, "creation_timestamp": 1795458619326, **kw}


def test_lire_instrument():
    e, k, t = c.lire_instrument("BTC-4DEC26-58000-P")
    assert e == dt.datetime(2026, 12, 4, 8, tzinfo=dt.timezone.utc) and k == 58000 and t == "P"
    e, k, t = c.lire_instrument("BTC-26MAR27-40000-C")
    assert e.year == 2027 and e.month == 3 and e.day == 26 and t == "C"


def test_filtre_echeance_et_zone():
    r = [opt("BTC-4DEC26-58000-P"), opt("BTC-4DEC26-20000-P"), opt("BTC-26MAR27-60000-C"), opt("BTC-23NOV26-60000-C"),
         opt("BTC-4DEC26-97000-C"), opt("BTC-4DEC26-98000-C"), opt("BTC-PERPETUAL")]
    L = c.filtrer(r, 61000.0, M)
    assert [l["instrument"] for l in L] == ["BTC-4DEC26-58000-P", "BTC-4DEC26-97000-C"]   # 23NOV26 échu à 08:00 ; 98 000 > 1,6 × 61 000 = 97 600
    assert 10 < L[0]["jours"] < 11 and L[0]["indice"] == 61000.0


def test_ecriture_en_ajout_seul():
    d = Path(tempfile.mkdtemp())
    L = c.filtrer([opt("BTC-4DEC26-58000-P"), opt("BTC-4DEC26-62000-C")], 61000.0, M)
    c.ecrire(d, L, M, "abc", 2)
    c.ecrire(d, L, M + dt.timedelta(hours=1), "def", 2)
    with gzip.open(d / "cotations_2026-11-23.csv.gz", "rt") as g:
        rows = list(csv.DictReader(g))
    assert len(rows) == 4 and rows[0]["instrument"] == "BTC-4DEC26-58000-P"
    j = (d / "journal_collecte.csv").read_text().splitlines()
    assert len(j) == 3 and j[2].endswith("cotations_2026-11-23.csv.gz") and ",def," in j[2]


if __name__ == "__main__":
    import traceback
    noms = [n for n in sorted(globals()) if n.startswith("test_")]
    e = 0
    for n in noms:
        try:
            globals()[n]()
        except Exception:
            e += 1
            print("ÉCHEC", n)
            traceback.print_exc()
    print(f"{len(noms) - e}/{len(noms)} tests verts")
    raise SystemExit(1 if e else 0)
