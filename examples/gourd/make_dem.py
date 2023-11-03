import numpy as np
from parflow.tools.io import write_pfb

nx, ny = 301, 401
dem = np.ones([1, ny, nx])

multiplier = np.linspace(1, 2, ny)
for iy in range(0, ny):
    for ix in range(0, nx):
        dem[0,iy,ix] *= multiplier[iy]

write_pfb("dem.pfb", dem)