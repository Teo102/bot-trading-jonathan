# Faisabilité DEX centrée sur les tokens — mode d'emploi

Écrit le 01/11/2026. Décision de Jonathan et Téo du même jour : approche par les wallets abandonnée (circulaire), étude de faisabilité par les tokens sur Dune avant tout code d'ingestion. Résultat de recherche, aucun ordre, aucune clé. **Ce n'est pas un backtest** : un seul mois, aucun essai de stratégie consommé. Si l'idée survit, une fiche passe par `validation-edge` (tri T1 à T10, puis § 1).

Requête : `faisabilite_tokens_solana.sql` (DuneSQL). Claude l'a écrite sans accès à Dune : **elle n'a jamais tourné**.

## 0. Contrôle du schéma, avant tout

```sql
SELECT block_month, block_time, project, token_bought_mint_address, token_sold_mint_address,
       token_bought_amount, token_sold_amount, amount_usd, trader_id, tx_id
FROM dex_solana.trades
WHERE block_month = DATE '2025-08-01' AND token_bought_mint_address LIKE '%pump'
LIMIT 20
```

Vérifier : noms de colonnes, `amount_usd` non nul sur les pools pump.fun et PumpSwap, quantités déjà en unités (et non en brut), présence des trades sur la courbe de lancement (`project`) [non nécessaire ici, le franchissement de 5 M$ se fait après migration]. Contrôler aussi sur 20 mints suffixés `pump` qu'ils viennent bien de pump.fun et que l'offre vaut 1 milliard.

## 1. Critères de lecture, écrits avant le premier passage

| Lecture | Seuil | Suite |
|---|---|---|
| **Arrêt** | Médiane nette à 7 j (morts à −100 %) ≤ −30 % **et** aucune classe d'âge ou de volume d'au moins 100 événements avec une moyenne `moyenne_mort_zero` > 0 | Idée écartée, consignée au journal |
| **Poursuite** | Au moins une classe d'au moins 100 événements avec moyenne et médiane `mort_zero` > 0 | Fiche de tri, puis second mois **différent** (pas un mois de la réserve) pour vérifier, avant toute ingestion |
| Entre les deux | — | Lecture commune, aucune variante ajoutée sur ce mois |

Huit classes sont lues (5 d'âge, 3 de volume) : une classe positive sur huit peut sortir par hasard. Ce n'est qu'une porte de faisabilité.

## 2. Hypothèses à relire

- Entrée au VWAP de la **première heure active après** l'heure de franchissement, pour éviter d'acheter au prix qui définit le seuil. Un franchissement sans trade dans les 6 h suivantes n'a pas d'entrée possible : il sort du tableau, et l'écart entre `franchissements_du_mois` et `evenements` le compte.
- Sortie au VWAP de la dernière heure active dans les 168 h. Un token sans trade depuis plus de 72 h compte à −100 % dans les colonnes `mort_zero` : le dernier prix d'un pool vidé n'est pas vendable. La colonne `moyenne_dernier_prix` donne la lecture optimiste.
- Coût : 1 % par côté [à mesurer sur la profondeur réelle]. Le VWAP horaire ne reflète pas l'impact d'un ordre réel.
- L'âge se mesure depuis le premier trade vu dans les 90 jours de recul. Au-delà, la classe est marquée « censure ».
- Le filtre anti-wash (20 trades et 10 signataires dans l'heure) est grossier.
- Le mois d'août 2025 est un choix arbitraire fait avant lecture. Septembre 2025 à octobre 2026 restent non lus.

## 3. Coût et exécution

La requête lit 4 mois de `dex_solana.trades` filtrés sur les mints `pump`. Le coût en crédits Dune et la durée sont [non mesurés]. En cas de dépassement, réduire `recul` à 30 jours (plus d'âges censurés) avant de toucher au reste.

## 4. Sorties à rapporter

Le tableau de synthèse complet (une ligne par classe), le nombre total d'événements, l'heure du passage et l'identifiant de la requête Dune. Ne rien filtrer avant de le partager.
