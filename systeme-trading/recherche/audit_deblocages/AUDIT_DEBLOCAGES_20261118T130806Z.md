# Audit des données de H28 (déblocages de jetons), 18/11/2026

Audit de disponibilité et de qualité, à coût nul. **Aucun prix, aucun rendement** : seuls des calendriers, des listes de symboles, des dates de cotation et des historiques de fichiers ont été lus. Résultat de recherche, aucune recommandation d'investissement.

Script `audit_deblocages.py` (écrit le 17/11 par un sous-agent interrompu par une coupure réseau, relu puis lancé par Claude), sortie brute `audit_deblocages_20261118T130806Z.json`. Exécution du 18/11/2026 de 13:08:06 à 13:21:52 UTC depuis le poste local : 523 appels publics, 23 erreurs (API payante de DefiLlama en 402, dépôt officiel en 404, 18 réponses 503 de la Wayback Machine, une liste S3 expirée), aucune clé.

## 1. Sources

| Jeu | Disponible | Ce qu'il contient | Limite |
|---|---|---|---|
| Calendriers publics de DefiLlama (`defillama-datasets.llama.fi/emissions/<protocole>`) | Oui, 376 fichiers lus sur 376 | 54 985 événements datés (42 770 cliffs), catégories « insiders » (313 protocoles) et « privateSale » (210) | **Instantané d'aujourd'hui** ; 12 protocoles sans événement |
| Correspondance avec CoinGecko (`coins/list`, un appel) | Oui | 368 protocoles résolus | 106 ambiguïtés, surtout des symboles partagés |
| Perpétuels Binance (`exchangeInfo` et listes des archives pour les contrats retirés) | Oui | **201 protocoles ont eu un perpétuel USDT**, dont 182 encore cotés | Une liste d'archives expirée [peut manquer quelques contrats retirés] |
| Dépôt officiel des adaptateurs d'émissions de DefiLlama | **Non** : 404 sur GitHub, l'API GitHub et Software Heritage | — | Dépôt retiré ou privé |
| Copie publique du dépôt (`Omni-Chain-Protocols/emissions-adapters`, non-fork, créée le 01/04/2026) | Oui, lecture de l'historique seulement, aucun code exécuté | 1 158 commits du 27/01/2023 au 01/04/2026, 318 fichiers de protocoles | Copie tierce, intégrité [non vérifiée] ; rien après le 01/04/2026 |
| Wayback Machine | Partielle | Aucun instantané des fichiers JSON par protocole ; des pages `defillama.com/unlocks/` archivées (de 2 à 15 par gros protocole) ; la liste des protocoles archivée en 2023 | 18 réponses 503 |

## 2. Nombre d'événements (critère T3)

Cliffs « insiders » et « privateSale » d'au moins 1 % de l'offre, regroupés par jeton et par jour, pendant que le perpétuel Binance est coté :

| Bloc | Événements | Jetons distincts | Événements non récurrents |
|---|---:|---:|---:|
| Développement (01/2021 à 06/2024) | **91** | 24 | 32 |
| Intervalle (07/2024 à 06/2025) | 92 | 28 | 43 |
| Hors échantillon probable (07/2025 à 10/2026) | 285 | 46 | 53 |

Par année : 2021 15, 2022 16, 2023 40, 2024 54, 2025 147, 2026 232. À 2 % de l'offre, le développement tombe à 32 événements.

Le développement n'atteint pas 100 décisions, et ses événements viennent de peu de jetons à déblocages mensuels (ImmutableX 20, Avalanche 14, Hedera 9, STEPN 9). Les jetons d'aujourd'hui dominent la fin de la période (EigenLayer, LayerZero, Renzo, BounceBit). **T3 échoue sur le développement.**

## 3. Connaissance à la date (critère T4), le point décisif

**Date d'ajout des calendriers, d'après l'historique de la copie du dépôt.** Pour les événements comptés au § 2 (version individuelle) :

| Bloc | Calendrier présent au moins 7 jours avant | Calendrier ajouté après l'événement | Ajouté moins de 7 jours avant |
|---|---:|---:|---:|
| Développement | 19 | **39** | 1 |
| Intervalle | 62 | 8 | 2 |
| Hors échantillon probable | 182 | 9 | 2 (et 30 sans fichier dans la copie) |

Sur le développement, **deux événements sur trois ont été documentés après coup** : le dépôt ne commence que le 27/01/2023. Un backtest sur 2021-2024 lirait des calendriers que personne ne publiait alors sous cette forme. Ce défaut n'est pas corrigible.

**Corrections rétroactives.** La page Arbitrum archivée le 16/04/2023 annonçait 64 cliffs à venir. Comparés aux données d'aujourd'hui, 61 ont changé de date et de montant et 3 ont été décalés (de −7 à +23 jours) ; 40 événements ont été ajoutés depuis. Sur les 253 événements couverts par la copie, 17 ont reçu un commit sur leur fichier entre 30 jours avant et 7 jours après l'événement, par exemple Blur le 14/06/2023 pour un cliff du 15/06/2023. **T4 échoue sur le développement**, et ne passe qu'à partir de mi-2024.

## 4. Biais du survivant

- 19 protocoles sur 201 n'ont plus que des contrats retirés de Binance (Fantom, Balancer, Raydium, Moonbeam…) ; ils restent dans les calendriers.
- La liste de DefiLlama comptait 78 protocoles le 21/06/2023 contre 376 aujourd'hui, et 34 noms de 2023 ont disparu ou ont été renommés depuis (dont « arbitrum », « sui », « near », « immutable »).
- Les jetons morts sans suivi ne sont pas dans les données : un backtest serait biaisé vers les survivants.

## 5. Conclusion

| Critère | Verdict |
|---|---|
| T3 (100 décisions en développement) | **Échoue** : 91 événements (24 jetons), 32 à 2 % |
| T4 (données connues à la date) | **Échoue sur 2021-2024** : 39 des 59 événements documentés après coup ; corrections de dates et de montants mesurées. Passe à peu près à partir de mi-2024 |
| T9 (orthogonalité, rappel du tri du 16/11) | Même facteur « alts moins BTC » que STRAT-06-bis |

**Selon la grille, un seul « non » écarte l'idée : H28 est écartée au tri pour un test sur l'historique.** Il reste deux voies, aucune proposée ici :
- un papier en avant, avec une collecte quotidienne des calendriers datée par nos soins. Il durerait plus d'un an, et il ajouterait une deuxième jambe courte d'alts au portefeuille ;
- un test limité à mi-2024 à 2026, soit moins de deux ans de données, sans découpage propre en trois blocs.
