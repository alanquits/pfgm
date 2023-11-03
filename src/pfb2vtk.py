#!/usr/bin/env python3.4

import sys
sys.path.append("/modeling/al/bin")

import glob
import os

TEMPLATE = """
#!/usr/bin/env tclsh

lappend auto_path $env(PARFLOW_DIR)/bin
package require parflow
namespace import Parflow::*

pfset FileVersion 4

set pfb_file "{{PFB_FILE}}"
set vtk_file "{{VTK_FILE}}"
set layer_count {{LAYER_COUNT}}

set file [pfload -pfb $pfb_file]

set tfg_value "{{LAYER_COUNT}} {{SPACE_SEPARATED_LAYERS}}"
set DEMdat [pfload -pfb "{{DEM_PATH}}"]

pfvtksave $file -vtk $vtk_file -dem $DEMdat -flt -tfg $tfg_value -var "value"
"""

def exit_with(msg):
    print(msg)
    exit(1)

def renderVtkGen(pfbPath, vtkPath, demPath, dzs, outfile):
    t = TEMPLATE
    t = t.replace("{{PFB_FILE}}", '%s' %pfbPath)
    t = t.replace("{{VTK_FILE}}", '%s' %vtkPath)
    t = t.replace("{{DEM_PATH}}", '%s' %demPath)
    t = t.replace("{{LAYER_COUNT}}", "%d" %(len(dzs)))
    t = t.replace("{{SPACE_SEPARATED_LAYERS}}", " ".join(list(map(str, dzs))))
    with open(outfile, "w") as f:
        f.write(t)