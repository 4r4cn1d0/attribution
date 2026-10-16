# Variance-ratio check (I): OLMo-7B a0 SD 6.36 (2 df) against Llama-8B a0 SD 1.06 (1 df).
from scipy.stats import f
x=(6.36/1.06)**2
print(round(x,1), 'one-sided p', round(f.sf(x,2,1),3), 'two-sided', round(2*min(f.sf(x,2,1), f.cdf(x,2,1)),3))
