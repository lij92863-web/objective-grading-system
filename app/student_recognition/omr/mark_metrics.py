from dataclasses import dataclass
from .omr_policy import DEFAULT_OMR_POLICY,OMRPolicy
from .cell_preprocessor import binary_mask
@dataclass(frozen=True)
class MarkMetrics:
    option:str; dark_ratio:float; center_density:float; largest_component_ratio:float; border_noise:float; fill_uniformity:float; erasure_score:float; mark_score:float; classification:str

def _largest(mask,w,h):
    seen=set(); best=0
    for i,on in enumerate(mask):
        if not on or i in seen: continue
        stack=[i];seen.add(i);size=0
        while stack:
            j=stack.pop();size+=1;x=j%w;y=j//w
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                k=ny*w+nx
                if 0<=nx<w and 0<=ny<h and mask[k] and k not in seen: seen.add(k);stack.append(k)
        best=max(best,size)
    return best/len(mask)
def extract_mark_metrics(image,option,policy:OMRPolicy=DEFAULT_OMR_POLICY):
    m=binary_mask(image,policy.dark_pixel_cutoff); w=image.width;h=image.height;n=len(m); dark=sum(m)/n
    x0,x1=w//4,(3*w)//4;y0,y1=h//4,(3*h)//4; center=[m[y*w+x] for y in range(y0,y1) for x in range(x0,x1)]; cd=sum(center)/len(center)
    border=[m[y*w+x] for y in range(h) for x in range(w) if x in (0,w-1) or y in (0,h-1)]; bn=sum(border)/len(border)
    qs=[]
    for ya,yb in ((0,h//2),(h//2,h)):
        for xa,xb in ((0,w//2),(w//2,w)): q=[m[y*w+x] for y in range(ya,yb) for x in range(xa,xb)];qs.append(sum(q)/len(q))
    uniform=max(0,1-(max(qs)-min(qs))); comp=_largest(m,w,h)
    transitions=sum(m[y*w+x]!=m[y*w+x-1] for y in range(h) for x in range(1,w))/(h*max(1,w-1)); erase=transitions if dark>policy.weak_dark_ratio else 0
    score=max(0,min(1,.45*dark+.35*cd+.2*comp-.25*bn))
    if bn>policy.border_noise_limit and cd<policy.weak_dark_ratio: cls="dirty"
    elif erase>policy.erasure_threshold and dark<policy.strong_dark_ratio: cls="erased"
    elif dark>=policy.strong_dark_ratio and cd>=policy.strong_dark_ratio: cls="strong"
    elif dark>=policy.weak_dark_ratio: cls="weak"
    else: cls="blank"
    return MarkMetrics(option,dark,cd,comp,bn,uniform,erase,score,cls)
