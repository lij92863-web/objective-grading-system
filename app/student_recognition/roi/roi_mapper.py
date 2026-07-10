import math
from dataclasses import dataclass
from typing import Mapping
@dataclass(frozen=True)
class PixelROI:
    x0:int;y0:int;x1:int;y1:int
    @property
    def width(self): return self.x1-self.x0
    @property
    def height(self): return self.y1-self.y0
def map_normalized_roi(roi:Mapping[str,float],width:int,height:int)->PixelROI:
    x,y,w,h=(float(roi[k]) for k in ("x","y","w","h"))
    if width<=0 or height<=0 or w<=0 or h<=0 or x<0 or y<0 or x+w>1 or y+h>1: raise ValueError("ROI_OUT_OF_BOUNDS")
    eps=1e-12
    box=PixelROI(math.floor(x*width+eps),math.floor(y*height+eps),math.ceil((x+w)*width-eps),math.ceil((y+h)*height-eps))
    if box.width<=0 or box.height<=0: raise ValueError("ROI_EMPTY_CROP")
    return box
