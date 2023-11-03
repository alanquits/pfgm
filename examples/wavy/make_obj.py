import numpy as np
import matplotlib.pylab as plt

def f(x, y):
    return (7*x*y)/(np.exp(x**2 + y**2))

def main():
    f = open("wavy.obj", "w")
    nx, ny = 50, 50
    xs = np.linspace(-2, 2, nx)
    ys = np.linspace(-1, 1, ny)

    xs, ys = np.meshgrid(xs, ys)
    zs = (7*xs*ys)/(np.exp(xs**2 + ys**2))

    verts = {}
    vertCounter = 1
    for ix in range(0, nx):
        for iy in range(0, ny):
            x = xs[ix, iy]
            y = ys[ix, iy]
            z = zs[ix, iy]
            f.write("v %f %f %f\n" %(x, y, z))
            verts[(ix, iy)] = vertCounter
            vertCounter += 1
        
    for ix in range(1, nx):
        for iy in range(1, ny):
            # triangles
            t1 = [(ix-1, iy-1), (ix, iy-1), (ix, iy)]
            t2 = [(ix-1, iy-1), (ix, iy), (ix-1, iy)]
            for t in [t1, t2]:
                v1, v2, v3 = map(lambda vertAddress: verts[vertAddress], t)
                f.write("f %d %d %d\n" %(v1, v2, v3))

if __name__ == "__main__":
    main()