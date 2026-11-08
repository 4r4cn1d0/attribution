# Erratum 1 to `k6-fix.md` (round 6's kit fix report): the seed evidence for K5v-9

Recorded 2026-11-08T14:36 UTC by General Implementation XI, the main-study lead (GXB O10: K6v-5 is the lead's step).
The committed report `k6-fix.md` is not edited; this file corrects one evidence line in it.

- **What is wrong.** `k6-fix.md`'s M #8 says that seeds 868 and 1027 give a collision of the old free-space test's
  folder names (K5v-9). That sweep ran Python with `-I` (R: `k6-fix.md:192`). `-I` implies `-E`, so Python ignores
  `PYTHONHASHSEED`, and the sweep's seeds were random draws, not the seeds named (R: `k6-verify.md:91-98`, its M #7).
  The same holds for `k5-verify.md:201`'s five-seed list.
- **What is right.** Measured without `-I` (R: `k6-verify.md` M #8, line 180): over seeds 0-1499 the old names collide
  at exactly 4 seeds: 54, 289, 772 and 1289. The old test fails at all 4 and the fixed test passes at all 4 (R:
  `k6-verify.md:167`, :181; its M #9, #10). Only seed 54 of `k6-fix.md`'s three checks was a real collision.
- **What does not change.** The fix itself (the test names its worlds `w-{i}`; R: `k6-verify.md:99`) is right and stays
  merged at `63b57c0`. No kit file, test result or mutant count changes.
