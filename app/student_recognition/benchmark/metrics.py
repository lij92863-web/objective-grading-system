import math
def percentile(values,p):
    if not values:return 0
    values=sorted(values); return values[min(len(values)-1,math.ceil(len(values)*p)-1)]
