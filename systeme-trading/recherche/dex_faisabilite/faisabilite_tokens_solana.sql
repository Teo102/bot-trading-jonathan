-- Faisabilité DEX, approche centrée sur les tokens (décision de Jonathan et Téo du 01/11/2026)
-- Moteur : DuneSQL (Trino). Table : dex_solana.trades. Écrite le 01/11/2026 sans accès à Dune : schéma à
-- contrôler avec la requête 0 de LISEZMOI.md avant le premier passage.
--
-- Question : un token Solana lancé sur pump.fun qui franchit 5 M$ de valorisation totale (FDV) offre-t-il,
-- acheté juste après le franchissement et revendu 7 jours plus tard, un rendement net de coûts exploitable,
-- rugs et tokens morts compris ?
--
-- Univers : mints suffixés « pump » (lancement pump.fun, offre fixe de 1 milliard, autorité de création
-- révoquée). FDV = VWAP horaire × 1e9. Heuristique déclarée : suffixe = pump.fun [à vérifier sur un tirage].
-- Mois testé : août 2025, et lui seul. Septembre 2025 à octobre 2026 restent non lus (réserve).
-- Aucune donnée de wallet n'entre dans la sélection.

WITH params AS (
    SELECT
        TIMESTAMP '2025-08-01 00:00:00' AS debut,        -- premier franchissement retenu, inclus
        TIMESTAMP '2025-09-01 00:00:00' AS fin,          -- exclus
        INTERVAL '90' DAY                AS recul,        -- historique lu avant le mois pour l'âge et le premier franchissement
        5e6                              AS seuil_fdv,    -- USD
        1e9                              AS offre,        -- offre fixe pump.fun
        0.01                             AS cout_cote,    -- 1 % par côté (frais, impact, priorité) [à mesurer]
        20                               AS min_trades,   -- trades minimum dans l'heure de franchissement
        10                               AS min_traders,  -- signataires distincts minimum (anti-wash grossier)
        INTERVAL '72' HOUR               AS seuil_mort    -- aucun trade sur les 72 dernières heures : token mort
),

-- 1. Jambes de trade où le token étudié est acheté ou vendu, avec son prix implicite en USD
jambes AS (
    SELECT t.block_time, t.token_bought_mint_address AS mint, t.amount_usd AS usd,
           t.token_bought_amount AS qte, t.trader_id
    FROM dex_solana.trades t CROSS JOIN params p
    WHERE t.block_month >= CAST(date_trunc('month', p.debut - p.recul) AS DATE)
      AND t.block_month <  CAST(date_trunc('month', p.fin + INTERVAL '9' DAY) AS DATE) + INTERVAL '1' MONTH
      AND t.block_time >= p.debut - p.recul
      AND t.block_time <  p.fin + INTERVAL '9' DAY
      AND t.token_bought_mint_address LIKE '%pump'
      AND t.amount_usd > 0 AND t.token_bought_amount > 0
    UNION ALL
    SELECT t.block_time, t.token_sold_mint_address, t.amount_usd,
           t.token_sold_amount, t.trader_id
    FROM dex_solana.trades t CROSS JOIN params p
    WHERE t.block_month >= CAST(date_trunc('month', p.debut - p.recul) AS DATE)
      AND t.block_month <  CAST(date_trunc('month', p.fin + INTERVAL '9' DAY) AS DATE) + INTERVAL '1' MONTH
      AND t.block_time >= p.debut - p.recul
      AND t.block_time <  p.fin + INTERVAL '9' DAY
      AND t.token_sold_mint_address LIKE '%pump'
      AND t.amount_usd > 0 AND t.token_sold_amount > 0
),

-- 2. Préfiltre de coût : mints dont au moins un trade du mois implique une FDV >= seuil
candidats AS (
    SELECT DISTINCT j.mint
    FROM jambes j CROSS JOIN params p
    WHERE j.block_time >= p.debut AND j.block_time < p.fin AND j.usd / j.qte * p.offre >= p.seuil_fdv
),

-- 3. Barres horaires par token : VWAP, volume, activité
heures AS (
    SELECT mint, date_trunc('hour', block_time) AS h,
           sum(usd) AS vol_usd, sum(qte) AS qte, count(*) AS n_trades,
           count(DISTINCT trader_id) AS n_traders
    FROM jambes
    WHERE mint IN (SELECT mint FROM candidats)
    GROUP BY 1, 2
),
barres AS (
    SELECT b.*, b.vol_usd / b.qte AS vwap, b.vol_usd / b.qte * p.offre AS fdv
    FROM heures b CROSS JOIN params p
),

-- 4. Premier franchissement du seuil (sur tout le recul), retenu seulement s'il tombe dans le mois
premiere_activite AS (
    SELECT mint, min(h) AS h_premiere FROM barres GROUP BY 1
),
franchissements AS (
    SELECT b.mint, min(b.h) AS h0
    FROM barres b CROSS JOIN params p
    WHERE b.fdv >= p.seuil_fdv AND b.n_trades >= p.min_trades AND b.n_traders >= p.min_traders
    GROUP BY 1
),
evenements AS (
    SELECT f.mint, f.h0, a.h_premiere,
           date_diff('hour', a.h_premiere, f.h0) AS age_h,
           a.h_premiere <= p.debut - p.recul + INTERVAL '1' DAY AS age_censure
    FROM franchissements f
    JOIN premiere_activite a ON a.mint = f.mint
    CROSS JOIN params p
    WHERE f.h0 >= p.debut AND f.h0 < p.fin
),

-- 5. Entrée : première heure active APRÈS l'heure de franchissement (aucune anticipation), sous 6 h
entree_h AS (
    SELECT e.mint, min(b.h) AS h_entree
    FROM evenements e JOIN barres b ON b.mint = e.mint AND b.h > e.h0 AND b.h <= e.h0 + INTERVAL '6' HOUR
    GROUP BY 1
),

-- 6. Sortie : dernière heure active dans ]entrée ; entrée + 168 h]
fenetre AS (
    SELECT n.mint, n.h_entree, b.h, b.vwap, b.vol_usd
    FROM entree_h n JOIN barres b ON b.mint = n.mint AND b.h > n.h_entree AND b.h <= n.h_entree + INTERVAL '168' HOUR
),
sortie AS (
    SELECT mint,
           max(h)                                   AS h_derniere,
           max_by(vwap, h)                          AS prix_sortie,
           min(vwap)                                AS prix_min,
           max(vwap)                                AS prix_max,
           sum(vol_usd)                             AS vol_7j
    FROM fenetre GROUP BY 1
),

-- 7. Table des événements, rugs et morts compris
table_ev AS (
    SELECT e.mint, e.h0, n.h_entree, e.age_h, e.age_censure,
           b0.fdv AS fdv_franchissement, b0.vol_usd AS vol_heure0, b0.n_traders AS traders_heure0,
           be.vwap AS prix_entree, s.prix_sortie, s.h_derniere, s.vol_7j,
           s.prix_min / be.vwap - 1 AS excursion_contre,
           s.prix_max / be.vwap - 1 AS excursion_pour,
           -- mort : aucun trade dans la fenêtre, ou dernier trade plus de 72 h avant la sortie prévue
           (s.h_derniere IS NULL OR s.h_derniere < n.h_entree + INTERVAL '168' HOUR - p.seuil_mort) AS mort,
           coalesce(s.prix_sortie, 0) / be.vwap - 1 AS r_brut
    FROM evenements e
    JOIN entree_h n ON n.mint = e.mint
    JOIN barres b0 ON b0.mint = e.mint AND b0.h = e.h0
    JOIN barres be ON be.mint = e.mint AND be.h = n.h_entree
    LEFT JOIN sortie s ON s.mint = e.mint
    CROSS JOIN params p
),
nets AS (
    SELECT t.*,
           (1 + r_brut) * (1 - p.cout_cote) * (1 - p.cout_cote) - 1 AS r_net,
           CASE WHEN mort THEN -1.0 ELSE (1 + r_brut) * (1 - p.cout_cote) * (1 - p.cout_cote) - 1 END AS r_net_mort_zero,
           CASE WHEN age_censure THEN '5. >= 90 j (censure)'
                WHEN age_h < 24 THEN '1. < 24 h'
                WHEN age_h < 24 * 7 THEN '2. 1 à 7 j'
                WHEN age_h < 24 * 30 THEN '3. 7 à 30 j'
                ELSE '4. 30 à 90 j' END AS classe_age,
           CASE WHEN vol_heure0 < 1e5 THEN '1. < 100 k$'
                WHEN vol_heure0 < 1e6 THEN '2. 100 k$ à 1 M$'
                ELSE '3. >= 1 M$' END AS classe_volume
    FROM table_ev t CROSS JOIN params p
)

-- 8. Synthèse : ensemble, par âge, par volume. Pour la table brute : SELECT * FROM nets
SELECT
    coalesce(classe_age, 'tous')                         AS classe_age,
    coalesce(classe_volume, 'tous')                      AS classe_volume,
    count(*)                                             AS evenements,
    (SELECT count(*) FROM evenements)                    AS franchissements_du_mois,  -- écart = aucun trade sous 6 h, aucune entrée possible
    avg(CAST(mort AS INTEGER))                           AS part_morts,
    approx_percentile(r_net_mort_zero, 0.10)             AS p10,
    approx_percentile(r_net_mort_zero, 0.25)             AS p25,
    approx_percentile(r_net_mort_zero, 0.50)             AS mediane,
    approx_percentile(r_net_mort_zero, 0.75)             AS p75,
    approx_percentile(r_net_mort_zero, 0.90)             AS p90,
    avg(r_net_mort_zero)                                 AS moyenne_mort_zero,
    avg(r_net)                                           AS moyenne_dernier_prix,
    avg(CASE WHEN r_net_mort_zero <= -0.9 THEN 1.0 ELSE 0 END) AS part_perte_90pct,
    avg(CASE WHEN r_net_mort_zero >= 1.0 THEN 1.0 ELSE 0 END)  AS part_double,
    approx_percentile(excursion_contre, 0.50)            AS excursion_contre_mediane
FROM nets
GROUP BY GROUPING SETS ((), (classe_age), (classe_volume))
ORDER BY 1, 2
