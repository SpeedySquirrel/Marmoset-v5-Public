import mset
import os
import re

VERSION = "1.03"
SUFFIX_PATTERN = re.compile(r"[\s_\-.]*(low|high|hi|lo|lp|hp|lod\d*|\d+)$", re.IGNORECASE)
TRANSFORM_KEYS = ("position", "rotation", "scale")
clipboard = {"one": None, "many": []}


def selection(message):
    objects = mset.getSelectedObjects()
    if not objects:
        mset.err(message)
    return objects


def all_meshes():
    return [o for o in mset.getAllObjects() if o.__class__ == mset.MeshObject]


def meshes_in(obj):
    if obj.__class__ == mset.MeshObject:
        return [obj]
    return [m for child in obj.getChildren() for m in meshes_in(child)]


def selected_meshes():
    meshes = {}
    for obj in mset.getSelectedObjects():
        for mesh in meshes_in(obj):
            meshes[mesh.uid] = mesh
    if not meshes:
        mset.err("Select at least one mesh.")
    return list(meshes.values())


def submeshes(mesh):
    return [c for c in mesh.getChildren() if c.__class__ == mset.SubMeshObject]


def base_name(name):
    while True:
        stripped = SUFFIX_PATTERN.sub("", name)
        if stripped in (name, ""):
            return name
        name = stripped


def shared_name(meshes):
    bases = set(base_name(m.name) for m in meshes)
    if len(bases) == 1:
        return bases.pop()
    prefix = os.path.commonprefix([m.name for m in meshes]).rstrip("_-. ")
    return prefix or meshes[0].name


def free_name(candidates, material):
    taken = [m.name for m in mset.getAllMaterials() if m.name != material.name]
    for candidate in candidates:
        if candidate not in taken:
            return candidate
    index = 1
    while "%s_%d" % (candidates[-1], index) in taken:
        index += 1
    return "%s_%d" % (candidates[-1], index)


def collapse_everything():
    for obj in mset.getAllObjects():
        if obj.name != "Scene":
            obj.collapsed = True
    mset.refreshUI()


def select_all_geometry():
    meshes = all_meshes()
    if meshes:
        mset.setSelectedObjects(meshes)
    else:
        mset.err("No geometry in the scene.")


def find_and_select():
    text = searchField.value.strip()
    if not text:
        mset.err("Type a name to search for.")
        return
    matches = [m for m in all_meshes() if text.lower() in m.name.lower()]
    if matches:
        mset.setSelectedObjects(matches)
    else:
        mset.err("No meshes found containing '" + text + "'.")


def read_transform(obj):
    return {key: list(getattr(obj, key)) for key in TRANSFORM_KEYS}


def write_transform(obj, transform):
    for key in TRANSFORM_KEYS:
        setattr(obj, key, list(transform[key]))


def copy_transform():
    objects = selection("Select an object to copy.")
    if objects:
        clipboard["one"] = read_transform(objects[0])


def paste_transform():
    if clipboard["one"] is None:
        mset.err("Nothing copied yet.")
        return
    for obj in selection("Select an object to paste onto."):
        write_transform(obj, clipboard["one"])
    mset.refreshUI()


def copy_multiple_transforms():
    objects = selection("Select the objects to copy.")
    if objects:
        clipboard["many"] = [read_transform(o) for o in objects]


def duplicate_and_paste_transforms():
    if not clipboard["many"]:
        mset.err("Nothing copied yet.")
        return
    placed = []
    for obj in selection("Select the object to duplicate."):
        targets = [obj] + [obj.duplicate(obj.name) for _ in clipboard["many"][1:]]
        for target, transform in zip(targets, clipboard["many"]):
            write_transform(target, transform)
        placed.extend(targets)
    if placed:
        mset.setSelectedObjects(placed)
        mset.refreshUI()


def rename_selected():
    text = renameField.value.strip()
    if not text:
        mset.err("Type a name first.")
        return
    suffix_only = not re.search(r"[A-Za-z]", text)
    for index, mesh in enumerate(selected_meshes(), 1):
        name = re.sub(r"#+", lambda m: str(index).zfill(len(m.group(0))), text)
        mesh.name = mesh.name + name if suffix_only else name
    mset.refreshUI()


def edit_suffix(suffix, add):
    for mesh in selected_meshes():
        has_suffix = mesh.name.lower().endswith(suffix.lower())
        if add and not has_suffix:
            mesh.name += suffix
        elif not add and has_suffix:
            mesh.name = mesh.name[:-len(suffix)]
    mset.refreshUI()


def assign_new_material():
    for mesh in selected_meshes():
        material = mset.Material(mesh.name)
        subs = submeshes(mesh)
        for sub in subs:
            sub.material = material
        if not subs:
            mesh.addSubmesh(mesh.name + "_submesh", material=material, startIndex=0, indexCount=-1)
    mset.refreshUI()


def rename_material_from_geometry():
    groups = {}
    for mesh in selected_meshes():
        for sub in submeshes(mesh):
            if sub.material is not None:
                material, users = groups.setdefault(sub.material.name, (sub.material, []))
                users.append(mesh)
                break
    if not groups:
        mset.err("The selected meshes have no material.")
        return
    for material, users in groups.values():
        if len(users) == 1:
            candidates = [users[0].name, base_name(users[0].name)]
        else:
            candidates = [shared_name(users)]
        material.name = free_name(candidates, material)
    mset.refreshUI()


def button(text, action):
    control = mset.UIButton(text)
    control.onClick = action
    return control


def field(action):
    control = mset.UITextField()
    control.onChange = action
    return control


def drawer(name, build):
    holder = mset.UIWindow(name=name + " Window")
    for row in build():
        for item in row:
            holder.addElement(mset.UILabel(item) if isinstance(item, str) else item)
        holder.addReturn()
    control = mset.UIDrawer(name=name)
    control.containedControl = holder
    control.open = True
    return control


window = mset.UIWindow("MarmoSquirrel v" + VERSION)
window.width = 360

searchField = field(find_and_select)
renameField = field(rename_selected)

layout = [
    drawer("Scene", lambda: [
        [button("Collapse Everything", collapse_everything)],
        [drawer("Transforms", lambda: [
            [button("Copy", copy_transform), button("Paste", paste_transform)],
            [button("Copy Multiple", copy_multiple_transforms),
             button("Duplicate and Paste", duplicate_and_paste_transforms)],
        ])],
    ]),
    drawer("Selecting", lambda: [
        [button("Select all geometry in the scene", select_all_geometry)],
        [searchField, button("Find and Select", find_and_select)],
    ]),
    drawer("Naming", lambda: [
        [renameField, button("Rename", rename_selected)],
        ["Use ## to mark the number: ## = 01, 02   #### = 0001, 0002"],
        ["On selected objects"],
        [button("Add suffix _low", lambda: edit_suffix("_low", True)),
         button("Remove suffix _low", lambda: edit_suffix("_low", False))],
        [button("Add suffix _high", lambda: edit_suffix("_high", True)),
         button("Remove suffix _high", lambda: edit_suffix("_high", False))],
    ]),
    drawer("Materials", lambda: [
        [button("Assign New Material", assign_new_material)],
        [button("Rename Material Based on Geometry Name", rename_material_from_geometry)],
    ]),
]

for section in layout:
    window.addElement(section)
    window.addReturn()
window.addElement(mset.UILabel(""))
window.addReturn()
window.addElement(mset.UILabel("Made by SpeedySquirrel  -  GitHub: SpeedySquirrel"))
window.addReturn()
