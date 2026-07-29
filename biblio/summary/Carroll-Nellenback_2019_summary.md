---
paper: The Fermi Paradox and the Aurora Effect — Exo-civilization Settlement, Expansion and Steady States
authors: Jonathan Carroll-Nellenback, Adam Frank, Jason Wright, Caleb Scharf
year: 2019
source: arXiv:1902.04450 ; Astronomical Journal 158, 117 (2019) ; DOI 10.3847/1538-3881/ab31a3
pages: ~15
status: résumé sur abstract + introduction (à lire intégralement)
---

# The Fermi Paradox and the Aurora Effect

## Thèse centrale
On peut « remplir » la galaxie d'établissements sans jamais visiter la
Terre. En modélisant la colonisation comme un **front de peuplement** (à
la manière d'une réaction-diffusion) plutôt que par les intentions des
civilisations, on obtient des **états stationnaires** où une fraction
0 < X < 1 des systèmes habitables est occupée. La "Fact A" de Hart
(aucun visiteur sur Terre aujourd'hui) n'implique donc PAS que nous
sommes seuls : la Terre peut rester non visitée au sein d'une galaxie
habitée.

## Méthode
- Front de colonisation via sondes de **vitesse et portée finies**
  (composante dirigée) + **mouvements stellaires** qui ajoutent une
  composante **diffusive** au front sur les temps longs.
- Fraction f de planètes réellement « établissables » (settleable) par
  une civ donnée → non toutes les cibles sont valables.
- Durée de vie finie des établissements → dynamique naissance/mort
  d'occupation → analyse de l'état stationnaire (fraction X occupée).
- Étude paramétrique : vitesse des sondes, taux de lancement, densité
  stellaire, durée de vie → régimes de remplissage vs clusters isolés.

## Résultats clés à retenir pour le simulateur
1. **Le front dirigé + diffusion stellaire suffit** à remplir la Voie
   lactée en un temps << âge galactique, sous hypothèses conservatrices
   (vitesses de sonde et cadences de lancement modestes).
2. **États stationnaires 0 < X < 1** : avec durée de vie finie des
   établissements, la galaxie peut soutenir une population de civ
   spatiales tout en laissant des systèmes vides — un régime d'équilibre,
   pas un tout-ou-rien.
3. **Fluctuations statistiques → clusters** : sur-densités locales de
   mondes habitables produisent des amas colonisés durables entourés de
   grandes régions vides. La structure spatiale compte.
4. **"Aurora effect"** : si certains mondes ne sont pas colonisables
   (f < 1), l'expansion ralentit/stoppe localement — un frein réaliste à
   la colonisation universelle.

## Conséquences pour notre modèle
- **Bench de calibration Phase 2/3 idéal** : reproduire leur front de
  peuplement (vitesse+portée finies, diffusion stellaire) valide notre
  moteur de colonisation et notre respect des vitesses finies.
- Modéliser la **durée de vie finie** des établissements est essentiel :
  c'est elle qui crée l'état stationnaire au lieu d'une saturation
  triviale. À coupler avec notre mortalité endogène (Phase 2).
- Intégrer le **mouvement propre stellaire** (Gaia DR3, Phase 2) n'est
  pas cosmétique : il change la nature du front (diffusif) sur temps longs.
- La **fraction f de mondes établissables** rejoint notre idée
  d'enveloppes d'habitabilité par civ → non-compétition / clusters.
- La sortie observable (X, taille des clusters, temps de remplissage)
  fournit des métriques directement mesurables dans nos runs Monte Carlo.

## Citations utiles
- "The Milky Way can be readily 'filled-in' with settled stellar systems
  under conservative assumptions about interstellar spacecraft velocities
  and launch rates."
- "We find a range of parameters for which 0 < X < 1 i.e. the galaxy
  supports a population of interstellar space-faring civilizations even
  though some settleable systems are uninhabited."
- "These results break the link between Hart's famous 'Fact A' … and the
  conclusion that humans must, therefore, be the only technological
  civilization in the galaxy."
