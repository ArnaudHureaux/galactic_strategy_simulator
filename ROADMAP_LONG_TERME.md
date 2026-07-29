# Roadmap long terme — Simulateur de civilisations galactiques

Horizon : 6 à 18 mois. Découpé en phases. Chaque phase a un **livrable scientifique**, pas seulement technique. On ne passe à la suivante qu'une fois la précédente validée.

---

## Phase 0 — Fondations conceptuelles (2-4 semaines)

**But** : ne pas coder le mauvais modèle pendant 6 mois.

- Revue bibliographique structurée :
  - Hanson, *Burning the Cosmic Commons* (1998) — colonisation et frontière
  - Sandberg, Drexler, Ord, *Dissolving the Fermi Paradox* (2018) — incertitude sur Drake
  - Armstrong & Sandberg, *Eternity in Six Hours* (2013) — colonisation intergalactique
  - Forgan, *A Numerical Testbed for Hypotheses of Extraterrestrial Life and Intelligence* — simulations SETI
  - Liu Cixin, *The Dark Forest* — formalisation du dilemme (lecture critique)
  - Cirkovic, *The Great Silence* — taxonomie des solutions au paradoxe de Fermi
- Production d'un **registre d'hypothèses** (markdown versionné) listant chaque paramètre du modèle, sa source, sa distribution a priori, et la sensibilité présumée.
- Choix tranchés et documentés sur les questions ouvertes :
  - FTL : autorisé / interdit / coûteux ?
  - Modèle de progrès techno (logistique, paliers Kardashev, singularité possible)
  - Hétérogénéité des niches d'habitabilité
  - Modèle de mortalité endogène (Great Filter post-techno)

**Livrable** : `HYPOTHESES.md` + `MODEL_CHOICES.md` versionnés. Aucune ligne de simulation écrite.

---

## Phase 1 — Modèle jouet end-to-end (3-5 semaines)

**But** : valider l'architecture, pas la science.

- 10-50 étoiles, 2 stratégies seulement (silencieuse vs broadcasteuse), pas de techno évolutive, pas de colonisation.
- Event loop avec priority queue temporelle, respect strict de la causalité (vitesse lumière).
- Séparation stricte `world_state` (vérité) vs `agent_beliefs` (vue retardée par chaque civ).
- Couche d'observation : tout est loggé en Parquet, indexable a posteriori.
- Reproductibilité totale : seed + config hashée.

**Livrable** : on peut lancer 1000 runs Monte Carlo, sortir une distribution de "qui survit", et l'analyser dans un notebook séparé. Le modèle est volontairement faux ; ce qui compte c'est que la plomberie est saine.

---

## Phase 2 — Moteur physique réaliste (6-10 semaines)

**But** : remplacer les nombres arbitraires par de la physique sourcée.

- Substrat stellaire réel : intégration catalogues Gaia DR3 + HYG pour le voisinage solaire (rayon ~100 pc), génération procédurale calibrée (IMF, densité spatiale par bras galactique) au-delà.
- Modèle de propulsion : Tsiolkovski relativiste, contrainte énergétique, fonction du niveau techno.
- Modèle de détection : signal + bruit galactique, atténuation 1/r², seuils de détection paramétrés.
- Modèle de destruction : asymétrie attaque/défense explicite (énergie de liaison gravitationnelle, RKM, etc.).
- Modèle de colonisation : population min viable, temps, coût énergétique, terraformation.
- Types de mondes + enveloppes d'habitabilité par civ → non-compétition naturelle.

**Livrable** : un moteur dont chaque règle est justifiable par un papier ou une équation. Bench de calibration : reproduit Hart (extinction silencieuse) et Sandberg (dissolution) sous leurs hypothèses respectives.

---

## Phase 3 — Stratégies civilisationnelles plurielles (4-6 semaines)

**But** : le cœur du projet — faire émerger l'optimum.

- API plugin pour les stratégies : `state → action`, fonction pure, testable.
- Bestiaire initial : Dark Forest, Berserker, Broadcasteur, Colonisateur agressif, Coopératif (partage techno), Hibernation, Mimétique.
- Partage de technologie modélisé comme transfert d'information sous contrainte de confiance.
- Évolution stratégique possible (une civ peut changer de policy selon son expérience).

**Livrable** : tournois multi-stratégies, matrices de dominance, identification des stratégies robustes vs fragiles selon le contexte.

---

## Phase 4 — Analyse de sensibilité et inférence (6-8 semaines)

**But** : transformer la simu en outil scientifique.

- Sobol indices sur tous les hyperparamètres → identifier ceux qui drivent vraiment les résultats.
- Latin Hypercube Sampling pour l'exploration de l'espace des paramètres.
- Inférence bayésienne : sachant ce qu'on observe (silence cosmique), quelle distribution a posteriori sur les paramètres ?
- Production de figures publiables : sous quelles conditions chaque stratégie domine.

**Livrable** : papier blanc / rapport reproductible répondant à *"sous quelles hypothèses la stratégie X est-elle optimale pour la survie de l'humanité ?"*

---

## Phase 5 — Performance et scaling (4-6 semaines, en parallèle si besoin)

**But** : ne pas être bloqué par le compute.

- Profiling, optimisation des hot loops (Numba/Rust pour les calculs de voisinage, priority queue).
- Parallélisation embarrassingly parallel (joblib/Ray) — 1 run = 1 process.
- Optionnel : portage cluster (SLURM) ou cloud si on veut scaler à 10⁵+ runs.

**Livrable** : capacité à lancer une étude de sensibilité complète (10⁴ runs) en une nuit.

---

## Phase 6 — Visualisation et communication (continue)

**But** : rendre le projet partageable et défendable.

- Notebooks d'analyse statistique (matplotlib, plotly).
- Viewer 3D galactique pour les runs marquants (Three.js dans Jupyter, ou Blender pour rendus statiques).
- Documentation utilisateur, tutorial, exemples reproductibles.

**Livrable** : un tiers (chercheur, ami techos) peut cloner, lancer, comprendre, et étendre.

---

## Principes transverses (tout au long du projet)

- **Tests d'invariants physiques** (Hypothesis) avant tests unitaires classiques.
- **Registre d'hypothèses tenu à jour à chaque changement de modèle.**
- **Aucune décision arbitraire non documentée.**
- **Le livrable final n'est pas la simu, c'est l'analyse de sensibilité qu'elle permet.**
