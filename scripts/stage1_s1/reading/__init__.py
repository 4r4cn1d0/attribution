"""B16: the stage-1 confirmatory reading (REV3 sections 3, 4, 5.3, 6.4-6.7; AMD sections A, B, D, E, F).

It turns text-free numeric tables (per arm x seed x item the U, O and L values, and the sealed design) into
the pre-registered estimates, tests, labels and headline words. numpy and the standard library only. No draw,
no network, no file written by the package itself except through ``__main__``.

Modules (each names the rule it implements):
- ``settings``   the pinned settings (SHA-256 literal), the sealed designs and the constants;
- ``schema``     the one input schema; anything else is refused;
- ``tdist``      Student t tail, quantile and Welch df (regularized incomplete beta);
- ``reml``       HB-C / HB: REML by Fisher scoring on log sigma^2, floors, the stop rule, the information matrix,
                 the two-arm cluster (REV3 3.2, 3.5; AMD A.3);
- ``contrast``   the estimator, seed part, crossed item part, Satterthwaite df, p-values and intervals, and the
                 LN-20 forms for theta0 and cross-cluster pairs (REV3 3.1-3.2, 3.6; AMD A.2-A.5, A.8);
- ``phi``        the graphical family Phi, IUT nodes, local levels, the update, Holm (REV3 4.1-4.3; AMD B.2-B.3);
- ``labels``     equivalence grades, feasibility states, the label row, the headline word, coherence flags,
                 the per-actor separation rule (REV3 3.7, 4.5-4.6, 4.9, 6.4; AMD B.5, F);
- ``sensitivities`` HB, S-a, S-aW, S-b2x, S-0, S-G, S-tok, S-A8, S-p (REV3 3.4);
- ``references`` "m beats r", the adapter-scaling curve matched on L, dominance (family 1b), the 3-seed fallback
                 (REV3 5.3; AMD D.1-D.4);
- ``reading``    the whole reading, one call: ``read(doc)``.
"""
