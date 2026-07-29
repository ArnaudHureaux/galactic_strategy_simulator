---
paper: A Numerical Testbed for Hypotheses of Extraterrestrial Life and Intelligence
author: Duncan H. Forgan
year: 2009
source: arXiv:0810.2222 (MNRAS 2009)
pages: 22
status: lu intégralement
---

# A Numerical Testbed for ETI Hypotheses

## Thèse centrale
Plutôt que d'argumenter analytiquement sur l'équation de Drake, on peut
construire une **simulation Monte Carlo** de la Galaxie (formation
stellaire, habitabilité, biogenèse, intelligence, communication) et
tester l'effet de différents scénarios. C'est le **premier testbed
numérique** publié, et il s'agit pratiquement de notre projet.

## Méthode
- Génération procédurale d'une galaxie : ~10^9 étoiles avec IMF
  réaliste, distribution spatiale par bras spiral, métallicité,
  formation stellaire dans le temps.
- Habitabilité par étoile : zone habitable continue, stabilité orbitale,
  contraintes sur masse et métallicité.
- Émergence de la vie : tirages stochastiques avec paramètres
  (probabilités/temps) variables selon le scénario.
- 3 scénarios testés :
  1. **Rare Life** : abiogenèse difficile.
  2. **Tortoise and Hare** : vie commune mais intelligence rare.
  3. **Panspermia** : la vie se propage entre étoiles proches.

## Résultats clés à retenir pour le simulateur
1. La distribution spatiale des civs est **fortement clusterée** (pas
   uniforme) — la métallicité et l'âge stellaire concentrent la vie
   dans certaines zones de la galaxie.
2. Sous Panspermia, les contacts inter-civ deviennent **statistiquement
   inévitables** dans le voisinage immédiat.
3. Le **temps médian au premier contact** varie de quelques Myr à
   plusieurs Gyr selon le scénario → critère discriminant fort.
4. Limitations identifiées par l'auteur : pas de stratégies, pas de
   colonisation active, pas de combat, pas de partage techno → c'est
   **exactement les manques que notre projet doit combler**.

## Conséquences pour notre modèle
- **Substrat galactique** : reproduire l'approche Forgan pour la
  génération stellaire (IMF + bras spiraux + métallicité), avec Gaia
  DR3 pour les <100 pc.
- Notre projet se positionne comme un **Forgan-like + couche
  stratégique** : c'est notre véritable apport.
- Calibration : faire tourner notre simu en mode "Forgan" (pas de
  stratégie active) doit **reproduire ses distributions** comme test de
  régression.
- Utiliser ses 3 scénarios (Rare/Tortoise/Panspermia) comme **suite de
  benchmarks** standards.

## Citations utiles
- "A numerical Monte Carlo approach to the Drake equation allows us to
  capture the stochastic nature of the process."
- Limitation reconnue : "No active strategies for contact or
  colonization are modelled."

---

## Glossaire & approfondissements (notes perso)

### "Testbed"
Mot anglais qui signifie littéralement **"banc d'essai"**. En sciences
computationnelles, un testbed est un **environnement de simulation
contrôlé** où l'on peut faire varier des hypothèses et mesurer leurs
conséquences, sans avoir à toucher au système réel (impossible ici,
puisqu'on ne peut pas "tester" une vraie galaxie). Forgan utilise le
terme pour dire : *je ne prétends pas donner la vérité, je donne un
outil pour comparer des hypothèses entre elles*. C'est exactement la
posture qu'on veut adopter — notre simulateur n'est pas une prédiction,
c'est un testbed pour comparer les stratégies civilisationnelles.

### IMF — Initial Mass Function
La **fonction de masse initiale** décrit *comment se répartissent les
masses des étoiles à leur naissance*. Empiriquement, on observe que
les étoiles peu massives sont **beaucoup** plus nombreuses que les
massives. La forme classique (Salpeter 1955, raffinée par Kroupa et
Chabrier) est une **loi de puissance** :

    dN/dM ∝ M^(-α)

avec α ≈ 2.35 pour M > 0.5 M☉. Concrètement : pour 1 étoile de 10 M☉,
on a ~300 étoiles type Soleil et ~30 000 naines rouges (M < 0.5 M☉).

**Pourquoi ça compte pour nous** :
- Les **naines rouges (M dwarfs)** dominent en nombre → si elles sont
  habitables (débat scientifique en cours : flares, tidal locking),
  alors la grande majorité des civilisations potentielles s'y trouvent.
- Les **étoiles massives** vivent peu (~quelques Myr pour les O/B) →
  pas le temps pour la vie complexe d'émerger. À exclure du substrat
  habitable.
- Le **Soleil (G2V)** est statistiquement rare (~7% des étoiles) → on
  est sur une niche.

Dans notre simulateur, l'IMF détermine *combien* d'étoiles de chaque
type on génère, et donc *combien* de mondes potentiellement habitables.

### Bras spiraux
La Voie lactée est une galaxie spirale barrée. Les étoiles ne sont **pas
uniformément réparties** : elles se concentrent dans 4 bras principaux
(Persée, Sagittaire, Écu-Centaure, Bras Extérieur) plus des structures
locales (Bras d'Orion où se trouve le Soleil). Les bras sont des **ondes
de densité** (théorie de Lin & Shu) — la matière y est compressée, ce
qui déclenche la formation stellaire.

**Pourquoi ça compte pour nous** :
- La **densité stellaire varie d'un facteur ~10** entre bras et
  inter-bras → la distance moyenne entre étoiles n'est pas une
  constante galactique.
- Les bras sont des **zones de formation stellaire active** → beaucoup
  de jeunes étoiles massives, donc beaucoup de supernovae → environnement
  **hostile à la vie complexe** (irradiation, perturbation des nuages
  d'Oort, extinction de masse).
- Une "**Galactic Habitable Zone**" (Lineweaver 2004) émerge : ni trop
  près du centre (rayonnement, encombrement), ni trop loin
  (métallicité trop basse), et préférablement entre les bras.

### Métallicité
En astrophysique, le mot "métal" désigne **tout élément plus lourd que
l'hélium** (donc C, N, O, Fe, Si... — pour un astrophysicien, le carbone
est un métal). La métallicité d'une étoile, notée [Fe/H], mesure
l'abondance du fer par rapport à l'hydrogène, en échelle log :

    [Fe/H] = log10((Fe/H)_étoile / (Fe/H)_Soleil)

[Fe/H] = 0 → comme le Soleil. [Fe/H] = -1 → 10× moins de métaux.
[Fe/H] = +0.3 → 2× plus.

**Pourquoi ça compte pour nous** :
- **Pas de métaux → pas de planètes rocheuses**. Les premières étoiles
  (Population III) n'avaient quasi pas de planètes. La métallicité a
  augmenté avec le temps (recyclage par supernovae).
- Les planètes telluriques (Terre-like) **exigent** [Fe/H] ≳ -0.5.
- Trop de métaux → davantage de Jupiters chauds, qui déstabilisent les
  orbites des planètes habitables. Optimum autour de [Fe/H] ~ 0.
- La métallicité **augmente vers le centre galactique** et **décroît
  vers la périphérie** — autre raison d'avoir une Habitable Zone
  galactique.

### "Distribution spatiale fortement clusterée"
"Clusterée" = en grappes, en amas. **Pas uniforme**. Si on avait jeté
les civilisations au hasard avec une probabilité constante par unité de
volume, elles seraient distribuées uniformément (processus de Poisson).

Or Forgan trouve qu'**elles s'agrègent** dans certaines régions, parce
que la probabilité dépend de variables corrélées spatialement :
- métallicité (croît vers le centre),
- âge stellaire (varie avec la position),
- densité stellaire (bras spiraux),
- supernovae voisines (anti-corrélé avec habitabilité).

Conséquence : la **distance au plus proche voisin civilisé** n'est PAS
celle qu'on calculerait avec une densité moyenne uniforme. Elle est
**plus courte qu'attendue** à l'intérieur d'un cluster, et infinie
entre clusters. Ça change tout pour les modèles de contact / détection
/ colonisation : un voisin n'est jamais "à distance moyenne", il est
soit très proche, soit hors de portée.

### "Quelques Myr à plusieurs Gyr"
Échelles de temps astronomiques :
- **Myr** = mégaannée = **million d'années** (10⁶ ans).
- **Gyr** = gigaannée = **milliard d'années** (10⁹ ans).
- Pour comparaison : âge de l'univers = 13.8 Gyr ; âge du Soleil = 4.6
  Gyr ; vie complexe sur Terre ≈ 0.5 Gyr ; *Homo sapiens* ≈ 0.3 Myr ;
  civilisation industrielle ≈ 200 ans.

#### Ce que Forgan trouve
Le **temps médian au premier contact** qui sort de ses simulations varie
sur **3 ordres de grandeur** (10⁶ à 10⁹ ans) selon le scénario.

#### "Ordre de grandeur" — rappel
Un ordre de grandeur = un facteur 10. **3 ordres de grandeur = facteur
1000**. Donc selon le scénario, on attend soit ~1 million d'années, soit
~1 milliard d'années avant le prochain contact. Ce n'est pas une petite
incertitude — c'est la différence entre "on devrait déjà avoir vu
quelqu'un" et "il est statistiquement normal qu'on ne voie personne".

#### Pourquoi cette dispersion est ÉNORME
Pour donner une intuition, on parle d'incertitudes équivalentes à :
- prédire le temps d'attente d'un bus entre **1 minute et 17 heures**,
- ou la durée d'une vie humaine entre **1 jour et 3 ans**.

Quand un modèle scientifique sort une réponse aussi étalée, ça veut dire
une de ces deux choses :
1. soit le modèle est cassé (paramètres mal calibrés),
2. soit le **vrai phénomène** est intrinsèquement aussi incertain.

Forgan montre que c'est (2) : la dispersion vient des hypothèses
elles-mêmes (Rare Life vs Panspermia, etc.), pas du bruit Monte Carlo.

#### Le lien avec le silence cosmique
On observe : **0 civilisation détectée** en ~60 ans de SETI.
Question naïve : est-ce surprenant ?

Si le modèle prédisait "premier contact en 10⁶ ans" avec une **faible
variance**, alors le silence actuel serait surprenant — il faudrait
expliquer pourquoi on n'a rien vu. Ça pousserait vers Dark Forest, Great
Filter, etc.

Si le modèle prédit "premier contact entre 10⁶ et 10⁹ ans" avec
**variance énorme**, alors le silence est **parfaitement compatible**
avec la quasi-totalité des scénarios — il ne tranche rien. On peut être
à 100 Myr en avance comme à 1 Gyr en retard ; les deux sont dans la
distribution.

**Conclusion de Forgan** : le silence cosmique, à lui seul, ne falsifie
aucune hypothèse majeure. Il faut **d'autres observables** (techno-
signatures, exoplanètes, biosignatures) pour discriminer. C'est un
résultat scientifique fort, et un peu décevant : le paradoxe de Fermi
ne **se** résout pas par l'absence d'observation.

#### Pourquoi Monte Carlo plutôt qu'analytique
L'équation de Drake classique donne **un nombre** :

    N = R* × f_p × n_e × f_l × f_i × f_c × L

Si tu mets les valeurs centrales (médianes) de chaque facteur, tu
obtiens un N "moyen". **C'est trompeur**, pour deux raisons :

1. **L'espérance d'un produit ≠ produit des espérances** quand les
   variables sont skewed (log-normales, log-uniformes). Pour des
   distributions log-uniformes sur plusieurs ordres de grandeur,
   E[X×Y] peut être des ordres de grandeur plus grand ou plus petit
   que E[X]×E[Y]. Le produit des médianes ne donne **pas** la médiane
   du produit.

2. **La distribution du produit est extrêmement étalée**. Même si la
   moyenne sort grande, la médiane peut être minuscule, ou inversement.
   Un nombre unique cache toute l'information utile.

L'approche Monte Carlo :
- tirer N_run = 10⁴–10⁶ fois chaque paramètre dans sa distribution a
  priori,
- calculer le produit pour chaque tirage,
- regarder la **distribution complète** de N (médiane, quantiles,
  probabilité que N=0).

Sandberg/Drexler/Ord 2018 vont encore plus loin : ils montrent qu'avec
des priors honnêtes, **P(N=0 dans la galaxie) ≈ 30-40%** — un résultat
qui ne peut PAS sortir d'un calcul analytique avec valeurs centrales.

#### Conséquence pour notre simulateur
- On ne sortira **jamais un nombre unique** ("il y aura X civilisations
  en Y années"). On sortira des **distributions** : histogrammes,
  quantiles, P(extinction), P(contact avant T).
- Chaque run doit être répété **10³ à 10⁶ fois** avec seeds différentes,
  paramètres tirés dans leurs priors → d'où l'importance de la
  Phase 5 (perf/parallélisation) et de la reproductibilité (Phase 1).
- Les figures de sortie (Phase 4) seront des **bandes de confiance**,
  pas des courbes uniques. C'est le standard scientifique pour ce type
  de question.
