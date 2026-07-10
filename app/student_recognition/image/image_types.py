from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class ImageMatrix:
    width:int
    height:int
    pixels:Tuple[int,...]
    def __post_init__(self):
        if self.width<=0 or self.height<=0 or len(self.pixels)!=self.width*self.height: raise ValueError("invalid image matrix")
    def at(self,x:int,y:int)->int: return self.pixels[y*self.width+x]

GrayImage=ImageMatrix
BinaryImage=ImageMatrix
