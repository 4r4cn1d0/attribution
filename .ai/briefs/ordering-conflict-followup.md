# Bounded follow-up to the read-only first pass

- Task ID and authorized outcome: ordering-conflict-followup; resolve the lead's two remaining objections to the first-pass analysis. This is read-only and does not authorize another experiment or implementation.
- Role: response to GPT questions and mathematical challenge.
- Model: claude-opus-5-5; effort: max.
- Previous run: `tmp/claude-handoffs/20260924T184537Z-1c8f800e`. Its report is available at `report.md` in that directory; this brief supplies the relevant new evidence below rather than assuming resumed conversational memory.
- Context supplied and input versions/hashes: the first-pass report, `research/pilot/ORDERING_CONFLICT.md`, `tmp/ordering-conflict/check_permuted_cdf.py`, `tmp/ordering-conflict/receipt.json`, and unchanged v1 raw records. The first-pass brief accidentally omitted nine characters from the B1 raw record's SHA256. GPT re-ran shasum: the full B1 SHA256 is `50a4294be16ac1d8ecedefab96b31723629278002f307280fb1d8e512f976cc0`; A2 remains `c340c0f6e5b05e7b36d4a98126294c14d7d5c090a3309883f74058f52555a2c2`. The archived first-pass request/brief retain the typo; the source brief was corrected after that run.
- Owned files and workspace: none; review mode, no edits.
- Excluded files and concurrent contributors: GPT lead owns the handoff and note. Do not edit files or launch Claude/Codex/agents.
- Deliverable and measurable acceptance criteria: answer the two questions below concisely; distinguish derived fact, checked measurement, hypothesis, and prospective plan. If a proof cannot be supplied, narrow the claim.
- Alternatives to consider: leave the K=3 statement as a 656-cell numerical observation; exact enumeration; a prospective cheap order selector rather than a general learned transport solver.
- Invariants and smallest decisive check: same one-occurrence suppression estimand and conditional marginals; no hindsight-selected order may be presented as a deployable rule. No new compute/training.
- Permitted execution commands: none; read-only tools only.
- Claude time/turn limits: none, per user instruction.
- Combined concurrency and scientific compute budget: one read-only Opus call; no scientific compute.

You are a worker, not the lead. Preserve all files and return a response only.

## GPT's questions

1. Your first-pass report says that with K=3, *every* optimal transportation plan at any decision node can be represented by a common-uniform CDF coupling with independently chosen action orders. GPT's script finds this numerically in all 656 nondegenerate H=2 records; a non-author GPT reviewer independently reproduced it, but neither is a universal proof. Give a short self-contained proof of the universal K=3 statement, including degenerate optimal faces, or retract it as unproved. Which assumption is weakest, what counterexample would break it, and what check settles the disagreement?
2. The user now asks for the **best-case scenario** for this project. Keeping the original intervention, what is the simplest plausible prospective online selector of the two action orders that could turn the witness into a useful method? Specify the information it would use *before* random draws, what it would cost, and the counterexample likely to make it fail. Explain why the post hoc median/entropy observations in your first pass are insufficient. Could a simpler existing hybrid still match it on fresh cases?

## Return

Concise answers with evidence boundaries. Report files read and any claim not independently verified. Do not claim effective model effort or test success beyond observed evidence.
