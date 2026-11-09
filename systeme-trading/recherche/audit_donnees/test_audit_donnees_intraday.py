"""Test hors ligne de l'analyse des listes S3 et des estimations. Exécution : python3 -B test_audit_donnees_intraday.py"""
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_donnees_intraday as a  # noqa: E402

XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>data.binance.vision</Name>
<Prefix>data/futures/um/monthly/klines/BTCUSDT/1m/</Prefix><Marker></Marker><MaxKeys>1000</MaxKeys><Delimiter>/</Delimiter>
<IsTruncated>true</IsTruncated><NextMarker>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-02.zip.CHECKSUM</NextMarker>
<Contents><Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip</Key><LastModified>2020-02-01T00:00:00.000Z</LastModified><Size>1500000</Size></Contents>
<Contents><Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip.CHECKSUM</Key><LastModified>2020-02-01T00:00:00.000Z</LastModified><Size>100</Size></Contents>
<Contents><Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-02.zip</Key><LastModified>2020-03-01T00:00:00.000Z</LastModified><Size>1600000</Size></Contents>
<CommonPrefixes><Prefix>data/futures/um/monthly/klines/BTCUSDT/1m/sub/</Prefix></CommonPrefixes>
</ListBucketResult>"""


class Liste(unittest.TestCase):
    def test_analyse(self):
        o, p, tr, nxt = a.analyser_liste(XML)
        self.assertEqual(len(o), 3)
        self.assertTrue(tr)
        self.assertTrue(nxt.endswith("2020-02.zip.CHECKSUM"))
        z = a.zips(o)
        self.assertEqual(len(z), 2)
        self.assertEqual(a.periode(z), ("2020-01", "2020-02"))
        self.assertEqual(p, ["data/futures/um/monthly/klines/BTCUSDT/1m/sub/"])

    def test_pagination(self):
        pages = [XML, XML.replace("<IsTruncated>true", "<IsTruncated>false")]
        appels = []
        def faux(url, timeout=60):
            appels.append(url)
            class R:
                def __enter__(s): return s
                def __exit__(s, *x): return False
                def read(s): return pages[len(appels) - 1].encode()
            return R()
        a.urllib.request.urlopen, ancien = faux, a.urllib.request.urlopen
        try:
            o, p = a.lister("data/futures/um/monthly/klines/BTCUSDT/1m/")
        finally:
            a.urllib.request.urlopen = ancien
        self.assertEqual(len(appels), 2)
        self.assertIn("marker=", appels[1])
        self.assertEqual(len(o), 6)

    def test_memoire(self):
        # 60 mois x 43 800 lignes x 24 octets x 2 = 0,126 Go
        self.assertAlmostEqual(a.memoire_requise(60, 1), 0.126144, places=4)
        self.assertAlmostEqual(a.memoire_requise(60, 50), 6.3072, places=3)


if __name__ == "__main__":
    unittest.main(verbosity=1)
