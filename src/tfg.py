import json
import sys
sys.path.append("/modeling/al/bin")

import numpy as np
from parflow.tools.io import write_pfb, read_pfb

class TFG:
    def __init__(self, x0, y0, dx, dy, nx, ny, dzs, demPfb):
        # dz comes in from bottom to top
        self.x0 = x0
        self.y0 = y0
        self.dx = dx
        self.dy = dy
        self.nx = nx
        self.ny = ny
        self.nz = len(dzs)
        self.dzs = dzs
        self.totalThickness = np.sum(dzs)
        self.zBottoms = [self.totalThickness]
        for i, dzThickness in enumerate(dzs):
            if i < self.nz - 1:
                self.zBottoms.append(self.zBottoms[-1] - dzThickness)   
        self.demPfb = demPfb         
        self.dem = read_pfb(demPfb)

    def cellCenter(self, ix, iy, iz):
        return self.xMid(ix), self.yMid(iy), self.zMid(ix, iy, iz)

    def xMin(self, ix):
        return self.x0 + self.dx*ix

    def xMax(self, ix):
        return self.xMin(ix) + self.dx
    
    def xMid(self, ix):
        return (self.xMin(ix) + self.xMax(ix)) / 2.0
    
    def xExtent(self):
        return self.xMin(0), self.xMax(self.nx-1)
    
    def yMin(self, iy):
        return self.y0 + self.dy*iy
    
    def yMax(self, iy):
        return self.yMin(iy) + self.dy
    
    def yMid(self, iy):
        return (self.yMin(iy) + self.yMax(iy)) / 2.0
    
    def yExtent(self):
        return self.yMin(0), self.yMax(self.ny-1)

    def zMin(self, ix, iy, iz):
        return self.dem[0][iy][ix] - self.zBottoms[iz]

    def zMax(self, ix, iy, iz):
        if iz == self.nz-1:
            return self.dem[0][iy][ix]
        else:
            return self.zMin(ix, iy, iz) + self.dzs[iz]
    
    def zMid(self, ix, iy, iz):
        return (self.zMin(ix, iy, iz) + self.zMax(ix, iy, iz)) / 2.0
        
    def cellVolume(self, iz):
        return self.dx * self.dy * self.dzs[iz]

    def cellIndexFromPosition2D(self, x, y):
        ix = int(np.floor((x - self.x_origin) / self.dx)) # 0-indexed
        iy = int(np.floor((y - self.y_origin) / self.dy)) # 0-indexed
        
        if self.isValidIndex(ix, iy, 0):
            return (ix, iy)
        else:
            return None

    def cellIndexFromPosition3D(self, x, y, z):
        cell_idx_2d = self.cellIndexFromPosition2D(x, y)
        
        if cell_idx_2d is None:
            return None
        else:
            ix, iy = cell_idx_2d

        for iz in range(0, self.nz):
            if self.zMin(ix, iy, iz) <= z and z < self.zMax(ix, iy, iz):
                return (ix, iy, iz)
        return None
    
    @staticmethod
    def fromJson(infile):
        """
        Read a terrain-following grid from json specification. Specification format will be intuitive from
        source code below
        :param infile: input filename
        :return: the first value is the terrain-following grid class instance on success, and None and failure.
            The second return value is None on success, and an error message on failure.
        """
        with open(infile, "r") as f:
            j = json.load(f)
            try:
                x0 = j["x"]
                y0 = j["y"]
                dx = j["dx"]
                dy = j["dy"]
                nx = j["nx"]
                ny = j["ny"]
                dzs = j["dzs"]
                demPfb = j["dem"]
                tfg = TFG(x0, y0, dx, dy, nx, ny, dzs, demPfb)
                return tfg, None
            except Exception as e:
                error_message = str(e)
                return None, error_message

    def isValidIndex(self, ix, iy, iz):
        if ix < 0 or ix >= self.nx:
            return False
        if iy < 0 or iy >= self.ny:
            return False
        if iz < 0 or iz >= self.nz:
            return False
        return True

    def wkt(self, ix, iy):
        xmin = self.xMin(ix)
        xmax = self.xMax(ix)
        ymin = self.yMin(iy)
        ymax = self.yMax(iy)
        p = "POLYGON ((%s %s, %s %s, %s %s, %s %s, %s %s))" \
            %(xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax, xmin, ymin)
        return p

    def shape(self):
        return self.nx, self.ny, self.nz

if __name__ == "__main__":
    pass
