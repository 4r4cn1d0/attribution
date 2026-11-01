# Operating characteristics of the blinded 7-8B seed rule on the paired scale (I): sigma-hat^2*df/sigma^2 ~ chi2(df).
from scipy.stats import chi2
cA=4.2233; cB9=5.5634
print("true sigma_pair | df | P(plan A) | P(plan B9) | P(high-sigma branch)")
for df in (4,2):
    for s in (2.5,3.0,3.5,4.0,4.5,5.0,6.0,8.24):
        pA=chi2.cdf(df*cA**2/s**2,df); pB=chi2.cdf(df*cB9**2/s**2,df)-pA
        print(f"{s:5.2f} | {df} | {pA*100:5.1f}% | {pB*100:5.1f}% | {(1-pA-pB)*100:5.1f}%")
# unpaired scale: with the a0 cells in hand (OLMo 3 seeds SD 6.36; Llama 2 seeds SD 1.06): SS = 2*6.36^2 + 1*1.06^2
ss0=2*6.36**2+1*1.06**2
for cthr,name in ((3.193,'A'),(4.205,'B9'),(4.856,'B12')):
    # with R arms adding 4 df (both families) and Llama a0-1103 adding 1 df: total df 3+4+1 = 8
    need=cthr**2*8-ss0
    print(f"unpaired rule, design {name}: pooled SD <= {cthr} needs the new 5 df to add SS <= {need:.1f} (SD of new terms <= {max(need,0)**0.5/5**0.5:.2f} pp)")
