"""Lot n° 2 du 17/11/2026 : probabilités écrites par Claude SANS lecture de prix (liste `candidats_sans_prix_20261116T092028Z.json`).
Recherche factuelle sans cote du 16/11/2026 vers 09:30 UTC (trois sous-agents), compteurs xtracker relus le 17/11 à 08:58 UTC,
état ouvert ou clos de chaque marché relu à la même heure (champs d'état seuls, aucun prix).
Règles du lot (leçons du lot 1) : aucun marché de prix crypto ni de matière première, pas de sport, rien sur Anthropic,
aucune grappe au-delà d'environ 20 % du lot, aucun événement déjà présent au journal.
Écartés avant écriture : 7 (Musk 160-179, clos), 115 (USS Theodore Roosevelt, clos), 132 (Bond, clos), 117 (diesel UE : publication
Eurostat vers février 2027, horizon réel trop long), 76 (Sánchez, horizon 2028), 80 (dérivé d'une cote), 128 (doublon de la Fed du lot 1),
133 (prix de l'or), 130 (sport), 78 (doublon de 111), 113 (doublon de 97), 89 et 91 (grappe FAA plafonnée), 92 (F3), 131 et 11 bis (grappe Huang)."""
R = "note de recherche sans cote du 16/11/2026 ; "
G_MUSK = (0, 1, 0, 1, 1, 1, 2)
G_TW = (0, 0, 1, 0, 0, 0, 2)
LOT = [
 (1, 0.03, "autre", "musk", G_MUSK, "Compteur à 51 le 17/11 à 08:58 UTC pour une fenêtre qui finit le 18/11 à 17:00 : rester sous 65 demande 13 publications au plus en 32 h ; le jour le plus calme des 21 derniers en compte 11", "xtracker (compteur seul) lu le 17/11 08:58 UTC"),
 (54, 0.01, "autre", "musk", G_MUSK, "580 en une semaine demande environ 83 par jour ; record des 8 dernières semaines : 394", R + "xtracker"),
 (125, 0.90, "autre", "musk", G_MUSK, "657 au 17/11 à 08:58 UTC ; il reste 343 à faire en 13,8 jours, soit 25 par jour, contre environ 40 par jour depuis le 1er ; octobre 1 504", "xtracker (compteur seul) lu le 17/11 08:58 UTC"),
 (11, 0.06, "tech", "huang", (2, 1, 0, 2, 2, 2, 3), "Trois relations déjà rapportées (épouse exclue) ; aucune quatrième personne dans un média qualifiant du 13 au 16/11 ; 4 jours restants", R + "NYT 11/11, Reuters 12/11"),
 (82, 0.12, "tech", "huang", (1, 1, 0, 1, 1, 1, 3), "Démission acceptée le 11/11, PDG par intérim nommé, cabinet de recrutement en cours ; pression d'investisseurs pour un retour (FT 15/11) mais le Trésor demande un PDG extérieur ; enquête interne ouverte", R + "CNBC 16/11, FT 15/11"),
 (103, 0.02, "tech", "huang", (1, 1, 0, 0, 1, 1, 2), "Aucune indication d'inculpation (Semafor 12/11) ; enquêtes visant des sociétés, pas Huang lui-même", R + "Semafor 12/11"),
 (114, 0.30, "tech", "huang", (2, 1, 1, 1, 1, 1, 3), "Relation avec son supérieur direct rapportée par le NYT (5 sources), contraire au code de conduite ; enquête du conseil en cours ; aucune annonce au 16/11", R + "NYT 11/11"),
 (86, 0.12, "politique", "", (1, 1, 0, 0, 1, 1, 2), "La Maison-Blanche aurait envisagé de l'écarter (Reuters 12/11), mais Trump affiche sa confiance ; il accompagne Trump en Chine et doit témoigner au Sénat le 10/12", R + "Reuters 12/11, Semafor 15/11"),
 (112, 0.07, "politique", "", (1, 1, 0, 0, 1, 1, 1), "Défaite électorale du 25/10, arrestations quotidiennes de proches ; aucune enquête ne le vise, et il est député (immunité à lever)", R + "BIRN 16/11"),
 (107, 0.45, "tech", "ia", (2, 1, 2, 1, 2, 2, 2), "Arena, 11/11 : MiMo (Xiaomi) premier modèle chinois, Qwen3.8-Max (Alibaba) juste derrière ; Qwen4-Max lancé vers le 16/11, pas encore classé ; égalités de rang fréquentes", R + "arena.ai lu le 16/11"),
 (111, 0.06, "tech", "ia", (1, 1, 0, 1, 1, 1, 2), "GPT-6.1 Astra annulé fin septembre pour des problèmes d'alignement ; rien de nouveau du 14 au 16/11 ; 2 semaines restantes", R + "Wikipedia GPT-6.1"),
 (84, 0.03, "politique", "faa", (2, 1, 1, 1, 1, 2, 2), "Explication officielle par un routeur défaillant ; « zero evidence of anything nefarious » (14/11) ; FBI en appui", R + "Fortune 15/11, Axios 14/11"),
 (87, 0.02, "politique", "faa", (1, 1, 1, 0, 1, 2, 2), "Aucun signe d'attaque étrangère selon le ministre (14-15/11) ; attribution officielle en moins de 3 semaines très rare", R + "Yahoo 15/11"),
 (32, 0.55, "politique", "iran", (1, 1, 1, 2, 2, 2, 1), "Aucune frappe américaine confirmée sur le sol iranien depuis le 6/11 ; il faut 14 jours sans frappe commencés au plus tard le 22/11 ; négociations bloquées, nouvelles frappes à l'étude selon le NYT", R + "GlobalSecurity 12/11, Gulf News 16/11"),
 (109, 0.05, "politique", "iran", (0, 0, 1, 1, 0, 0, 1), "Moyenne sur 7 jours vers 26 au 8/11 ; jamais sous 23 depuis décembre 2023 ; les Houthis avancent près du détroit", R + "IMF PortWatch lu le 16/11"),
 (116, 0.15, "politique", "iran", (1, 1, 1, 1, 2, 2, 1), "Houthis à environ 60 km d'Aden, en progression ; la ville se fortifie ; 2 semaines restantes", R + "AFP 15-16/11"),
 (118, 0.18, "politique", "iran", (1, 1, 1, 1, 2, 2, 1), "Attaques iraniennes contre Bahreïn les 13 et 15/11 ; dernière attaque contre les Émirats début septembre ; trois porte-avions américains dans la zone", R + "Gulf News 16/11"),
 (81, 0.05, "politique", "russie", (1, 1, 1, 1, 2, 2, 2), "Poutine refuse la trêve énergétique selon Zelensky (13-14/11) ; le sommet du 19/11 ne porte pas sur l'Ukraine", R + "Kyiv Post 14/11"),
 (97, 0.88, "politique", "russie", (1, 1, 1, 0, 1, 1, 2), "Sommet à trois Trump, Xi, Poutine annoncé à Shenzhen le 19/11 par la Maison-Blanche (13/11) et confirmé par le Kremlin (14/11) ; une rencontre à trois suffit ; risque d'annulation", R + "TASS 14/11, AA"),
 (98, 0.07, "politique", "russie", (2, 1, 1, 2, 2, 2, 1), "Incidents de drones fréquents mais affrontement armé confirmé avec des forces russes rare depuis 2022 ; origine souvent non établie", R + "Euronews 11/11"),
 (99, 0.04, "politique", "apec", (2, 1, 1, 1, 2, 3, 1), "Aucun président américain n'a soutenu explicitement la revendication ; Trump élude la question ; la politique d'une seule Chine ne suffit pas", R + "CNBC 15/5, CFR"),
 (105, 0.15, "politique", "apec", (1, 2, 1, 2, 2, 2, 2), "Relations tendues, mais Xi doit saluer chaque dirigeant au dîner ; une poignée de main brève est l'hypothèse de la presse japonaise ; « Yes » veut dire aucune poignée de main", R + "Bloomberg 8/11, Kyodo"),
 (110, 0.20, "politique", "apec", (1, 2, 1, 1, 2, 2, 2), "Trump prolonge souvent ses poignées de main ; 15 secondes est long ; mesure manuelle sur vidéo, durées passées avec Xi non trouvées", R + "programme APEC"),
 (72, 0.62, "politique", "taiwan", G_TW, "Maire sortante soutenue par le KMT ; TVBS fin octobre 46-31, sondage automatisé du 14-15/11 à égalité avec 36 % d'indécis", R + "TVBS 5/11, Newtalk 16/11"),
 (73, 0.42, "politique", "taiwan", G_TW, "Ville tenue par le KMT depuis 2010 ; sondages partagés (Li +3,6, Su +8,4, Li +4,7)", R + "China Times 15/11, LTN 13/11"),
 (74, 0.40, "politique", "taiwan", G_TW, "Ville sortante KMT (59 % en 2022) ; sondages partagés et commandités des deux côtés", R + "LTN 3/11, Newtalk 9/11"),
 (79, 0.12, "politique", "", (2, 1, 1, 1, 2, 2, 2), "Participation finale, étranger compris : 66,2 % (nov. 2019), 66,6 % (2023) ; 70 % franchi une seule fois depuis 2011 (avril 2019) ; le chiffre du soir sans l'étranger est plus haut que le chiffre final", R + "Intérieur, INE"),
 (69, 0.06, "autre", "", (1, 1, 1, 2, 1, 1, 2), "Liste de 34 titres fuitée le 14/11 sans lui ; il anime une radio du jeu, son titre est à la radio et non sur l'album", R + "RockstarINTEL 14/11, The FADER 8/10"),
 (134, 0.01, "politique", "", (1, 2, 1, 2, 1, 1, 3), "Il faut être chef de l'État en titre du Venezuela ; Rubio est secrétaire d'État américain et la Constitution exige d'être Vénézuélien de naissance", R + "AP 1/11"),
 (135, 0.06, "autre", "", (1, 0, 1, 1, 1, 1, 2), "Annonce vers le 10/12 ; un seul maire désigné depuis 1927 ; pas de liste courte au 16/11", R + "TIME, Al Jazeera 11/11"),
]
A_RELIRE = {}
