# Passation de session (2026-11-18)

Ce document résume l'état du projet à la fin de la session du 2026-11-15 au 2026-11-18 (fin de la phase 2,
deux audits, test de taille de région). Il complète, sans les remplacer :
[ROADMAP.md](../ROADMAP.md) (plan), [MODEL_CHOICES.md](../MODEL_CHOICES.md) (chaque décision, datée),
[HYPOTHESES.md](../HYPOTHESES.md) (registre généré depuis `data_model/parameters.json`),
[docs/findings/](findings/) (résultats chiffrés).

## Règles de travail avec l'utilisateur

- Répondre en français. L'utilisateur peut suivre à distance (Remote Control) : chaque message final doit
  se suffire à lui-même.
- **« Réponds avant de coder sans mon accord »** : ne rien implémenter qui n'a pas été approuvé.
  Proposer d'abord (formule, intervalle, alternative écartée), coder après le « ok ».
- Un commit par point approuvé, une fois les tests passés. Pousser seulement sur demande.
  `_old/` et `pdfs/` ne sont jamais commités.
- Le rythme de progrès de l'humanité est une observation, pas une hypothèse : `humanity_tech_fraction`
  ne doit pas varier (son statut E dans le registre est une incohérence connue, à corriger).

## Mécanique du dépôt

- Deux moteurs **bit-identiques** : Python (référence, `python/`) et Rust (`rust/core`, exposé par
  `rust/py` via maturin/PyO3, ~30x plus rapide). Toute modification se fait dans les deux, avec
  `pymath::exp/log/log1p/pow/cos/sin` et `pymin/pymax` côté Rust pour rester identique à CPython.
- Construire le Rust (PowerShell) :
  `$env:CARGO_TARGET_DIR="D:\rust\targets\galactic"; cd rust/py; python -m maturin build --release -i python -o D:\rust\wheels`
  puis `pip install --force-reinstall --no-deps <wheel le plus récent>`.
  **Attention** : réinstaller la roue pendant une exploration en cours fait charger le nouveau code aux
  processus suivants (un processus par job).
- Tests : `cd python; python -m pytest tests -q -p no:cacheprovider` (161 tests, ~12 min), dont la parité
  Python/Rust (`tests/test_rust_parity.py`).
- Fast-forward : `python compare_fast_forward.py --seeds 8 --span 1e7` (aujourd'hui exact : 8/8 seeds,
  0 écart, accélération x1,2 à x1,5).
- Registre : `python registry.py check` puis `python registry.py doc` (régénère HYPOTHESES.md ; un test
  échoue si on l'oublie).
- Explorations : `python explore.py plan|run|status|collect` (voir son docstring). Les résultats vont
  dans `explorations/`, **ignoré par git** et sans sauvegarde : seuls les specs (`python/specs/`), le code
  et les rapports de `docs/findings/` sont versionnés. Un dossier nommé `results/` est ignoré par
  `.gitignore`, d'où `docs/findings/`.
- Beaucoup de fichiers sont en CRLF : les éditer sans casser les fins de ligne.

## Ce qui a été fait (commits du 2026-11-15 au 2026-11-18)

Premier audit de la phase 2 (`26b9c58` à `d5569e3`) :
1. Fuites radio de l'humanité observées, nombre de mondes sur le disque, détection des sondes par territoire.
2. `natural_tech_progress_mean` : intervalle [3e-11 ; 8e-6], l'humanité au 75e centile (25 % des runs
   progressent plus vite qu'elle) ; croissance de la tech exacte par pas (`grow`).
3. Dégâts d'une attaque sur la loi d'énergie : la cible perd la part d de sa puissance, soit ln(1−d)/k
   niveaux de tech (k ≈ 6,1), son rayon x (1−d)^(1/3) (`_damaged_tech`).
4. Sensibilité d'écoute ancrée sur la tech de l'observateur (Breakthrough Listen pour l'humanité,
   `seti_flux_threshold_cap_w_m2` exploré au plafond).
5. Comparaison du fast-forward : seeds dont les naissances diffèrent marquées (devenu sans objet, voir plus bas).

Second audit (« le simulateur est-il publiable ? »), verdict : pas en l'état ; ingénierie solide, mais
biais en faveur du silence et méthode incomplète. Suites données :
- `f79dca3` Coût d'une attaque pour l'attaquant sur la même loi d'énergie (au lieu de x(1−c) sur la tech).
- `5413bca` Autodestruction et dispersion : part ρ = `self_destruction_correlation` (explorée, log
  [1e-3 ; 1], défaut 0,1) des catastrophes touche tous les mondes ; les autres ne tuent qu'une civ à un
  seul monde (passage linéaire de 1 à 2 mondes).
- Le départ il y a 1 Ga (sursaut gamma, Annis 1999) est jugé logique et sourcé : rien à changer.
- `bcfdc00` **Zone habitable galactique et régions emboîtées** (le plus gros changement, détaillé ci-dessous).

## Le test de taille de région et sa conclusion

1. Test naïf (500 pc, 1, 2, 4 kpc à densité constante, une galaxie tirée par taille) : silence 34 %,
   13 %, 7 %. Brouillé par le hasard du tirage.
2. Test emboîté (même galaxie de 4 kpc recadrée à 1 kpc, 2 kpc ou entière ; rapport complet dans
   [findings/region_size_nested_2026-11-17.md](findings/region_size_nested_2026-11-17.md)) :
   - 28 des 150 points sont silencieux à 1 kpc ; dans la galaxie de 4 kpc, 3 le restent, 15 perdent leur
     silence, 10 runs expirent. 2 kpc ne suffit pas non plus.
   - Mécanisme : le responsable est un voisin (~600 pc), mais il a été **stimulé par des civs lointaines**
     (partages de tech) : seul à 1 kpc, il restait à tech 0,1 ; dans la grande galaxie il connaît des
     dizaines à des centaines de civs et monte à tech 3.
   - Aucun rejet à 1 kpc ne redevient silencieux plus grand (1/122 entre 1 et 2 kpc, cas marginal) :
     **un rejet en petite région est définitif ; un silence doit être revérifié sur la galaxie entière**.
   - Ni la densité ni une portée calculée a priori ne prédisent quels silences tombent (les 3 survivants
     sont peu denses, mais des galaxies aussi éparses tombent).
   - Conséquence : la fréquence de silence mesurée à 1 kpc est fortement surestimée.
3. D'où `bcfdc00` :
   - La vie suit un **anneau gaussien** (zone habitable galactique, Lineweaver et al. 2004 ; Gowanlock
     et al. 2011) centré sur le rayon du Soleil (`galactic_radius_sun_pc` = 8200), de largeur
     `ghz_width_pc` explorée [0,5 ; 4] kpc. Les bras spiraux ne sont pas modélisés (les étoiles les
     traversent et dérivent radialement sur 1 Ga ; notre résumé de Forgan 2009 les dit plutôt hostiles).
   - `bubble_density_kpc2` et `civ_birth_rate_kpc2` (densités au rayon du Soleil) remplacent
     `expected_bubbles` et `civ_birth_rate` (anciens intervalles divisés par π). `crop_radius_pc` disparaît.
   - Toute la galaxie est toujours tirée avec les mêmes nombres aléatoires (un flux par bulle et par
     naissance) ; `region_radius_pc` (distance horizontale au Soleil, 0 = toute la galaxie) choisit ce qui
     est simulé. Des régions de tailles différentes sont **exactement emboîtées** (testé).
   - Les naissances sont un processus de Poisson **tiré dès le départ** : identiques avec ou sans
     fast-forward (l'écart résiduel du fast-forward a disparu).
   - Anciennes specs de taille : `python/specs/archive/` (à relancer aux commits indiqués dans son README).

## Points ouverts (par priorité)

1. **Performance sur la galaxie entière** (bloquant pour la règle « silence => galaxie entière ») :
   ~4400 civs initiales au défaut ; un run rejeté au pas 179 prend déjà 210 s en Rust (0,1 s à 1 kpc).
   Suspect principal : l'index de voisinage (`geometry.py` / `NeighborIndex`, tri de toutes les paires,
   O(n²)). 17 des 44 runs à 4 kpc ont expiré à 1 h. À profiler, puis phase 4 du ROADMAP.
2. **Règle de l'étude** : simuler 1 kpc, garder les rejets, relancer chaque silence sur la galaxie entière
   (même seed, `region_radius_pc = 0`). À écrire dans `explore.py` (deuxième passe) et à décrire dans le papier.
3. **Relancer l'exploration** avec le modèle actuel (specs `lhs25` converties, 28 dimensions) : aucun
   résultat n'a été mesuré depuis les corrections du 2026-11-17.
4. Densité de mondes habitables (vitesse des fronts) fixe : elle devrait suivre le rayon galactique.
5. `humanity_tech_fraction` encore « E » dans le registre alors qu'il est fixé.
6. Phase 3 (vérification) non faite : convergence en dt, cas analytiques, tests de propriétés, CI.
7. Méthode statistique : 1 seed par point, timeouts exclus (données censurées corrélées aux paramètres),
   pas encore de Morris, Sobol ni catégorisation f(θ) sur plusieurs seeds.
8. A priori : beaucoup d'intervalles « provisoires » ; références à vérifier avant citation (dont
   Lineweaver 2004, Gowanlock 2011, GRAVITY 2019).
9. Simplifications à déclarer dans le papier : attaques à la vitesse de la lumière, partages implicites
   instantanés, sphères de sondes qui visitent toutes les étoiles, naissances possibles dans le territoire d'autrui.
