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

## Décidés, à implémenter

### Point 11 : observation SETI réaliste (point 4 : la tech reste abstraite)

*Décidé le 2026-11-05.*

**La tech reste une échelle abstraite.** Face à une incertitude totale, une échelle arbitraire est assumée. L'indice de Kardashev est seulement un **indicateur de sortie**, calculé à partir de la puissance donnée par nos formules : K = (log₁₀ P − 6) / 10 (interpolation de Sagan). Il sert à comparer avec la littérature, pas à paramétrer le modèle.

**Ancrage par les conséquences.** L'échelle est arbitraire, mais ce qu'elle produit doit être borné. Chaque loi « par niveau de tech » (puissance émise, vitesse des sondes, vitesse des fronts, durée de vie des sondes) est calée par deux ancres :
- la valeur au niveau de l'humanité, qui est observée (Voyager ≈ 5·10⁻⁵ c ; EIRP de l'ordre de 10¹³ W pour le radar d'Arecibo) ;
- la valeur au plafond techno, explorée sur un intervalle tiré de la littérature (par exemple 0,01 à 0,5 c pour les sondes, d'après Armstrong & Sandberg 2013).

Cela impose de **placer l'humanité sur l'échelle**. Aujourd'hui, elle part de 0,1 et croît pendant 10 000 ans sans justification. Or son niveau intervient dans la discrétion des sondes, et interviendra dans la sensibilité SETI.

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
- À revoir : le niveau de tech de l'humanité, et les lois des sondes et des fronts, à recaler sur les ancres.

**Sous-questions ouvertes.**
- Forme de la conversion tech → effet entre les deux ancres. Il ne s'agit pas de la loi de progrès techno dans le temps, qui est déjà un paramètre ; il s'agit de la puissance ou de la vitesse d'une civ à un niveau intermédiaire. Par défaut, chaque niveau de tech multiplie l'effet par un facteur constant, et les deux ancres fixent alors la courbe. Une forme alternative pourra être explorée comme un paramètre ordinaire si le criblage de Morris montre qu'elle compte.
- Niveau de tech de l'humanité sur l'échelle.
- Faut-il aussi rendre imparfaite la détection entre civs non humaines ? Une tech plus élevée donnerait une meilleure sensibilité.

**Robustesse (phase 7).** Autres valeurs de F_min et de c(d) ; ancienne détection déterministe en comparaison.

## À décider

Points 3 et 5 à 10 de la phase 2.
