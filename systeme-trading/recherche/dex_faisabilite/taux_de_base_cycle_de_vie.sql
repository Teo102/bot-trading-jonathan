-- Taux de base du cycle de vie des tokens pump.fun sur Solana (descriptif, aucune stratégie)
-- Moteur : DuneSQL (Trino), table dex_solana.trades. Écrite le 02/11/2026 sans accès à Dune : jamais exécutée,
-- schéma à contrôler avec la requête 0 de LISEZMOI.md.
--
-- Cohorte : mints suffixés « pump » dont le PREMIER trade vu dans dex_solana.trades tombe en juillet 2025.
-- Suivi : 30 jours après ce premier trade, en barres journalières. Lecture jusqu'au 31/08/2025 au plus :
-- septembre 2025 à octobre 2026 restent la réserve non lue de l'étude par les tokens.
-- Si dex_solana.trades ne contient pas la courbe de lancement pump.fun, « premier trade » veut dire « migration »
-- [à vérifier sur la colonne project avant lecture].
--
-- Sorties : entonnoir de valorisation (FDV maximale atteinte), survie à 7 et 30 jours, et pour les tokens qui
-- franchissent 5 M$ : rapport entre la FDV au jour 30 et le pic, et délai jusqu'au franchissement.

WITH params AS (
    SELECT TIMESTAMP '2025-07-01 00:00:00' AS debut,
           TIMESTAMP '2025-08-01 00:00:00' AS fin,
           TIMESTAMP '2025-09-01 00:00:00' AS borne_lecture,   -- jamais au-delà (réserve)
           1e9 AS offre,
           3   AS min_trades_jour                             -- jours à moins de 3 trades : prix non retenu
),
jambes AS (
    SELECT t.block_time, t.token_bought_mint_address AS mint, t.amount_usd AS usd, t.token_bought_amount AS qte
    FROM dex_solana.trades t CROSS JOIN params p
    WHERE t.block_month IN (DATE '2025-07-01', DATE '2025-08-01')
      AND t.block_time >= p.debut AND t.block_time < p.borne_lecture
      AND t.token_bought_mint_address LIKE '%pump' AND t.amount_usd > 0 AND t.token_bought_amount > 0
    UNION ALL
    SELECT t.block_time, t.token_sold_mint_address, t.amount_usd, t.token_sold_amount
    FROM dex_solana.trades t CROSS JOIN params p
    WHERE t.block_month IN (DATE '2025-07-01', DATE '2025-08-01')
      AND t.block_time >= p.debut AND t.block_time < p.borne_lecture
      AND t.token_sold_mint_address LIKE '%pump' AND t.amount_usd > 0 AND t.token_sold_amount > 0
),
premiers AS (
    -- premier trade dans la fenêtre lue ; un mint actif dès le 01/07 00:00 peut être plus ancien : il est écarté
    SELECT mint, min(block_time) AS t0 FROM jambes GROUP BY 1
),
cohorte AS (
    SELECT pr.mint, pr.t0 FROM premiers pr CROSS JOIN params p
    WHERE pr.t0 >= p.debut + INTERVAL '1' DAY AND pr.t0 < p.fin
      AND pr.t0 + INTERVAL '30' DAY <= p.borne_lecture
),
jours AS (
    SELECT j.mint, date_diff('day', c.t0, j.block_time) AS jour,
           sum(j.usd) AS vol_usd, sum(j.qte) AS qte, count(*) AS n
    FROM jambes j JOIN cohorte c ON c.mint = j.mint
    WHERE j.block_time >= c.t0 AND j.block_time < c.t0 + INTERVAL '30' DAY
    GROUP BY 1, 2
),
barres AS (
    SELECT j.*, CASE WHEN j.n >= p.min_trades_jour THEN j.vol_usd / j.qte * p.offre END AS fdv
    FROM jours j CROSS JOIN params p
),
par_token AS (
    SELECT mint,
           max(fdv)                                                  AS fdv_pic,
           max_by(fdv, jour) FILTER (WHERE fdv IS NOT NULL)          AS fdv_derniere,
           max(jour)                                                 AS dernier_jour_actif,
           sum(vol_usd)                                              AS vol_30j,
           min(jour) FILTER (WHERE fdv >= 5e6)                       AS jour_5m,
           max(CASE WHEN jour >= 27 THEN 1 ELSE 0 END)               AS actif_j27_j29,
           max(CASE WHEN jour BETWEEN 4 AND 6 THEN 1 ELSE 0 END)     AS actif_j4_j6
    FROM barres GROUP BY 1
),
classes AS (
    SELECT *,
           CASE WHEN fdv_pic IS NULL THEN '0. jamais coté (moins de 3 trades par jour)'
                WHEN fdv_pic < 1e5 THEN '1. < 100 k$'
                WHEN fdv_pic < 1e6 THEN '2. 100 k$ à 1 M$'
                WHEN fdv_pic < 5e6 THEN '3. 1 à 5 M$'
                WHEN fdv_pic < 2e7 THEN '4. 5 à 20 M$'
                ELSE '5. >= 20 M$' END AS palier_pic
    FROM par_token
)
SELECT
    palier_pic,
    count(*)                                                        AS tokens,
    count(*) * 1.0 / sum(count(*)) OVER ()                          AS part_de_la_cohorte,
    avg(actif_j4_j6 * 1.0)                                          AS part_actifs_j4_j6,
    avg(actif_j27_j29 * 1.0)                                        AS part_actifs_j27_j29,
    approx_percentile(fdv_derniere / nullif(fdv_pic, 0), 0.5)       AS mediane_fdv_finale_sur_pic,
    approx_percentile(jour_5m, 0.5)                                 AS mediane_jours_jusqu_a_5m,
    approx_percentile(vol_30j, 0.5)                                 AS mediane_volume_30j_usd,
    (SELECT count(*) FROM cohorte)                                  AS cohorte_totale
FROM classes
GROUP BY palier_pic
ORDER BY palier_pic
