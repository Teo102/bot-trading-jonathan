# Tri en 10 minutes : STRAT-07 et STRAT-08

Écrit le 09/11/2026, avant toute lecture de rendement, selon la grille de `validation-edge` § 0 bis. Résultat de recherche, aucune recommandation, aucun ordre.

## Correction préalable (avocat du diable contre le Cerveau)

Le 09/11, j'ai recommandé STRAT-07 (portage de financement delta neutre) sans rappeler deux décisions passées :
- **H02** a été rejetée pour son jeu de paramètres sur les grandes paires ;
- **H10** (« long comptant, short perpétuel sur financement positif des alts encombrés ») a été **écartée au criblage le 02/11**. Elle rapportait environ 2,5 % par an sur le capital avant coûts, sous le taux court de 3,875 % (T2).

STRAT-07 ne peut donc passer le tri que si elle **diffère réellement** de H02 et de H10. Sinon, c'est T9 : une stratégie déjà rejetée sous un autre nom.

---

## STRAT-07 — Portage de financement conditionnel aux pointes (long comptant, short perpétuel)

**Définition proposée, distincte de H10 :**
- n'entrer que quand le financement d'un perpétuel dépasse un seuil élevé (de l'ordre de 30 à 50 % par an) ;
- sortir dès qu'il retombe ;
- univers : tous les perpétuels USDT qui ont une paire au comptant de même nom ;
- le reste du temps, le capital reste en trésorerie.

| N° | Question | Réponse | Verdict |
|---|---|---|---|
| T1 | Qui perd en face ? | Les acheteurs à levier, qui paient le financement pour garder une exposition sans échéance. Ils continuent par demande de levier et faute d'accès au comptant à crédit | passe |
| T2 | Le mouvement espéré dépasse-t-il 3 fois le coût ? | Quatre jambes à 0,10–0,15 % par côté, soit un aller-retour d'environ 0,4 à 0,6 %. À 50 % par an (≈ 0,14 % par jour), il faut environ 12 jours de pointe pour atteindre 3 fois le coût. Or les pointes de financement des jeunes perpétuels sont brèves (90e centile à +55 %/an, recherche STRAT-06 § 4.1). La persistance des pointes est **inconnue** | **conditionnel**, le point dur |
| T3 | 100 décisions en développement, 30 hors échantillon ? | Les pointes sont fréquentes sur environ 200 perpétuels | passe |
| T4 | Données connues à la date ? | Financement mensuel et comptant 1h dans les archives ; date de cotation au comptant lisible. Rien à emprunter (long au comptant) | passe, à confirmer par l'audit (jeux F et G) |
| T5 | Vitesse requise ? | Non, l'échelle est l'heure | passe |
| T6 | Exécution possible ? | Comptant et perpétuel sur la même plateforme. Accès depuis les Émirats (§ 1 bis) [à vérifier] | passe sous réserve |
| T7 | Perte bornée ? | La jambe courte peut être liquidée sur une forte hausse si la marge est mince ; risques de déleveraging automatique et de plateforme. Bornée avec une marge pleine (1×) et un seuil de rééquilibrage | passe sous règle |
| T8 | Plus de 5 paramètres ? | Seuil d'entrée, seuil de sortie, fenêtre de lissage, taille de l'univers : 4 | passe |
| T9 | Déjà rejetée sous un autre nom ? | **Proche de H10 et de H02.** La seule différence défendable est le caractère conditionnel aux pointes, que H10 n'a pas testé (H10 sélectionnait par encombrement, intérêt ouvert et financement mêlés) | **conditionnel** |
| T10 | Un seul régime ? | Le financement est positif surtout en marché haussier (C3 : +32,6 %, puis +0,8 % par an). Hors pointes, la stratégie reste en trésorerie : elle ne perd pas, elle attend. Exiger 3 années sur 4 avec au moins une pointe exploitable | conditionnel |

**Verdict : affaiblie. Elle passe le tri seulement après un criblage de faisabilité sans fiche** (étape 1 de l'entonnoir) :
- mesurer, sur les archives de financement des blocs déjà consommés (2021 à 07/2025, contamination déclarée), la **durée des pointes** au-dessus de 30 et de 50 % par an, et le financement cumulé par pointe ;
- comparer ce cumul au coût d'un aller-retour à quatre jambes.

Si le financement cumulé médian d'une pointe est inférieur à 3 fois le coût, **STRAT-07 est écartée comme H10**, sans fiche.

Ce criblage lit le financement, composante des rendements. Il s'inscrit au registre et se déclare comme une lecture de blocs consommés.

---

## STRAT-08 — Contre-tendance après une cascade de liquidations (intra-journalier)

**Définition proposée :**
- sur environ 200 perpétuels USDT, détecter à la minute une cascade : chute rapide du prix, pic de volume, baisse brutale de l'intérêt ouvert (ou liquidations, si l'archive existe) ;
- acheter la minute suivante ;
- sortie par objectif, par durée maximale ou par stop.

| N° | Question | Réponse | Verdict |
|---|---|---|---|
| T1 | Qui perd en face ? | Les longs liquidés. Le moteur de liquidation vend au marché, sans tenir compte du prix. C'est une contrepartie forcée, le meilleur cas de la grille | passe |
| T2 | Le mouvement espéré dépasse-t-il 3 fois le coût ? | Coût : 0,05 % de frais par côté, plus un glissement fort dans la cascade (0,1 à 0,3 %), soit environ 0,3 à 0,7 % aller-retour. Il faut un rebond moyen d'environ 1 à 2 % après l'entrée. Plausible sur les alts, **inconnu** | conditionnel |
| T3 | 100 décisions en développement, 30 hors échantillon ? | Des dizaines de cascades par semaine sur l'ensemble des perpétuels, si le seuil est raisonnable. H04 n'avait que 65 événements en données journalières | passe, à confirmer |
| T4 | Données connues à la date ? | Klines 1m, prix de marque 1m et metrics (intérêt ouvert 5 min) existent dans les archives. L'archive des liquidations `liquidationSnapshot` couvrirait seulement une partie de l'historique [à vérifier par l'audit, jeu C]. Sinon, indicateur indirect par prix, volume et intérêt ouvert | **conditionnel à l'audit** |
| T5 | Vitesse requise ? | **Risque principal.** Si le rebond se joue en secondes, les teneurs de marché rapides le prennent avant nous. Test imposé : entrée à l'ouverture de la minute suivant la détection, puis avec 5 minutes de retard ; l'edge doit survivre aux deux | **conditionnel, point dur** |
| T6 | Exécution possible ? | Long ou short sur perpétuel, stop posé sur la plateforme. Mêmes réserves d'accès que les autres stratégies | passe sous réserve |
| T7 | Perte bornée ? | Stop par position. Mais les cascades se regroupent dans les krachs (mai 2021, 10/10/2025) : pertes corrélées. Plafond de positions simultanées et perte maximale par jour obligatoires | passe sous règle |
| T8 | Plus de 5 paramètres ? | Seuil de chute, seuil de volume ou d'intérêt ouvert, retard d'entrée, sortie (objectif ou durée), stop : 5. **Risque de surapprentissage élevé** : grille déclarée d'avance, voisins exigés, avocat du diable avant la fiche | limite |
| T9 | Déjà rejetée sous un autre nom ? | H04 (rebond après cascade, journalier) était **non testable**, pas rejetée. Ce n'est pas du bêta déguisé : on achète des mèches, pas le marché | passe |
| T10 | Un seul régime ? | Les cascades se concentrent en forte volatilité, et le rebond peut échouer dans une baisse durable (2022). Exiger 3 années sur 4 et un résultat positif en 2022 | conditionnel |

**Verdict : passe le tri sous trois conditions** :
1. l'audit des données (T4) ;
2. le test de retard d'entrée, inscrit dans la fiche (T5) ;
3. une grille de paramètres déclarée d'avance (T8).

C'est la piste de fréquence prioritaire. Fiche après l'audit.

**Infrastructure.** La mémoire est à mesurer par l'audit (jeu H). Traiter symbole par symbole évite de tout charger en RAM : environ 0,1 Go par symbole pour 5 ans de klines 1m en float32.
