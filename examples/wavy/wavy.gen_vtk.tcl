
#!/usr/bin/env tclsh

lappend auto_path $env(PARFLOW_DIR)/bin
package require parflow
namespace import Parflow::*

pfset FileVersion 4
set layer_count 60

set tfg_value "60 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 
    0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1 0.1"
set DEMdat [pfload -pfb "dem.pfb"]

set pfb_file "wavy.x.pfb"
set vtk_file "wavy.x.vtk"
set file [pfload -pfb $pfb_file]
pfvtksave $file -vtk $vtk_file -dem $DEMdat -flt -tfg $tfg_value -var "value"

set pfb_file "wavy.y.pfb"
set vtk_file "wavy.y.vtk"
set file [pfload -pfb $pfb_file]
pfvtksave $file -vtk $vtk_file -dem $DEMdat -flt -tfg $tfg_value -var "value"

set pfb_file "wavy.z.pfb"
set vtk_file "wavy.z.vtk"
set file [pfload -pfb $pfb_file]
pfvtksave $file -vtk $vtk_file -dem $DEMdat -flt -tfg $tfg_value -var "value"