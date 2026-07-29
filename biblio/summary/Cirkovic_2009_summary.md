---
paper: Fermi's Paradox — The Last Challenge for Copernicanism?
author: Milan M. Ćirković
year: 2009
source: arXiv:0907.3432
pages: 39
status: lu intégralement
---

# Fermi's Paradox — The Last Challenge for Copernicanism?

## Thèse centrale
Le paradoxe de Fermi n'est pas un détail astronomique mais une remise
en question profonde du **principe copernicien** (nous ne sommes pas
spéciaux). Cirkovic propose une **taxonomie exhaustive** des solutions
proposées depuis 60 ans et un cadre d'évaluation. C'est la référence
encyclopédique du domaine.

## Méthode
Classification des solutions en trois familles :

1. **Solutions "soft"** : nous ne voyons pas mais ils sont là (zoo
   hypothesis, sanctuary, simulation, transcendence).
2. **Solutions "rare"** : ils n'existent quasiment pas (Rare Earth,
   Great Filter en amont, contraintes astrobiologiques).
3. **Solutions "catastrophic"** : ils ont existé mais s'auto-détruisent
   (Great Filter en aval, guerres, IA out-of-control).

Pour chaque famille : critères de testabilité, predictions falsifiables,
compatibilité avec données SETI/exoplanètes.

## Résultats clés à retenir pour le simulateur
1. **Le Great Filter peut être devant nous** : implication majeure pour
   la survie humaine — c'est précisément ce que notre projet veut
   quantifier.
2. **Dark Forest = sous-cas de "catastrophic"** : la peur mutuelle
   produit silence + extinction préventive. À implémenter explicitement.
3. **Solutions ne sont pas exclusives** : on peut avoir Rare Earth *et*
   Dark Forest *et* Great Filter. Notre simu doit permettre des
   **combinaisons**.
4. **Asymétrie information** : la plupart des solutions reposent sur le
   décalage entre ce que A sait et ce que B sait → notre séparation
   `world_state` vs `agent_beliefs` est centrale.
5. Critique des Dyson sphères : leur absence est une **vraie contrainte
   observationnelle** (papiers Carrigan, Wright), pas juste un argument
   théorique.

## Conséquences pour notre modèle
- Le bestiaire de stratégies (Phase 3) doit couvrir au moins une
  stratégie par famille de Cirkovic.
- Implémenter le **Great Filter post-techno** comme mortalité endogène
  (paramètre dans HYPOTHESES.md).
- Permettre **plusieurs filtres simultanés** dans la config (pas un
  unique mécanisme d'extinction).
- L'analyse de sensibilité doit identifier **quelle famille de solutions
  domine** selon les paramètres tirés.

## Citations utiles
- "Fermi's paradox is the strongest argument against orthodox
  Copernicanism."
- "The Great Silence is data — possibly the most important data SETI
  will ever produce."
- "No single solution is likely to be the complete answer; reality is
  almost certainly a combination."
