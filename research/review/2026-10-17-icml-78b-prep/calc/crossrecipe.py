# $0 check (I): same-seed pairs ACROSS recipes (shared init, data order and sampling seeds) vs unpaired SD; per-seed E (SIDE; FOCUS).
import math
def sd(v):
    m=sum(v)/len(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
pairs={
 'OLMo-1B B vs G (seeds 1101-1103)':([43.5,43.7,48.2],[29.0,31.0,26.5]),
 'OLMo-7B B 1e-4 vs B 5e-5':([49.67,37.17,45.50],[33.5,30.8,31.5]),
 'OLMo-7B B 1e-4 vs G':([49.67,37.17,45.50],[51.0,58.0,41.8]),
 'Llama-8B B 1e-4 vs G':([70.2,55.8,56.2],[60.2,61.8,55.5]),
 'Llama-1B B 1e-4 vs G (Constant vs Scheduled)':([62.5,61.3,54.0],[60.0,56.5,54.8]),
}
for k,(a,b) in pairs.items():
    d=[x-y for x,y in zip(a,b)]
    un=math.sqrt(sd(a)**2+sd(b)**2)
    print(f"{k}: SD(paired diff) {sd(d):.2f} vs unpaired {un:.2f} -> ratio {sd(d)/un:.2f}")
a0=[280/6,281/6,308/6]; R=[46.0,44+1/3,47.0]
d=[x-y for x,y in zip(a0,R)]
print(f"OLMo-1B a0 vs R (Gate B wave 0a): SD(r) {sd(d):.2f} vs unpaired {math.sqrt(sd(a0)**2+sd(R)**2):.2f} -> ratio {sd(d)/math.sqrt(sd(a0)**2+sd(R)**2):.2f}")
