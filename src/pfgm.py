# The ParFlow Geometry Mapper is a CLI tool for mapping geologies and faults in .obj format
# onto a terrain-following ParFlow grid. 
# 
# The ray-casting method is used to determine if a cell is contained within a geometry. The ray being
# casted begins at each cell center and ends at a point that is parallel to the z-dimension and is 
# above the zmax of the geometry. If the number of intersections with triangles in the .obj object is
# odd, the cell is considered to be inside of the geometry. For faults, a pair of adjacent cells are 
# considered to be seperated by the fault if the number of intersections is odd in the ray cast from one
# cell center to the next.
# 
# Exceptions are deliberately avoided in favor of returning a pair of form (obj, error message).
# This pattern is not in common Python as other languages, but does force deliberate writing of 
# error-handling code at the point the function is called. 

import argparse
import os
import numpy as np
from rtree import index
import sys
from pfb2vtk import renderVtkGen
from tfg import TFG
from parflow.tools.io import write_pfb

def exitWith(msg):
    print(msg)
    sys.exit(1)

class Progress:
    def __init__(self, nticks):
        self.nticks = nticks
        self.pct = nticks // 100
        self.tick = 0

    def __del__(self):
        sys.stdout.write("\n")
        sys.stdout.flush()

    def inc(self):
        self.tick += 1
        if self.tick % self.pct == 0:
            sys.stdout.write(" %d%%" %(round(100*self.tick/self.nticks)))
            sys.stdout.flush()

class TriangulatedSurface():
    def __init__(self, verts, triangles):
        self.verts = verts
        self.triangles = triangles
        self.buildIndex()
        self.zMax = np.max(np.array(list(map(lambda v: v[2], self.verts))))

    def buildIndex(self):
        p = index.Property()
        p.dimension = 2
        self.index = index.Index(properties=p)
        for tId, _ in enumerate(self.triangles):
            v0, v1, v2 = self.verticesFromTriangle(tId)
            xmin = np.min([v0[0], v1[0], v2[0]])
            xmax = np.max([v0[0], v1[0], v2[0]])
            ymin = np.min([v0[1], v1[1], v2[1]])
            ymax = np.max([v0[1], v1[1], v2[1]])
            self.index.insert(tId, (xmin, ymin, xmax, ymax))

    @staticmethod
    def fromObj(infile):
        '''
        Read simple .obj file. Function only reads vertices (v) and faces (f) of order 3 (e.g., triangles)
        
        :param: name of input file
        :return: the triangulated surface or an possible error message if reading failed.
        '''
        verts, triangles = [], []
        with open(infile, "r") as f:
            for line_no, line in enumerate(f):
                if line.startswith("v "):
                    parts = line.strip().split()
                    if len(parts) != 4:
                        return None, "encountered vertex with more than three values defined on line %d" %(line_no+1)
                    x, y, z = map(float, parts[1:])
                    verts.append(np.array([x, y, z]))
                if line.startswith("f "):
                    parts = line.strip().split()
                    if len(parts) != 4:
                        return None, "encountered face with more than three vertices defined on line %d" %(line_no+1)
                    try:
                        p1, p2, p3 = map(lambda n: int(n) - 1, parts[1:])
                    except ValueError as e:
                        return None, str(e) + ", line %d of %s" %(line_no, infile) 
                    triangles.append([p1, p2, p3])
        return TriangulatedSurface(verts, triangles), None
    
    def verticesFromTriangle(self, tId):
        """
        retrieves vertices associated with a particular triangle id.
        :param tId: index of triangle of interest
        :return: three vertices, each a size three numpy array
        """
        p0, p1, p2 = self.triangles[tId]
        v0 = self.verts[p0]
        v1 = self.verts[p1]
        v2 = self.verts[p2]
        return v0, v1, v2

    def rayIntersectsTriangle(self, rayOrigin, tId, rayEnd=None):
        """
        Determines if a line segment intersects a triangle. 
        """
        EPSILON = 0.0000001
        if rayEnd is None:
            rayEnd = np.array([rayOrigin[0], rayOrigin[1], self.zMax+1])
        rayVector = rayEnd - rayOrigin
        v0, v1, v2 = self.verticesFromTriangle(tId)
        edge1 = v1 - v0
        edge2 = v2 - v0
        h = np.cross(rayVector, edge2)
        a = np.dot(edge1, h)
        if a > -EPSILON and a < EPSILON:
            return False
        
        f = 1.0/a
        s = rayOrigin - v0
        u = f * np.dot(s, h)
        if u < 0.0 or u > 1.0:
            return False
        
        q = np.cross(s, edge1)
        v = f * np.dot(rayVector, q)
        if v < 0.0 or u + v > 1.0:
            return False
        
        t = f * np.dot(edge2, q)

        if t <= EPSILON:
            return False
        
        # At this point, the ray intersects. Now, we must determine if the potentional
        # point of intersection actually lies on the line between rayOrigin and rayEnd
        potentialP = rayOrigin + rayVector*t
        K_AC = rayVector.dot(rayEnd - potentialP)
        K_AB = rayVector.dot(rayVector)
        if K_AC < 0 or K_AC > K_AB:
            return False
        
        return True
        
    @staticmethod
    def writeApproxObj(tfg, indi_x, indi_y, indi_z, outfile):
        f = open(outfile, "w")
        nFaces = 0
        for ix in range(0, tfg.nx):
            for iy in range(0, tfg.ny):
                for iz in range(0, tfg.nz):
                    xmin, xmax = tfg.xMin(ix), tfg.xMax(ix)
                    ymin, ymax = tfg.yMin(iy), tfg.yMax(iy)
                    zmin, zmax = tfg.zMin(ix, iy, iz), tfg.zMax(ix, iy, iz)
                    if indi_x[iz][iy][ix] == 1:
                        f.write("v %f %f %f\n" %(xmax, ymin, zmin))
                        f.write("v %f %f %f\n" %(xmax, ymin, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymax, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymax, zmin))
                        nFaces += 1
                    if indi_y[iz][iy][ix] == 1:
                        f.write("v %f %f %f\n" %(xmin, ymax, zmin))
                        f.write("v %f %f %f\n" %(xmin, ymax, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymax, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymax, zmin))
                        nFaces += 1
                    if indi_z[iz][iy][ix] == 1:
                        f.write("v %f %f %f\n" %(xmin, ymin, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymin, zmax))
                        f.write("v %f %f %f\n" %(xmax, ymax, zmax))
                        f.write("v %f %f %f\n" %(xmin, ymax, zmax))
                        nFaces += 1
        for i in range(0, nFaces):
            n = i*4
            f.write("f %d %d %d %d\n" %(n+1, n+2, n+3, n+4))
        
    def processVolume(self, tfg, output_root):
        indi = np.zeros([tfg.nz, tfg.ny, tfg.nx])
        ncells = tfg.nx * tfg.ny * tfg.nz
        print("Processing volume for %s. %d cells. %d faces" %(output_root, ncells, len(self.index)))
        bump = tfg.dx * 0.1
        progress = Progress(ncells)
        for ix in range(0, tfg.nx):
            for iy in range(0, tfg.ny):
                x, y = tfg.xMid(ix), tfg.yMid(iy)
                tIds = list(self.index.intersection((x, y, x+bump, y+bump)))
                for iz in range(0, tfg.nz):
                    z = tfg.zMid(ix, iy, iz)
                    if z > self.zMax:
                        progress.inc()
                        continue

                    intersections = 0
                    for tId in tIds:
                        if self.rayIntersectsTriangle(np.array([x, y, z]), tId):
                            intersections += 1
                    if intersections % 2 != 0:
                        indi[iz][iy][ix] = 1
                    progress.inc()

        pfbPath = "%s.pfb" %output_root
        write_pfb(pfbPath, indi, x=tfg.x0, y=tfg.y0, dx=tfg.dx, dy=tfg.dy, dz=1)
        renderVtkGen(pfbPath, "%s.vtk" %output_root, tfg.demPfb, tfg.dzs, "%s.gen_vtk.tcl" %output_root)

    def processSurface(self, tfg, output_root):
        indi_x = np.zeros([tfg.nz, tfg.ny, tfg.nx])
        indi_y = np.zeros([tfg.nz, tfg.ny, tfg.nx])
        indi_z = np.zeros([tfg.nz, tfg.ny, tfg.nx])
        ncells = tfg.nx * tfg.ny * tfg.nz
        print("Processing volume for %s. %d cells. %d faces" %(output_root, ncells, len(self.index)))
        progress = Progress((tfg.nx-1) * (tfg.ny-1) * (tfg.nz-1))
        for ix in range(0, tfg.nx-1):
            for iy in range(0, tfg.ny-1):
                x0, xf = tfg.xMid(ix), tfg.xMid(ix+1)
                y0, yf = tfg.yMid(iy), tfg.yMid(iy+1)
                tIds = list(self.index.intersection((x0, y0, xf, yf)))
                for iz in range(0, tfg.nz-1):
                    z = tfg.zMid(ix, iy, iz)
                    if z > self.zMax:
                        progress.inc()
                        continue

                    # Surface intersections in x-direction
                    intersections = 0
                    for tId in tIds:
                        rayOrigin = np.array(tfg.cellCenter(ix, iy, iz))
                        rayEnd = np.array(tfg.cellCenter(ix+1, iy, iz))
                        if self.rayIntersectsTriangle(rayOrigin, tId, rayEnd=rayEnd):
                            intersections += 1
                    if intersections % 2 != 0:
                        indi_x[iz][iy][ix] = 1

                    # Surface intersections in y-direction
                    intersections = 0
                    for tId in tIds:
                        rayOrigin = np.array(tfg.cellCenter(ix, iy, iz))
                        rayEnd = np.array(tfg.cellCenter(ix, iy+1, iz))
                        if self.rayIntersectsTriangle(rayOrigin, tId, rayEnd=rayEnd):
                            intersections += 1
                    if intersections % 2 != 0:
                        indi_y[iz][iy][ix] = 1

                    # Surface intersections in z-direction
                    intersections = 0
                    for tId in tIds:
                        rayOrigin = np.array(tfg.cellCenter(ix, iy, iz))
                        rayEnd = np.array(tfg.cellCenter(ix, iy, iz+1))
                        if self.rayIntersectsTriangle(rayOrigin, tId, rayEnd=rayEnd):
                            intersections += 1
                    if intersections % 2 != 0:
                        indi_z[iz][iy][ix] = 1

                    progress.inc()

        pfbPath = lambda dim: "%s.%s.pfb" %(output_root, dim)
        write_pfb(pfbPath("x"), indi_x, x=tfg.x0, y=tfg.y0, dx=tfg.dx, dy=tfg.dy, dz=1)
        write_pfb(pfbPath("y"), indi_y, x=tfg.x0, y=tfg.y0, dx=tfg.dx, dy=tfg.dy, dz=1)
        write_pfb(pfbPath("z"), indi_z, x=tfg.x0, y=tfg.y0, dx=tfg.dx, dy=tfg.dy, dz=1)
        self.writeApproxObj(tfg, indi_x, indi_y, indi_z, "%s.faces.obj" %output_root)

def getArgs():
    parser = argparse.ArgumentParser(description="ParFlow Geometry Mapper. A tool for mapping .obj files onto "
                                    + "a ParFlow-style terrain-following grid.")
    parser.add_argument('-kind', metavar="k", type=str, required=True,
                        help="Kind of analysis. Options are 'volume' or 'surface'")
    parser.add_argument('-tfg', type=str, required=True,
                        help="json-formatted metadata for terrain-following grid")
    parser.add_argument('-obj', type=str, required=True,
                        help="obj-formatted input file. Faces must all be order 3 (triangles)")
    parser.add_argument('-o', required=True,
                        help="root name of output file(s)")
    args = parser.parse_args()
    
    if args.kind not in ["volume", "surface"]:
        exitWith("error: '%s' is not a valid kind. Choose 'volume' or 'surface'" %args.kind)
    if not os.path.exists(args.tfg):
        exitWith("error: '%s' does not exist" %args.tfg)
    if not os.path.exists(args.obj):
        exitWith("error: '%s' does not exist" %args.obj)

    return args

def processVolume(args):
    ts, err = TriangulatedSurface.fromObj(args.obj)
    if err != None:
        exitWith(err)

    tfg, err = TFG.fromJson(args.tfg)
    if err != None:
        exitWith(err)

    ts.processVolume(tfg, args.o)

def processSurface(args):
    ts, err = TriangulatedSurface.fromObj(args.obj)
    if err != None:
        exitWith(err)

    tfg, err = TFG.fromJson(args.tfg)
    if err != None:
        exitWith(err)

    ts.processSurface(tfg, args.o)

if __name__ == "__main__":
    args = getArgs()
    if args.kind == "volume":
        processVolume(args)
    elif args.kind == "surface":
        processSurface(args)
    else:
        print("unknown 'kind' argument. Must be either 'volume' or 'surface'")
        sys.exit(1)