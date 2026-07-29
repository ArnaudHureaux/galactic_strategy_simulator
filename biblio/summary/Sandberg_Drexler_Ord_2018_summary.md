---
paper: Dissolving the Fermi Paradox
authors: Anders Sandberg, Eric Drexler, Toby Ord
year: 2018
source: arXiv:1806.02404
pages: 19
status: lu intégralement
---

# Dissolving the Fermi Paradox

## Thèse centrale
Le paradoxe de Fermi disparaît quand on traite correctement l'incertitude
sur les paramètres de l'équation de Drake. Au lieu de multiplier des
valeurs ponctuelles (qui donnent des espérances absurdement grandes),
il faut propager des distributions a priori reflétant l'état réel de la
connaissance. Le résultat est une probabilité **substantielle** que nous
soyons effectivement seuls dans la galaxie observable.

## Méthode
- Revue de la littérature pour chaque paramètre de Drake (taux de
  formation stellaire, fraction d'étoiles avec planètes, f_l, f_i, f_c,
  L) → extraction de distributions log-uniformes / log-normales
  couvrant **plusieurs ordres de grandeur**.
- Monte Carlo sur le produit, plutôt que produit des moyennes.
- Mise à jour bayésienne par le grand silence (Bayes sur l'absence
  d'observation).

## Résultats clés à retenir pour le simulateur
1. **Variance >> moyenne** : l'espérance E[N] cache le fait que la
   distribution est extrêmement skewed. La médiane peut être <<1 même
   quand la moyenne est >>1.
2. **f_l (abiogenèse) domine l'incertitude** : son a priori s'étend sur
   ~200 ordres de grandeur selon les modèles d'abiogenèse.
3. **P(seuls dans la galaxie) ≈ 30-40%**, **P(seuls dans l'univers
   observable) ≈ 10-20%** sous leurs priors.
4. Le paradoxe n'a pas besoin de "Great Filter" exotique — la simple
   ignorance suffit à le dissoudre.

## Conséquences pour notre modèle
- **Ne pas calibrer sur des valeurs ponctuelles** : nos paramètres
  d'origine de civilisations doivent être des distributions, pas des
  scalaires.
- Le réalisme exige de modéliser des mondes où **aucune autre civ
  n'existe** — c'est un cas important, pas un edge case.
- L'analyse de sensibilité (Phase 4) doit explicitement quantifier la
  contribution de chaque incertitude à la variance de sortie (Sobol).

## Citations utiles
- "When the model is updated to reflect realistic uncertainty, we find a
  substantial *ex ante* probability of there being no other intelligent
  life in our observable universe."
- "The expected number of civilizations is dominated by a tiny fraction
  of the parameter space."
