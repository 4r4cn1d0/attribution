"""Copy only pure numerical functions, preserving their original formulas."""
from pathlib import Path
import shutil
import ast,json
M=Path('/Users/spiderishi/Coding/attribution');W=M/'.claude/worktrees/peaceful-jepsen-8b8eee';S=M/'tmp/side-paper-continuation-20261012';OUT=S/'numerical-package/analysis'
def functions(path,names):
 text=path.read_text();tree=ast.parse(text);parts=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef) and node.name in names:parts.append(ast.get_source_segment(text,node))
 assert len(parts)==len(names),(path,names,len(parts));return '\n\n'.join(parts)
welch=W/'research/side-notes/scripts/interaction_test_20261011.py'
(OUT/'welch_math.py').write_text('"""Original registered Welch/logit arithmetic, copied without dataset access."""\nimport math,statistics\nCELLS=("olmo_constant","olmo_scheduled","llama_constant","llama_scheduled")\n\n'+functions(welch,{'t_quantile','welch_contrast','test'})+'\n')
fiction=W/'research/side-fiction/analysis/analyze_fiction.py'
prefix='''"""Original registered pooled-t fiction arithmetic; data loading omitted."""
import math
from fractions import Fraction
DOLLY_DIFFERS="fiction differs from Dolly ({})"
LABEL_NAMES={"content":{"both":"content matters, smaller than m","matters":"content matters","within":"no difference larger than m","none":"inconclusive"},"fiction_minus_dolly":{"both":"fiction differs from Dolly, smaller than m","matters":DOLLY_DIFFERS,"within":"no difference from Dolly larger than m","none":"inconclusive"}}
'''
(OUT/'fiction_math.py').write_text(prefix+'\n'+functions(fiction,{'mean','t_cdf','t_quantile','excludes_zero','inside_margin','pooled_t','outcome_of','label_of'})+'\n')
legacy=W/'writing/side-notes/arxiv/release/release_files/analysis/recompute.py'
(OUT/'auxiliary_math.py').write_text('"""Original numerical helpers for binomial intervals, kappa and opening decomposition."""\nimport math\nfrom collections import OrderedDict\n\n'+functions(legacy,{'_betacf','betainc','t_cdf','t_ppf','binom_cdf','clopper_pearson','cohen_kappa','decompose','blind_scores'})+'\n')
shutil.copyfile(S/'recompute.py',OUT/'recompute.py')
print('copied original pure arithmetic modules')
