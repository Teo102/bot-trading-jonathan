# Tri en 10 minutes : H24 et H25 (Polymarket)

Écrit le 02/11/2026 avant toute lecture de prix Polymarket historiques. Grille `validation-edge` § 0 bis. Résultat de recherche, aucune recommandation.

## Avertissement préalable (avocat du diable)

H24 et H25 sont **le même trade vu de deux côtés**. Vendre un longshot à 3 c revient à acheter le « non » à 97 c. La seule différence tient à la fenêtre :

- **H24, biais du longshot** : tout marché, contrats côtés 1 à 10 c, à n'importe quel moment de leur vie.
- **H25, portage de quasi-certitude** : contrats côtés 95 à 99 c dans les **derniers jours** avant résolution, rendement par le passage du temps.

Conséquence : une seule fiche, deux bandes déclarées avant les résultats, et les deux comptées dans N. Les présenter comme deux découvertes indépendantes serait un biais de comptage (T9).

## H24 — biais du longshot

| N° | Réponse | Verdict |
|---|---|---|
| T1 | Contrepartie : acheteurs de loterie (petite mise, gros gain espéré), surestimation des faibles probabilités, documentée sur les paris sportifs et hippiques [littérature générale ; sur Polymarket, non vérifié] | passe |
| T2 | Gain brut d'un « non » à 97 c : 3,1 %. Frais Polymarket nuls sur la plupart des marchés, frais preneur sur certains [à vérifier par marché]. Un écart de 1 c mange un tiers du gain. Ordre de grandeur connu seulement après mesure des écarts | **conditionnel** |
| T3 | Des milliers de marchés résolus par an : plus de 100 décisions possibles | passe |
| T4 | Historique des prix par jeton via l'API CLOB (`prices-history`), marchés résolus listés par l'API Gamma. Granularité et profondeur sur marchés anciens [à vérifier par Téo]. Carnet historique absent : écart reconstruit, pas observé | **conditionnel** |
| T5 | Aucune vitesse requise | passe |
| T6 | Accès depuis les Émirats : avis juridique local en attente (`commun-trading` § 1 bis, risque pénal signalé). Pas de vente à découvert nécessaire (achat du « non ») | **bloquant tant que l'avis manque** |
| T7 | Perte bornée à la mise par contrat. Mais profil « beaucoup de petits gains, rares pertes de 100 % » : la perte maximale se borne par la taille et la diversification, pas par un stop | passe, sous plafond de taille |
| T8 | Deux paramètres (bande de prix, horizon) | passe |
| T9 | Distinct de H07 (maker passif) : ici on prend la liquidité. Voisin de H25 (voir ci-dessus) | passe, fusion avec H25 |
| T10 | Risque de dépendance au cycle électoral américain de 2024 (volume record). Exiger 3 années sur 4 positives hors 2024 | **conditionnel** |

**Verdict H24 : passe le tri sous trois conditions** (T2 écarts mesurés, T4 données confirmées, T6 avis juridique). Aucune fiche avant T6.

## H25 — portage de quasi-certitude

| N° | Réponse | Verdict |
|---|---|---|
| T1 | Contrepartie : détenteurs qui vendent avant terme pour libérer du capital (coût d'opportunité), et acheteurs de « oui » improbables. Contrepartie plus faible qu'en H24 : le rendement peut n'être que le prix du temps et du risque de résolution | **faible** |
| T2 | 1 à 5 % brut sur quelques jours. Annualisé élevé, mais capacité faible (carnets minces près de 99 c) | conditionnel |
| T3 | Passe si la fenêtre « derniers jours » couvre assez de marchés | passe |
| T4 | Comme H24 | conditionnel |
| T5 | Non | passe |
| T6 | Comme H24 | **bloquant** |
| T7 | Le risque central est **la résolution elle-même** : clause ambiguë, contestation UMA, issue surprise. Ce risque est exactement ce que Jonathan lit le mieux (`REGISTRE_MARCHES_UMA.md`, H08). Perte de 100 % possible sur un contrat | passe, avec filtre de clauses |
| T8 | Trois paramètres (bande, jours avant terme, filtre de clause) | passe |
| T9 | Proche d'une vente d'assurance : « gagner 2 %, perdre 100 % ». À traiter comme une prime de risque, pas comme un edge, sauf preuve que le filtre de clauses réduit les pertes | **alerte** |
| T10 | Comme H24 | conditionnel |

**Verdict H25 : passe le tri, affaiblie.** Son seul edge plausible est le filtre de clauses de Jonathan. La variante sans filtre sert de témoin : si elle fait aussi bien, l'« edge » est une prime de risque.

## Prochaines étapes (aucun prix lu)

1. Jonathan : avis juridique local sur Polymarket aux Émirats (T6). Sans lui, aucune fiche.
2. Téo : vérifier sur 20 marchés résolus pris au hasard (graine écrite avant) que `prices-history` rend des points horaires jusqu'à la résolution. Compter les marchés résolus par an depuis 2022. Aucune lecture de rendement.
3. Cerveau : fiche unique H24/H25 avec deux bandes figées, coût d'écart modélisé à 1 c minimum, témoin sans filtre de clauses, seuil de Sharpe calculé sur N.
