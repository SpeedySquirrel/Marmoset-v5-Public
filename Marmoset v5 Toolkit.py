import mset
import re
import os

SUFFIX_PATTERN = re.compile(r"[\s_\-.]*(low|high|hi|lo|lp|hp|lod\d*|\d+)$", re.IGNORECASE)

copiedTransform = None
copiedTransforms = []


def get_all_meshes():
    return [obj for obj in mset.getAllObjects() if obj.__class__ == mset.MeshObject]


def get_meshes_in(obj):
    if obj.__class__ == mset.MeshObject:
        return [obj]
    meshes = []
    for child in obj.getChildren():
        meshes.extend(get_meshes_in(child))
    return meshes


def get_selected_meshes():
    meshes = []
    seen = set()
    for obj in mset.getSelectedObjects():
        for mesh in get_meshes_in(obj):
            if mesh.uid not in seen:
                seen.add(mesh.uid)
                meshes.append(mesh)
    return meshes


def get_material(mesh):
    for child in mesh.getChildren():
        if child.__class__ == mset.SubMeshObject and child.material is not None:
            return child.material
    return None


def assign_material(mesh, material):
    submeshes = [c for c in mesh.getChildren() if c.__class__ == mset.SubMeshObject]
    if submeshes:
        for sub in submeshes:
            sub.material = material
    else:
        mesh.addSubmesh(mesh.name + "_submesh", material=material, startIndex=0, indexCount=-1)


def base_name(name):
    stripped = name
    while True:
        result = SUFFIX_PATTERN.sub("", stripped)
        if result == stripped or result == "":
            break
        stripped = result
    return stripped


def shared_name(meshes):
    bases = set(base_name(mesh.name) for mesh in meshes)
    if len(bases) == 1:
        return bases.pop()
    prefix = os.path.commonprefix([mesh.name for mesh in meshes]).rstrip("_-. ")
    if prefix:
        return prefix
    return meshes[0].name


def free_name(candidates, material):
    taken = [m.name for m in mset.getAllMaterials()]
    if material.name in taken:
        taken.remove(material.name)
    for candidate in candidates:
        if candidate not in taken:
            return candidate
    index = 1
    while candidates[-1] + "_" + str(index) in taken:
        index += 1
    return candidates[-1] + "_" + str(index)


def collapse_everything():
    for obj in mset.getAllObjects():
        if obj.name != "Scene":
            obj.collapsed = True
    mset.refreshUI()


def select_all_geometry():
    meshes = get_all_meshes()
    if not meshes:
        mset.err("No geometry in the scene.")
        return
    mset.setSelectedObjects(meshes)


def find_and_select():
    text = searchField.value.strip().lower()
    if not text:
        mset.err("Type a name to search for.")
        return
    matches = [mesh for mesh in get_all_meshes() if text in mesh.name.lower()]
    if not matches:
        mset.err("No meshes found containing '" + searchField.value.strip() + "'.")
        return
    mset.setSelectedObjects(matches)


def read_transform(obj):
    return {
        "position": list(obj.position),
        "rotation": list(obj.rotation),
        "scale": list(obj.scale),
    }


def write_transform(obj, transform):
    obj.position = list(transform["position"])
    obj.rotation = list(transform["rotation"])
    obj.scale = list(transform["scale"])


def copy_transform():
    global copiedTransform
    selected = mset.getSelectedObjects()
    if not selected:
        mset.err("Select an object to copy.")
        return
    copiedTransform = read_transform(selected[0])


def paste_transform():
    if copiedTransform is None:
        mset.err("Nothing copied yet.")
        return
    selected = mset.getSelectedObjects()
    if not selected:
        mset.err("Select an object to paste onto.")
        return
    for obj in selected:
        write_transform(obj, copiedTransform)
    mset.refreshUI()


def copy_multiple_transforms():
    global copiedTransforms
    selected = mset.getSelectedObjects()
    if not selected:
        mset.err("Select the objects to copy.")
        return
    copiedTransforms = [read_transform(obj) for obj in selected]


def duplicate_and_paste_transforms():
    if not copiedTransforms:
        mset.err("Nothing copied yet.")
        return
    selected = mset.getSelectedObjects()
    if not selected:
        mset.err("Select the object to duplicate.")
        return
    placed = []
    for obj in selected:
        write_transform(obj, copiedTransforms[0])
        placed.append(obj)
        for transform in copiedTransforms[1:]:
            duplicate = obj.duplicate(obj.name)
            write_transform(duplicate, transform)
            placed.append(duplicate)
    mset.setSelectedObjects(placed)
    mset.refreshUI()


def number_pattern(text, index):
    return re.sub(r"#+", lambda m: str(index).zfill(len(m.group(0))), text)


def rename_selected():
    text = renameField.value.strip()
    if not text:
        mset.err("Type a name first.")
        return
    meshes = get_selected_meshes()
    if not meshes:
        mset.err("Select at least one mesh.")
        return
    suffix_only = not re.search(r"[A-Za-z]", text)
    for index, mesh in enumerate(meshes, 1):
        new_name = number_pattern(text, index)
        mesh.name = mesh.name + new_name if suffix_only else new_name
    mset.refreshUI()


def add_suffix(suffix):
    meshes = get_selected_meshes()
    if not meshes:
        mset.err("Select at least one mesh.")
        return
    for mesh in meshes:
        if not mesh.name.lower().endswith(suffix.lower()):
            mesh.name = mesh.name + suffix
    mset.refreshUI()


def remove_suffix(suffix):
    meshes = get_selected_meshes()
    if not meshes:
        mset.err("Select at least one mesh.")
        return
    for mesh in meshes:
        if mesh.name.lower().endswith(suffix.lower()):
            mesh.name = mesh.name[:-len(suffix)]
    mset.refreshUI()


def assign_new_material():
    meshes = get_selected_meshes()
    if not meshes:
        mset.err("Select at least one mesh.")
        return
    for mesh in meshes:
        material = mset.Material(mesh.name)
        assign_material(mesh, material)
    mset.refreshUI()


def rename_material_from_geometry():
    meshes = get_selected_meshes()
    if not meshes:
        mset.err("Select at least one mesh.")
        return

    groups = {}
    order = []
    for mesh in meshes:
        material = get_material(mesh)
        if material is None:
            continue
        if material.name not in groups:
            groups[material.name] = (material, [])
            order.append(material.name)
        groups[material.name][1].append(mesh)

    if not groups:
        mset.err("The selected meshes have no material.")
        return

    for key in order:
        material, users = groups[key]
        if len(users) == 1:
            candidates = [users[0].name, base_name(users[0].name)]
        else:
            candidates = [shared_name(users)]
        material.name = free_name(candidates, material)

    mset.refreshUI()


window = mset.UIWindow("Marmoset v5 Toolkit")
window.width = 360

sceneDrawer = mset.UIDrawer(name="Scene")
sceneWindow = mset.UIWindow(name="Scene Window")
sceneDrawer.containedControl = sceneWindow
sceneDrawer.open = True

collapseButton = mset.UIButton("Collapse Everything")
collapseButton.onClick = collapse_everything
sceneWindow.addElement(collapseButton)
sceneWindow.addReturn()

transformsDrawer = mset.UIDrawer(name="Transforms")
transformsWindow = mset.UIWindow(name="Transforms Window")
transformsDrawer.containedControl = transformsWindow
transformsDrawer.open = True

copyButton = mset.UIButton("Copy")
copyButton.onClick = copy_transform
transformsWindow.addElement(copyButton)

pasteButton = mset.UIButton("Paste")
pasteButton.onClick = paste_transform
transformsWindow.addElement(pasteButton)
transformsWindow.addReturn()

copyMultipleButton = mset.UIButton("Copy Multiple")
copyMultipleButton.onClick = copy_multiple_transforms
transformsWindow.addElement(copyMultipleButton)

duplicatePasteButton = mset.UIButton("Duplicate and Paste")
duplicatePasteButton.onClick = duplicate_and_paste_transforms
transformsWindow.addElement(duplicatePasteButton)
transformsWindow.addReturn()

sceneWindow.addElement(transformsDrawer)
sceneWindow.addReturn()

window.addElement(sceneDrawer)
window.addReturn()

selectingDrawer = mset.UIDrawer(name="Selecting")
selectingWindow = mset.UIWindow(name="Selecting Window")
selectingDrawer.containedControl = selectingWindow
selectingDrawer.open = True

selectAllButton = mset.UIButton("Select all geometry in the scene")
selectAllButton.onClick = select_all_geometry
selectingWindow.addElement(selectAllButton)
selectingWindow.addReturn()

searchField = mset.UITextField()
searchField.onChange = find_and_select
selectingWindow.addElement(searchField)

findButton = mset.UIButton("Find and Select")
findButton.onClick = find_and_select
selectingWindow.addElement(findButton)
selectingWindow.addReturn()

window.addElement(selectingDrawer)
window.addReturn()

namingDrawer = mset.UIDrawer(name="Naming")
namingWindow = mset.UIWindow(name="Naming Window")
namingDrawer.containedControl = namingWindow
namingDrawer.open = True

renameField = mset.UITextField()
renameField.onChange = rename_selected
namingWindow.addElement(renameField)

renameButton = mset.UIButton("Rename")
renameButton.onClick = rename_selected
namingWindow.addElement(renameButton)
namingWindow.addReturn()

namingWindow.addElement(mset.UILabel("Use ## to mark the number: ## = 01, 02   #### = 0001, 0002"))
namingWindow.addReturn()

namingWindow.addElement(mset.UILabel("On selected objects"))
namingWindow.addReturn()

addLowButton = mset.UIButton("Add suffix _low")
addLowButton.onClick = lambda: add_suffix("_low")
namingWindow.addElement(addLowButton)

removeLowButton = mset.UIButton("Remove suffix _low")
removeLowButton.onClick = lambda: remove_suffix("_low")
namingWindow.addElement(removeLowButton)
namingWindow.addReturn()

addHighButton = mset.UIButton("Add suffix _high")
addHighButton.onClick = lambda: add_suffix("_high")
namingWindow.addElement(addHighButton)

removeHighButton = mset.UIButton("Remove suffix _high")
removeHighButton.onClick = lambda: remove_suffix("_high")
namingWindow.addElement(removeHighButton)
namingWindow.addReturn()

window.addElement(namingDrawer)
window.addReturn()

materialsDrawer = mset.UIDrawer(name="Materials")
materialsWindow = mset.UIWindow(name="Materials Window")
materialsDrawer.containedControl = materialsWindow
materialsDrawer.open = True

assignButton = mset.UIButton("Assign New Material")
assignButton.onClick = assign_new_material
materialsWindow.addElement(assignButton)
materialsWindow.addReturn()

renameMaterialButton = mset.UIButton("Rename Material Based on Geometry Name")
renameMaterialButton.onClick = rename_material_from_geometry
materialsWindow.addElement(renameMaterialButton)
materialsWindow.addReturn()

window.addElement(materialsDrawer)
window.addReturn()

window.addElement(mset.UILabel(""))
window.addReturn()
window.addElement(mset.UILabel("Made by SpeedySquirrel  -  GitHub: SpeedySquirrel"))
window.addReturn()
