# Initial diagnostic replication: non-author recommendation

2 October 2026. GPT /root/minimal_date_audit, read-only with shared context;
no heldout outcomes. Lead records the recommendation, not a frozen N or empirical
variance estimate. Current development is13arms×2seeds under the fixed StageA recipe.

Two development seeds do not estimate complete-policy-block variance reliably.
Development measures throughput, observed endpoint spread, within-arm differences,
classifier failures and some selector instability. Cross-arm observed ranges do
not bound outcomes at unseen seeds; repeated replays of the same pool do not add
independent disagreement trials. The example Y=0 with probability.95 and
Y=±.4 with total probability.05 has SD about.089 and a90% chance of two zeros.
This is a counterexample to zero-variance planning, not a forecast.

Use explicit normal-theory scenarios, with r=max_j sigma_j/h_j and
N(r)=min{n: t_(1-.05/12,n-1)*r/sqrt(n)<=1}; six-endpoint family includes
T=Cplus-1.10Cminus, not the unadjusted cost difference. Use the larger lower/upper
measurement-series SD where applicable. Recommended conservative rounded scenarios:

| r | Safety SD | Each utility/refusal SD | SD(T/B) | N |
|---|---:|---:|---:|---:|
|1|.05|.02|.10|12|
|2|.10|.04|.20|35|
|3|.15|.06|.30|70|
|4|.20|.08|.40|120|

These are assumptions, not estimated effects, guaranteed precision or power.
Sparse disagreement/mixtures can undermine small-sample t coverage. After actual
development, describe how observed quantities compare and stress for unseen
variation. Select and freeze a defensible scenario, workload estimate, seed schedule
and same-seed failure rule before hidden outcomes. If no empirical envelope is
justified, identify the selection as an investigator planning assumption. Never
add blocks because an interval nearly excludes zero; report missed precision and
use a separately planned study for more evidence.

Economic endpoint variance is Var(Cplus)+1.21Var(Cminus)-2.20Cov(Cplus,Cminus).
Use selection-plus-one-freshly-trained-and-audited-chosen-model costs and show the
one-off margin adding Dplus-1.10Dminus. Both scopes must be acceptable for the
stronger economic interpretation. Unresolved costs cannot pass. Walltime is
unbounded; intervals are model-dependent and need jitter sensitivity.

All scheduled blocks remain in the analysis. Same-seed retries bounded, no fresh
replacement draws until N successes; missing outcomes retain worst-case bounds
and incurred/unknown timing. Family Hoeffding widths5pp and2pp for[-1,1]
contrasts need roughly4400/27400blocks: report this conservative sensitivity,
not as a practical demand. More prompts do not replace independent blocks;
persistent measurement ambiguity does not shrink with N. Initial diagnostic
cannot promise to resolve2pp safety benefit or boundary feasibility.
