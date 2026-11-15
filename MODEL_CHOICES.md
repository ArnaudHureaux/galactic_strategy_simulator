# Choix de modèle

Livrable de la phase 2 de la [roadmap](ROADMAP.md). Un paragraphe par choix : décision, justification, paramètres touchés, alternatives écartées ou testées en robustesse (phase 7). Les numéros renvoient aux points de la phase 2.

## Décidés et implémentés

### Point 2 : date de départ

**Constat.** Le départ était une date absolue, `last_grb_date_years` = 10⁹ ans après le Big Bang. La simulation démarrait donc il y a 12,8 Ga, et non il y a 1 Ga comme prévu. Tous les runs antérieurs (pilote, LHS25) couvrent ainsi 12,8 Ga.

**Décision.** Le paramètre devient une durée, `start_lookback_years` : le départ a lieu à présent − `start_lookback_years`. Défaut : 1 Ga. Il est exploré entre 0,1 et 5,2 Ga, en échelle log.

**Justification.**
- Le départ représente le dernier épisode stérilisant, un sursaut gamma galactique (Annis 1999, arXiv:astro-ph/9901322). Ces sursauts resynchronisent l'apparition de l'intelligence, et l'intervalle actuel entre eux est d'environ 10⁸ ans. C'est la borne basse.
- D'après Piran & Jimenez 2014 (PRL 113, 231102), la vie telle que sur Terre n'a pas pu exister à z > 0,5. Cela correspond à 5,2 Ga avant le présent (H0 = 67,66, Ωm = 0,3111, Planck 2018). C'est la borne haute.
- L'échelle log est retenue parce que les deux bornes sont séparées de plus d'un ordre de grandeur.

**Conséquences.**
- Aucune civ n'existe avant le départ, donc aucune sonde ne peut être plus ancienne. Dès que le départ est plus récent que 4,5 Ga, la fenêtre des critères « colonized » et « artefact » couvre toute la simulation. C'est cohérent.
- Le temps simulé baisse fortement : au plus 5,2 Ga, contre 12,8 Ga auparavant. Le nombre de pas ne peut donc que diminuer.

**Reste ouvert.** La naissance simultanée des civs avec la même tech relève du point 3.

### Point 12 : guerre et réputation en taux, indépendants du pas

*Décidé le 2026-11-05.*

**Constat.** Trois règles s'appliquaient une fois par pas de temps, si bien que leur effet annuel dépendait de `dt` :
- chaque pas, une civ frappait ses cibles, avec des dégâts `min(1, damage_coef × ratio)` par frappe ;
- chaque frappe coûtait `attack_cost_tech` de tech à l'attaquant ;
- tout témoin perdait `reputation_trust_drop` de confiance à chaque pas où il voyait une victime. Comme la victime gardait à vie la marque de son dernier attaquant, cette baisse continuait indéfiniment, même pour une attaque vieille d'1 Ga.

**Décision : la guerre est un processus continu, sur le modèle des partages.**
- `share_period_years` devient `interaction_period_years` (1000 ans, une convention d'unité). C'est la période commune à tous les taux d'interaction.
- Une guerre détruit `d = min(1, damage_coef × ratio)` de la cible par période. Chaque pas de guerre applique 1 − (1 − d)^(dt/T). Le cas d = 1 (supériorité écrasante) reste une destruction immédiate, quel que soit dt.
- Le coût suit la même règle : `attack_cost_tech` est la fraction de tech dépensée par période, pour chaque guerre en cours.
- `attacks_per_tech_population` donne désormais le nombre de guerres menées en même temps, et non plus un nombre de frappes par pas.
- Réputation : un témoin perd `reputation_trust_drop` de confiance par période, mais seulement s'il voit la victime subir une guerre en cours. Concrètement, il faut que la victime ait été frappée pendant le pas qu'il observe, ce que permet le nouveau champ `attacked_at`. La baisse s'arrête avec la guerre.

**Alternative écartée.** Des frappes discrètes à cadence fixe seraient plus fidèles à l'idée de frappe. Mais le régime deviendrait périodique sur plusieurs pas, le fast-forward ne pourrait plus le sauter, et les timeouts exploseraient.

**Vérification.**
- `tests/test_rates.py` vérifie que n pas de T/n ans ont le même effet qu'un pas de T ans (dégâts, coût, réputation, synergie).
- La parité Python/Rust est contrôlée.
- La convergence globale en dt reste à faire en phase 3.

### Point 1 : information imparfaite (« explosion technologique »)

*Décidé le 2026-11-05.*

**Constat.** Une civ connaissait exactement la tech de sa cible, telle qu'elle était au départ de la lumière. `tech_level_uncertainty` valait toujours 0, donc le trait `caution_k` n'avait aucun effet.

**Décision.** L'incertitude est le progrès que la cible a pu faire pendant le trajet de la lumière :

u = grow(T_vue, r_vue, cap, d/c) − T_vue

où `grow` est la solution exacte de la loi de croissance techno, et `r_vue` le rythme de la cible vu en même temps que sa tech. Une civ attaque si l'écart diminué de `caution_k × u` dépasse `attack_gap_min`. On peut lire `caution_k` ainsi :
- 0 : la civ ignore le retard de la lumière ;
- 1 : elle suppose que la cible a progressé au rythme vu ;
- au-delà : elle est de plus en plus prudente.

**Justification.** C'est l'argument d'« explosion technologique » de la Forêt sombre : on ne sait pas de combien la cible a progressé depuis. Une cible lointaine ou en forte croissance paraît donc plus risquée. Le modèle est déterministe et n'ajoute aucun paramètre. On suppose seulement que le rythme de la cible est observable, à partir de l'historique vu.

**Alternatives écartées.**
- Retirer `caution_k` : c'est parcimonieux, mais on perd la nuance de la Forêt sombre.
- Ajouter un bruit aléatoire sur la tech estimée : cela introduit deux paramètres inconnus (un σ par canal) et casse le fast-forward si le bruit est retiré à chaque observation.

**Fast-forward.** Pendant un saut, l'incertitude peut varier entre 0 et une borne. La marge de décision et la marge de classement des cibles retranchent donc `caution_k × borne`. La borne est le maximum exact de grow(x) − x sur l'intervalle des tech possibles (fonction concave dans le cas logistique, maximum en x* = cap·√q/(1+√q), avec q = e^(−rτ)).

**Constat quantitatif.** Avec l'intervalle actuel du rythme de progrès (3·10⁻¹¹ à 3·10⁻¹⁰ par an), u vaut environ 10⁻⁶. Les écarts de tech qui décident d'une attaque sont, eux, de l'ordre de 0,1 à 1. Une civ progresse en milliards d'années, alors que la lumière met au plus quelques milliers d'années à traverser la région : l'effet de `caution_k` est donc négligeable. Sur 80 runs du pilote, activer ou désactiver la prudence ne change aucune issue. Ce sera à confirmer au criblage de Morris, et à revoir avec l'intervalle du rythme de progrès (point 5 et phase 5).

### Point 5 : position et tech de l'humanité

*Décidé le 2026-11-05.*

**Constat.** L'humanité était tirée au hasard dans la région, comme une civ quelconque. Sa tech partait de 0,1 et croissait pendant 10 000 ans au rythme d'une civ ordinaire, donc ne bougeait pratiquement pas. Or sa tech sert de référence pour la discrétion des sondes, et servira d'ancre « niveau humain » aux lois tech → effet (point 4).

**Décision : l'humanité est observée, pas tirée.**
- **Position** : au centre de la région, à sun_height_pc = 20,8 pc au-dessus du plan médian (Bennett & Bovy 2019, Gaia DR2). La région représente le voisinage du Soleil, et toutes les observations (silence, couverture SETI selon la distance) sont centrées sur la Terre. Cela supprime aussi un effet de bord artificiel.
- **Trajectoire de tech** : l'humanité naît il y a 10 000 ans (Néolithique) au niveau de naissance commun initial_tech_level = T₀. Elle atteint aujourd'hui T_h = T₀ · (plafond / T₀)^f, où f = humanity_tech_fraction est la fraction du chemin parcouru, en ordres de grandeur. Son rythme n'est pas tiré : on le déduit pour relier ces deux points sur la loi de croissance (logistique ou exponentielle). Sa tech suit la solution exacte de cette loi, pas un pas d'Euler, car le rythme humain peut atteindre 5·10⁻⁴ par an.
- **Pas de colonisation** : colonization_aggressiveness = 0 pour l'humanité (aucun monde colonisé hors de la Terre).
- Le rythme des autres civs reste tiré dans la loi explorée (`natural_tech_progress_mean`, `natural_tech_progress_spread`, `tech_growth_model`, `tech_population_exponent`), sans contrainte liée au rythme humain.

**Intervalle de f : [10⁻⁶ ; 0,95], en échelle log, déclaré inconnu.** La question « sommes-nous loin du plafond technologique ? » est réellement ouverte. Au rythme humain déduit, le plafond est à environ 10⁴ / f ans :

| f | rythme humain | plafond atteint à notre rythme dans |
|---|---|---|
| 10⁻⁶ | 3,5·10⁻¹⁰ /an | ≈ 2·10¹⁰ ans |
| 10⁻⁴ | 3,5·10⁻⁸ /an | ≈ 2·10⁸ ans |
| 0,01 | 3,5·10⁻⁶ /an | ≈ 2·10⁶ ans |
| 0,5 | 1,9·10⁻⁴ /an | ≈ 3·10⁴ ans |
| 0,95 | 5·10⁻⁴ /an | ≈ 6·10³ ans |

(Valeurs pour T₀ = 0,1 et un plafond à 3.) Exprimer T_h comme une fraction évite une contrainte d'ordre avec T₀ dans l'hypercube latin.

**Conséquences directes.**
- **Discrétion des sondes** : elle se compare à la tech **actuelle** de l'humanité (T_h), celle avec laquelle on cherche aujourd'hui. Avant, c'était sa tech au moment du tirage, souvent avant sa naissance, donc T₀.
- **Partage reçu par l'humanité** : il rejette le run (contact_share), car recevoir de la technologie est un contact qu'on aurait remarqué. Avant, un partage modifiait silencieusement sa tech, et la synergie pouvait plafonner son rythme. Avec la détection imparfaite du point 11, un partage pourra passer inaperçu, et alors ne rien apporter.
- **Prudence (caution_k)** : le rythme humain est vu par les autres civs. Quand f est grand, l'humanité paraît en « explosion technologique », et caution_k agit envers elle.

**Alternatives écartées.**
- Toutes les civs naissent au niveau humain actuel : cela ignore le passage du Néolithique à la radio.
- Contraindre le rythme des autres civs à inclure le rythme humain (principe de médiocrité) : ce rythme reste un paramètre exploré comme un autre.

### Point 8 : fronts de colonisation bloqués par direction

*Décidé le 2026-11-14.*

**Constat.** Chaque civ n'avait qu'un rayon d'expansion. Au premier contact avec un concurrent (même biochimie), les deux fronts s'arrêtaient dans toutes les directions, même à l'opposé du concurrent.

**Décision : suivre la part libre du ciel, une variable par civ.**
- Deux concurrents dont les sphères se touchent restent **en contact**. Vu du centre de A, B (à la distance d, de rayon R_B) cache une calotte de demi-angle θ = asin(R_B / d), soit une part du ciel f_B = (1 − cos θ) / 2. Elle grandit quand B s'étend, et rétrécit s'il est attaqué.
- Les calottes peuvent se chevaucher. Au lieu de calculer leurs intersections, on les suppose indépendantes : **free_fraction** φ = Π (1 − f_i). C'est l'approximation classique des obstacles placés au hasard, et φ reste dans [0 ; 1].
- Le rayon R est la portée du front dans les directions libres. Il avance au rythme habituel, et le territoire ne croît que dans la part libre : dN = densité × φ × 4πR² dR. Une attaque réduit le territoire de façon homothétique : R × (1 − dégâts), et N − 1 × (1 − dégâts)³.
- **Enclave** : une civ née dans la sphère d'un concurrent qu'elle n'a jamais rencontré ne peut pas croître, et ne bloque pas l'autre. C'est la règle d'avant.
- **Critère « colonized »** : le Soleil est tenu s'il est à portée du front et hors de l'ombre (le cône de demi-angle θ) d'un concurrent en contact.
- Fast-forward : un saut s'arrête avant que deux concurrents ne se touchent, et le budget de rayon tient compte de φ.

**Conséquence.** Les fronts ne se figent plus au premier contact. Sur le scénario de test du fast-forward (fronts rapides, 8 seeds), les runs sont rejetés plus tôt qu'avant ; la cause (Soleil atteint ou contact) reste à mesurer au pilote.

**Alternatives écartées.**
- Calcul exact des recouvrements : il demande une géométrie détaillée pour un gain faible. Il est gardé pour comparaison en phase 7.
- Tessellation (Voronoï) du voisinage : trop lourde pour un gain d'interprétation faible.

### Point 7 : attaque

*Décidé le 2026-11-14.*

**Attribution.** Avant, la victime identifiait toujours l'attaquant, et les témoins aussi. Désormais, elle l'identifie avec la probabilité p = exp(−k × max(0, T_attaquant − T_victime)), où k = `attack_stealth_per_tech` est exploré dans [0 ; 5] (inconnu). C'est la même forme que la discrétion des sondes.
- Le tirage a lieu **une fois par guerre**, à la première attaque d'un couple, sur un flux aléatoire dédié. Ainsi le résultat ne dépend pas de dt, et les autres tirages ne changent pas. Avec k = 0 (la valeur par défaut), rien n'est tiré.
- Une attaque non attribuée fait les mêmes dégâts, mais la victime ne baisse pas sa confiance et les témoins ne pénalisent pas l'attaquant.
- Une attaque contre l'humanité rejette le run, attribuée ou non : une attaque se remarque.
- **Résultat attendu, à mesurer et non à coder** : dans les mondes où k est grand, les stratégies agressives subissent moins de représailles. Elles devraient donc survivre plus souvent.

**Dégâts : déterministes**, pour ne pas ajouter d'aléa inconnu et garder le fast-forward simple.

**Écart plutôt que rapport.** La fenêtre de décision était un écart de tech, alors que les dégâts dépendaient d'un rapport de tech. La tech est une échelle logarithmique de la puissance (point 4) : un écart de tech est donc un rapport de puissance. Les dégâts par période deviennent min(1, `damage_coef` × exp(`damage_gap_scale` × écart)). `damage_coef` est la part détruite à tech égale, et `damage_gap_scale` (exploré dans [0,1 ; 10], échelle log) mesure combien chaque niveau d'avance multiplie les dégâts. Il faudra le recaler sur le facteur par niveau de tech quand les ancres du point 11 seront en place.

### Point 3 : naissances étalées

*Décidé le 2026-11-14.*

**Constat.** Toutes les civs initiales naissaient au départ, avec la même tech. Le sursaut gamma justifie de resynchroniser l'apparition de la vie (Annis 1999), mais pas une naissance simultanée de l'intelligence.

**Décision.** Chaque civ initiale naît à départ + U(0, f × start_lookback_years), au niveau initial_tech_level, avec f = `birth_spread_fraction` exploré dans [0 ; 1] (inconnu). La loi est uniforme faute d'information. Exprimer l'étalement en fraction de la durée simulée évite une contrainte d'ordre avec start_lookback_years dans l'hypercube latin. Avec f = 0 (la valeur par défaut), on retrouve la cohorte synchrone. Les naissances qui continuent ensuite (civ_birth_rate) ne changent pas.

Un saut du fast-forward s'arrête avant chaque naissance à venir.

### Points 6, 9 et 10 : hypothèses gardées

*Décidé le 2026-11-14.*

- **6. Taille de la région** : on garde le modèle abstrait, sans catalogue stellaire. Avec l'humanité au centre, le bord ne compte que si des civs extérieures auraient pu atteindre la Terre. À vérifier en phase 3, en comparant 1 et 2 kpc.
- **9. Détection entre civs** : elle reste certaine dès qu'une sphère (signal ou sondes) atteint l'autre. Une sonde sur place voit une civilisation même avec une technologie modeste (Voyager 2). Seule l'observation humaine devient probabiliste (point 11).
- **10. Stratégies figées** : c'est une hypothèse déclarée en V1. La sélection existe déjà, puisque les stratégies qui meurent plus deviennent plus rares parmi les survivantes. Une sortie la mesure : le mélange de stratégies des survivantes au présent, comparé au mélange initial. Par run : `attack_threshold_born_mean` et `attack_threshold_alive_mean` (seuil d'attaque moyen des civs nées et des survivantes), leur écart `strategy_selection` (> 0 : les stratégies agressives ont été sélectionnées), et `survival_<archétype>` (part des civs de chaque archétype encore en vie). L'apprentissage (une civ change de stratégie après ce qu'elle observe) viendra en extension en phase 7, si cette sortie montre que la sélection pèse sur les résultats.

## Décidés, à implémenter

### Point 11 : observation SETI réaliste (point 4 : la tech reste abstraite)

*Décidé le 2026-11-05.*

**La tech reste une échelle abstraite.** Face à une incertitude totale, une échelle arbitraire est assumée. L'indice de Kardashev est seulement un **indicateur de sortie**, calculé à partir de la puissance donnée par nos formules : K = (log₁₀ P − 6) / 10 (interpolation de Sagan). Il sert à comparer avec la littérature, pas à paramétrer le modèle.

**Ancrage par les conséquences.** L'échelle est arbitraire, mais ce qu'elle produit doit être borné. Chaque loi « par niveau de tech » (puissance émise, vitesse des sondes, vitesse des fronts, durée de vie des sondes) est calée par deux ancres :
- la valeur au niveau de l'humanité, qui est observée (Voyager ≈ 5·10⁻⁵ c ; EIRP de l'ordre de 10¹³ W pour le radar d'Arecibo) ;
- la valeur au plafond techno, explorée sur un intervalle tiré de la littérature (par exemple 0,01 à 0,5 c pour les sondes, d'après Armstrong & Sandberg 2013).

Cela impose de **placer l'humanité sur l'échelle** : c'est fait au point 5 (T_h = `humanity_present_tech`).

**Émission.** EIRP(tech) en watts, multipliée par `passive_leakage_factor` pour une civ qui n'émet pas volontairement. La loi est calée par les deux ancres ci-dessus.

**Détection par l'humanité (SETI).** Pour chaque civ non humaine, pendant la fenêtre d'écoute :
1. elle est **détectable** si EIRP ≥ 4π d² F_min, avec d la distance d'un bord de sphère à l'autre et F_min la sensibilité des relevés, calée sur Breakthrough Listen (Enriquez et al. 2017 ; Price et al. 2020 ; Wlodarczyk-Sroka et al. 2020) ;
2. si elle est détectable, elle est **détectée** avec probabilité 1 − (1 − c(d) · p_on)^n, où :
   - c(d) est la fraction des étoiles réellement observées à la distance d, d'après les catalogues des relevés ;
   - p_on est la probabilité d'émettre dans la bonne bande, au bon moment et vers nous (paramètre inconnu, exploré) ;
   - n est le nombre de systèmes de la civ à portée.

   Le tirage se fait une fois par civ, comme pour les artefacts.

**Fenêtres.** Deux paramètres distincts : l'humanité est **détectable** depuis les années 1930 (fuites radio) et **écoute** depuis 1960 (Project Ozma, Drake 1961).

**Artefacts.** `artefact_detection_probability` est bornée par la part du Système solaire réellement fouillée (Haqq-Misra & Kopparapu 2012 ; Benford 2019).

**Justification.** Le modèle actuel suppose un SETI exhaustif : tout signal couvrant la Terre est détecté. Il mélange aussi puissance et sensibilité dans un seul rayon. Or Wright, Kanodia & Lubar 2018 estiment à environ 10⁻¹⁷ la fraction de l'espace de recherche réellement fouillée. Le rayon actuel est un cas particulier du nouveau modèle : rayon = √(EIRP / 4π F_min).

**Paramètres touchés.**
- Remplacés : `emit_radius_per_tech`, `max_broadcast_radius` et `signal_window_years`.
- Nouveaux : la loi EIRP(tech) et ses ancres, F_min (sourcé), c(d) (sourcé), p_on (exploré), et les deux fenêtres (définitions).
- À revoir : les lois des sondes et des fronts, à recaler sur les ancres (niveau humain T_h du point 5, et plafond).

**Sous-questions ouvertes.**
- Forme de la conversion tech → effet entre les deux ancres. Il ne s'agit pas de la loi de progrès techno dans le temps, qui est déjà un paramètre ; il s'agit de la puissance ou de la vitesse d'une civ à un niveau intermédiaire. Par défaut, chaque niveau de tech multiplie l'effet par un facteur constant, et les deux ancres fixent alors la courbe. Une forme alternative pourra être explorée comme un paramètre ordinaire si le criblage de Morris montre qu'elle compte.
- Faut-il aussi rendre imparfaite la détection entre civs non humaines ? Une tech plus élevée donnerait une meilleure sensibilité.

**Robustesse (phase 7).** Autres valeurs de F_min et de c(d) ; ancienne détection déterministe en comparaison.

**Étape 1, faite le 2026-11-15 : ancres, EIRP en watts et vitesse des sondes.**
- Loi ancrée : effet(T) = E_h × (E_cap / E_h)^((T − T_h) / (T_cap − T_h)), où T_h = `humanity_present_tech`. Au-delà du plafond, l'effet reste à E_cap.
- **Émission** : EIRP humaine `eirp_human_w` = 2·10¹³ W (radar d'Arecibo, Sheikh et al. 2025). EIRP au plafond `eirp_cap_w` explorée dans [10¹⁶ ; 10²⁶] W (types I à II de Kardashev dans l'interpolation de Sagan). Les fuites valent `passive_leakage_factor` × EIRP, soit 2·10⁻⁴ pour l'humanité (LTE 4 GW / Arecibo 20 TW), exploré dans [10⁻⁵ ; 10⁻²].
- **Portée d'un signal** : d = √(EIRP / 4π F_min), avec `seti_flux_threshold_w_m2` = 3,3·10⁻²⁵ W/m² (Breakthrough Listen : 10¹³ W à 50 pc, Enriquez et al. 2017). Le radar d'Arecibo porte ainsi à 71 pc, et nos fuites LTE à environ 1 pc. Ce seuil sert à toutes les civs (point 9). `max_broadcast_radius` disparaît : la recherche de voisins est bornée par la plus grande portée jamais atteinte.
- **Sondes** : Voyager 1 (5,67·10⁻⁵ c) au niveau humain, `probe_speed_cap_c` exploré dans [0,01 ; 0,99] c au plafond (Bond 1978, Lubin 2016, Armstrong & Sandberg 2013).
- Supprimés : `emit_radius_per_tech`, `max_broadcast_radius`, `probe_speed_per_tech`.

**Conséquence.** Une civ qui émet volontairement, au niveau humain, porte à 71 pc, contre environ 1 pc avec l'ancienne loi. Les contacts entre civs deviennent bien plus fréquents, et les simulations plus denses, donc plus lentes en Python.

**Question ouverte.** Une civ qui « émet volontairement » le fait-elle en continu et dans toutes les directions, à l'EIRP d'un radar dirigé ? Pour une émission isotrope, 20 TW d'EIRP correspondent à 20 TW réels, soit à peu près la consommation énergétique actuelle de l'humanité. C'est une surestimation probable. Le facteur p_on de l'étape 2 en tiendra compte pour la détection par l'humanité, mais la détection entre civs reste à discuter.

## À décider

Aucun point de la phase 2 (le point 11 est décidé, reste à implémenter).
