"""Lot du 09/11/2026 : probabilités écrites par Claude Fable 5.2 SANS lecture de prix (liste `candidats_sans_prix_20261109T205024Z.json`).
Chaque ligne : indice dans la liste, probabilité de « Yes », catégorie, grappe de corrélation, grille F S A C L V M, base, sources.
Notes de grille proposées par trois sous-agents de recherche (sans cote), relues par Claude. Cours crypto : Binance, 09/11/2026 21:05 UTC."""
R = "note de recherche sans cote du 09/11/2026 ; "
CR = "Binance spot 09/11/2026 21:05 UTC, volatilité journalière 30 j et 7 j horaire, modèle lognormal sans dérive"
G_CR = (1, 2, 1, 1, 0, 0, 2)
LOT = [
 # indice, proba, catégorie, grappe, (F,S,A,C,L,V,M), base, sources
 (1, 0.82, "autre", "crypto", G_CR, "BTC 74 968 contre seuil 72 000 à 2,8 j ; modèle 0,80 à 0,86, baisse récente prise en compte", CR),
 (10, 0.80, "autre", "crypto", G_CR, "ETH 2 131 contre 2 000 à 3,8 j ; modèle 0,78 à 0,84", CR),
 (11, 0.98, "autre", "crypto", G_CR, "XRP 1,095 contre 0,90 à 3,8 j ; il faudrait −18 %", CR),
 (24, 0.97, "autre", "crypto", G_CR, "BTC 74 968 contre 66 000 à 5,8 j ; il faudrait −12 %", CR),
 (34, 0.74, "autre", "crypto", G_CR, "BTC à 1,4 % du seuil de 76 000, 6,3 j restants, plus haut depuis le 9/11 : 75 568 ; modèle de toucher 0,81, réduit pour la tendance baissière", CR),
 (88, 0.73, "autre", "crypto", G_CR, "BTC à 3,3 % du seuil de 72 500, 21 j restants, plus bas de novembre 73 510 (non touché) ; modèle de toucher 0,75 à 0,80", CR),
 (90, 0.06, "autre", "crypto", G_CR, "ETH doit monter de 31 % en 21 j ; modèle 0,07 à 0,16, tendance baissière", CR),
 (91, 0.01, "autre", "crypto", G_CR, "SOL 86,7 contre 50 : −42 % en 21 j ; plancher pour une mèche isolée", CR),
 (7, 0.03, "autre", "musk", (1, 1, 1, 2, 2, 1, 2), "Compte 90 à environ 2,4 j, rythme 38 par jour ; la tranche 160-179 demande 15 à 19 par jour ensuite ; aucune des 11 dernières semaines sous 200", R + "xtracker (extrait), lines.com"),
 (55, 0.04, "autre", "musk", (1, 1, 1, 2, 2, 1, 2), "120-139 demande 17 à 20 par jour ; 6 dernières fenêtres entre 200 et 399 ; rythme en cours 38 par jour", R + "lines.com"),
 (32, 0.12, "tech", "", (2, 1, 1, 2, 2, 2, 2), "Carbon annoncé le 28/10 en accès restreint (cyberdéfense), aucun élargissement au 09/11 ; précédent Argon : 13 j entre accès restreint et disponibilité générale ; 6 j restants", R + "blog Google 28/10, apidog"),
 (56, 0.02, "tech", "gta", (1, 1, 0, 1, 1, 1, 2), "Préchargement ouvert les 9-10/11, bande-annonce de lancement, date confirmée ; un report à 10 jours serait sans précédent chez Rockstar", R + "PlayStation LifeStyle 09/11"),
 (83, 0.975, "tech", "gta", (1, 0, 0, 1, 1, 1, 2), "Même fait que le marché du report, avec 11 jours de marge", R + "PlayStation LifeStyle 09/11"),
 (82, 0.03, "tech", "", (2, 2, 1, 1, 1, 1, 2), "Apple 5,11 T$ contre Nvidia 4,30 T$ le 09/11 ; il faut +19 % relatif en 15 séances ; enquête sur le dirigeant ; résultats le 17/11", R + "stockanalysis, Business Standard 09/11"),
 (87, 0.01, "macro", "", (1, 1, 1, 2, 0, 1, 2), "WTI à 86,9 ; il faudrait +73 % ; 150 jamais atteint ; plancher pour une mèche du flux Pyth", R + "Investing, Trading Economics 09/11"),
 (92, 0.20, "macro", "", (0, 0, 1, 0, 0, 0, 2), "Contrats à terme : hausse de 25 pb vers 80 % le 09/11 après l'emploi d'octobre ; deux dissidents pour la hausse en octobre ; IPC d'octobre le 10/11", R + "CME FedWatch cité le 09/11, InvestmentNews 06/11"),
 (60, 0.40, "politique", "taiwan", (0, 1, 1, 0, 2, 0, 1), "Sondages partagés (TVBS 46-42 pour le sortant, UDN 45-41 pour Shen) ; Taipei penche vers le KMT ; dynamique pour Shen", R + "TVBS 31/10, UDN 28/10"),
 (62, 0.80, "politique", "taiwan", (0, 1, 1, 0, 2, 0, 1), "Kaohsiung bastion du DPP ; sondages de l'égalité à +20 pour Lai", R + "ETtoday 20-25/10, UDN 28-31/10"),
 (63, 0.94, "politique", "taiwan", (1, 1, 1, 1, 1, 0, 1), "KMT 14 contre DPP 5 en 2022 ; modèle TPOC de septembre 14 contre 7 ; l'égalité irait au DPP", R + "TPOC 07/09, Focus Taiwan"),
 (65, 0.07, "politique", "", (1, 1, 1, 0, 1, 0, 2), "PP devant dans tous les sondages (écart moyen 4,7 points) ; erreur de 2023 d'environ 4 points en faveur du PSOE", R + "Demócrata 09/11, GAD3, 40dB"),
 (68, 0.01, "politique", "", (2, 2, 0, 1, 2, 2, 0), "Aucun acte de disqualification ; la fenêtre se ferme au serment de la Knesset prévu le 10/11", R + "Jerusalem Post, Times of Israel 08/11"),
 (73, 0.15, "macro", "", (2, 2, 0, 2, 2, 2, 1), "Aucune livraison en 31 j ; 2 navires sur 4 déroutés, aucun acheteur connu ; loi de 2022 en vigueur ; 21 j restants et prix du diesel élevés", R + "United24 09/11, Al Jazeera 07/11"),
 (75, 0.10, "politique", "", (1, 1, 0, 1, 1, 1, 2), "En poste ; défendu par Trump les 4 et 8/11 ; pression forte après le mi-mandat ; 5 départs de haut niveau en 2026", R + "Boston Globe 09/11, The Intercept 05/11"),
 (78, 0.06, "politique", "ukraine", (2, 2, 0, 2, 2, 3, 2), "Moscou rejette toute trêve le 09/11 ; deux trêves générales courtes en 2026 ; pourparlers les 10-11/11", R + "RFE/RL 03/11, The National 09/11"),
 (84, 0.87, "politique", "ukraine", (2, 2, 0, 1, 1, 2, 2), "Pourparlers trilatéraux prévus les 10-11/11 à Abou Dhabi, délégation ukrainienne partie ; une réunion annulée en octobre", R + "RFE/RL 03/11, European Pravda 09/11"),
 (81, 0.60, "politique", "", (1, 1, 0, 1, 1, 1, 1), "Environ un contact public par mois ; aucun trouvé depuis le 31/10 ; 21 j restants et diplomatie active sur l'Ukraine", R + "France 24, CNN 06/11"),
 (85, 0.40, "politique", "", (2, 1, 0, 3, 2, 2, 0), "Poste vacant depuis 24 j ; épisode Dana White des 7-8/11 ; la vacance précédente a duré 43 j", R + "Variety 08/11, Wikipedia"),
 (29, 0.04, "politique", "iran", (2, 1, 0, 2, 2, 2, 1), "Blocus étendu les 7-8/11 ; positions divisées le 09/11 ; 6 j restants ; une annonce de Trump reste possible", R + "CBS 09/11, Iran International 09/11"),
 (30, 0.90, "politique", "iran", (2, 2, 1, 2, 2, 2, 2), "Aucun échange Israël-Iran trouvé en 90 j ; 6 j restants ; risque d'attribution des explosions de Qeshm et plans israéliens d'après élections", R + "CBS 03/11, NPR 22/10"),
 (69, 0.01, "macro", "iran", (0, 0, 1, 1, 0, 0, 0), "Moyenne sur 7 j à 4,4 transits contre un seuil de 60", R + "IMF PortWatch lu le 09/11"),
 (70, 0.40, "politique", "iran", (2, 2, 0, 1, 2, 2, 1), "Rencontre Vance-Rezaei annoncée par la Turquie pour la semaine suivante, démentie par Téhéran ; médiation qatarie active ; aucune rencontre en 48 j", R + "Iran International 09/11, Mehr 09/11"),
 (71, 0.12, "politique", "iran", (2, 2, 1, 2, 2, 2, 2), "Plan qatari sur la table, parties divisées ; deux accords en 2026, aucun depuis juillet ; baisse du pétrole lue comme un signe de détente", R + "Al Jazeera 09/11, CBS 09/11"),
 (72, 0.01, "politique", "iran", (2, 1, 1, 1, 1, 1, 1), "Aucun texte final en vue ; refus iraniens du 09/11", R + "Iran International 09/11"),
 (77, 0.06, "politique", "iran", (2, 2, 1, 2, 2, 2, 1), "Déclaration conjointe du 25/08 antérieure au marché ; aucune annonce depuis le 06/10", R + "Al Jazeera 26/08 et 09/11"),
 (79, 0.09, "politique", "iran", (2, 1, 0, 1, 1, 1, 1), "Suppose une reprise des frappes Israël-Iran (environ 0,12 en 21 j) puis une fermeture générale", R + "Israel Hayom 02/11, NPR 22/10"),
 (80, 0.12, "politique", "iran", (2, 2, 1, 2, 2, 2, 1), "Les frappes limitées de novembre n'ont pas fermé l'espace aérien ; une fermeture de deux heures suffirait en cas d'escalade", R + "Safe Airspace lu le 09/11"),
 (86, 0.03, "politique", "", (2, 2, 1, 1, 2, 1, 0), "Ville assiégée mais tenue par le gouvernement, aucun combat au centre", R + "Al Jazeera 07/11"),
]
# Marchés écartés de la saisie : un 3 en F, S ou L impose une relecture humaine (mode d'emploi, règle 8).
A_RELIRE = {26: "L3 : explosions de Qeshm du 08/11 non attribuées, postérieures à la création",
            67: "L3 : oléoduc « visé » le 09/11, arme non précisée, cas ouvert",
            74: "F3 : « de facto leader » et « prevented from acting » non définis"}
