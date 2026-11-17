# Archived specs

Region-size tests of 2026-11-17, run before the galactic habitable annulus (they use the former
parameters expected_bubbles, civ_birth_rate and crop_radius_pc):

- size_r500/1000/2000/4000: one galaxy drawn per size (commit 4195e0c, code at 5413bca);
- nested_r4000_c1000/c2000/full: one 4 kpc galaxy cropped to 1 kpc, 2 kpc or kept whole (code at 6f59540).

Rerun them at those commits. Analysis: python/analyze_region_size.py.
