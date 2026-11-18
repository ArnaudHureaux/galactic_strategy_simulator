# Region-size convergence (nested galaxies), 2026-11-17

Code: commit 6f59540 (before the habitable annulus). Specs: python/specs/archive/nested_r4000_*.json
(150 points of lhs25 with expected_bubbles and civ_birth_rate scaled by 16 for a 4 kpc galaxy).
Runs: explore.py, Rust engine, 1 seed per point; crops at 1 and 2 kpc with a 900 s wall budget,
whole 4 kpc galaxy with 3600 s (4 runs stopped at ~11 900 s: the budget is checked between steps).
Raw results: explorations/nested_r4000_* (not versioned). Report: python analyze_region_size.py
(reach_cfg needs the code of 6f59540).

Points: 150 cropped to 1 and 2 kpc; 44 run whole at 4 kpc (29 silent at 1 or 2 kpc, 15 random controls).

## Outcomes

| size | consistent | colonized | attacked | contact_share | artefact | signal_in_window | timeout |
|---|---|---|---|---|---|---|---|
| c1000 | 28 | 99 | 8 | 11 | 1 | 1 | 2 |
| c2000 | 15 | 91 | 5 | 9 | 1 | 1 | 28 |
| full | 3 | 21 | 0 | 1 | 1 | 1 | 17 |

## Transitions of the points silent at the smaller size

- silent at c1000 (28) -> c2000: consistent 14, colonized 7, timeout 4, attacked 2, contact_share 1
- silent at c1000 (28) -> full: colonized 13, timeout 10, consistent 3, signal_in_window 1, contact_share 1
- silent at c2000 (15) -> full: colonized 6, timeout 5, consistent 3, signal_in_window 1
- not silent at c1000 but silent whole: 0 []

## Who breaks the silence (nearest covering civ, pc)

- c1000: n=99, quantiles 15.8 / 201 / 379 / 595 / 1.23e+03, beyond 1 kpc 1, beyond 2 kpc 0
- c2000: n=91, quantiles 15.8 / 201 / 408 / 604 / 1.9e+03, beyond 1 kpc 8, beyond 2 kpc 0
- full: n=21, quantiles 86.2 / 328 / 595 / 732 / 1.31e+03, beyond 1 kpc 3, beyond 2 kpc 0

## Criteria

Silence lost = silent at 1 kpc, rejected at a larger size of the same galaxy (2 kpc or whole).
Kept = silent at 1 kpc and silent at every larger size run. Timeouts are left out.

| criterion | lost (quantiles) | kept (quantiles) | not silent at 1 kpc (quantiles) |
|---|---|---|---|
| density (civs/kpc^2) | 2.49 / 5.42 / 8.84 / 17.7 / 41 | 2.29 / 2.29 / 3.09 / 3.09 / 12 | 2.11 / 11.8 / 23.8 / 36.3 / 117 |
| reach_obs (pc) | 0 / 0 / 1.15e+03 / 1.53e+03 / 1.18e+05 | 0 / 0 / 0 / 0 / 0 | 0 / 547 / 977 / 1.7e+03 / 9.18e+06 |

lost 16: [76, 81, 90, 101, 107, 115, 116, 117, 118, 122, 123, 130, 133, 134, 137, 147]
kept 3: [22, 37, 68]

## Points silent at 1 kpc

| point | c1000 | c2000 | full | density | reach_obs | reach_cfg | culprit (pc) |
|---|---|---|---|---|---|---|---|
| 1 | consistent | consistent | timeout | 15.4 | 0 | nan | 279 |
| 3 | consistent | timeout | timeout | 57 | 0 | nan | - |
| 16 | consistent | timeout | timeout | 8.24 | 243 | nan | 271 |
| 18 | consistent | consistent | timeout | 19.4 | 0 | nan | 797 |
| 22 | consistent | consistent | consistent | 3.09 | 0 | nan | - |
| 30 | consistent | timeout | timeout | 18.4 | 34 | nan | - |
| 37 | consistent | consistent | consistent | 12 | 0 | nan | - |
| 38 | consistent | consistent | timeout | 8.94 | 0 | nan | 610 |
| 55 | consistent | timeout | timeout | 7.89 | 957 | nan | 843 |
| 68 | consistent | consistent | consistent | 2.29 | 0 | nan | - |
| 76 | consistent | colonized | colonized | 23 | 1327 | nan | 949 |
| 81 | consistent | colonized | colonized | 41 | 1964 | nan | 732 |
| 89 | consistent | consistent | timeout | 7.9 | 175 | nan | - |
| 90 | consistent | consistent | colonized | 12.2 | 0 | nan | 779 |
| 101 | consistent | consistent | colonized | 6.47 | 0 | nan | 590 |
| 104 | consistent | consistent | timeout | 12.5 | 0 | nan | 471 |
| 107 | consistent | attacked | timeout | 12.7 | 1526 | nan | 332 |
| 115 | consistent | colonized | colonized | 23.5 | 1444 | nan | 290 |
| 116 | consistent | colonized | colonized | 8.28 | 2581 | nan | 685 |
| 117 | consistent | consistent | signal_in_window | 12.6 | 67 | nan | 603 |
| 118 | consistent | colonized | colonized | 7.5 | 1719 | nan | 595 |
| 122 | consistent | consistent | colonized | 17.7 | 0 | nan | 310 |
| 123 | consistent | consistent | colonized | 8.84 | 0 | nan | 1255 |
| 130 | consistent | consistent | colonized | 2.72 | 0 | nan | 710 |
| 133 | consistent | colonized | colonized | 23 | 1146 | nan | 328 |
| 134 | consistent | attacked | colonized | 2.49 | 117803 | nan | 1092 |
| 137 | consistent | colonized | colonized | 5.35 | 1310 | nan | 1310 |
| 147 | consistent | contact_share | contact_share | 5.42 | 576 | nan | 332 |
