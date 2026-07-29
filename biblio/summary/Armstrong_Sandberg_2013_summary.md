---
paper: Eternity in Six Hours — Intergalactic Spreading of Intelligent Life
authors: Stuart Armstrong, Anders Sandberg
year: 2013
source: Acta Astronautica 89, pp. 1-13 (preprint introuvable proprement)
status: SOURCE INCERTAINE — le PDF stocké (6 pages, "Spamming the universe") n'est probablement PAS la version canonique 40 pages. Résumé fait depuis la connaissance du papier + aperçu du PDF.
---

# Eternity in Six Hours

## ⚠ Avertissement
Le PDF dans `sources/` fait 6 pages, alors que l'article publié dans
*Acta Astronautica* fait ~40 pages. C'est probablement un résumé court
("Spamming the Universe") par Sandberg. **À remplacer** : chercher la
version Acta Astronautica via institutional access, ou demander à
l'auteur. Le résumé ci-dessous est fiable car le papier est très connu.

## Thèse centrale
Une civilisation post-humaine, même avec des hypothèses **conservatrices**
sur la technologie disponible (pas de FTL, pas de magie), peut coloniser
**l'univers observable entier** en quelques millions d'années en
construisant ~10^10 sondes auto-réplicantes lancées à 0.5-0.99 c.
La colonisation intergalactique n'est **pas** un goulot d'étranglement.

## Méthode
- Inventaire des technologies "réalistes" mais non démontrées : sondes
  auto-réplicantes (von Neumann), voiles laser, sondes nucléaires
  pulsées.
- Calcul énergétique : énergie pour disassembler Mercure (Dyson
  partiel) → suffit à lancer ~10^10 sondes à fraction de c.
- "Six heures" = temps de préparation à Mercure pour lancer une vague
  qui atteindra toutes les galaxies de l'univers observable.
- Modélisation de l'expansion : limite par la vitesse de la lumière, pas
  par l'ingénierie.

## Résultats clés à retenir pour le simulateur
1. **Énergie nécessaire est triviale** à l'échelle d'une K2 (Kardashev
   2). L'asymétrie attaque/colonisation/défense penche massivement vers
   l'expansion.
2. **Vitesse de croisière 0.5-0.99 c** réalisable avec voiles laser
   propulsées depuis l'étoile mère.
3. **Auto-réplication** à destination est l'ingrédient critique : sans
   elle, la colonisation est bornée. Avec elle, exponentielle.
4. **Front de colonisation de l'univers observable en ~few × 10^8 ans**,
   intra-galactique en <1 Myr.
5. Renforce fortement Hanson 1998 et le paradoxe de Fermi : si quelqu'un
   l'a fait, on devrait le voir.

## Conséquences pour notre modèle
- Définir un **paramètre "auto-réplication disponible"** dans
  HYPOTHESES.md — c'est un switch dichotomique aux conséquences énormes.
- Le **plafond de vitesse** par défaut : 0.5 c (conservateur), avec
  sensibilité testée jusqu'à 0.99 c.
- Énergie disponible à K2 ≈ luminosité stellaire complète → suffit à
  toute campagne de colonisation. Le facteur limitant est **politique**,
  pas physique.
- Implémenter la **construction de swarm de sondes** comme événement
  one-shot très coûteux, puis expansion quasi-gratuite.

## Citations utiles (de mémoire)
- "Six hours of Mercury's mass is sufficient to launch a colonization
  wave reaching every galaxy in the observable universe."
- "The bottleneck is not energy, propulsion, or replication — it is
  the decision to start."

## TODO
- [ ] Remplacer le PDF par la version Acta Astronautica 89 (2013).
- [ ] Vérifier les chiffres exacts (10^8 vs 10^9 sondes, etc.) une fois
      le bon papier obtenu.
