"""Post-W1 deviation D-1 (addendum section 18): REQ-6 with the S3 subset size k instead of 1,000.

``d1_s_pool.py`` loads the W1 file ``scripts/stage1/build_s_pool.py`` by path after its SHA-256 check (against the W1
manifest's entry and this package's pinned settings) and runs its build() with two module functions replaced for that
call: the S3 subset size rule (``lists_of``) and the stop (``check_sizes``). Every W1 file stays byte-identical.
"""
