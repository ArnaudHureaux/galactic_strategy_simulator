# Research Report: Positioning and Grounding an Agent-Based Monte Carlo Simulator of the Great Silence

*Methodology note: All citations below were checked by background research agents against arXiv (API), Crossref (API), NASA ADS, OpenAlex, and publisher pages. Verified items carry a DOI and/or arXiv ID with URL. Items that could not be confirmed to exist, or whose details differ from what is commonly assumed, are explicitly flagged — do not use them in the manuscript without independent verification.*

---

## 1. Closest prior work to cite and position against

### 1.1 Hanson, Martin, McCarter & Paulson 2021 — "Grabby Aliens"

**Hanson, R., Martin, D., McCarter, C., & Paulson, J. (2021).** "If Loud Aliens Explain Human Earliness, Quiet Aliens Are Also Rare." *The Astrophysical Journal*, 922(2), 182.
DOI: [10.3847/1538-4357/ac2369](https://doi.org/10.3847/1538-4357/ac2369) · arXiv: [2102.01522](https://arxiv.org/abs/2102.01522)

Derives a population-level birth-rate/expansion-speed model (fit to "hard steps" and humanity's temporal rank among possible observers) for "loud," volume-transforming civilizations, predicting that a large fraction of the universe's volume is already claimed and that contact is likely within ~200 Myr–2 Gyr. **Difference from our approach:** it is a statistical/cosmological model with no discrete agents, no interaction strategies, and no 1-kpc galactic-disk geometry — expansion is a uniform constant-speed front over Hubble volumes, not causal light-cones between individually modeled civilizations within one galaxy. Our simulator resolves individual agents, discrete chosen strategies (aggressive/passive/dark-forest/broadcaster/cooperative, etc.), and explicit Great-Silence rejection criteria (attack, colonization-front-covers-Sun, signal-detection, probe-discovery) — Hanson et al. have no analogue of any of these.

### 1.2 Dark Forest game theory / deterrence literature

- **"Yu 2015" dark-forest game-theory paper: NOT VERIFIED.** Extensive arXiv/Crossref search found no peer-reviewed paper by an author "Yu" formalizing the Dark Forest hypothesis game-theoretically. Treat this citation as unconfirmed unless you have a specific source.
- **Closest match found — WITHDRAWN, do not cite as reliable:** Yan, X. (2025). "The Recursive Panopticon Hypothesis." arXiv:[2509.02625](https://arxiv.org/abs/2509.02625v2) — **withdrawn by the author** for "improper use of AI tools in preparation." It proposed an ABM of utility-maximizing agents under recursive deterrence, finding silence as an evolutionarily stable strategy. Thematically close to our `dark_forest` strategy but unusable as a citation.
- **Gros 2019 "aliens/universal subroutine" paper: NOT VERIFIED** under that title (128 Gros arXiv papers scanned). Two genuine, relevant Gros papers exist instead:
  - Gros, C. (2005). "Expanding advanced civilizations in the universe." *JBIS*, 58, 108. arXiv:[astro-ph/0501119](https://arxiv.org/abs/astro-ph/0501119) (no DOI, pre-CrossRef JBIS). Analytic model of coexisting "sleeper"/expanding civilizations compatible with non-detection — relevant to percolation but not game-theoretic or strategy-based.
  - Gros, C. (2016). "Developing ecospheres on transiently habitable planets: the Genesis Project." *Astrophysics and Space Science*, 361(10), 324. DOI: [10.1007/s10509-016-2911-0](https://doi.org/10.1007/s10509-016-2911-0). About panspermia/terraforming, not deterrence.
- **Verified percolation papers adjacent to "dark forest" dynamics:**
  - Kinouchi, O. (2001). "Persistence solves Fermi Paradox but challenges SETI projects." arXiv:[cond-mat/0112137](https://arxiv.org/abs/cond-mat/0112137) (arXiv-only, no DOI).
  - Galera, E., Galanti, G.R. & Kinouchi, O. (2018). "Invasion percolation solves Fermi Paradox but challenges SETI projects." *International Journal of Astrobiology*, 18(4), 316–322. DOI: [10.1017/S1473550418000101](https://doi.org/10.1017/s1473550418000101).

**Difference from our approach:** None of the verified items implement discrete, named, per-agent interaction strategies with payoff consequences (random/aggressive/passive/anti-competitor/dark_forest/broadcaster/cooperative), nor explicit light-cone-causal attack/colonization mechanics tied to Great-Silence rejection criteria. They are population-level percolation/persistence lattice models, not strategy-driven agent decisions.

### 1.3 David Forgan's works on SETI and game theory

- Forgan, D.H. (2009). "A numerical testbed for hypotheses of extraterrestrial life and intelligence." *IJA*, 8(2), 121–131. DOI: [10.1017/S1473550408004321](https://doi.org/10.1017/s1473550408004321), arXiv:[0810.2222](https://arxiv.org/abs/0810.2222). *(Already known — confirmed, not elaborated.)*
- **Forgan, D.H. (2011).** "Spatio-temporal constraints on the zoo hypothesis, and the breakdown of total hegemony." *IJA*, 10(4), 341–347. DOI: [10.1017/S147355041100019X](https://doi.org/10.1017/S147355041100019X), arXiv:[1105.2497](https://arxiv.org/abs/1105.2497). Uses Monte Carlo Realization (MCR) to show that finite light-speed causal connectivity breaks "total hegemony" (Zoo Hypothesis) across the Galaxy. **Closest Forgan paper to our light-speed-causal-front logic**, but tests only one strategy (zoo/non-contact hegemony), not a multi-strategy decision space.
- **Forgan, D.H. & Rice, K. (2010).** "Numerical Testing of The Rare Earth Hypothesis using Monte Carlo Realisation Techniques." *IJA*, 9(2), 73–80. DOI: [10.1017/S1473550410000030](https://doi.org/10.1017/s1473550410000030), arXiv:[1001.1680](https://arxiv.org/abs/1001.1680). ⚠️ **Title correction:** uses "Monte Carlo Realisation Techniques," not "genetic algorithm" — no genetic-algorithm variant was found; verify your source if that specific method matters.
- **Forgan, D.H. (2016/2017).** "The Galactic Club, or Galactic Cliques? Exploring the limits of interstellar hegemony and the Zoo Hypothesis." *IJA*. DOI: [10.1017/S1473550416000392](https://doi.org/10.1017/S1473550416000392), arXiv:[1608.08770](https://arxiv.org/abs/1608.08770). Toy ABM-like model where civilizations form causally-connected "cliques" rather than one "Club" — the closest Forgan paper to multi-agent cultural-connectivity dynamics, still single-strategy (hegemony enforcement).
- Forgan, D.H. & Elvis, M. (2011). "Extrasolar asteroid mining as forensic evidence for extraterrestrial intelligence." *IJA*. DOI: [10.1017/S1473550411000127](https://doi.org/10.1017/S1473550411000127), arXiv:[1103.5369](https://arxiv.org/abs/1103.5369).
- Stevens, A., Forgan, D.H. & O'Malley-James, J. (2016). "Observational Signatures of Self-Destructive Civilisations." *IJA*, 15(4). DOI: [10.1017/S1473550415000397](https://doi.org/10.1017/S1473550415000397), arXiv:[1507.08530](https://arxiv.org/abs/1507.08530).
- Forgan, D.H. & Scholz, A. (2016). "#FoundThem - 21st Century Pre-Search and Post-Detection SETI Protocols for Social and Digital Media." *Acta Astronautica*. DOI: [10.1016/j.actaastro.2016.05.008](https://doi.org/10.1016/j.actaastro.2016.05.008), arXiv:[1605.02947](https://arxiv.org/abs/1605.02947).
- "Forgan — classify the galaxy by terraforming techniques": **NOT FOUND**, flag as unverified.

**Difference from our approach:** All Forgan papers use Monte Carlo Realisation (random draws over Drake-equation-like parameters, then pairwise causal-connectivity checks) — methodologically close to our causal-front logic — but Forgan's civilizations are passive statistical draws, not deciding agents choosing among named strategies with attack/tech-share payoffs.

### 1.4 Agent-based / Monte Carlo Fermi-paradox simulations, 2015–2026

- Cartin, D. (2014/2015). "Quantifying the Fermi paradox in the local Solar neighborhood," *JBIS*, 67, 119–126, arXiv:[1404.0204](https://arxiv.org/abs/1404.0204) (no DOI); and "Upper limits on the probability of an interstellar civilization arising in the local Solar neighborhood," *IJA*, DOI: [10.1017/S1473550415000105](https://doi.org/10.1017/s1473550415000105), arXiv:[1501.05904](https://arxiv.org/abs/1501.05904). Percolation using real 3D stellar positions within 40 pc. ⚠️ "Cartin 2020/2021" **not found** — his 2020s arXiv output is in loop quantum gravity, unrelated.
- Balbi, A. & Ćirković, M.M. (2021). "Longevity Is the Key Factor in the Search for Technosignatures." *AJ*, 161(5), 222. DOI: [10.3847/1538-3881/abec48](https://doi.org/10.3847/1538-3881/abec48) (cited by Hanson et al. 2021).
- Balbi, A. & Grimaldi, C. (2024). "Technosignatures longevity and Lindy's law." *AJ*, 167, 119. DOI: [10.3847/1538-3881/ad217d](https://doi.org/10.3847/1538-3881/ad217d), arXiv:[2405.00020](https://arxiv.org/abs/2405.00020).
- Grimaldi, C., Marcy, G.W., Tellis, N.K. & Drake, F. (2018). "Area Coverage of Expanding E.T. Signals in the Galaxy: SETI and Drake's N." *PASP*. DOI: [10.1088/1538-3873/aaac6a](https://doi.org/10.1088/1538-3873/aaac6a), arXiv:[1802.09399](https://arxiv.org/abs/1802.09399). ⚠️ "Balbi & Grimaldi 2021, relativistic civilizations" (exact title) **not found** — these are the verified closest substitutes.
- Hair, T.W. & Hedman, A.D. (2013). "Spatial dispersion of interstellar civilizations: a probabilistic site percolation model in three dimensions." *IJA*, 12(1), 45–52. DOI: [10.1017/s1473550412000420](https://doi.org/10.1017/s1473550412000420).
- Hair, T.W. (2011). "Temporal dispersion of the emergence of intelligence: an inter-arrival time analysis." *IJA*, 10(2), 131–135. DOI: [10.1017/s1473550411000024](https://doi.org/10.1017/s1473550411000024). ⚠️ "Hair 2011 'Does pessimism about colonization prospects solve Fermi's paradox?'" not found under that exact title — likely a misattribution of this paper.
- Wright, J.T. (2017/2018). "Exoplanets and SETI." In *Handbook of Exoplanets* (Springer), 3405–3412. DOI: [10.1007/978-3-319-55333-7_186](https://doi.org/10.1007/978-3-319-55333-7_186), arXiv:[1707.02175](https://arxiv.org/abs/1707.02175). ⚠️ Dated 2017/2018, not 2020 as sometimes cited.
- Carroll-Nellenback, J. et al. (2019) ("Aurora effect"), *AJ*, 158(3), 117. DOI: [10.3847/1538-3881/ab31a3](https://doi.org/10.3847/1538-3881/ab31a3), arXiv:[1902.04450](https://arxiv.org/abs/1902.04450). *(Already known — confirmed, not elaborated.)*

**Difference from our approach:** All are stochastic percolation/signal-coverage models on randomly drawn civilization parameters; none implement agent decision strategies, bilateral attack/tech-sharing interactions, or the full Great-Silence rejection taxonomy.

### 1.5 Galactic settlement percolation papers

- **Landis, G.A. (1998).** "The Fermi Paradox: An Approach Based on Percolation Theory." *JBIS*, 51, 163–166. No DOI (pre-CrossRef); verified via author's hosted copy: http://www.geoffreylandis.com/percolation.htp (originally presented at NASA Vision-21 Symposium, 1993). ⚠️ One subagent flagged this as independently unconfirmed via ADS/ResearchGate in a separate session (both blocked) — recommend a final check via a library database before citing, though the author-hosted copy is strong evidence of existence.
- **Newman, W.I. & Sagan, C. (1981).** "Galactic civilizations: Population dynamics and interstellar diffusion." *Icarus*, 46(3), 293–327. DOI: [10.1016/0019-1035(81)90135-4](https://doi.org/10.1016/0019-1035(81)90135-4).
- Hair, T.W. (2011) and Hair & Hedman (2013) — see §1.4.
- Kinouchi (2001) and Galera, Galanti & Kinouchi (2018) — see §1.2.

**Difference from our approach:** These are the closest classical precedents to our colonization-front mechanics, but use homogeneous lattices/mean-field diffusion with a single binary colonize/don't-colonize rule — no discrete interaction strategies, tech/population growth, or probe/signal/attack channels as distinct observables.

### 1.6 Grimm et al. ODD protocol

- Grimm, V., Berger, U., Bastiansen, F., et al. (2006). "A standard protocol for describing individual- and agent-based models." *Ecological Modelling*, 198(1–2), 115–126. DOI: [10.1016/j.ecolmodel.2006.04.023](https://doi.org/10.1016/j.ecolmodel.2006.04.023).
- Grimm, V., Berger, U., DeAngelis, D.L., Polhill, J.G., Giske, J. & Railsback, S.F. (2010). "The ODD protocol: A review and first update." *Ecological Modelling*, 221(23), 2760–2768. DOI: [10.1016/j.ecolmodel.2010.08.019](https://doi.org/10.1016/j.ecolmodel.2010.08.019).
- Grimm, V., Railsback, S.F., Vincenot, C.E., Berger, U., Gallagher, C., DeAngelis, D.L., et al. (2020). "The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update to Improve Clarity, Replication, and Structural Realism." *JASSS*, 23(2), 7. DOI: [10.18564/jasss.4259](https://doi.org/10.18564/jasss.4259).

**Relevance:** Documentation/methodology standards, not substantive ABM content — directly actionable for structuring the paper's model description (Overview, Design concepts, Details) to meet ODD 2.0/JASSS reporting norms. Notably, none of the Forgan/Cartin/Hair/Kinouchi papers above follow ODD-style structured reporting — adopting it is a methodological differentiator for our paper.

---

## 2. Observational constraints for grounding rejection criteria

### 2.1 SETI search completeness and sensitivity (grounds criteria c/e)

- **Enriquez, J.E. et al. (2017).** "The Breakthrough Listen Search for Intelligent Life: 1.1–1.9 GHz Observations of 692 Nearby Stars." *ApJ*, 849(2), 104. DOI: [10.3847/1538-4357/aa8d1b](https://doi.org/10.3847/1538-4357/aa8d1b), arXiv:[1709.03491](https://arxiv.org/abs/1709.03491). **692 stars**, Green Bank, L-band (1.1–1.9 GHz), zero candidates; limit: no systems with EIRP ≳ **10¹³ W** within 50 pc for <~0.1% of stellar systems.
- **Price, D.C. et al. (2020).** "The Breakthrough Listen Search for Intelligent Life: Observations of 1327 Nearby Stars Over 1.10–3.45 GHz." *AJ*, 159(3), 86. DOI: [10.3847/1538-3881/ab65f1](https://doi.org/10.3847/1538-3881/ab65f1), arXiv:[1906.07750](https://arxiv.org/abs/1906.07750). ⚠️ Actual coverage is 1.10–3.45 GHz (not 1.1–1.9 GHz, which is Enriquez 2017). **1138 stars** (GBT) + **189 stars** (Parkes) from a 1702-star list; zero candidates; EIRP limits ≤ **2×10¹² W** (GBT) / ≤ **9×10¹² W** (Parkes); ~219 TB released.
- **Wlodarczyk-Sroka, B.S., Garrett, M.A. & Siemion, A.P.V. (2020).** "Extending the Breakthrough Listen nearby star survey to other stellar objects in the field." *MNRAS*, 498(4), 5720–5729. DOI: [10.1093/mnras/staa2672](https://doi.org/10.1093/mnras/staa2672), arXiv:[2006.09756](https://arxiv.org/abs/2006.09756). Extends sample to **288,315 stellar objects** via Gaia DR2. Results: **≲0.066%** of systems within 50 pc host EIRP ≳ 10¹³ W transmitters; **≲0.039%** within 200 pc for EIRP ≳ 2.5×10¹⁴ W.
- **Gajjar, V. et al. (2021).** "The Breakthrough Listen Search For Intelligent Life Near the Galactic Center I." *AJ*. DOI: [10.3847/1538-3881/abfd36](https://doi.org/10.3847/1538-3881/abfd36), arXiv:[2104.14148](https://arxiv.org/abs/2104.14148). 600 h planned (0.7–93 GHz); preliminary 7.0 h (Parkes) + 11.2 h (GBT). EIRP limits: ≥**4×10¹⁸ W** across 1–4 GHz among ~60 million stars; ≥**5×10¹⁷ W** across 3.9–8 GHz among ~500,000 stars; also constrains one-off dispersed transients at EIRP ≥**1×10¹⁴ W/Hz** — directly relevant to criterion (e). *(Related: Margot, J.-L. et al. 2021, "A Search for Technosignatures around 31 Sun-like Stars...," AJ 161, 55, DOI: [10.3847/1538-3881/abcc77](https://doi.org/10.3847/1538-3881/abcc77) — UCLA SETI survey, comparable sensitivity.)*
- **Wright, J.T., Kanodia, S. & Lubar, E.G. (2018).** "How Much SETI Has Been Done? Finding Needles in the n-Dimensional Cosmic Haystack." *AJ*, 156(6), 260. DOI: [10.3847/1538-3881/aae099](https://doi.org/10.3847/1538-3881/aae099), arXiv:[1809.07252](https://arxiv.org/abs/1809.07252). 8-dimensional haystack framework; **quantitative conclusion (direct quote):** the fraction searched is "similar to the ratio of the volume of a large hot tub or small swimming pool to that of the Earth's oceans." Open-source Python tool provided — directly usable for quantifying criterion (c/e) search-completeness fractions.
- **Drake, F.D. (1961).** "Project Ozma." *Physics Today*, 14(4), 40–46. DOI: [10.1063/1.3057500](https://doi.org/10.1063/1.3057500). April 1960, 85-ft Tatel telescope, NRAO Green Bank; targets Tau Ceti & Epsilon Eridani; 21 cm (1420 MHz) line. ⚠️ The commonly cited "400 hours" figure is **unverified** — Drake's own account and NRAO historical summaries suggest ~150 hours; verify before using a specific number in the paper.

### 2.2 Searches for non-terrestrial artefacts/probes in the Solar System (grounds criterion d)

- **Freitas, R.A. Jr. (1983).** "The Search for Extraterrestrial Artifacts (SETA)." *JBIS*, 36, 501–506. No DOI (pre-DOI era); confirmed via two independent secondary reference lists (not a primary-source fetch).
- Freitas, R.A. Jr. (1983). "If they are here, where are they? Observational and search considerations." *Icarus*, 55, 337–343. DOI: [10.1016/0019-1035(83)90086-6](https://doi.org/10.1016/0019-1035(83)90086-6).
- Freitas, R.A. Jr. & Valdes, F. (1985). "The search for extraterrestrial artifacts (SETA)." *Acta Astronautica*, 12(12), 1027–1034. DOI: [10.1016/0094-5765(85)90031-1](https://doi.org/10.1016/0094-5765(85)90031-1) — a distinct, expanded follow-up to the 1983 JBIS piece.
- **Haqq-Misra, J. & Kopparapu, R.K. (2012).** "On the likelihood of non-terrestrial artifacts in the Solar System." *Acta Astronautica*, 72, 15–20. DOI: [10.1016/j.actaastro.2011.10.010](https://doi.org/10.1016/j.actaastro.2011.10.010). ⚠️ **Title correction:** the actual title is about artifacts in the Solar System, not "non-destructive extraterrestrial contact." Argues probe/artefact searches are tractable and cheap relative to radio SETI; cites Freitas 1983 and Hart 1975.
- **Benford, J. (2019).** "Looking for Lurkers: Co-orbiters as SETI Observables." *AJ*, 158(4), 150. DOI: [10.3847/1538-3881/ab3e35](https://doi.org/10.3847/1538-3881/ab3e35), arXiv:[1903.09582](https://arxiv.org/abs/1903.09582). Proposes ETI probes would plausibly be parked on Earth co-orbital objects (e.g. 2016 HO3) rather than conspicuous locations — directly relevant to designing a probability model for criterion (d).

### 2.3 Earth/Solar System non-colonization arguments ("Fact A")

- **Hart, M.H. (1975).** "An Explanation for the Absence of Extraterrestrials on Earth." *QJRAS*, 16, 128–135. No DOI; verified via NASA ADS bibcode 1975QJRAS..16..128H and two independent secondary-citation cross-checks. The classic "Fact A" paper. Reprinted in Zuckerman & Hart (eds.), *Extraterrestrials: Where Are They?* (2nd ed., CUP, 1995), pp. 1–8, DOI: [10.1017/CBO9780511564970.003](https://doi.org/10.1017/CBO9780511564970.003).
- **Tipler, F.J. (1980).** "Extraterrestrial Intelligent Beings Do Not Exist." *QJRAS*, 21, 267–281. No DOI; verified via ADS bibcode 1980QJRAS..21..267T. Popular-science version: Tipler, F.J. (1981), *Physics Today*, 34(4), DOI: [10.1063/1.2914542](https://doi.org/10.1063/1.2914542) (correction at DOI: [10.1063/1.2914555](https://doi.org/10.1063/1.2914555)). Argues von Neumann probes would already have colonized the Galaxy; non-detection ⇒ ETI doesn't exist.
- **Sagan, C. & Newman, W.I. (1983).** "The Solipsist Approach to Extraterrestrial Intelligence." *QJRAS*, 24, 113–121. No DOI; verified via ADS bibcode 1983QJRAS..24..113S. Direct critique of Tipler's argument — relevant balance citation for why "Fact A" alone should not be treated as decisive.

### 2.4 Anthropic / observer-selection caveats

- Ćirković, M.M. (2009) — already known, anchors the classification scheme.
- **Ćirković, M.M., Dragićević, I. & Berić-Bjedov, T. (2005).** "Adaptationism Fails to Resolve Fermi's Paradox." *Serbian Astronomical Journal*, 170, 89–100. DOI: [10.2298/saj0570089c](https://doi.org/10.2298/saj0570089c). ⚠️ Published **2005**, not 2007.
- Vukotić, B. & Ćirković, M.M. (2008). "Neocatastrophism and the Milky Way Astrobiological Landscape." *Serbian Astronomical Journal*, 176, 71–79. DOI: [10.2298/saj0876071v](https://doi.org/10.2298/saj0876071v). Connects Carter's anthropic argument and Fermi's paradox via cellular-automaton GHZ modeling.
- **Ćirković, M.M., Sandberg, A. & Bostrom, N. (2010).** "Anthropic Shadow: Observation Selection Effects and Human Extinction Risks." *Risk Analysis*, 30(10), 1495–1506. DOI: [10.1111/j.1539-6924.2010.01460.x](https://doi.org/10.1111/j.1539-6924.2010.01460.x). Shows observation selection systematically biases naive frequency estimates of civilization-ending events downward — directly relevant anthropic caveat for interpreting "no Great Filter event has hit us" as evidence.
- Bostrom, N. (2002). *Anthropic Bias: Observation Selection Effects in Science and Philosophy*. Routledge, ISBN 978-0-415-93858-7. Formal Self-Sampling/Self-Indication Assumption machinery underlying Fermi-paradox anthropic arguments. (Critical review: Ćirković, M.M. 2003, *Foundations of Science*, 8, 417–423, DOI: [10.1023/A:1026375105749](https://doi.org/10.1023/A:1026375105749).)
- Bostrom, N. (2008). "Where Are They? Why I Hope the Search for Extraterrestrial Life Finds Nothing." *MIT Technology Review*, May/June 2008. No DOI (magazine essay); full text at https://nickbostrom.com/papers/where-are-they/. Introduces the "Great Filter" concept with the explicit anthropic argument that finding ETI would be bad news.

**Flagged uncertainty across §2:** the Project Ozma "400 hours" duration figure; the exact page range/verbatim title of Hart 1975 and Tipler 1980 (verified by existence via ADS PDF retrieval, not full OCR); and the Haqq-Misra & Kopparapu title correction.

---

## 3. Candidate target journals

| Journal | Scope fit | Fermi/SETI precedent | OA model | APC (most recent) | ODD/code mandate |
|---|---|---|---|---|---|
| **IJA** (Cambridge) | Excellent | Forgan 2009; Galera et al. 2019; Ćirković & Balbi 2020; Haqq-Misra et al. 2018 | Fully Gold OA | ~$3,550 | Unconfirmed (pages blocked) |
| **Acta Astronautica** (Elsevier) | Good | Almár 1992; Forgan & Scholz 2016; Friconnet 2025 | Hybrid | ~$3,350 | Unconfirmed (403 on guide) |
| **Astrobiology** (SAGE, ex-Liebert) | Good | Gray 2015; Benford et al. 2010 | Hybrid | Unconfirmed | Unconfirmed (403) |
| **JASSS** | Weak domain fit, strong methods fit | **None found** (novel niche) | Fully free OA, CC-BY | Site states free; OpenAlex lists $1,300 (**conflict**) | **Explicitly NOT required** |
| **JBIS** | Excellent, historic | Freitas 1983 (no DOI); Landis 1998 (flagged); still active 2025–26 | Hybrid, transparent fee table | Gold £100 (£60 Fellows); Green free, 1-yr embargo | N/A |
| **MNRAS / ApJ / AJ** | Strong for quantitative core | Carroll-Nellenback 2019 (AJ); Hanson et al. 2021 (ApJ) | Fully OA since 2021 (ApJ/AJ) / 2023 (MNRAS) | ApJ/AJ $4,499; MNRAS ~$3,046 | Unconfirmed (403 on OUP) |

### 3.1 International Journal of Astrobiology (Cambridge University Press)
Scope explicitly includes SETI and societal aspects of astrobiology — the most direct topical fit of the six. Example papers: Forgan & Rice (2009) IJA 8(2), 121–131, DOI: [10.1017/S1473550408004321](https://doi.org/10.1017/s1473550408004321); Galera, Galanti & Kinouchi (2019) IJA 18(4), 316–322, DOI: [10.1017/S1473550418000101](https://doi.org/10.1017/s1473550418000101); Ćirković & Balbi (2020) IJA 19(2), 101–109, DOI: [10.1017/S1473550419000223](https://doi.org/10.1017/S1473550419000223); Haqq-Misra, Kopparapu & Wolf (2018) IJA 17(1), 77–86, DOI: [10.1017/S1473550417000118](https://doi.org/10.1017/S1473550417000118). Fully Gold OA; APC ≈ $3,550 (2025), may be waived under CUP Read & Publish agreements. Word limits/code-deposit requirements could not be confirmed live (pages 404'd/behind JS). Official Clarivate IF not retrieved (Scimago blocked); OpenAlex shows h-index 54.

### 3.2 Acta Astronautica (Elsevier/IAF)
Good fit, more engineering-oriented, long history with the interstellar-studies (Project Icarus) community shared with JBIS. Examples: Almár (1992) 26(3–4), 253–256, DOI: [10.1016/0094-5765(92)90107-T](https://doi.org/10.1016/0094-5765(92)90107-T); Forgan & Scholz (2016) 126, 312–315, DOI: [10.1016/j.actaastro.2016.05.008](https://doi.org/10.1016/j.actaastro.2016.05.008); Friconnet (2025) 226, 42–49, DOI: [10.1016/j.actaastro.2024.10.023](https://doi.org/10.1016/j.actaastro.2024.10.023) (confirms the journal still actively accepts Fermi-paradox papers as of 2025); Crawford (2011) 68(7–8), 691–699, DOI: [10.1016/j.actaastro.2010.10.016](https://doi.org/10.1016/j.actaastro.2010.10.016). Hybrid OA, APC ≈ $3,350 (2025). Author-guide pages returned 403 in all attempts — formatting/data-availability requirements unconfirmed.

### 3.3 Astrobiology (now published by SAGE; legacy Mary Ann Liebert imprint)
⚠️ Note: Crossref lists current publisher as SAGE (DOI prefix still `10.1089/ast.*`) — a transfer from Liebert that should be verified/dated before describing "NASA Astrobiology Institute ties." High-prestige dedicated venue. Examples: Gray (2015) 15(3), 195–199, DOI: [10.1089/ast.2014.1247](https://doi.org/10.1089/ast.2014.1247); Benford, Benford & Benford (2010) 10(5), 491–498, DOI: [10.1089/ast.2009.0394](https://doi.org/10.1089/ast.2009.0394) (companion: DOI: [10.1089/ast.2009.0393](https://doi.org/10.1089/ast.2009.0393)). Hybrid OA; APC unconfirmed (SAGE author pages behind Cloudflare wall).

### 3.4 Journal of Artificial Societies and Social Simulation (JASSS)
Methodology-first, not domain-first — scope emphasizes social-process simulation. A targeted Crossref/table-of-contents search found **no prior JASSS paper on the Fermi paradox, SETI, or galactic civilizations** — a novelty opportunity but also a scope-fit risk requiring strong methodological framing (e.g., evolutionary game theory of strategies). Confirmed directly from JASSS's own submission page:
- Length: 5,000–8,000 words, abstract ≤300 words, ≤6 keywords.
- **ODD protocol explicitly NOT required** ("recommended... although use of this protocol is not a requirement," citing Grimm et al. 2006 and Polhill et al. 2008, JASSS 11(2):3).
- Code/model sharing strongly encouraged (CoMSES Net Computational Model Library) but not mandatory.
- Double-blind review, ~3 referees, ~8-week decisions; Word or LaTeX (Overleaf template available); preprinting on arXiv/SSRN permitted.
- Fully open access, CC-BY 4.0, historically free. ⚠️ **Conflict**: OpenAlex/DOAJ list an APC of $1,300, contradicting JASSS's own no-fee submission page — verify directly with jasss@surrey.ac.uk before assuming either figure.

### 3.5 Journal of the British Interplanetary Society (JBIS)
Historically the most important niche venue for exactly this topic. Freitas (1983), "Extraterrestrial intelligence in the solar system — resolving the Fermi Paradox," JBIS 36, 496 (no DOI, cited via Almár 1992); Landis (1998) JBIS 51(5), 163–166 (⚠️ existence well-established in the literature but not independently re-verified via live web fetch in this session — recommend a final ADS/library check). Confirmed still active on this topic: Zhang (2026) JBIS 79(2), 70, DOI: [10.59332/jbis-079-02-0070](https://doi.org/10.59332/jbis-079-02-0070); Swinney et al. (2025) JBIS 78(5), 143–154, DOI: [10.59332/jbis-078-05-0143](https://doi.org/10.59332/jbis-078-05-0143). Submission: ~5,000–6,000 words, bracketed references, submitted as Word+PDF by email. Hybrid OA with a transparent fee table: Gold (CC-BY-NC) £100 (£60 BIS Fellows); Green free but with a 1-year embargo. Not JCR-indexed (no official impact factor); low OpenAlex 2-yr citedness (0.34).

### 3.6 MNRAS and ApJ/AJ (mainstream astronomy)
Appropriate for the quantitative/dynamical core if framed as astrophysics rather than pure social-science ABM — exactly how the two benchmark papers were framed:
- Carroll-Nellenback et al. (2019), confirmed published in **AJ** (not ApJ/MNRAS): 158(3), 117, DOI: [10.3847/1538-3881/ab31a3](https://doi.org/10.3847/1538-3881/ab31a3).
- Hanson et al. (2021), confirmed published in **ApJ**: 922(2), 182, DOI: [10.3847/1538-4357/ac2369](https://doi.org/10.3847/1538-4357/ac2369).
AAS journals use AASTeX v7.0, abstracts <250 words, a "digital quanta" publication-charge system; both ApJ and AJ are now **fully Open Access since 2021** (APC ≈ $4,499 flat, per OpenAlex). **MNRAS flipped to fully Open Access in 2023** (APC ≈ £2,310/$3,046). arXiv (astro-ph) simultaneous posting is near-universal community practice, though exact embargo/licensing text could not be re-confirmed live (OUP pages returned 403).

### Overall assessment
- **Best scope fit + precedent:** IJA (strongest direct Fermi-paradox/SETI publication history) and JBIS (historic home of percolation/SETA literature, cheapest Gold OA route).
- **Best for the quantitative/dynamical-modeling framing:** AJ or ApJ, following the Carroll-Nellenback (2019, AJ) and Hanson et al. (2021, ApJ) precedents — but at a much higher APC ($4,499) now that both are mandatory-OA.
- **Methodologically interesting but scope-risky:** JASSS — zero prior Fermi-paradox papers found, free/CC-BY publishing, and the ODD protocol is explicitly optional rather than mandatory there (contrary to a common assumption) — still worth adopting for rigor regardless of venue.
- **Key open item:** several publisher author-guideline pages (Cambridge/IJA, Elsevier/Acta Astronautica, SAGE/Astrobiology, OUP/MNRAS) returned HTTP 403 in every fetch attempt in this session and should be checked directly (or via institutional access) before final submission-requirement decisions.

---

## Consolidated list of flagged / unverified items (do not cite without independent confirmation)

1. "Yu 2015" Dark Forest game-theory paper — not found.
2. Yan (2025) arXiv:2509.02625 "Recursive Panopticon Hypothesis" — withdrawn, unreliable.
3. "Gros 2019" aliens/universal-subroutine paper — not found under that title (Gros 2005, 2016 substituted).
4. Forgan & Rice "genetic algorithm" Rare Earth paper — actual method is "Monte Carlo Realisation Techniques."
5. Forgan "classify the galaxy by terraforming techniques" — not found.
6. "Cartin 2020/2021" Fermi-paradox papers — not found (2014/2015 Cartin papers substituted).
7. "Balbi & Grimaldi 2021, relativistic civilizations" (exact title) — not found; related technosignature-longevity papers substituted.
8. "Hair 2011 'Does pessimism...'" — not found under that exact title.
9. Wright "Exoplanets and SETI" — dated 2017/2018, not 2020.
10. Project Ozma "400 hours" — likely should be ~150 hours; verify against primary NRAO sources.
11. Landis (1998) JBIS percolation paper — existence well-established in the secondary literature, author-hosted copy found, but not independently re-verified via ADS/Crossref in this session.
12. Hart 1975 / Tipler 1980 / Sagan & Newman 1983 — confirmed to exist via direct ADS PDF retrieval (bibcode-watermarked), but exact verbatim titles/pages not independently OCR-confirmed beyond secondary citations.
13. Haqq-Misra & Kopparapu — correct title is "On the likelihood of non-terrestrial artifacts in the Solar System," not "non-destructive extraterrestrial contact."
14. Astrobiology journal's current publisher (SAGE vs. legacy Liebert) and its APC — transfer date and fee unconfirmed.
15. JASSS APC — direct conflict between the journal's own free-OA submission page and OpenAlex/DOAJ's $1,300 figure; needs direct email confirmation.
16. No official Clarivate Journal Impact Factor was retrieved for any of the six candidate journals (Scimago/JCR pages were blocked); only OpenAlex proxies are reported.
17. IJA, Acta Astronautica, Astrobiology (SAGE), and MNRAS/OUP author-guideline pages were inaccessible (HTTP 403) in this research session — word limits, mandatory data/code statements, and exact embargo terms should be reconfirmed directly with each publisher before submission.
