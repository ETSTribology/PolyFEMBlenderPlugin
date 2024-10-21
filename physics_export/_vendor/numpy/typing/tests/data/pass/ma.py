from typing import Any

from ...... import numpy as np
from ...... import numpy
from ......numpy import ma as ___vendorize__0
numpy.ma = ___vendorize__0


m : np.ma.MaskedArray[Any, np.dtype[np.float64]] = np.ma.masked_array([1.5, 2, 3], mask=[True, False, True])

