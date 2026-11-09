# Registre des marchés UMA — actualisation du 09/11/2026

Complément de `REGISTRE_MARCHES_UMA.md` (version du 01/11/2026, 40 marchés notés le 31/10). Écrit le 09/11/2026 par Claude Fable 5.2. Heures en UTC. Résultat de recherche : aucun ordre, aucune recommandation. **Cette grille n'est pas un avis juridique, et le statut légal de Polymarket dépend du pays de résidence de chacun.**

Ce fichier est séparé du registre parce que `genere_registre.py` réécrit le registre à chaque passage. Il sort de `genere_actualisation_20261109.py`.

## 1. Méthode

- Liste lue le 09/11/2026 à 20:50 UTC sur l'API Gamma par `calibration/liste_candidats_sans_prix.py`, depuis le serveur (l'API n'est pas joignable depuis le poste local, voir le § 4). 2 100 marchés lus, 96 événements candidats : fin Gamma entre 2 et 45 jours, hors mi-mandat, liquidité ≥ 10 000, volume sur 24 h ≥ 5 000, un marché par événement.
- 40 marchés notés ici : tous les candidats hors sport et e-sport, hors marchés sur Anthropic (écartés par prudence, le prévisionniste étant un modèle d'Anthropic), hors marché dérivé d'une cote Polymarket, hors « Feijóo prochain Premier ministre » (horizon trop long), une seule tranche pour la Fed, et 8 marchés de prix crypto sur 12.
- Règles lues mot pour mot dans le champ `description` (fichier `calibration/lots/candidats_sans_prix_20261109T205024Z.json`). Notes proposées par trois sous-agents de recherche, relues par Claude. **Ce sont des jugements de lecture, non calibrés, comme au § 2 du registre.**

## 2. Grille des 40 marchés

| Marché | Fin Gamma | F S A C L V M | Total | Niveau | Point à lire |
|---|---|---|---:|---|---|
| Will the price of Bitcoin be above $72,000 on November 12? | 2026-11-12 | 1 2 1 1 0 0 2 | 7 | modéré | Bougie 1 minute Binance « closing at 12:00 ET » : doute entre la bougie de 11:59 et celle de 12:00 ; comparaison stricte ; fenêtre de contestation de 600 s |
| Will the price of Ethereum be above $2,000 on November 13? | 2026-11-13 | 1 2 1 1 0 0 2 | 7 | modéré | Idem |
| Will the price of XRP be above $0.90 on November 13? | 2026-11-13 | 1 2 1 1 0 0 2 | 7 | modéré | Idem ; quatre décimales |
| Will the price of Bitcoin be above $66,000 on November 15? | 2026-11-15 | 1 2 1 1 0 0 2 | 7 | modéré | Idem ; un dimanche |
| Will Bitcoin reach $76,000 November 9-15? | 2026-11-16 | 1 2 1 1 0 0 2 | 7 | modéré | Une mèche isolée sur Binance suffit (« High » ≥ seuil) ; fenêtre en ET |
| Will Bitcoin dip to $72,500 in November? | 2026-12-01 | 1 2 1 1 0 0 2 | 7 | modéré | Fenêtre ouverte depuis le 01/11 : vérifier que le seuil n'a pas déjà été touché (plus bas de novembre 73 510 au 09/11) |
| Will Ethereum reach $2,800 in November? | 2026-12-01 | 1 2 1 1 0 0 2 | 7 | modéré | Mèche isolée ; fenêtre déjà ouverte |
| Will Solana dip to $50 in November? | 2026-12-01 | 1 2 1 1 0 0 2 | 7 | modéré | Mèche vers le bas (krach éclair) ; fenêtre déjà ouverte |
| Will Elon Musk post 160-179 tweets from November 6 to November 13, 2026? | 2026-11-13 | 1 1 1 2 2 1 2 | 10 | modéré | Le compteur xtracker fait foi, même s'il diverge de la règle écrite ; total près d'une borne contestable |
| Will Elon Musk post 120-139 tweets from November 10 to November 17, 2026? | 2026-11-17 | 1 1 1 2 2 1 2 | 10 | modéré | Idem |
| Gemini Carbon released by November 15, 2026? | 2026-11-16 | 2 1 1 2 2 2 2 | 12 | élevé | Annonce ≠ sortie ; l'accès « trusted partners » est privé ; une liste d'attente ouverte suffit ; un modèle sous un autre nom demande une confirmation d'identité |
| GTA 6 launch postponed again? | 2026-11-20 | 1 1 0 1 1 1 2 | 7 | modéré | « Yes » veut dire report ; un glissement d'un jour suffit ; le préchargement ne compte pas |
| GTA VI released by November 30? | 2026-12-01 | 1 0 0 1 1 1 2 | 6 | modéré | Préchargement et précommande ne sont pas une sortie ; même fait que le précédent, sens inversé |
| Will NVIDIA be the largest company in the world by market cap on November 30, 2026? | 2026-12-01 | 2 2 1 1 1 1 2 | 10 | modéré | Aucune source nommée, aucune méthode de capitalisation, place de cotation non précisée |
| Will WTI Crude Oil (WTI) hit (HIGH) $150 in November? | 2026-12-01 | 1 1 1 2 0 1 2 | 8 | modéré | Contrat ICE Europe et non NYMEX ; flux Pyth « without rounding » : une mèche erronée compterait ; bascule du mois actif |
| Will there be no change in Fed interest rates after the December 2026 meeting? | 2026-12-09 | 0 0 1 0 0 0 2 | 3 | faible | Sans communiqué, résolution « No change » ; arrondi au 25 supérieur |
| Will Puma Shen win the next Taipei Mayor election? | 2026-11-29 | 0 1 1 0 2 0 1 | 5 | faible | La date de fin Gamma (29/11) est indicative ; « Other » si inconnu au 30/06/2027 |
| Will Lai Jui-lung win the next Kaohsiung Mayor election? | 2026-11-29 | 0 1 1 0 2 0 1 | 5 | faible | Idem |
| Will Kuomintang (KMT) win the most head of local government elections in the 2026 Taiwan local elections? | 2026-11-29 | 1 1 1 1 1 0 1 | 6 | modéré | Indépendants non comptés ; égalité tranchée par l'ordre alphabétique anglais (Democratic avant Kuomintang) |
| Will PSOE win the most seats in the 2026 Spanish general election? | 2026-11-30 | 1 1 1 0 1 0 2 | 6 | modéré | PSC compté avec le PSOE, UPN avec le PP ; égalité tranchée par les voix |
| Israel Election: Arab party disqualified? | 2026-11-30 | 2 2 0 1 2 2 0 | 9 | modéré | « final and operative », confirmé par la Cour suprême ; fenêtre close au serment de la Knesset |
| US imports Russian diesel by November 30? | 2026-12-01 | 2 2 0 2 2 2 1 | 11 | élevé | « physically delivered » : arrivée au port contre déchargement ; entrepôt sous douane exclu ; territoires américains non précisés |
| Pete Hegseth out as Secretary of Defense by November 30? | 2026-12-01 | 1 1 0 1 1 1 2 | 7 | modéré | L'annonce suffit ; une mise en accusation ne compte pas |
| Russia x Ukraine ceasefire agreement by November 30, 2026? | 2026-12-01 | 2 2 0 2 2 3 2 | 13 | élevé | Pause générale seulement ; date de l'accord et non de son effet ; une trêve courte mais générale compterait |
| Russia-Ukraine peace talks by November 30, 2026? | 2026-12-01 | 2 2 0 1 1 2 2 | 10 | modéré | « indirect in-person » admis ; humanitaire seul exclu ; début de fenêtre non écrit |
| Will Trump speak to Emmanuel Macron by November 30? | 2026-12-01 | 1 1 0 1 1 1 1 | 6 | modéré | Date de l'échange et non de sa révélation ; confirmation au plus tard le 03/12 ; appel à plusieurs non traité |
| Next White House Press Secretary announced by November 30, 2026? | 2026-12-01 | 2 1 0 3 2 2 0 | 10 | modéré | « announces » non défini : l'épisode Dana White (offre le 07/11, « kidding » le 08/11) est un conflit déjà visible |
| US announces end of Iranian blockade by November 15, 2026? | 2026-11-16 | 2 1 0 2 2 2 1 | 10 | modéré | L'annonce suffit, même annulée ensuite ; précédent du 14/06 (Trump annonce, CENTCOM maintient) |
| Israel x Iran ceasefire continues through November 15? | 2026-11-16 | 2 2 1 2 2 2 2 | 13 | élevé | « Yes » veut dire aucune frappe ; heure limite en IRST alors que Gamma affiche minuit ET ; attribution Israël ou États-Unis |
| Strait of Hormuz traffic returns to normal by November 30? | 2026-12-01 | 0 0 1 1 0 0 0 | 2 | faible | Moyenne sur 7 jours, date de la donnée et non de sa publication ; révisions admises |
| Next US-Iran senior diplomatic meeting by November 30, 2026? | 2026-12-01 | 2 2 0 1 2 2 1 | 10 | modéré | L'indirect exige les deux délégations dans la même ville le même jour ; pas de clause « après création » |
| US-Iran Hormuz Agreement by November 30? | 2026-12-01 | 2 2 1 2 2 2 2 | 13 | élevé | Annonce d'acceptation par tous, pas application ; un accord intérimaire suffit |
| US-Iran Final Nuclear Deal by November 30, 2026? | 2026-12-01 | 2 1 1 1 1 1 1 | 8 | modéré | Signature ou adoption d'un texte identifié comme l'accord final ; intérimaire exclu |
| Iran-Oman Hormuz Agreement by November 30? | 2026-12-01 | 2 2 1 2 2 2 1 | 12 | élevé | Déclaration conjointe du 25/08 antérieure au marché, sans clause « après création » |
| Israeli airspace closed by November 30, 2026? | 2026-12-01 | 2 1 0 1 1 1 1 | 7 | modéré | Fermeture générale seulement ; heure d'effet |
| Iran full airspace closure by November 30, 2026? | 2026-12-01 | 2 2 1 2 2 2 1 | 12 | élevé | « initiates » : fermeture nouvelle ; une fermeture de deux heures a servi d'exemple qualifiant |
| Houthis capture Taiz city by November 30? | 2026-12-01 | 2 2 1 1 2 1 0 | 9 | modéré | C'est le château Al-Qahira qui compte, pas la ville ; contrôle contesté exclu |
| US x Iran Effective Ceasefire by November 15? | 2026-11-15 | 2 2 1 2 3 2 2 | 14 | élevé **relecture humaine** | Le 15/11 borne le début d'une fenêtre de 14 jours sans frappe, pas sa fin ; titre « ceasefire », règle limitée aux frappes américaines |
| Military action against Saudi Oil Pipeline (East-West) by November 30? | 2026-11-30 | 2 1 1 2 3 2 0 | 11 | élevé **relecture humaine** | Type d'arme qualifiant ; Riyad dit « targeted » sans nommer l'arme (09/11) |
| Iran leadership change by November 30? | 2026-12-01 | 3 2 1 3 2 2 0 | 13 | élevé **relecture humaine** | « de facto leader » et « prevented from acting » non définis |

Répartition : 4 faibles, 26 modérés, 10 élevés, 0 très élevé. Trois marchés portent un 3 en F ou en L et attendent une relecture humaine avant toute prévision (mode d'emploi de la calibration, règle 8).

## 3. Constats transverses

1. **La date de fin Gamma n'est pas l'échéance de la règle.** Sur les élections de Taïwan et d'Espagne, la règle court jusqu'au 30/06/2027 ou au 30/11/2027. Le marché « Feijóo prochain Premier ministre » affiche le 30/11/2026 et se résout au plus tard le 31/03/2028.
2. **Fenêtre de contestation de 10 minutes** (`customLiveness` = 600) sur les 8 marchés de prix crypto, avec une caution de 250. Le registre du 01/11 avait signalé ce cas hors de son périmètre (§ 1.2) : il est maintenant dans la liste.
3. **Clause « après la création » absente** sur quatre marchés (rencontre États-Unis-Iran, accord d'Ormuz, accord Iran-Oman, pourparlers Russie-Ukraine). Un fait antérieur à la création pourrait être invoqué. Pour Iran-Oman, une déclaration conjointe du 25/08 existe.
4. **L'annonce vaut fait** sur trois marchés (fin du blocus, départ de Hegseth, porte-parole). Le précédent du 14/06/2026 (levée annoncée par Trump, maintenue par CENTCOM) et l'épisode Dana White des 7 et 8/11 montrent le risque.
5. **Titre contre règle** : « US x Iran Effective Ceasefire by November 15 » ne demande pas un cessez-le-feu. Il demande 14 jours sans frappe américaine sur le sol iranien, commencés au plus tard le 15/11.
6. **Source privée unique** : Binance pour les prix crypto, le flux Pyth pour le WTI, le compteur xtracker pour Elon Musk. Une mèche ou une erreur de la source fait foi.
7. **Deux cas ouverts au 09/11** pèsent sur une résolution : l'oléoduc Est-Ouest « visé » le 09/11 (arme non précisée) et les explosions de Qeshm du 08/11 au soir (non attribuées).

## 4. Retard connu du 01/11 et limites

- Les 5 marchés non notés du classement du 01/11 : « Fed décembre sans changement » est noté ici (total 3, faible). Les quatre autres (Iowa R, Sénat D, NC-13, ME-02) sont des marchés du mi-mandat du 03/11/2026. Leur état de résolution est [non relu le 09/11] ; ils restent hors calibration (`mi_mandat = oui`).
- **Accès.** Depuis le poste local, l'API Polymarket renvoie une erreur de certificat le 09/11/2026 à 20:48 UTC, ce qui correspond au blocage en France noté dans `commun-trading` § 1 bis. Les lectures ont été faites depuis le serveur d'Amsterdam, comme les collectes précédentes. Aucun compte, aucun ordre, lecture seule. La question de savoir si cette lecture convient à chacun selon son pays de résidence reste à trancher par Jonathan et Téo.
- Les faits datés qui appuient chaque note sont dans les notes de recherche du 09/11/2026, résumées dans la colonne `base_de_la_proba` du journal de calibration. Plusieurs sources n'ont été lues qu'en résumé de moteur de recherche.
- Les précédents de litige du § 1.5 du registre n'ont pas été relus.
