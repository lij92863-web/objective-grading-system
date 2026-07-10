"""Image backend abstraction. Optional cv2 detection is isolated here."""
from abc import ABC,abstractmethod
from .image_types import ImageMatrix

class ImageBackend(ABC):
    @abstractmethod
    def crop(self,image:ImageMatrix,box): ...
    @abstractmethod
    def resize(self,image:ImageMatrix,width:int,height:int): ...

class StdlibImageBackend(ImageBackend):
    def crop(self,image,box):
        x0,y0,x1,y1=box
        if x0<0 or y0<0 or x1>image.width or y1>image.height or x1<=x0 or y1<=y0: raise ValueError("invalid crop")
        return ImageMatrix(x1-x0,y1-y0,tuple(image.at(x,y) for y in range(y0,y1) for x in range(x0,x1)))
    def resize(self,image,width,height):
        if width<=0 or height<=0: raise ValueError("invalid target size")
        return ImageMatrix(width,height,tuple(image.at(min(image.width-1,x*image.width//width),min(image.height-1,y*image.height//height)) for y in range(height) for x in range(width)))

def cv2_available():
    try:
        import cv2  # optional import is deliberately isolated
        return cv2 is not None
    except ImportError: return False

def get_backend()->ImageBackend: return StdlibImageBackend()
