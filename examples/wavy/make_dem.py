import numpy as np
from parflow.tools.io import write_pfb

nx, ny = 81, 41
dem = np.ones([1, ny, nx])*3

write_pfb("dem.pfb", dem)