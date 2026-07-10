from app.student_recognition.image.image_types import ImageMatrix
def binary_mask(image:ImageMatrix,cutoff:int): return tuple(v<cutoff for v in image.pixels)
