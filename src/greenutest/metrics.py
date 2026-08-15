from __future__ import annotations

def brier_score(p,y):
    if len(p)!=len(y) or not p: raise ValueError("equal-length non-empty inputs required")
    return sum((a-b)**2 for a,b in zip(p,y))/len(y)

def expected_calibration_error(p,y,bins=10):
    if len(p)!=len(y) or not p: raise ValueError("equal-length non-empty inputs required")
    n=len(y); total=0.
    for b in range(bins):
        lo,hi=b/bins,(b+1)/bins; idx=[i for i,a in enumerate(p) if lo<=a<hi or (b==bins-1 and a==1.)]
        if idx:
            conf=sum(p[i] for i in idx)/len(idx); acc=sum(y[i] for i in idx)/len(idx); total+=len(idx)/n*abs(conf-acc)
    return total

def wh_from_joules(j): return j/3600.
def quality_per_kj(q,j): return None if j<=0 else q/(j/1000.)
