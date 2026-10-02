# Stage B non-author review, 2 October 2026

Reviewer /root/minimal_date_audit, shared context, read-only. Active author
snapshot, not final clearance; no code/tests executed by reviewer. Root owns
TF-IDF/ridge inspection separately. Follow-up required after fixes.

P1: outcomes.py conflates operational Unsafe flags/unique-argmax accuracy with
broader completion/ambiguity/tie intervals and drops raw diagnostic counts in
Evaluation.to_json. Root accepted the explicit pre-heldout outcome-definition
amendment; retain broader sensitivity and empty/repetition/censor counts.
Example development a0 q: old conservative interval[18/72,30/72], emitted-text
Unsafe with one invalid unresolved[22/72,23/72]. Neither is human harm or safety
of unrestricted continuation.

P2: controller.execute unexpected exceptions retain default status=refused;
receipts ignores them for spend and retry max. A relevance computation followed
by failed write is charged zero and can repeat indefinitely. Once execution
begins, exceptions must be timed failed attempts, preserve error, count against
same-seed retry bound. Only explicit validation refusals before any work can be
exempt.

P2: verify_study skips missing choice lock despite final-* artifacts; backend
checks only arbitrary lock file hash. Require matching config/block/seed/both
choices and authorized final arms for every fresh or reused hidden access and
archived final operation. Normal run_block ordering already locks both choices
before finals.

Reporting: final-operation quotes omitted from overruns map, so final overruns
are missing although costs included. Add their quotes and regression.

No additional defect found in reviewed acquisition arithmetic: final reserve,
charged attribution prerequisites, per-policy a0 reuse, all12edits/fresh repeats,
and selector/final seed separation. Development input/output and controller hooks
only reviewed; not blanket certification.

Snapshot SHA256:
policy.py ff84bb73cad69067acffd8e50bb2de3c85d2529465d2d1f66391b470d058e71d
costs.py 4c3320b6fe6664e16065eba348a82443d2217ce612b1ab197a3f6f81bc1749ea
outcomes.py 22253be9c1dc1cb3db7ccb8d1aace155a071f2b18b790c4fe8fa2f9289acbfa9
config.py 4f5d828cef38d9e2fa6cd7b1afa8a741e0d77e1dfb5261136d733a77a07f5ee5
backend.py a50c0e0f3473e275039b0b5f4c662ec3c29aaf14eee4c1ca889134c853025d95
development.py 8eb39d986308678f7e5ed232836fc25f59977eb29ef83b142cb17df7a5634ded
controller.py 646b7c96d529247816b6f523b0ac85c747987393e682967d77bddb685623c391
