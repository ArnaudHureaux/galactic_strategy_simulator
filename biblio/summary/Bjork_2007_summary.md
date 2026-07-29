---
paper: Exploring the Galaxy Using Space Probes
authors: Rasmus Bjørk
year: 2007
source: arXiv:astro-ph/0701238 ; International Journal of Astrobiology ; DOI 10.1017/S1473550407003709
pages: 6
status: résumé sur abstract + introduction/§1 (à lire intégralement)
---

# Exploring the Galaxy Using Space Probes

## Thèse centrale
Combien de temps faut-il à une flotte de sondes auto-réplicantes /
hiérarchiques pour explorer la Galaxie ? Bjørk simule numériquement
l'exploration de la Zone Galactique Habitable (GHZ, 3–11 kpc du centre)
au moyen de sondes mères déployant des **sous-sondes**. Résultat : même
avec des moyens modestes, l'exploration prend des **centaines de millions
d'années** — long, mais << âge de la Galaxie. La lenteur de l'exploration
est donc une composante quantifiable du paradoxe de Fermi.

## Méthode
- Modèle galactique : densité stellaire disque décroissant
  exponentiellement (longueur d'échelle 3 kpc), GHZ de Lineweaver
  (3–11 kpc), échelle de hauteur du disque mince 300 pc.
- ~1,17·10¹⁰ étoiles habitables estimées → trop pour simuler directement.
- **Approche multi-échelle** : mesurer le temps d'exploration de 40 000
  étoiles dans une boîte (±300 pc) en fonction du rayon galactique, puis
  paver la GHZ avec ~260 000 de ces boîtes et agréger.
- Sondes organisées hiérarchiquement (sondes mères × sous-sondes) se
  déplaçant d'étoile en étoile ; balayage du plus proche voisin.

## Résultats clés à retenir pour le simulateur
1. **Ordres de grandeur du temps d'exploration** : 8 sondes × 8
   sous-sondes → ~4 % de la Galaxie en 2,92·10⁸ ans ; 200 sondes × 8
   sous-sondes → 1,52·10⁷ ans. Bornes concrètes pour calibrer notre
   moteur de détection/couverture.
2. **La couverture scale avec le nombre de sondes** (quasi-linéaire sur la
   plage étudiée) → paramètre de flotte directement exploitable.
3. **Découpage multi-échelle** : astuce méthodologique pour éviter de
   simuler 10¹⁰ étoiles — pertinent pour notre Phase 5 (scaling) et pour
   la génération procédurale au-delà du voisinage Gaia (Phase 2).
4. Choix de population stellaire : F, G, K, M (+ A) retenues, O/B exclues
   (durée de vie trop courte) → grille pour notre filtre d'habitabilité.

## Conséquences pour notre modèle
- Fournit des **valeurs de référence** (temps de couverture vs taille de
  flotte) pour valider notre modèle de sondes/détection en Phase 2 avant
  d'ajouter la stratégie.
- La **stratégie de plus proche voisin** et la hiérarchie mère/sous-sonde
  sont un point de départ simple pour la policy « Colonisateur » (Phase 3).
- Le **découpage en boîtes représentatives** est une technique de scaling
  à garder pour dépasser le rayon Gaia (~100 pc) sans exploser le compute.
- Les **coupes de population stellaire** (GHZ, types spectraux, binaires
  comptées comme une étoile) informent directement notre substrat
  physique (Phase 2) et notre `HYPOTHESES.md`.

## Citations utiles
- "With 8 probes, each with 8 subprobes ∼4% of the Galaxy can be explored
  in 2.92·10⁸ years. Increasing the number of probes to 200 … reduces the
  exploration time to 1.52·10⁷ years."
- "The fraction of these stars that have planets suitable for harboring
  life is estimated to be ≃10%, all located in the … Galactic Habitable
  Zone."
