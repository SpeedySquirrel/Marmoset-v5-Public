# Marmoset Toolkit

A collection of small scripts I use every day to speed up work in Marmoset Toolbag.

---

## Scene

### Collapse Everything
Collapses all folders and objects in the Scene/Outliner panel. Handy when your scene is cluttered with lots of cameras, lights, folders, and meshes.

---

## Selection

### Select All Geometry
Selects every mesh in the scene and nothing else. Cameras, lights, and other non-geometry objects are ignored.

### Find and Select
Selects all meshes whose name contains the text you type. Partial matches work.

**Example:** a mesh named `groundplane_AB_low` can be found by searching for any of:
`groundplane`, `plane`, `low`, `_low`, `AB`

---

## Materials

### Assign New Material
Creates a new default material for each selected mesh and names it after that mesh.

### Rename Material Based on Geometry Name
Renames the materials on the selected meshes to match the mesh names in the Scene/Outliner.

- **Separate materials:** select `helmet` and `armor`, each with its own material, and the materials are renamed to `helmet` and `armor`.
- **Shared material:** if several meshes share one material and have similar names (e.g. `helmet_low` and `helmet_high`), the material gets the common part of the name: `helmet`.
