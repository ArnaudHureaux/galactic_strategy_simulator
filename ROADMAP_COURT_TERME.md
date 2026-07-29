# Roadmap court terme — Next steps

Horizon : 2-4 semaines. Couvre la Phase 0 et le tout début de la Phase 1. **Aucun code de simulation à ce stade** — on construit les fondations conceptuelles et l'environnement de travail.

---

## Semaine 1 — Cadrage scientifique

### S1.1 — Lecture ciblée (priorité absolue)
- [ ] Sandberg, Drexler, Ord (2018) — *Dissolving the Fermi Paradox*
- [ ] Hanson (1998) — *Burning the Cosmic Commons*
- [ ] Armstrong & Sandberg (2013) — *Eternity in Six Hours*
- [ ] Forgan (2009+) — papiers sur le testbed numérique SETI
- [ ] Notes prises dans un fichier `notes/biblio.md` : pour chaque papier, **les 3 idées qu'on retient pour le modèle**.

### S1.2 — Décisions structurantes
Rédiger `MODEL_CHOICES.md` qui tranche, avec justification courte :
- [ ] FTL autorisé ou non ? (recommandation : non, force la stratégie à compter)
- [ ] Modèle de progrès techno : logistique bornée vs paliers Kardashev
- [ ] Mortalité endogène : oui/non, quelle forme ?
- [ ] Granularité temporelle minimale (année ? siècle ?)
- [ ] Échelle spatiale max simulée (100 pc ? 1 kpc ? galaxie entière ?)

---

## Semaine 2 — Registre d'hypothèses et données réelles

### S2.1 — `HYPOTHESES.md`
- [ ] Tableau exhaustif : paramètre, symbole, valeur centrale, distribution a priori, source, sensibilité présumée (low/med/high).
- [ ] Couvre au minimum : taux de formation stellaire, fraction d'étoiles avec planètes habitables, longévité civ moyenne, vitesse max réaliste, énergie de destruction planétaire, distance moyenne entre étoiles dans le voisinage.

### S2.2 — Acquisition données stellaires réelles
- [ ] Télécharger HYG database v3 (catalogue d'étoiles à <100 pc, accessible publiquement).
- [ ] Explorer dans un notebook : distribution spatiale, types spectraux, positions par rapport au Soleil.
- [ ] **Pas encore d'intégration** dans un moteur, juste de la familiarisation.

---

## Semaine 3 — Environnement projet et architecture

### S3.1 — Setup technique
- [ ] Git init, structure de dossiers (`docs/`, `notebooks/`, `data/raw/`, `data/processed/`).
- [ ] Environnement Python reproductible (`uv` ou `poetry` + `pyproject.toml`).
- [ ] Pre-commit hooks : ruff, mypy strict, tests qui tournent.
- [ ] Convention de seed RNG, hash de config — documentée dans `docs/reproducibility.md`.

### S3.2 — Squelette d'architecture
Document `docs/architecture.md` détaillant les 7 couches :
- [ ] Substrat physique, moteur physique, civilisation, stratégie, scheduler, observation, analyse.
- [ ] Pour chaque couche : responsabilités, API exposée, ce qu'elle ne fait PAS.
- [ ] Schéma de dépendances (couche N ne connaît que N-1).
- [ ] Décision : monorepo ou packages séparés ? (recommandation : monorepo avec sous-packages).

---

## Semaine 4 — Premier prototype de plomberie

**Objectif** : pas une simulation, juste prouver qu'on sait construire une event loop propre et observable.

### S4.1 — Event loop minimaliste
- [ ] Priority queue temporelle (heapq).
- [ ] Événements bidons (ex : 5 "civilisations" qui émettent un ping à intervalle aléatoire).
- [ ] Respect causalité : un événement ne peut pas être ordonnancé "plus vite que c" relativement à sa cause.

### S4.2 — Observation
- [ ] Chaque événement écrit une ligne dans un buffer.
- [ ] Flush en Parquet à la fin du run.
- [ ] Notebook qui relit le Parquet et trace une timeline.

### S4.3 — Reproductibilité
- [ ] Même seed + même config = même fichier Parquet bit-à-bit (test).
- [ ] Hash de config inclus dans le nom de fichier de sortie.

---

## Critères de passage en Phase 1 "réelle"

On ne commence à coder la simulation scientifique tant que :
- [ ] `HYPOTHESES.md` couvre ≥ 20 paramètres avec source.
- [ ] `MODEL_CHOICES.md` tranche les 5 questions structurantes.
- [ ] L'event loop jouet est reproductible et observable.
- [ ] L'architecture en couches est documentée et acceptée.

**Tant que ces 4 cases ne sont pas cochées, on ne touche pas au moteur physique.** C'est la discipline qui fait la différence entre un jouet et un outil scientifique.

---

## Ce qu'on NE fait PAS pendant ces 4 semaines

- Pas de modèle physique (pas de propulsion, pas de détection, pas de combat).
- Pas de stratégies "intelligentes".
- Pas de visualisation 3D.
- Pas d'optimisation perf.
- Pas de Rust, pas de Numba — Python pur partout.

Tout ça vient après. La tentation sera forte. Y résister.
