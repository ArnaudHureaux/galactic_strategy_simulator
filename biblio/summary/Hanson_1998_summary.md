---
paper: Burning the Cosmic Commons — Evolutionary Strategies for Interstellar Colonization
author: Robin Hanson
year: 1998
source: mason.gmu.edu/~rhanson/filluniv.pdf
pages: 10
status: lu intégralement
---

# Burning the Cosmic Commons

## Thèse centrale
Si la colonisation interstellaire est possible, alors la **sélection
évolutive** sur la frontière de colonisation favorise les "colonisateurs
rapides et économes", qui consomment massivement les ressources locales
pour envoyer la prochaine vague. Le front d'expansion atteint des
vitesses proches d'une fraction non-triviale de c, et **brûle les
communs** : les colons qui hésitent ou conservent sont dépassés.

## Méthode
- Modèle économique simple : à chaque étoile, un colon doit décider
  combien investir en *reproduction* (envoi de sondes vers de nouvelles
  étoiles) vs *consommation locale*.
- Sélection évolutive : seuls les patterns "rush" se propagent.
- Calcul de la vitesse de front en fonction du coût énergétique de
  l'accélération, de la distance moyenne entre étoiles, et du temps de
  préparation sur place.

## Résultats clés à retenir pour le simulateur
1. **Vitesse de front ≈ 0.5-0.99 c** selon les hypothèses techno.
   Asymptote sub-relativiste.
2. **Pas de "civilisation lente sage"** : toute civ qui colonise plus
   lentement que ses voisines disparaît du front. Sélection brutale.
3. **Asymétrie attaque/défense** : un colonisateur rapide arrive avant
   que les défenseurs ne puissent se préparer.
4. Conséquence : si la colonisation existe, l'univers devrait être
   visiblement colonisé → renforce le paradoxe de Fermi (sauf si
   personne ne colonise jamais).
5. Le front d'expansion **épuise** les étoiles traversées (matière,
   énergie) — d'où "burning the commons".

## Conséquences pour notre modèle
- La stratégie "Colonisateur agressif" doit être **dominante** dans
  notre bestiaire (Phase 3) tant que la colonisation est techniquement
  possible.
- Implémenter explicitement la **pression sélective** sur le front :
  une civ trop lente perd les étoiles disponibles.
- La vitesse de propulsion n'est pas seulement physique, c'est
  économique : compromis énergie locale vs envoi.
- Le silence cosmique → ou bien la colonisation est impossible, ou bien
  personne n'a jamais essayé. À tester dans la simu.

## Citations utiles
- "The colonists who burn through the cosmic commons fastest will
  inherit the universe."
- "Slow careful colonization is not a stable equilibrium."
