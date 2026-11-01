"""Accès en lecture seule au RPC public Solana et à GeckoTerminal, et lecture d'une transaction.
Aucune clé, aucune signature, aucun envoi de transaction."""
import os, sqlite3, threading, time
from pathlib import Path
import requests

ICI = Path(__file__).resolve().parent
BASE = Path(os.environ.get("DEX_DONNEES", ICI / "donnees"))
FICHIER_CLE = Path(os.environ.get("DEX_CLE_HELIUS", "/root/.helius_env"))


def adresse_rpc():
    """RPC Helius si une clé est déposée sur la machine, RPC public sinon. L'adresse contient la clé : elle ne s'affiche jamais."""
    try:
        for ligne in FICHIER_CLE.read_text().splitlines():
            if ligne.startswith("HELIUS_API_KEY=") and ligne.split("=", 1)[1].strip():
                return "https://mainnet.helius-rpc.com/?api-key=" + ligne.split("=", 1)[1].strip(), 8.0
    except OSError:
        pass
    return "https://api.mainnet-beta.solana.com", 2.5


RPC, RPC_PAR_S = adresse_rpc()
VERSION_TX = 1  # les transactions de version 1 représentaient 12 sur 43 d'un échantillon du 01/11/2026 ; une valeur plus basse les refuse
GECKO = "https://api.geckoterminal.com/api/v2"
WSOL = "So11111111111111111111111111111111111111112"
STABLES = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
LAMPORTS = 1e9
METHODES_RPC = {"getSignaturesForAddress", "getTransaction"}  # lecture seule, liste fermée


class Limiteur:
    def __init__(self, par_seconde):
        self.pas, self.suivant, self.verrou = 1.0 / par_seconde, 0.0, threading.Lock()

    def attendre(self):
        with self.verrou:
            maintenant = time.monotonic()
            attente = max(0.0, self.suivant - maintenant)
            self.suivant = max(maintenant, self.suivant) + self.pas
        if attente:
            time.sleep(attente)


LIM_RPC = Limiteur(float(os.environ.get("DEX_RPC_PAR_S", RPC_PAR_S)))
LIM_GECKO = Limiteur(float(os.environ.get("DEX_GECKO_PAR_MIN", "25")) / 60)
SESSION = requests.Session()


def rpc(methode, params, essais=6):
    if methode not in METHODES_RPC:
        raise ValueError(f"méthode RPC non autorisée : {methode}")
    for i in range(essais):
        LIM_RPC.attendre()
        try:
            r = SESSION.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": methode, "params": params}, timeout=45)
            if r.status_code == 200:
                corps = r.json()
                if "error" not in corps:
                    return corps.get("result")
        except (requests.RequestException, ValueError):
            pass
        time.sleep(min(30, 2 * 2 ** i))
    raise RuntimeError(f"RPC en échec après {essais} essais : {methode}")


def gecko(chemin, essais=5):
    for i in range(essais):
        LIM_GECKO.attendre()
        try:
            r = SESSION.get(GECKO + chemin, headers={"Accept": "application/json;version=20230302"}, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(min(90, 15 * 2 ** i))
    raise RuntimeError(f"GeckoTerminal en échec : {chemin}")


def base(nom="dex.sqlite"):
    BASE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(BASE / nom, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS trades_gecko(tx TEXT, pool TEXT, wallet TEXT, ts TEXT, sens TEXT, mint TEXT, usd REAL, prix REAL,
        vu_le TEXT, PRIMARY KEY(tx, pool, wallet));
    CREATE TABLE IF NOT EXISTS wallets(wallet TEXT PRIMARY KEY, statut TEXT, n_sig INTEGER, max_par_min INTEGER, lu_le TEXT);
    CREATE TABLE IF NOT EXISTS signatures(sig TEXT, wallet TEXT, ts INTEGER, PRIMARY KEY(sig, wallet));
    CREATE TABLE IF NOT EXISTS mouvements(sig TEXT, wallet TEXT, ts INTEGER, type TEXT, mint TEXT, qte REAL, sol REAL, stable REAL,
        priorite_sol REAL, financeur TEXT, PRIMARY KEY(sig, wallet));
    """)
    return c


def lire_transaction(tx, wallet):
    """Résume l'effet d'une transaction sur un wallet. Type : achat, vente, entree_jeton, sortie_jeton, financement, complexe, autre."""
    meta, msg = tx["meta"], tx["transaction"]["message"]
    if meta.get("err") is not None:
        return None
    cles = list(msg["accountKeys"])
    charge = meta.get("loadedAddresses") or {}
    cles += charge.get("writable", []) + charge.get("readonly", [])
    if wallet not in cles:
        return None
    i = cles.index(wallet)
    sol = (meta["postBalances"][i] - meta["preBalances"][i]) / LAMPORTS
    deltas = {}
    for signe, cle in ((-1, "preTokenBalances"), (1, "postTokenBalances")):
        for b in meta.get(cle) or []:
            if b.get("owner") == wallet:
                q = float(b["uiTokenAmount"].get("uiAmountString") or 0)
                deltas[b["mint"]] = deltas.get(b["mint"], 0.0) + signe * q
    sol += deltas.pop(WSOL, 0.0)
    stable = sum(deltas.pop(m, 0.0) for m in STABLES)
    jetons = {m: q for m, q in deltas.items() if abs(q) > 1e-9}
    n_sig = len(tx["transaction"].get("signatures", [])) or 1
    priorite = max(0, meta.get("fee", 0) - 5000 * n_sig) / LAMPORTS
    sortie = dict(type="autre", mint=None, qte=0.0, sol=sol, stable=stable, priorite_sol=priorite, financeur=None)
    if len(jetons) > 1:
        sortie["type"] = "complexe"
    elif len(jetons) == 1:
        (mint, q), = jetons.items()
        sortie.update(mint=mint, qte=q)
        paye = sol < -0.001 or stable < -0.01
        recu = sol > 0.001 or stable > 0.01
        if q > 0:
            sortie["type"] = "achat" if paye else "entree_jeton"
        else:
            sortie["type"] = "vente" if recu else "sortie_jeton"
    elif sol > 0.05 and stable == 0:
        ecarts = [(meta["postBalances"][k] - meta["preBalances"][k], cles[k]) for k in range(len(meta["postBalances"]))]
        perte, source = min(ecarts)
        sortie["type"] = "financement"
        sortie["financeur"] = source if perte < 0 else None
    return sortie
