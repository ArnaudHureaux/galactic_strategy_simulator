# Roadmap vers la publication

Remplace `_old/ROADMAP_LONG_TERME.md` et `_old/ROADMAP_COURT_TERME.md`. État de départ : moteur Python de référence + moteur Rust bit-identique, colonisation, archétypes, sondes discrètes, LHS 25 dimensions (500 points, 1 graine par point).

## Règle d'or : aucun paramètre orphelin

Chaque élément du modèle (les 80 paramètres de `Config`, les constantes codées en dur, les choix de structure) doit avoir **un statut et une justification écrite** :

| Statut | Sens | Preuve attendue |
|---|---|---|
| **E** exploré | varie dans l'étude | intervalle (et échelle log ou linéaire) justifié par la littérature, ou déclaré « inconnu, intervalle large » |
| **S** sourcé | fixé à une valeur de la littérature | citation |
| **N** numérique | paramètre de calcul | test de convergence montrant que les résultats n'en dépendent pas |
| **D** définition | convention ou donnée d'observation (âge de l'Univers, fenêtre SETI…) | citation |
| **I** non influent | fixé parce que le criblage (phase 5) montre qu'il ne pèse pas sur son intervalle plausible | indices de Morris |
| **M** choix de modèle | forme d'une loi, règle de comportement | justification + alternatives testées en robustesse (phase 7) |

Un paramètre sans statut bloque la publication. Ce registre est la colonne vertébrale du papier.

---

## Phase 0 : Cadrage scientifique (à faire en premier)

Sans question précise, impossible de savoir quels paramètres comptent.

- [x] Formuler les questions et le type de conclusion visé (voir [docs/QUESTIONS.md](docs/QUESTIONS.md)) :
  - Q1 : délimiter l'espace des paramètres compatible avec le Grand Silence, en quatre catégories selon la fréquence de silence entre graines ;
  - Q2 : dans cet espace, relier les paramètres au succès écologique des archétypes ;
  - aucune probabilité sur les paramètres (incertitude profonde) ;
  - la stratégie de l'humanité, qui demande une projection dans le futur, est reportée au papier 2.
- [x] Définir **l'observation** de façon sourcée : chaque critère de rejet est rattaché à ses sources. Quatre écarts entre le modèle et les observations réelles sont reportés en phase 2 (point 11).
- [x] Positionnement bibliographique : [biblio/phase0_research_report.md](biblio/phase0_research_report.md), avec la liste des références non vérifiées à ne pas citer. L'apport est rédigé dans `docs/QUESTIONS.md`.
- [x] Revue cible : choix reporté à la phase 8, la rigueur ne dépend pas de la revue. Liste courte : IJA, Acta Astronautica, JASSS. Le protocole ODD est adopté, même s'il n'est obligatoire nulle part.

**Livrable** : [docs/QUESTIONS.md](docs/QUESTIONS.md) (questions, définitions, observation, positionnement, revue). ✅

## Phase 1 : Audit exhaustif et registre des hypothèses ✅

- [x] Registre lisible par machine : [data_model/parameters.json](data_model/parameters.json). Chaque paramètre de `Config` y a un statut, une unité, une justification, un intervalle s'il est exploré (avec sa base : littérature, inconnu, provisoire) et ses points ouverts. Il contient aussi 19 règles codées en dur (formes de lois, conventions).
- [x] Tests ([test_registry.py](python/tests/test_registry.py)). La suite échoue dans quatre cas :
  - un champ de `Config` manque au registre ;
  - un intervalle est invalide ;
  - une spec fait varier un paramètre ni exploré ni numérique ;
  - `HYPOTHESES.md` n'est pas à jour.

  Les specs se génèrent depuis le registre (`python registry.py spec`).
- [x] [HYPOTHESES.md](HYPOTHESES.md) est généré par `python registry.py doc`.
- [x] Constantes cachées sorties dans `Config`, en Python et en Rust, bit-identiques (160 runs comparés avec des valeurs non défaut) :
  - `natural_tech_progress_spread` et `natural_population_growth_spread`, autrefois U(0,5 ; 1,5) en dur ;
  - `attacks_per_tech_population`, autrefois `max(1, int(tech × pop))` en dur.

  Les autres éléments codés en dur sont des formes de lois ou des règles : ils sont inscrits comme règles **M** du registre et rattachés à leur point de la phase 2.
- [x] Statut des 83 paramètres : 44 E, 1 S, 7 N, 17 D, 14 M. Les intervalles marqués « provisoire » sont à justifier en phase 5.

**Livrable** : registre complet, tests verts, aucun champ sans statut. ✅

## Phase 2 : Corrections et choix de modèle en suspens

Chaque point se décide avec toi, puis est implémenté en Python, reporté en Rust, avec tests de parité.

1. **Information imparfaite.** ✅ Fait : l'incertitude est le progrès que la cible a pu faire pendant le trajet de la lumière (« explosion technologique »), et `caution_k` la pondère. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md). Avec l'intervalle actuel du rythme de progrès, l'effet est négligeable entre civs non humaines (u ≈ 10⁻⁶), mais pas envers l'humanité depuis le point 5 : à revoir en phase 5.
2. **Date de départ.** ✅ Fait : le départ était une date absolue (1 Ga après le Big Bang), donc la simulation démarrait il y a 12,8 Ga au lieu d'il y a 1 Ga. Le paramètre devient `start_lookback_years` (défaut 1 Ga), exploré entre 0,1 Ga (Annis 1999) et 5,2 Ga (Piran & Jimenez 2014), en échelle log. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md).
3. **Cohorte synchrone.** ✅ Fait : les civs initiales naissent à départ + U(0, `birth_spread_fraction` × durée simulée), `birth_spread_fraction` ∈ [0 ; 1] exploré. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md).
4. **Unité de tech sans ancrage physique.** ✅ Décidé : la tech reste abstraite, ses conséquences sont calées par deux ancres (niveau humain observé, plafond tiré de la littérature) ; Kardashev en indicateur de sortie (voir [MODEL_CHOICES.md](MODEL_CHOICES.md)). Ainsi les intervalles explorés peuvent être sourcés.
5. **Position et tech de l'humanité.** ✅ Fait : l'humanité est au centre de la région (z = 20,8 pc, Gaia DR2) et suit sa trajectoire observée, du niveau de naissance commun il y a 10 000 ans à T_h aujourd'hui. T_h est exploré en fraction du chemin vers le plafond, en ordres de grandeur (`humanity_tech_fraction` ∈ [10⁻⁶ ; 0,95]), et son rythme s'en déduit. Un partage reçu par l'humanité est un contact. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md).
6. **Taille de la région.** Décidé : on garde le modèle abstrait, sans catalogue stellaire ; effets de bord à vérifier en phase 3 (comparer 1 et 2 kpc). Une région de 1 kpc pose la question des effets de bord, à vérifier en phase 3. Faut-il un substrat stellaire réel (Gaia, HYG) ou le modèle abstrait suffit-il, en le justifiant ?
7. **Attaque.** ✅ Fait : attribution tirée une fois par guerre, avec la probabilité exp(−`attack_stealth_per_tech` × avance de l'attaquant) ; dégâts déterministes, fonction de l'écart de tech (`damage_gap_scale`), comme la fenêtre de décision. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md).
8. **Colonisation V1.** ✅ Fait : un concurrent en contact ne bloque plus que la calotte de ciel que couvre sa sphère ; le territoire croît dans la part libre (`free_fraction`, produit des calottes supposées indépendantes). Voir [MODEL_CHOICES.md](MODEL_CHOICES.md).
9. **Détection.** ✅ Décidé : on garde la détection certaine entre civs dès qu'une sphère (signal ou sondes) atteint l'autre. Une sonde sur place voit une civilisation même avec une technologie modeste (Voyager 2). Seule l'observation humaine devient probabiliste (point 11).
10. **Stratégies figées à vie.** ✅ Décidé : hypothèse déclarée en V1. La sélection (les stratégies agressives meurent plus ou moins) est déjà dans le modèle et se mesure par le mélange de stratégies des survivantes comparé au mélange initial (sortie `strategy_selection`). L'apprentissage viendra en extension (phase 7) si cette sortie montre que la sélection compte.
11. **Complétude des observations.** ✅ Fait en trois étapes : ancres, EIRP en watts et vitesse des sondes ; fuites et faisceaux, détection progressive, relevés humains c(d) et fenêtres d'émission et d'écoute ; artefacts bornés par la fouille réelle, fronts par sauts (Carroll-Nellenback et al. 2019), dégâts sur la loi d'énergie ; durées de fonctionnement et de persistance des sondes, colonisation seulement si la portée couvre un saut. ✅ Décidé : EIRP, seuil de sensibilité et couverture, tirage par civ (voir [MODEL_CHOICES.md](MODEL_CHOICES.md)). Contexte : [docs/QUESTIONS.md](docs/QUESTIONS.md). Aujourd'hui, SETI est supposé exhaustif : tout signal couvrant la Terre est détecté. Il faut une couverture partielle et un seuil de puissance (EIRP) calés sur Breakthrough Listen. Il faut aussi deux fenêtres distinctes : depuis quand l'humanité est détectable (fuites radio dès les années 1930), et depuis quand elle écoute (1960). Enfin, la probabilité de trouver un artefact doit être bornée par ce qu'on a réellement fouillé du Système solaire.
12. **Règles appliquées « par pas ».** ✅ Fait : la guerre est un processus continu, comme les partages. Dégâts, coût et baisse de réputation sont des taux par `interaction_period_years`, et la baisse de réputation ne s'applique que pendant une guerre en cours. Voir [MODEL_CHOICES.md](MODEL_CHOICES.md). La convergence en dt reste à vérifier en phase 3.

**Livrable** : `MODEL_CHOICES.md`, un paragraphe par choix : décision, justification, alternatives écartées ou reportées en phase 7.

## Phase 3 : Vérification numérique (le code fait-il ce que dit le modèle ?)

- [ ] **Convergence** : en `dt` (1000, puis 100, puis 10 ans), `max_jump_years`, `jump_max_relative_change`, fast-forward activé ou non, `region_radius_pc` à densité constante (effets de bord), `max_civs`. On compare des **distributions** de résultats, pas un run isolé.
- [ ] **Cas analytiques** : croissance logistique d'une civ seule, date d'arrivée d'un front ou d'une sonde, comptages de Poisson des bulles, temps de colonisation de Hart.
- [ ] **Tests de propriétés** (Hypothesis) : causalité (rien de plus rapide que la lumière), bornes (tech ≤ plafond, population ≤ capacité), reproductibilité à graine égale.
- [ ] Garder la parité Python/Rust à chaque changement. Mettre en place une CI GitHub Actions (pytest, cargo test, parité).

**Livrable** : `docs/VERIFICATION.md` avec les figures de convergence. Les valeurs **N** du registre y renvoient.

## Phase 4 : Performance (prérequis des phases 5 à 7)

- [ ] Ramener les timeouts à environ 0 %. Aujourd'hui il y en a 23 % sur LHS25, surtout des galaxies denses et coopératives où les pas coûtent cher. Les timeouts sont des **données censurées corrélées aux paramètres** : les ignorer biaise les conclusions.
- [ ] Profiler les points de LHS25 qui expirent, et rendre le partage stable moins coûteux.
- [ ] Budget visé : environ 10⁵ runs pour Morris et Sobol avec réplicats. Estimer le temps de calcul et décider : machine locale, cloud ou cluster.

## Phase 5 : Intervalles sourcés et criblage de tous les paramètres

Ces intervalles délimitent ce qui est physiquement plausible. Ce ne sont pas des croyances : pas de probabilité sur les paramètres (voir [docs/QUESTIONS.md](docs/QUESTIONS.md)).

- [ ] **Intervalles** : pour chaque paramètre physique, bornes et échelle (log ou linéaire) tirées de la littérature :
  - η⊕ (Kepler) pour la densité de mondes habitables ;
  - Armstrong & Sandberg et Bjork pour la vitesse des sondes ;
  - Carroll-Nellenback pour les fronts ;
  - Sandberg-Drexler-Ord pour f_l, f_i et L ;
  - limites SETI pour les portées d'émission.

  Les paramètres stratégiques ou sociaux (dégâts, confiance, partage) sont **déclarés inconnus** et explorés sur des intervalles larges : les conclusions seront conditionnelles à eux, et le papier le dira explicitement.
- [ ] **Criblage de Morris** sur **tous** les paramètres non numériques et non définitionnels (environ 60, y compris les 55 actuellement figés et les constantes sorties en phase 1), avec plusieurs graines par point. Les non influents passent au statut **I**.

**Livrable** : intervalles dans le registre, figure de Morris (μ*, σ) sur la fréquence de silence f(θ) et sur chaque critère de rejet.

## Phase 6 : Cartographie de l'espace compatible et des stratégies gagnantes

- [ ] **Geler le plan d'analyse avant les gros runs** (pré-enregistrement interne) : questions, métriques, critères, tests. On évite ainsi de choisir l'analyse après avoir vu les résultats.
- [ ] **Q1** : f(θ) sur environ 20 graines par point, puis catégories (pas, peu, compatible, très compatible), avec les points proches d'un seuil marqués incertains. Découverte de scénarios (PRIM, arbres de classification) pour décrire chaque catégorie par des règles simples. Un émulateur de f(θ) est envisageable si le budget l'exige.
- [ ] **Sobol** (Saltelli) sur f(θ) avec les paramètres influents. Intervalles de confiance par bootstrap et convergence des indices en fonction de N.
- [ ] **Q2** : dans les régions compatibles, succès écologique par archétype (survie relative, part des mondes), découverte de scénarios sur l'archétype gagnant et sensibilité du succès de chaque archétype.

## Phase 7 : Robustesse structurelle

- [ ] Rejouer les conclusions principales avec chaque choix **M** remplacé par son alternative : modèles de croissance, formes d'autodestruction, lois de dégâts, modèle de détection, échelle des axes (log ou linéaire), seuils des catégories de compatibilité, nombre de graines, taille de la région.
- [ ] Toute conclusion qui ne survit pas est présentée comme conditionnelle.

## Phase 8 : Reproductibilité et rédaction

- [ ] Description du modèle au format **ODD** (Overview, Design concepts, Details), avec les équations : on part de `pseudocode/`.
- [ ] Une commande qui régénère toutes les figures du papier depuis les specs. Environnement figé (lockfile, conteneur). Code et données archivés sur Zenodo avec un DOI.
- [ ] Section limites honnête : ce qui n'est pas modélisé et pourquoi.
- [ ] Prépublication arXiv (astro-ph.EP ou physics.soc-ph), puis soumission.

---

## Ordre et dépendances

```
0 Cadrage ──► 1 Registre ──► 2 Choix de modèle ──► 3 Vérification ──┐
                                   4 Performance (en parallèle) ────┴─► 5 Intervalles + Morris ──► 6 Cartographie + Sobol ──► 7 Robustesse ──► 8 Papier
```

Les résultats de LHS25 sont **exploratoires** : ils guident les phases 2 et 4 mais n'iront pas dans le papier.
