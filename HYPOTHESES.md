# Registre des hypothèses

Fichier généré par `python registry.py doc` depuis [data_model/parameters.json](data_model/parameters.json) : ne pas le modifier à la main.

Statuts :

- **E** exploré : varie dans l'étude, intervalle justifié par la littérature ou déclaré inconnu
- **S** sourcé : fixé à une valeur de la littérature
- **N** numérique : paramètre de calcul, sans effet sur les résultats (test de convergence)
- **D** définition : convention d'unité ou donnée d'observation
- **I** non influent : fixé car le criblage de Morris montre qu'il ne pèse pas
- **M** choix de modèle : forme d'une loi ou règle, alternatives testées en robustesse

85 paramètres : 45 E, 2 S, 7 N, 17 D, 14 M.
23 règles codées en dur. 50 points ouverts.

## E : exploré

| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |
|---|---|---|---|---|---|---|
| `panspermia_range_pc` | 300 | pc | [30 ; 1000] log (provisoire) | Rayon des bulles de vie autour de leur centre. | Regroupement spatial de la vie (Forgan 2009 : apparition en amas). Valeur inconnue. | Phase 5 : intervalle. |
| `expected_bubbles` | 5 | bulles | [1 ; 10] log (provisoire) | Nombre moyen de bulles de vie dans la région (loi de Poisson). | Fréquence de l'apparition de la vie : inconnue (Sandberg, Drexler & Ord 2018). | Phase 5 : intervalle (zéro bulle inclus ?). |
| `civs_per_bubble` | 20 | civs | [5 ; 40] log (provisoire) | Nombre moyen de civs initiales par bulle (loi de Poisson). | Fréquence de l'émergence de l'intelligence : inconnue. | Phase 5 : intervalle. |
| `civ_birth_rate` | 1e-08 | civs/an | [1e-10 ; 1e-07] log (provisoire) | Taux de naissance de nouvelles civs après le départ. | Inconnu. | Phase 5 : intervalle. |
| `start_lookback_years` | 1e+09 | an (avant le présent) | [1e+08 ; 5.2e+09] log (littérature) | Début de la simulation, compté avant le présent : dernier épisode stérilisant (sursaut gamma galactique). Les civs initiales y naissent toutes. | Annis 1999 : des sursauts gamma stérilisent périodiquement la Galaxie et resynchronisent l'apparition de l'intelligence ; intervalle actuel entre sursauts ≈ 10^8 ans (borne basse). Piran & Jimenez 2014 : la vie telle que sur Terre n'a pas pu exister à z > 0,5, soit ≈ 5,2 Ga avant le présent en cosmologie Planck (borne haute). Aucune civ n'existant avant ce départ, aucune sonde plus ancienne n'est possible : la fenêtre d'artefacts (4,5 Ga) couvre donc toute la simulation dès que le départ est plus récent. Source : Annis, J. 1999, JBIS (janvier 1999), arXiv:astro-ph/9901322 ; Piran, T. & Jimenez, R. 2014, PRL 113, 231102 (arXiv:1409.2506). Âge à z = 0,5 calculé avec H0 = 67,66, Ωm = 0,3111 (Planck 2018). | Phase 2, point 3 : cohorte synchrone. |
| `artefact_detection_probability` | 0.1 | probabilité | [0.001 ; 0.5] log (provisoire) | Probabilité de trouver la sonde d'une civ qui a visité le Système solaire. | Dépend de la part du Système solaire fouillée. | Phase 2, point 11 : borner par la recherche réelle (Haqq-Misra & Kopparapu 2012 ; Benford 2019). |
| `artefact_stealth_per_tech` | 0 | 1/tech | [0 ; 5] linear (inconnu) | Discrétion des sondes : probabilité de découverte multipliée par exp(-k × écart entre la tech du propriétaire et la tech actuelle de l'humanité, humanity_present_tech). | Une civ avancée peut faire des sondes discrètes. Forme et intensité inconnues. |  |
| `initial_tech_level` | 0.1 | tech | [0.01 ; 1] log (provisoire) | Tech d'une civ à sa naissance, y compris l'humanité il y a 10 000 ans (Néolithique). | Niveau où une civ devient une civilisation, relatif au plafond : inconnu. | Phase 5 : intervalle. |
| `humanity_tech_fraction` | 0.001 | sans dimension | [1e-06 ; 0.95] log (inconnu) | Position actuelle de l'humanité sur l'échelle de tech, en fraction du chemin entre la naissance et le plafond, en ordres de grandeur : T_h = initial_tech_level × (tech_cap / initial_tech_level)^f. L'humanité suit la trajectoire exacte de la loi de croissance de initial_tech_level (il y a 10 000 ans) à T_h (aujourd'hui) ; son rythme s'en déduit. | Inconnu : sommes-nous loin du plafond technologique ? Au rythme humain déduit, le plafond est à environ 10^4 / f ans : de quelques millénaires (f = 0,95) à l'âge de l'Univers (f = 10^-6). Une fraction évite une contrainte d'ordre avec initial_tech_level dans l'hypercube latin (décision du 2026-11, phase 2, point 5). |  |
| `self_destruction_risk` | 1e-08 | 1/an | [1e-10 ; 1e-06] log (provisoire) | Taux d'autodestruction au pic de la fenêtre de danger. | Inconnu (Ćirković 2009, scénario « catastrophique »). | Phase 5 : intervalle. |
| `danger_window_center` | 1.5 | tech | [0.2 ; 2.8] linear (inconnu) | Niveau de tech du pic de risque d'autodestruction. | Inconnu. |  |
| `danger_window_width` | 0.5 | tech | [0.1 ; 1.5] log (inconnu) | Largeur de la fenêtre de danger. | Inconnu. |  |
| `emit_radius_per_tech` | 10 | pc/tech | [1 ; 30] log (provisoire) | Portée des signaux d'une civ qui émet volontairement, par niveau de tech. | Mélange puissance et sensibilité. | Phase 2, point 11 : remplacer par une puissance émise (EIRP) et un seuil de sensibilité sourcé. |
| `passive_leakage_factor` | 0.1 | sans dimension | [0.01 ; 1] log (provisoire) | Portée des fuites d'une civ qui n'émet pas volontairement, relative à l'émission volontaire. | Inconnu. | Phase 2, point 11 : devient un rapport de puissance (EIRP) entre fuites et émission volontaire. Phase 5 : intervalle. |
| `probe_speed_per_tech` | 0.0001 | pc/an/tech | [1e-05 ; 0.001] log (provisoire) | Vitesse d'expansion de la sphère des sondes, par niveau de tech. | À caler par deux ancres : vitesse humaine (Voyager ≈ 5·10⁻⁵ c) et vitesse au plafond (0,01 à 0,5 c, Armstrong & Sandberg 2013 ; Bjork 2007). | Phase 2, point 4 : recaler sur les ancres. |
| `probe_lifetime_per_tech` | 1e+06 | an/tech | [1e+05 ; 1e+08] log (provisoire) | Durée de vie des sondes, par niveau de tech. | Inconnu. | Phase 2, point 4 : recaler sur les ancres. |
| `front_speed_per_tech` | 1e-07 | pc/an/tech | [1e-10 ; 1e-06] log (provisoire) | Vitesse du front de colonisation par niveau de tech, pour une agressivité de 1. | Fronts de colonisation : Carroll-Nellenback et al. 2019 ; Newman & Sagan 1981. | Phase 2, point 4 : recaler sur les ancres. Phase 5 : sourcer. |
| `habitable_world_density` | 0.01 | mondes/pc³ | [0.0001 ; 0.1] log (provisoire) | Densité de mondes habitables (tous types de biochimie). | À sourcer : densité stellaire locale (≈ 0,1 étoile/pc³) × η⊕ (Kepler). | Phase 5 : sourcer η⊕. |
| `belief_memory_years` | 0 | an | [0 ; 1e+05] linear (inconnu) | Durée pendant laquelle une civ continue d'agir envers une cible qu'elle ne voit plus. | Comportemental : inconnu (0 = n'agit que sur ce qu'elle voit). |  |
| `share_catchup` | 0.5 | fraction/période | [0.05 ; 0.95] linear (inconnu) | Part de l'écart de tech comblée par le receveur d'un partage, par période. | Comportemental : inconnu. |  |
| `share_backflow` | 0.05 | fraction/période | [0 ; 0.2] linear (inconnu) | Gain de tech du plus avancé lors d'un partage. | Comportemental : inconnu. |  |
| `share_decay` | 0.5 | tech | [0.1 ; 2] log (inconnu) | Échelle de décroissance du gain du plus avancé avec l'écart de tech. | Comportemental : inconnu. |  |
| `share_synergy_bonus` | 0.1 | fraction/période | [0 ; 0.5] linear (inconnu) | Gain du rythme de progrès techno par période de partage continu. | Comportemental : inconnu. |  |
| `share_trust_gain` | 0.3 | fraction/période | [0.05 ; 0.9] linear (inconnu) | Part de la confiance manquante gagnée par période de partage. | Comportemental : inconnu. |  |
| `forgiveness` | 0.2 | sans dimension | [0 ; 1] linear (inconnu) | Facteur sur le gain de confiance envers une civ qui nous a attaqués. | Comportemental : inconnu. |  |
| `damage_coef` | 0.3 | fraction/période | [0.05 ; 1] linear (inconnu) | Une guerre détruit min(1, damage_coef × tech attaquant / tech cible) de la cible par période d'interaction ; 1 = destruction immédiate. | Inconnu. | Phase 2, point 7 : forme de la loi de dégâts. |
| `attacks_per_tech_population` | 1 | guerres/(tech × population) | [0.1 ; 10] log (inconnu) | Nombre maximal de guerres menées en même temps = max(1, int(coef × tech × population)). | Capacité offensive : inconnue. Constante cachée sortie en phase 1. |  |
| `attack_cost_tech` | 0.05 | fraction/période | [0 ; 0.3] linear (inconnu) | Fraction de sa tech qu'une civ dépense par période d'interaction, pour chaque guerre en cours. | Inconnu. |  |
| `reputation_trust_drop` | 0.3 | confiance/période | [0 ; 1] linear (inconnu) | Baisse de confiance envers un attaquant connu, par période d'interaction, chez les civs qui voient sa victime subir une guerre en cours. | Comportemental : inconnu. |  |
| `natural_tech_progress_mean` | 1e-10 | 1/an | [3e-11 ; 3e-10] log (provisoire) | Rythme moyen de progrès techno. | Inconnu. | Phase 5 : intervalle. |
| `natural_tech_progress_spread` | 0.5 | sans dimension | [0 ; 0.9] linear (inconnu) | Dispersion du rythme de progrès entre civs : moyenne × U(1 - s, 1 + s). | Hétérogénéité des civs : inconnue. Constante cachée sortie en phase 1. |  |
| `natural_population_growth_spread` | 0.5 | sans dimension | [0 ; 0.9] linear (inconnu) | Dispersion du taux de croissance démographique entre civs : moyenne × U(1 - s, 1 + s). | Hétérogénéité des civs : inconnue. Constante cachée sortie en phase 1. |  |
| `tech_population_exponent` | 1 | sans dimension | [0 ; 1] linear (inconnu) | Rendement de la population sur le progrès techno (rythme × population^exposant). | Inconnu : de 0 (tech indépendante de la population) à 1 (rendement linéaire). |  |
| `natural_population_growth_mean` | 1e-09 | 1/an | [1e-10 ; 1e-08] log (provisoire) | Taux moyen de croissance démographique. | Inconnu. | Phase 5 : intervalle. |
| `max_natural_tech_progress` | 1e-07 | 1/an | [1e-09 ; 1e-06] log (provisoire) | Plafond du rythme de progrès atteignable par synergie de partage. | Inconnu. | Phase 5 : intervalle (doit rester au-dessus du rythme naturel maximal). |
| `broadcast_probability` | 0.5 | probabilité | [0 ; 1] linear (inconnu) | Probabilité d'émettre volontairement pour une civ de l'archétype « random ». | Inconnu. |  |
| `strategy_mix_random` | 1 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « random » (tous les traits tirés uniformément). | Composition stratégique de la galaxie : inconnue. | Phase 6 : couvrir aussi les galaxies dominées par un seul archétype (plan de mélange). |
| `strategy_mix_full_aggressive` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « full_aggressive ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_full_passive` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « full_passive ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_anti_competitors` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « anti_competitors ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_anti_weaker_competitors` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « anti_weaker_competitors ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_dark_forest` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « dark_forest ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_broadcaster` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « broadcaster ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_mix_cooperative` | 0 | poids | [0.01 ; 1] log (inconnu) | Poids de l'archétype « cooperative ». | Composition stratégique de la galaxie : inconnue. |  |
| `strategy_noise` | 0.05 | fraction de l'intervalle du trait | [0 ; 0.3] linear (inconnu) | Dispersion des civs autour de leur archétype. | Inconnu. |  |

## S : sourcé

| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |
|---|---|---|---|---|---|---|
| `scale_height_pc` | 300 | pc |  | Hauteur d'échelle du profil vertical exponentiel des positions. | Hauteur d'échelle du disque mince d'environ 300 pc. Source : Jurić et al. 2008, ApJ 673, 864 (disque mince H ≈ 300 pc). | Vérifier la référence avant citation. |
| `sun_height_pc` | 20.8 | pc |  | Hauteur de l'humanité (le Soleil) au-dessus du plan médian ; elle est placée au centre de la région. | Position observée. La région représente le voisinage du Soleil, et les observations (silence, couverture SETI selon la distance) sont centrées sur la Terre : l'humanité est au centre, ce qui supprime aussi un effet de bord artificiel (décision du 2026-11, phase 2, point 5). Source : Bennett, M. & Bovy, J. 2019, MNRAS 482, 1417, arXiv:1809.03507 (Gaia DR2 : z☉ = 20,8 ± 0,3 pc). |  |

## N : numérique

| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |
|---|---|---|---|---|---|---|
| `dt` | 1000 | an |  | Pas de temps de la simulation. | Paramètre de calcul : les taux sont définis par an ou par période d'interaction (interaction_period_years), donc indépendants du pas. | Phase 3 : convergence en dt (1000, 100, 10 ans). |
| `max_civs` | 100000 | civs |  | Nombre maximal de civs avant d'arrêter le run comme intraitable. | Garde-fou de calcul. | Phase 3 : vérifier qu'aucun run de l'étude ne l'atteint. |
| `max_steps` | 0 | pas |  | Budget de calcul déterministe (0 = sans limite) ; au-delà, le run est classé timeout. | Garde-fou de calcul. | Phase 4 : ramener les timeouts à environ 0 %, car ce sont des données censurées corrélées aux paramètres. |
| `fast_forward` | oui | booléen |  | Saut des régimes stationnaires. | Accélération : les sauts reproduisent la loi des tirages pas à pas (compare_fast_forward.py). | Phase 3 : comparer les distributions de résultats avec et sans fast-forward. |
| `max_jump_years` | 1e+07 | an |  | Durée maximale d'un saut. | Paramètre de calcul du fast-forward. | Phase 3 : convergence. |
| `jump_max_relative_change` | 0.01 | sans dimension |  | Variation relative maximale d'une variable lente pendant un saut. | Paramètre de calcul du fast-forward. | Phase 3 : convergence. |
| `max_probe_radius` | 1e+12 | pc |  | Plafond technique du rayon des sondes. | Valeur jamais atteinte (10¹² pc) : sans effet. |  |

## D : définition

| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |
|---|---|---|---|---|---|---|
| `humanity_birth_date_years` | 1.38e+10 | an (depuis le Big Bang) |  | Début de la civilisation humaine (présent - 10 000 ans) : à partir de là, l'humanité peut être vue par des sondes et attaquée, et sa tech suit sa trajectoire observée. | Début du Néolithique, environ 10 000 à 12 000 ans avant le présent. Source : À sourcer (révolution néolithique). |  |
| `present_date_years` | 1.38e+10 | an (depuis le Big Bang) |  | Date du présent. | Âge de l'Univers. Source : Planck Collaboration 2020 (13,787 ± 0,020 Ga). |  |
| `signal_window_years` | 100 | an |  | Fenêtre pendant laquelle l'humanité émet et écoute. | Durée des technosignatures humaines, environ un siècle. | Phase 2, point 11 : remplacer par deux fenêtres (détectable depuis les années 1930, écoute depuis 1960). |
| `artefact_window_years` | 4.5e+09 | an |  | Fenêtre des critères « colonized » et « artefact » : âge du Système solaire. | Le Système solaire aurait gardé la trace d'une occupation ou d'une sonde depuis sa formation (« Fait A » de Hart). Source : Âge du Système solaire 4,567 Ga (à sourcer) ; Hart 1975. |  |
| `tech_cap` | 3 | tech |  | Plafond de tech. | Convention : fixe l'unité de l'échelle de tech, qui est abstraite (MODEL_CHOICES.md, point 4). Les effets sont calés par deux ancres : niveau humain et plafond. |  |
| `population_per_world` | 1 | population/monde |  | Capacité d'un monde. | Convention : unité de population (un monde plein = 1). |  |
| `interaction_period_years` | 1000 | an |  | Période de référence des taux d'interaction : partages (share_*), guerre (damage_coef, attack_cost_tech) et réputation (reputation_trust_drop). | Convention : unité de temps de ces taux, qui sont explorés. Chaque événement applique un pas dt de ces taux, si bien que leur effet annuel ne dépend pas de dt (phase 2, point 12). |  |
| `attack_when_trust_inferior_than_low` | 0 | confiance |  | Borne basse du seuil de confiance sous lequel une civ attaque. | Convention : la confiance est dans [0, 1]. |  |
| `attack_when_trust_inferior_than_high` | 1 | confiance |  | Borne haute du seuil de confiance sous lequel une civ attaque. | Convention : la confiance est dans [0, 1]. |  |
| `trust_default_competitor_low` | 0 | confiance |  | Borne basse de la confiance initiale envers un concurrent. | Convention : la confiance est dans [0, 1]. |  |
| `trust_default_competitor_high` | 1 | confiance |  | Borne haute de la confiance initiale envers un concurrent. | Convention : la confiance est dans [0, 1]. |  |
| `trust_default_noncompetitor_low` | 0 | confiance |  | Borne basse de la confiance initiale envers un non-concurrent. | Convention : la confiance est dans [0, 1]. |  |
| `trust_default_noncompetitor_high` | 1 | confiance |  | Borne haute de la confiance initiale envers un non-concurrent. | Convention : la confiance est dans [0, 1]. |  |
| `share_trust_threshold_low` | 0 | confiance |  | Borne basse du seuil de confiance au-dessus duquel une civ partage. | Convention : la confiance est dans [0, 1]. |  |
| `share_trust_threshold_high` | 1 | confiance |  | Borne haute du seuil de confiance au-dessus duquel une civ partage. | Convention : la confiance est dans [0, 1]. |  |
| `colonization_aggressiveness_low` | 0 | fraction |  | Borne basse de l'agressivité de colonisation. | Convention : fraction dans [0, 1]. |  |
| `colonization_aggressiveness_high` | 1 | fraction |  | Borne haute de l'agressivité de colonisation. | Convention : fraction dans [0, 1]. |  |

## M : choix de modèle

| Paramètre | Valeur par défaut | Unité | Intervalle | Description | Justification | Points ouverts |
|---|---|---|---|---|---|---|
| `region_radius_pc` | 1000 | pc |  | Rayon de la région simulée (disque). | Choix de l'échelle simulée : une région autour du Soleil, pas la Galaxie entière. | Phase 2, point 6 : justifier la taille. Phase 3 : effets de bord à densité constante. |
| `biochem_types` | water, ammonia, silicon | liste |  | Types de biochimie ; deux civs du même type sont concurrentes. | Représente la non-concurrence pour les mêmes mondes entre formes de vie différentes. | Phase 2 : justifier la concurrence binaire par biochimie. |
| `world_type_fractions` | 0.7, 0.2, 0.1 | fractions |  | Probabilité de chaque type de biochimie. | Fixe la part de paires concurrentes. Valeurs 70/20/10 non sourcées. | Phase 2 : réduire à un paramètre explorable (par exemple la probabilité que deux civs soient concurrentes). |
| `tech_growth_model` | logistic | choix |  | Loi de croissance de la tech. | Logistique : croissance bornée par un plafond. Alternatives : exponential. | Phase 7 : robustesse. |
| `population_growth_model` | logistic | choix |  | Loi de croissance de la population. | Logistique : bornée par la capacité des mondes occupés. Alternatives : exponential. | Phase 7 : robustesse. |
| `initial_population` | 1 | population |  | Population d'une civ à sa naissance. | Une civ naît avec son monde d'origine peuplé (= population_per_world). |  |
| `self_destruction_shape` | danger_window | choix |  | Forme du risque d'autodestruction en fonction de la tech. | Fenêtre de danger : risque maximal à un niveau de tech intermédiaire (filtre lié à la technologie). Alternatives : constant, increasing. | Phase 7 : robustesse. |
| `max_broadcast_radius` | 100 | pc |  | Plafond dur de la portée des signaux. | Plafond sans justification. | Phase 2, point 11 : disparaît avec le modèle EIRP. |
| `attack_gap_min_low` | -2 | tech |  | Borne basse du trait attack_gap_min (écart de tech minimal pour attaquer). | Définition de l'espace des stratégies : couvre de « attaque même plus fort que soi » à « attaque seulement nettement plus faible ». | Phase 2, point 7 : écart ou rapport de tech. |
| `attack_gap_min_high` | 2 | tech |  | Borne haute du trait attack_gap_min. | Définition de l'espace des stratégies. |  |
| `attack_gap_max_low` | 2 | tech |  | Borne basse du trait attack_gap_max (écart de tech maximal pour attaquer). | Définition de l'espace des stratégies. |  |
| `attack_gap_max_high` | 10 | tech |  | Borne haute du trait attack_gap_max. | Définition de l'espace des stratégies. |  |
| `caution_k_low` | 0 | sans dimension |  | Borne basse du trait caution_k : poids donné au progrès possible de la cible pendant le trajet de la lumière (0 = l'ignore). | Définition de l'espace des stratégies : 0 = naïf, ignore le retard de la lumière. |  |
| `caution_k_high` | 3 | sans dimension |  | Borne haute du trait caution_k. | Définition de l'espace des stratégies : 1 = suppose que la cible a progressé au rythme vu ; au-delà, prudence croissante (3 = triple de ce progrès). |  |

## Règles codées en dur

| Règle | Statut | Où | Description | Justification | Points ouverts |
|---|---|---|---|---|---|
| `light_speed` | D | python/constants.py | Vitesse de la lumière : 1/3,262 pc/an ; aucune information ne voyage plus vite. | Constante physique. Pas de voyage plus rapide que la lumière. |  |
| `home_world` | M | python/generate_world/_new_civ.py | Une civ naît avec un seul monde. | Point de départ de la colonisation. |  |
| `synchronized_cohort` | M | python/generate_world/_seed_life_in_bubbles.py | Toutes les civs initiales naissent au départ (présent - start_lookback_years), avec la même tech. | Partielle : Annis 1999 justifie une resynchronisation par le dernier sursaut gamma, mais pas une naissance simultanée avec la même tech (l'évolution vers l'intelligence prend du temps et varie). | Phase 2, point 3 : étaler les naissances. |
| `bubble_geometry` | M | python/generate_world/_sample_lens_position.py, _seed_life_in_bubbles.py | Centres des bulles : disque uniforme en surface, profil vertical exponentiel. Civs uniformes dans une boule autour du centre. | Approximation du disque mince. | Phase 2, point 6. |
| `humanity_strategy` | M | python/generate_world/_make_humanity.py | L'humanité tire une stratégie, puis n'attaque jamais, n'émet jamais volontairement et ne colonise pas (colonization_aggressiveness = 0). Le reste de sa stratégie n'agit pas : tout contact rejette le run. | Comportement historique de l'humanité (aucune colonisation hors de la Terre). |  |
| `humanity_observed` | D | python/generate_world/_make_humanity.py, python/p0_passive_update/_tech_growth.py | L'humanité n'est pas tirée au hasard : elle est au centre de la région (à sun_height_pc), et sa tech suit exactement la loi de croissance de initial_tech_level à humanity_present_tech, avec le rythme qui relie ces deux points en 10 000 ans. La discrétion des sondes se compare à sa tech actuelle, celle avec laquelle on cherche aujourd'hui. | Données d'observation (décision du 2026-11, phase 2, point 5). Solution exacte plutôt qu'un pas d'Euler : le rythme humain peut atteindre 5e-4 par an, bien trop rapide pour des pas de 1 000 ans. |  |
| `share_to_humanity_is_contact` | M | python/p3_apply_events/__init__.py | Un partage (ou partage implicite) reçu par l'humanité rejette le run (« contact_share ») sans modifier sa tech. | Recevoir de la technologie est un contact qu'on aurait remarqué. Auparavant, un partage modifiait silencieusement la tech et le rythme de l'humanité (la synergie pouvait même plafonner son rythme). | Phase 2, point 11 : avec une détection imparfaite, un partage pourrait passer inaperçu (et alors ne rien apporter). |
| `competition_by_biochem` | M | python/p0_passive_update/_detect.py, _advance_fronts.py | Deux civs sont concurrentes si et seulement si elles ont la même biochimie. | Compétition pour les mêmes mondes habitables. | Phase 2. |
| `tech_uncertainty_projection` | M | python/p0_passive_update/_detect.py, python/p1_from_strat_to_actions/_compute_attack_interest_score.py | Une civ voit la tech exacte de sa cible, mais retardée par la lumière. Son incertitude est le progrès que la cible a pu faire pendant ce trajet, au rythme de croissance vu en même temps : u = grow(T_vue, r_vue, cap, d/c) − T_vue. Une civ attaque si l'écart diminué de caution_k × u dépasse attack_gap_min. | « Explosion technologique » de la Forêt sombre (Liu 2008) : on ne sait pas de combien la cible a progressé depuis le départ de la lumière ; une cible lointaine ou en forte croissance paraît plus risquée. Déterministe et sans paramètre nouveau (décision du 2026-11, phase 2, point 1). On suppose le rythme de la cible observable, à partir de l'historique vu.       Alternatives écartées : retirer caution_k (perd la nuance de la Forêt sombre) ; bruit aléatoire sur l'estimation (2 paramètres inconnus, casse le fast-forward). | Phase 5 : avec un rythme de progrès entre 3e-11 et 3e-10 par an, u ≈ 1e-6, donc caution_k est sans effet en pratique, sauf envers l'humanité, dont le rythme déduit va jusqu'à 5e-4 par an (point 5) ; à revoir avec l'intervalle du rythme de progrès. |
| `deterministic_detection` | M | python/p0_passive_update/_detect.py | Détection entre civs certaine dès qu'une sphère (signal ou sondes) atteint l'autre. | Simplification. | Phase 2, points 9 et 11. |
| `attack_decision` | M | python/p1_from_strat_to_actions/_compute_attack_interest_score.py | Une civ attaque si l'écart de tech est dans [attack_gap_min, attack_gap_max] et la confiance sous son seuil ; elle attaque d'abord les plus grands écarts. | Formalise les stratégies nommées (Forêt sombre, etc.). | Phase 2, point 7 : écart pour décider mais rapport pour les dégâts. |
| `min_one_attack` | M | python/p1_from_strat_to_actions/_compute_max_number_of_attack.py | Toute civ peut mener au moins une guerre à la fois. | Une civ jeune peut quand même agir. |  |
| `war_as_rate` | M | python/p3_apply_events/_attack_damage.py, python/p2_from_actions_to_events.py, python/p3_apply_events/_rates.py | La guerre est un processus continu : tant que la décision d'attaquer tient, chaque pas envoie un événement d'attaque qui applique un pas dt des dégâts et du coût (1 - (1 - taux)^(dt/période)). | Rend l'effet annuel indépendant de dt, comme pour les partages ; garde le fast-forward applicable (décision du 2026-11, phase 2, point 12). Alternative écartée : frappes discrètes à cadence fixe, périodiques sur plusieurs pas, donc incompatibles avec le fast-forward. |  |
| `reputation_witness` | M | python/p0_passive_update/_detect.py | Un témoin perd confiance envers l'attaquant tant qu'il voit la victime subir une guerre en cours (frappée pendant le pas observé) ; la baisse s'arrête avec la guerre. | Décision du 2026-11 (phase 2, point 12). Auparavant, la marque du dernier attaquant restait à vie et la confiance baissait à chaque pas, indéfiniment. |  |
| `attack_damage_law` | M | python/p3_apply_events/_attack_damage.py | Dégâts = min(1, damage_coef × rapport de tech), appliqués à la tech, la population et le rayon colonisé ; mort seulement si dégâts = 1. Déterministe. | Le plus fort fait plus de dégâts. | Phase 2, point 7 : forme, aléa, coût de la défense. |
| `attack_attribution` | M | python/p3_apply_events/__init__.py, python/p0_passive_update/_detect.py | La victime n'identifie l'attaquant que si elle le connaissait déjà ; les témoins ne voient que le dernier attaquant de la victime. | Simplification. | Phase 2, point 7 : probabilité d'attribution. |
| `share_laws` | M | python/p3_apply_events/_share_tech_update.py, _share_trust_update.py, _rates.py | Partage : le receveur comble une fraction de l'écart, le donneur gagne un peu (décroissance exponentielle avec l'écart), synergie multiplicative du rythme de progrès, confiance qui tend vers 1. | Formes simples, coefficients explorés. |  |
| `tech_cost_of_expansion` | M | python/p0_passive_update/_tech_growth.py | Le progrès techno est multiplié par (1 - colonization_aggressiveness). | S'étendre coûte du progrès maintenant mais apporte de la population, donc du progrès plus tard (décision du 2026-11). |  |
| `front_blocking` | M | python/p0_passive_update/_advance_fronts.py | Deux concurrents dont les sphères se touchent restent en contact. Chacun cache à l'autre la calotte de ciel que couvre sa sphère, de demi-angle asin(R_autre / d), soit une part (1 - cos) / 2. Le territoire ne croît que dans la part libre du ciel, free_fraction = produit des (1 - calotte), calottes supposées indépendantes. Le rayon R reste la portée du front dans les directions libres. Une civ née dans la sphère d'un concurrent jamais rencontré (une enclave) ne croît pas et ne le bloque pas. Le Soleil caché par un concurrent en contact n'est pas tenu. | Un concurrent ne bloque que les directions qu'il occupe : une seule variable par civ, sans géométrie détaillée. Auparavant, le premier contact arrêtait le front dans toutes les directions (décision du 2026-11, phase 2, point 8). | Phase 7 : comparer avec un calcul exact des recouvrements entre calottes. |
| `fixed_strategies` | M | python/generate_world/_sample_strategy.py | Une civ garde sa stratégie toute sa vie (pas d'apprentissage ni d'imitation). | Hypothèse déclarée. | Phase 2, point 10. |
| `archetype_definitions` | M | python/config.py (ARCHETYPES), data_model/strategies/strategy_presets.json | Valeurs des traits de chaque archétype. | Traduction des stratégies nommées de la littérature ; strategy_noise explore autour. |  |
| `artefact_single_draw` | M | python/p0_passive_update/_check_silence.py | Un seul tirage de découverte par civ, à la première arrivée de ses sondes pendant la fenêtre, avec la tech de la civ à ce moment. | Simplification. | Phase 2, point 11. |
| `colonized_criterion` | M | python/p0_passive_update/_check_silence.py | Rejet si un territoire couvre le Soleil à un moment de la fenêtre d'artefacts : le Soleil est à portée du front, hors de l'ombre d'un concurrent en contact. | « Fait A » de Hart 1975 : le Système solaire n'est pas occupé. |  |
