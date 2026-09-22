import math
import mset
import os
import re

VERSION = "2.10"
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


def hide_everything():
    for mesh in all_meshes():
        set_visible(mesh, False)
    mset.refreshUI()


def show_everything():
    for mesh in all_meshes():
        set_visible(mesh, True)
    mset.refreshUI()


visibilitySnapshot = {"value": None}


def isolate_selected():
    chosen = set(mesh.uid for mesh in selected_meshes())
    if not chosen:
        return
    meshes = all_meshes()
    visibilitySnapshot["value"] = {mesh.uid: mesh.visible for mesh in meshes}
    for mesh in meshes:
        set_visible(mesh, mesh.uid in chosen)
    mset.refreshUI()
    isolateButton.text = "Undo Isolate Selected"


def undo_isolate_selected():
    snapshot = visibilitySnapshot["value"]
    if snapshot is None:
        mset.err("Nothing to undo.")
        return
    for mesh in all_meshes():
        if mesh.uid in snapshot:
            set_visible(mesh, snapshot[mesh.uid])
    mset.refreshUI()
    visibilitySnapshot["value"] = None
    isolateButton.text = "   Isolate Selected   "


def toggle_isolate_selected():
    if visibilitySnapshot["value"] is None:
        isolate_selected()
    else:
        undo_isolate_selected()


LIGHT_CLASS_NAMES = (
    "LightObject", "PointLightObject", "SpotLightObject",
    "DirectionalLightObject", "AreaLightObject", "OmniLightObject", "SunObject",
    "SkyObject", "EnvironmentObject", "HDRIObject", "DomeLightObject", "SkyDomeObject",
)

LIGHT_DUCK_TYPE_ATTRS = ("intensity", "power", "brightness", "exposure", "brightnessScale")


def is_light_or_sky(obj):
    class_name = getattr(obj.__class__, "__name__", "")
    if class_name in LIGHT_CLASS_NAMES:
        return True
    if obj.name != "Scene" and any(hasattr(obj, attr) for attr in LIGHT_DUCK_TYPE_ATTRS):
        return True
    return obj.name == "Sky"


def select_all_lights():
    lights = [o for o in mset.getAllObjects() if is_light_or_sky(o)]
    if lights:
        mset.setSelectedObjects(lights)
    else:
        mset.err("No lights or sky found in the scene.")


def select_all_cameras():
    cameras = [o for o in mset.getAllObjects() if getattr(o.__class__, "__name__", "") == "CameraObject"]
    if cameras:
        mset.setSelectedObjects(cameras)
    else:
        mset.err("No cameras found in the scene.")


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


def reset_transform(reset_position, reset_rotation, reset_scale):
    objects = selection("Select an object first.")
    for obj in objects:
        if reset_position:
            obj.position = [0.0, 0.0, 0.0]
        if reset_rotation:
            obj.rotation = [0.0, 0.0, 0.0]
        if reset_scale:
            obj.scale = [1.0, 1.0, 1.0]
    if objects:
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


def get_bakers():
    return [o for o in mset.getAllObjects() if getattr(o.__class__, "__name__", "") == "BakerObject"]


def get_bake_groups():
    groups = []
    for baker in get_bakers():
        for child in baker.getChildren():
            if not hasattr(child, "findInChildren"):
                continue
            try:
                high = child.findInChildren("High")
                low = child.findInChildren("Low")
            except Exception:
                continue
            if high is not None and low is not None:
                groups.append(child)
    return groups


LIST_HEADER_COUNT = 1

bakeIndex = {"value": 0}
bakeMode = {"value": "both"}
viewMode = {"value": "all"}


def current_bake_group(quiet=False):
    if not bakeGroups:
        if not quiet:
            mset.err("No bake groups found. Create a bake project first.")
        return None
    return bakeGroups[bakeIndex["value"]]


def low_folder(group):
    return group.findInChildren("Low")


def safe_select(objects, context):
    try:
        mset.setSelectedObjects(objects)
        return True
    except Exception as error:
        print("Could not select " + context + ": " + str(error))
        return False


def force_redraw():
    safe_select(mset.getSelectedObjects(), "current selection (redraw)")


def set_visible(obj, visible):
    if obj is None:
        return None
    try:
        obj.visible = visible
        if obj.visible != visible:
            print("Set visible=" + str(visible) + " on '" + obj.name + "' but it reads back as " + str(obj.visible) + ".")
        return True
    except Exception as error:
        print("Could not set visible on '" + getattr(obj, "name", "?") + "': " + str(error))
        return False


def apply_visibility():
    results = []
    if viewMode["value"] == "all":
        for candidate in bakeGroups:
            results.append(set_visible(candidate.findInChildren("Low"), True))
            results.append(set_visible(candidate.findInChildren("High"), True))
    elif viewMode["value"] == "group":
        group = current_bake_group(quiet=True)
        for candidate in bakeGroups:
            current = candidate is group
            results.append(set_visible(candidate.findInChildren("Low"), current and bakeMode["value"] in ("low", "both")))
            results.append(set_visible(candidate.findInChildren("High"), current and bakeMode["value"] in ("high", "both")))
    mset.refreshUI()
    results = [r for r in results if r is not None]
    if results and not any(results):
        mset.err("Visibility could not be changed on this Toolbag build - see console.")


def sync_list_selection():
    try:
        if viewMode["value"] == "all":
            groupList.selectedItem = 0
        else:
            groupList.selectedItem = bakeIndex["value"] + LIST_HEADER_COUNT
    except Exception:
        pass


def show_all():
    viewMode["value"] = "all"
    sync_list_selection()
    bakers = get_bakers()
    safe_select([bakers[0]] if bakers else [], "the Bake Project")
    apply_visibility()


def select_low(group):
    low = low_folder(group)
    target = low if low is not None else group
    if safe_select([target], "'" + target.name + "'"):
        return
    if low is not None:
        safe_select([group], "'" + group.name + "'")


def go_to_group_index(index):
    viewMode["value"] = "group"
    bakeIndex["value"] = index
    sync_list_selection()
    select_low(bakeGroups[index])
    load_cage_values(bakeGroups[index])
    apply_visibility()


def step_bake_group(delta):
    if not bakeGroups:
        mset.err("No bake groups found. Create a bake project first.")
        return
    if viewMode["value"] == "group":
        index = (bakeIndex["value"] + delta) % len(bakeGroups)
    else:
        index = 0 if delta > 0 else len(bakeGroups) - 1
    go_to_group_index(index)


def pick_bake_group():
    index = groupList.selectedItem
    if index == 0:
        show_all()
        return
    if bakeGroups:
        go_to_group_index(max(0, min(index - LIST_HEADER_COUNT, len(bakeGroups) - 1)))


def set_bake_mode(name):
    bakeMode["value"] = name
    lowCheck.value = name == "low"
    highCheck.value = name == "high"
    bothCheck.value = name == "both"
    if bakeGroups:
        viewMode["value"] = "group"
        sync_list_selection()
    apply_visibility()
    force_redraw()


def current_group_and_low():
    group = current_bake_group(quiet=True)
    return (group, None) if group is None else (group, low_folder(group))


def apply_offset(name, value):
    group, low = current_group_and_low()
    if low is None:
        return
    try:
        setattr(low, name, value)
    except Exception as error:
        print("Could not set " + name + " on '" + group.name + "': " + str(error))
    mset.refreshUI()
    force_redraw()


CAGE_OPACITY_PROPERTIES = ("cageOpacity", "opacity", "previewOpacity", "cageAlpha", "cagePreviewOpacity")


def apply_cage_opacity(value):
    group, low = current_group_and_low()
    if low is None:
        return
    applied = False
    for prop in CAGE_OPACITY_PROPERTIES:
        try:
            setattr(low, prop, value)
            applied = True
            break
        except Exception:
            continue
    if not applied:
        matches = [name for name in dir(low) if not name.startswith("_")
                   and ("opac" in name.lower() or "cage" in name.lower())]
        print("'Low' opacity property not found. Candidates tried: " + ", ".join(CAGE_OPACITY_PROPERTIES) +
              ". Attributes on '" + group.name + "' that look related: " + (", ".join(matches) if matches else "none found"))
    mset.refreshUI()
    force_redraw()


def load_cage_values(group):
    low = low_folder(group)
    if low is None:
        return
    for control, prop in ((minOffsetSlider, "minOffset"), (maxOffsetSlider, "maxOffset")):
        try:
            value = getattr(low, prop)
            control.value = value
            if value > control.max:
                print(prop + " on '" + group.name + "' is " + str(value) +
                      ", above the slider's max of " + str(control.max) + " - it will show clamped.")
        except Exception:
            pass
    for prop in CAGE_OPACITY_PROPERTIES:
        try:
            cageOpacitySlider.value = getattr(low, prop)
            break
        except Exception:
            continue


def bind_events(control, names, handler):
    for name in names:
        try:
            setattr(control, name, handler)
        except Exception:
            pass


def button(text, action):
    control = mset.UIButton(text)
    control.onClick = action
    return control


def field(action):
    control = mset.UITextField()
    control.onChange = action
    return control


def checkbox(label, action):
    try:
        control = mset.UICheckBox(name=label)
    except Exception:
        control = mset.UICheckBox()
        try:
            control.text = label
        except Exception:
            pass
    bind_events(control, ("onChange",), action)
    return control


def slider(label, default, log_scale, action):
    try:
        control = mset.UISliderFloat(min=0.0, max=1.0, name=label, logScale=log_scale) if log_scale \
            else mset.UISliderFloat(min=0.0, max=1.0, name=label)
    except Exception:
        control = mset.UISliderFloat(min=0.0, max=1.0, name=label)
    control.value = default
    bind_events(control, ("onChange",), action)
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
isolateButton = button("   Isolate Selected   ", toggle_isolate_selected)

bakeGroups = get_bake_groups()
groupList = mset.UIListBox("")
try:
    groupList.width = 220
except Exception:
    pass
groupList.addItem("Show All")
for group in bakeGroups:
    groupList.addItem(group.name)
sync_list_selection()
bind_events(groupList, ("onChange", "onClick", "onSelect", "onItemSelected"), pick_bake_group)

lowCheck = checkbox("Low", lambda: set_bake_mode("low"))
highCheck = checkbox("High", lambda: set_bake_mode("high"))
bothCheck = checkbox("Both", lambda: set_bake_mode("both"))
bothCheck.value = True

apply_visibility()

minOffsetSlider = slider("Min Offset", 0.0, 2.0, lambda: apply_offset("minOffset", minOffsetSlider.value))
maxOffsetSlider = slider("Max Offset", 0.01, 2.0, lambda: apply_offset("maxOffset", maxOffsetSlider.value))
cageOpacitySlider = slider("Cage Opacity", 0.5, None, lambda: apply_cage_opacity(cageOpacitySlider.value))

layout = [
    drawer("Scene", lambda: [
        [button("Collapse Everything", collapse_everything)],
        [button("Hide Everything", hide_everything),
         button("Show Everything", show_everything)],
        [isolateButton],
        [drawer("Transforms", lambda: [
            [button("Copy", copy_transform), button("Paste", paste_transform)],
            [button("Copy Multiple", copy_multiple_transforms),
             button("Duplicate and Paste", duplicate_and_paste_transforms)],
            [""],
            [button("Reset All", lambda: reset_transform(True, True, True)), ""],
            [button("Reset Position", lambda: reset_transform(True, False, False)),
             button("Reset Scale", lambda: reset_transform(False, False, True)),
             button("Reset Rotation", lambda: reset_transform(False, True, False))],
        ])],
    ]),
    drawer("Selecting", lambda: [
        [button("Select all geometry in the scene", select_all_geometry)],
        [button("Select all light sources in the scene", select_all_lights)],
        [button("Select all cameras in the scene", select_all_cameras)],
        [searchField, button("Find geo and Select", find_and_select)],
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
    drawer("Baking", lambda: [
        [button("<", lambda: step_bake_group(-1)), groupList, button(">", lambda: step_bake_group(1))],
        [lowCheck, highCheck, bothCheck],
        [minOffsetSlider],
        [maxOffsetSlider],
        [cageOpacitySlider],
    ]),
]

for section in layout:
    window.addElement(section)
    window.addReturn()
window.addElement(mset.UILabel(""))
window.addReturn()
window.addElement(mset.UILabel("Made by SpeedySquirrel  -  GitHub: SpeedySquirrel"))
window.addReturn()
