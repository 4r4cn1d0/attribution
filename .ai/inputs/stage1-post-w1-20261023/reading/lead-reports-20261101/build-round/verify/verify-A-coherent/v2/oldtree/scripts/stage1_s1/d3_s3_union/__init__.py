"""Post-W1 deviation D-3 (addendum section 28): S3's scorer (REQ-11) on the union of J5's two passes.

``d3_s3_union.py`` checks J5's main pass (plant, decoy, s3_safe and the dev units) and its pools-only pass (s3_orig)
by SHA-256, writes their union (the main pass's s3_safe rows, then the pools-only pass's s3_orig rows, each unchanged)
and a union summary, then runs the W1 file ``scripts/stage1/score_s3_datarx.py``, loaded by path after its SHA-256
check against the W1 manifest, unchanged on the union. Every W1 file stays byte-identical.
"""
