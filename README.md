# MarmoSquirrel

A collection of small scripts I use every day to speed up work in Marmoset Toolbag.

---

## Installation

1. Copy the Python script into your Marmoset plugins folder. The usual path is:

`C:\Users\<your-username>\AppData\Local\Marmoset Toolbag 5\plugins`

2. In Marmoset Toolbag, go to **Edit > Plugins > Refresh**.
3. Open it from **Edit > Plugins > MarmoSquirrel**.


---

## Scene

### Collapse Everything
Collapses all folders and objects in the Scene/Outliner panel. Handy when your scene is cluttered with lots of cameras, lights, folders, and meshes.

### Transforms

#### Copy / Paste
**Copy** stores the position, rotation and scale of the selected object. 
**Paste** applies them to every object you have selected. The pivot is left untouched.



#### Copy Multiple / Duplicate and Paste
**Copy Multiple** stores the transforms of all selected objects, in selection order. 
**Duplicate and Paste** takes the selected object, duplicates it as many times as needed, and places each copy on one of the stored transforms.

**Example:** you have 4 `cubes` in the scene and you want to replace them with spheres. Select all 4 cubes and click **Copy Multiple**. Then select a single `sphere` mesh and click **Duplicate and Paste**. The sphere is duplicated 3 times, giving you 4 spheres, and each one moves onto a cube's transform.

---

## Selection

### Select All Geometry
Selects every mesh in the scene and nothing else. Cameras, lights, and other non-geometry objects are ignored.

### Find and Select
Selects all meshes whose name contains the text you type. Partial matches work.

**Example:** a mesh named `groundplane_AB_low` can be found by searching for any of:
`groundplane`, `plane`, `low`, `_low`, `AB`

---

## Naming

### Rename
Renames the selected meshes to the text you type. Use `#` to mark where the number goes. The number of `#` sets how many digits it is padded to, and meshes are numbered in the order they were selected.

**Examples:**
- `tree_##` gives `tree_01`, `tree_02`, `tree_03`
- `tree####` gives `tree0001`, `tree0002`, `tree0003`

If you type only a pattern with no letters, such as `_##`, it is added to the end of each mesh's current name instead of replacing it.

### On Selected Objects
- **Add suffix _low / Remove suffix _low** adds or removes `_low` at the end of the selected mesh names.
- **Add suffix _high / Remove suffix _high** adds or removes `_high` at the end of the selected mesh names.

Adding skips meshes that already end with the suffix, and removing only touches names that actually end with it.

---

## Materials

### Assign New Material
Creates a new default material for each selected mesh and names it after that mesh. If you select multiple meshes all of them will have a separate material named correctly.

### Rename Material Based on Geometry Name
Renames the materials on the selected meshes to match the mesh names in the Scene/Outliner.

- **Separate materials:** select `helmet` and `armor`, each with its own material, and the materials are renamed to `helmet` and `armor`.
- **Shared material:** if several meshes share one material and have similar names (e.g. `helmet_low` and `helmet_high`), the material gets the common part of the name: `helmet`.


---

## Support the Project

If this toolkit saved you time:

<a href="https://buymeacoffee.com/speedysquirrel">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" width="200">
</a>
