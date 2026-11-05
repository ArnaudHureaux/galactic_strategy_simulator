# Questions de recherche et cadre méthodologique

Phase 0 de la [roadmap](../ROADMAP.md). Ce document fixe ce que le papier 1 cherche à établir, et comment. Toute analyse ultérieure doit s'y conformer. Un changement ici est une décision explicite, datée dans l'historique git.

## Questions

**Q1 — Délimiter l'espace compatible avec le Grand Silence.**
Dans l'espace des paramètres explorés, quelles régions produisent un univers où l'humanité n'observe rien, et lesquelles l'excluent ? Quels paramètres déterminent la frontière ?

**Q2 — Stratégies gagnantes au sein de cet espace.**
Dans les régions compatibles, quel est le lien entre les paramètres explorés et le succès écologique des stratégies (archétypes) ?

**Hors périmètre du papier 1 : ce que devrait faire l'humanité.**
Dans un univers silencieux, la stratégie de l'humanité n'a encore eu aucun effet : par construction, elle n'a ni été attaquée ni contacté personne. La tester demanderait de simuler le futur, après le présent, avec différentes stratégies humaines. Ce sera le papier 2. Dans le papier 1, l'humanité n'apparaît qu'en discussion, avec trois réserves explicites :
1. le succès moyen d'un archétype ne transpose pas tel quel à une civ jeune, peu avancée et arrivée tard ;
2. le succès d'une population n'est pas la meilleure réponse d'un agent isolé ;
3. la stratégie humaine n'a pas encore été mise à l'épreuve.

## Position sur l'incertitude : pas de probabilité sur les hypothèses

Les paramètres du modèle (fréquence des civilisations, lois de conflit, mélange des stratégies…) sont soumis à une **incertitude profonde** : aucune base ne permet de leur attribuer une distribution de probabilité. Le papier ne donne donc **aucune probabilité sur les paramètres** : ni postérieur, ni « probabilité que la Forêt sombre soit vraie ». Il cartographie des régions de l'espace des paramètres. C'est le cadre de la prise de décision sous incertitude profonde (découverte de scénarios, Lempert, Bankes et al.) et du *history matching* (Vernon et al., appliqué à la formation des galaxies).

Conséquences :
- L'échantillonnage (LHS, Sobol) ne sert qu'à **couvrir** l'espace. Il ne représente pas une croyance.
- Le **volume** d'une région ne sera jamais présenté comme une probabilité, car il dépend du choix d'échelle (log ou linéaire) de chaque axe.
- Les intervalles explorés sont justifiés par la littérature (ce qui est physiquement plausible), pas par une croyance sur la valeur réelle.

Seule la **variabilité aléatoire interne au modèle** est quantifiée en probabilité. Pour un même jeu de paramètres, des graines différentes (positions, naissances, tirages de stratégies, autodestructions) donnent des histoires différentes. C'est une propriété mesurable du modèle, pas une croyance.

## Définitions

**Jeu de paramètres θ** : une combinaison de valeurs des paramètres explorés, c'est-à-dire un point du plan d'expérience. Chaque θ est simulé avec **N graines** (N = 20 par défaut, à confirmer en phase 3 selon le bruit observé).

**Simulation rejetée** : une simulation où l'humanité aurait observé autre chose que le silence (critères ci-dessous).

**Fréquence de silence f(θ)** : proportion des N graines non rejetées.

**Compatibilité de θ avec le Grand Silence** :

| Catégorie | f(θ) |
|---|---|
| Pas compatible | 0 graine silencieuse |
| Peu compatible | < 10 % |
| Compatible | 10 % à 50 % |
| Très compatible | ≥ 50 % |

Les seuils sont une convention. Les points dont l'intervalle de confiance (Wilson, 95 %) chevauche un seuil sont marqués **incertains**. Les conclusions doivent être vérifiées avec des seuils décalés.

**Succès écologique d'un archétype**, mesuré dans les seules graines silencieuses :
- **principal** : taux de survie jusqu'au présent des civs de cet archétype, rapporté au taux de survie moyen de la galaxie. Un ratio > 1 signifie que l'archétype survit mieux que la moyenne. Contrôles : date de naissance et voisinage, puisque les civs nées tôt ont plus d'occasions de mourir ;
- **secondaire** : part des mondes occupés au présent détenue par cet archétype.

**Stratégie gagnante** dans une région : l'archétype dont le succès principal est le plus élevé, avec un écart au suivant plus grand que la variabilité entre graines.

## Critères de rejet et contraintes d'observation

Chaque critère correspond à une contrainte observationnelle réelle. Références complètes (DOI, arXiv) dans [biblio/phase0_research_report.md](../biblio/phase0_research_report.md).

| Critère | Ce qu'on suppose observé | Paramètres liés | Sources |
|---|---|---|---|
| `attacked` | l'humanité n'a jamais été attaquée | — | constat historique, pas de source à citer |
| `colonized` | le Système solaire n'est pas occupé par une autre civ depuis 4,5 Ga (« Fait A ») | `artefact_window_years` | Hart 1975 ; Tipler 1980 ; contrepoint : Sagan & Newman 1983 |
| `contact_signal`, `contact_probe`, `signal_in_window` | aucune technosignature détectée par SETI | `signal_window_years`, portées d'émission | Project Ozma (Drake 1961) ; Enriquez et al. 2017 ; Price et al. 2020 ; Wlodarczyk-Sroka et al. 2020 ; Gajjar et al. 2021 ; Wright, Kanodia & Lubar 2018 |
| `artefact` | aucune sonde ni artefact trouvé dans le Système solaire | `artefact_detection_probability`, `artefact_stealth_per_tech` | Freitas 1983 ; Freitas & Valdes 1985 ; Haqq-Misra & Kopparapu 2012 ; Benford 2019 |

### Écarts entre le modèle et les observations réelles (à traiter en phase 2)

1. **SETI n'est pas exhaustif.** Le modèle suppose que tout signal couvrant la Terre pendant la fenêtre est détecté. En réalité, SETI n'a fouillé qu'une infime fraction de l'espace de recherche (directions, fréquences, durée : Wright et al. 2018). Ses limites s'expriment en puissance émise (EIRP) et en fraction d'étoiles : ≲ 0,066 % des systèmes à moins de 50 pc émettent plus de 10¹³ W (Wlodarczyk-Sroka et al. 2020). Il faut une probabilité de détection, ou un seuil EIRP/distance avec une couverture partielle, à la place d'une détection certaine.
2. **La fenêtre SETI ne dure pas 100 ans.** La recherche active commence en 1960 (Ozma), soit environ 65 ans, et n'est sensible que depuis quelques décennies. Les fuites humaines, elles, datent des années 1930. Il faut deux fenêtres distinctes : quand l'humanité est détectable, et quand elle écoute.
3. **La recherche d'artefacts est très incomplète.** Seule une petite partie du Système solaire a été examinée à une résolution suffisante (Haqq-Misra & Kopparapu 2012), et des sondes pourraient être parquées sur des co-orbiteurs (Benford 2019). `artefact_detection_probability` doit être bornée en s'appuyant sur ces travaux.
4. **Biais de sélection anthropique.** On ne simule que des univers où l'humanité existe. L'« ombre anthropique » (Ćirković, Sandberg & Bostrom 2010) biaise les fréquences d'événements destructeurs observées depuis l'intérieur. À discuter dans les limites du papier.

## Positionnement

Travaux les plus proches (détails dans le rapport bibliographique) :
- **Monte Carlo et percolation** : Forgan 2009, 2011 et 2016 (*Galactic Club*) ; Hair 2011 ; Hair & Hedman 2013 ; Cartin 2014 et 2015 ; Kinouchi 2001 ; Galera, Galanti & Kinouchi 2018 ; Landis 1998 ; Newman & Sagan 1981 ; Carroll-Nellenback et al. 2019.
- **Modèles de population** : Hanson et al. 2021 (*Grabby Aliens*) ; Balbi & Ćirković 2021 ; Balbi & Grimaldi 2024 ; Grimaldi et al. 2018.
- **Forêt sombre** : aucune formalisation à comité de lecture trouvée. La seule tentative multi-agents récente (Yan 2025, arXiv:2509.02625) a été retirée.

**Apport** : à notre connaissance, aucun travail ne combine (1) des agents qui **décident** selon des stratégies nommées (attaque, partage, émission, colonisation), (2) une causalité stricte à la vitesse de la lumière entre agents individuels, et (3) une confrontation explicite aux contraintes observationnelles du silence, critère par critère. Les travaux existants tirent des civilisations passives ou raisonnent sur des populations moyennes. Nous adoptons aussi le protocole ODD (Grimm et al. 2006, 2010, 2020), qu'aucun de ces travaux n'utilise.

## Méthode d'analyse prévue

1. **Q1** : carte de f(θ) sur l'espace exploré, puis découverte de scénarios (PRIM, arbres de classification) pour décrire les régions de chaque catégorie par des règles simples sur les paramètres. Les indices de sensibilité (Morris, puis Sobol) sont calculés sur f(θ).
2. **Q2** : dans les régions compatibles, découverte de scénarios sur l'archétype gagnant et indices de sensibilité sur le succès de chaque archétype.
3. **Robustesse** : seuils de catégories, nombre de graines, choix d'échelle des axes, choix de modèle alternatifs (phase 7 de la roadmap).

Le plan d'analyse détaillé sera gelé avant les gros runs (phase 6).

## Revue cible

Choix reporté à la phase 8 : la rigueur visée ne dépend pas de la revue. Le papier est rédigé au format ODD avec des annexes complètes. Le cœur doit tenir en environ 8 000 mots, pour rester compatible avec toutes les revues de la liste courte. Prépublication arXiv dans tous les cas.

Liste courte : *International Journal of Astrobiology* (meilleur ajustement thématique, open access payant), *Acta Astronautica* (hybride, gratuit en voie abonnement), *JASSS* (cadrage méthodologique, gratuit, aucun précédent sur le sujet). À vérifier directement auprès des éditeurs avant soumission : formats et exigences de dépôt de code (pages inaccessibles pendant la recherche).
