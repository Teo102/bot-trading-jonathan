#!/usr/bin/env python3
"""Génère REGISTRE_UMA_ACTUALISATION_20261109.md à partir du lot noté le 09/11/2026 (aucun réseau, aucun prix)."""
import importlib.util, json
from pathlib import Path
ICI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("lot", ICI / "calibration/lots/lot_20261109_previsions.py"); lot = importlib.util.module_from_spec(spec); spec.loader.exec_module(lot)
c = json.loads((ICI / "calibration/lots/candidats_sans_prix_20261109T205024Z.json").read_text())["candidats"]
P = {1: "Bougie 1 minute Binance « closing at 12:00 ET » : doute entre la bougie de 11:59 et celle de 12:00 ; comparaison stricte ; fenêtre de contestation de 600 s",
     10: "Idem", 11: "Idem ; quatre décimales", 24: "Idem ; un dimanche",
     34: "Une mèche isolée sur Binance suffit (« High » ≥ seuil) ; fenêtre en ET",
     88: "Fenêtre ouverte depuis le 01/11 : vérifier que le seuil n'a pas déjà été touché (plus bas de novembre 73 510 au 09/11)",
     90: "Mèche isolée ; fenêtre déjà ouverte", 91: "Mèche vers le bas (krach éclair) ; fenêtre déjà ouverte",
     7: "Le compteur xtracker fait foi, même s'il diverge de la règle écrite ; total près d'une borne contestable", 55: "Idem",
     32: "Annonce ≠ sortie ; l'accès « trusted partners » est privé ; une liste d'attente ouverte suffit ; un modèle sous un autre nom demande une confirmation d'identité",
     56: "« Yes » veut dire report ; un glissement d'un jour suffit ; le préchargement ne compte pas",
     83: "Préchargement et précommande ne sont pas une sortie ; même fait que le précédent, sens inversé",
     82: "Aucune source nommée, aucune méthode de capitalisation, place de cotation non précisée",
     87: "Contrat ICE Europe et non NYMEX ; flux Pyth « without rounding » : une mèche erronée compterait ; bascule du mois actif",
     92: "Sans communiqué, résolution « No change » ; arrondi au 25 supérieur",
     60: "La date de fin Gamma (29/11) est indicative ; « Other » si inconnu au 30/06/2027", 62: "Idem",
     63: "Indépendants non comptés ; égalité tranchée par l'ordre alphabétique anglais (Democratic avant Kuomintang)",
     65: "PSC compté avec le PSOE, UPN avec le PP ; égalité tranchée par les voix",
     68: "« final and operative », confirmé par la Cour suprême ; fenêtre close au serment de la Knesset",
     73: "« physically delivered » : arrivée au port contre déchargement ; entrepôt sous douane exclu ; territoires américains non précisés",
     75: "L'annonce suffit ; une mise en accusation ne compte pas",
     78: "Pause générale seulement ; date de l'accord et non de son effet ; une trêve courte mais générale compterait",
     84: "« indirect in-person » admis ; humanitaire seul exclu ; début de fenêtre non écrit",
     81: "Date de l'échange et non de sa révélation ; confirmation au plus tard le 03/12 ; appel à plusieurs non traité",
     85: "« announces » non défini : l'épisode Dana White (offre le 07/11, « kidding » le 08/11) est un conflit déjà visible",
     29: "L'annonce suffit, même annulée ensuite ; précédent du 14/06 (Trump annonce, CENTCOM maintient)",
     30: "« Yes » veut dire aucune frappe ; heure limite en IRST alors que Gamma affiche minuit ET ; attribution Israël ou États-Unis",
     69: "Moyenne sur 7 jours, date de la donnée et non de sa publication ; révisions admises",
     70: "L'indirect exige les deux délégations dans la même ville le même jour ; pas de clause « après création »",
     71: "Annonce d'acceptation par tous, pas application ; un accord intérimaire suffit",
     72: "Signature ou adoption d'un texte identifié comme l'accord final ; intérimaire exclu",
     77: "Déclaration conjointe du 25/08 antérieure au marché, sans clause « après création »",
     79: "Fermeture générale seulement ; heure d'effet",
     80: "« initiates » : fermeture nouvelle ; une fermeture de deux heures a servi d'exemple qualifiant",
     86: "C'est le château Al-Qahira qui compte, pas la ville ; contrôle contesté exclu",
     26: "Le 15/11 borne le début d'une fenêtre de 14 jours sans frappe, pas sa fin ; titre « ceasefire », règle limitée aux frappes américaines",
     67: "Type d'arme qualifiant ; Riyad dit « targeted » sans nommer l'arme (09/11)",
     74: "« de facto leader » et « prevented from acting » non définis"}


def niveau(t):
    return "faible" if t <= 5 else "modéré" if t <= 10 else "élevé" if t <= 14 else "très élevé"


L = ["# Registre des marchés UMA — actualisation du 09/11/2026", "",
     "Complément de `REGISTRE_MARCHES_UMA.md` (version du 01/11/2026, 40 marchés notés le 31/10). Écrit le 09/11/2026 par Claude Fable 5.2. Heures en UTC. Résultat de recherche : aucun ordre, aucune recommandation. **Cette grille n'est pas un avis juridique, et le statut légal de Polymarket dépend du pays de résidence de chacun.**", "",
     "Ce fichier est séparé du registre parce que `genere_registre.py` réécrit le registre à chaque passage. Il sort de `genere_actualisation_20261109.py`.", "",
     "## 1. Méthode", "",
     "- Liste lue le 09/11/2026 à 20:50 UTC sur l'API Gamma par `calibration/liste_candidats_sans_prix.py`, depuis le serveur (l'API n'est pas joignable depuis le poste local, voir le § 4). 2 100 marchés lus, 96 événements candidats : fin Gamma entre 2 et 45 jours, hors mi-mandat, liquidité ≥ 10 000, volume sur 24 h ≥ 5 000, un marché par événement.",
     "- 40 marchés notés ici : tous les candidats hors sport et e-sport, hors marchés sur Anthropic (écartés par prudence, le prévisionniste étant un modèle d'Anthropic), hors marché dérivé d'une cote Polymarket, hors « Feijóo prochain Premier ministre » (horizon trop long), une seule tranche pour la Fed, et 8 marchés de prix crypto sur 12.",
     "- Règles lues mot pour mot dans le champ `description` (fichier `calibration/lots/candidats_sans_prix_20261109T205024Z.json`). Notes proposées par trois sous-agents de recherche, relues par Claude. **Ce sont des jugements de lecture, non calibrés, comme au § 2 du registre.**", "",
     "## 2. Grille des 40 marchés", "",
     "| Marché | Fin Gamma | F S A C L V M | Total | Niveau | Point à lire |", "|---|---|---|---:|---|---|"]
rows = [(i, g) for i, _, _, _, g, _, _ in lot.LOT] + [(26, (2, 2, 1, 2, 3, 2, 2)), (67, (2, 1, 1, 2, 3, 2, 0)), (74, (3, 2, 1, 3, 2, 2, 0))]
for i, g in rows:
    m = c[i]; t = sum(g)
    L.append(f"| {m['question']} | {m['endDate'][:10]} | {' '.join(map(str, g))} | {t} | {niveau(t)}{' **relecture humaine**' if max(g[0], g[1], g[4]) == 3 else ''} | {P[i]} |")
n = {k: sum(1 for _, g in rows if niveau(sum(g)) == k) for k in ("faible", "modéré", "élevé", "très élevé")}
L += ["", f"Répartition : {n['faible']} faibles, {n['modéré']} modérés, {n['élevé']} élevés, {n['très élevé']} très élevé. Trois marchés portent un 3 en F ou en L et attendent une relecture humaine avant toute prévision (mode d'emploi de la calibration, règle 8).", "",
      "## 3. Constats transverses", "",
      "1. **La date de fin Gamma n'est pas l'échéance de la règle.** Sur les élections de Taïwan et d'Espagne, la règle court jusqu'au 30/06/2027 ou au 30/11/2027. Le marché « Feijóo prochain Premier ministre » affiche le 30/11/2026 et se résout au plus tard le 31/03/2028.",
      "2. **Fenêtre de contestation de 10 minutes** (`customLiveness` = 600) sur les 8 marchés de prix crypto, avec une caution de 250. Le registre du 01/11 avait signalé ce cas hors de son périmètre (§ 1.2) : il est maintenant dans la liste.",
      "3. **Clause « après la création » absente** sur quatre marchés (rencontre États-Unis-Iran, accord d'Ormuz, accord Iran-Oman, pourparlers Russie-Ukraine). Un fait antérieur à la création pourrait être invoqué. Pour Iran-Oman, une déclaration conjointe du 25/08 existe.",
      "4. **L'annonce vaut fait** sur trois marchés (fin du blocus, départ de Hegseth, porte-parole). Le précédent du 14/06/2026 (levée annoncée par Trump, maintenue par CENTCOM) et l'épisode Dana White des 7 et 8/11 montrent le risque.",
      "5. **Titre contre règle** : « US x Iran Effective Ceasefire by November 15 » ne demande pas un cessez-le-feu. Il demande 14 jours sans frappe américaine sur le sol iranien, commencés au plus tard le 15/11.",
      "6. **Source privée unique** : Binance pour les prix crypto, le flux Pyth pour le WTI, le compteur xtracker pour Elon Musk. Une mèche ou une erreur de la source fait foi.",
      "7. **Deux cas ouverts au 09/11** pèsent sur une résolution : l'oléoduc Est-Ouest « visé » le 09/11 (arme non précisée) et les explosions de Qeshm du 08/11 au soir (non attribuées).", "",
      "## 4. Retard connu du 01/11 et limites", "",
      "- Les 5 marchés non notés du classement du 01/11 : « Fed décembre sans changement » est noté ici (total 3, faible). Les quatre autres (Iowa R, Sénat D, NC-13, ME-02) sont des marchés du mi-mandat du 03/11/2026. Leur état de résolution est [non relu le 09/11] ; ils restent hors calibration (`mi_mandat = oui`).",
      "- **Accès.** Depuis le poste local, l'API Polymarket renvoie une erreur de certificat le 09/11/2026 à 20:48 UTC, ce qui correspond au blocage en France noté dans `commun-trading` § 1 bis. Les lectures ont été faites depuis le serveur d'Amsterdam, comme les collectes précédentes. Aucun compte, aucun ordre, lecture seule. La question de savoir si cette lecture convient à chacun selon son pays de résidence reste à trancher par Jonathan et Téo.",
      "- Les faits datés qui appuient chaque note sont dans les notes de recherche du 09/11/2026, résumées dans la colonne `base_de_la_proba` du journal de calibration. Plusieurs sources n'ont été lues qu'en résumé de moteur de recherche.",
      "- Les précédents de litige du § 1.5 du registre n'ont pas été relus."]
(ICI / "REGISTRE_UMA_ACTUALISATION_20261109.md").write_text("\n".join(L) + "\n")
print(n, len(rows))
