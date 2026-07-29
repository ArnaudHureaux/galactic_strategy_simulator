---
paper: Too Damned Quiet?
authors: Adrian Kent
year: 2011
source: arXiv:1104.0624 (rédigé 2005, publié 2011)
pages: 14
status: résumé sur abstract + introduction (à lire intégralement)
---

# Too Damned Quiet?

## Thèse centrale
Le silence cosmique n'implique pas forcément la rareté de la vie. Deux
possibilités alternatives méritent examen : (1) la vie capable de se
manifester à l'échelle interstellaire a évolué en de **nombreux
endroits**, mais une **sélection à l'échelle cosmique** élimine les
espèces qui se signalent bruyamment ; (2) indépendamment de la situation
réelle, une espèce intelligente peut **rationnellement redouter** les
dangers de l'auto-révélation et donc pencher vers la **discrétion**. Le
silence serait alors une stratégie (ou le résultat d'une sélection),
pas une preuve d'absence.

## Méthode
- Argumentation qualitative de théorie des jeux / sélection évolutive
  appliquée à l'échelle galactique (pas de simulation numérique).
- Analyse coût/bénéfice de l'auto-signalement (broadcast) sous incertitude
  radicale sur l'intention des receveurs potentiels.
- Discussion des **contre-arguments** et facteurs compliquant l'analyse
  (asymétrie information, irréversibilité d'un signal émis, etc.).

## Résultats clés à retenir pour le simulateur
1. **Fondement rationnel du Dark Forest** : sous incertitude sur la
   bienveillance d'autrui et asymétrie attaque/défense, le silence est un
   équilibre plausible → justifie nos policies « Silencieuse » et
   « Dark Forest ».
2. **Sélection au niveau cosmique** : les broadcasteurs peuvent être
   systématiquement éliminés → au fil des runs, une **pression sélective**
   contre le broadcast devrait émerger si l'asymétrie de destruction est
   forte.
3. **Irréversibilité** : un signal émis ne se rétracte pas ; le coût est
   asymétrique dans le temps → à modéliser comme engagement définitif.
4. Ce n'est pas un théorème : Kent liste des contre-arguments → utile pour
   ne pas hard-coder « le silence gagne toujours » et laisser l'issue
   dépendre des paramètres.

## Conséquences pour notre modèle
- Notre **matrice attaque/défense** (Phase 2) et l'incertitude sur les
  intentions (couche croyances) sont exactement les ingrédients qui
  rendent le silence rationnel chez Kent → vérifier que « Silencieuse »
  domine « Broadcasteuse » seulement quand l'asymétrie dépasse un seuil.
- Fournit une **hypothèse testable** pour la Phase 3 : sous quelle
  combinaison (probabilité de rencontre × asymétrie destruction ×
  incertitude d'intention) la discrétion devient-elle l'optimum ?
- La « sélection cosmique » suggère de tracer l'**évolution de la
  composition des stratégies** au cours d'un run (pas seulement l'état
  final) pour observer l'extinction des broadcasteurs.

## Citations utiles
- "Evolutionary selection, acting on a cosmic scale, tends to extinguish
  species which conspicuously advertise themselves and their habitats."
- "Intelligent species might reasonably worry about the possible dangers
  of self-advertisement and hence incline towards discretion."
