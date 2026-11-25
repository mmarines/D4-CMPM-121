# /// script
# requires-python = "==3.13.*"
# dependencies = ["bpy==5.2.*"]
# ///
"""Blender as a library: build the kit, art/dragon_kit.glb and art/dragon_kit.blend.

deno task art      uses Blender 5.2 (the header above)
deno task art:lts  uses Blender 4.5 LTS, for Intel Macs, which Blender 5 dropped
deno task blender  opens art/dragon_kit.blend in the Blender app, to look around

Every piece fills one 1x1 grid cell and is made by a builder function listed in
PIECES (the dragon) or TILES (the ground). The starter's builders all use voxels(),
but a builder can make any geometry: swap one out and the game picks it up by name.

Conventions the game relies on (Blender coordinates, Z up):
  - A cell spans x and y from -0.5 to 0.5. +Y is the direction of travel.
  - Openings must match Kit.OPENINGS in core/kit.gd: the head and tail join the
    body at the back and front, the turn joins the back and the right side.
  - Floors lie with their top at z = 0; everything else stands on z = 0.

All models are generated here. Run deno task art to rebuild both files.
The food mesh is exported separately from the body and tile registries.
"""

from pathlib import Path

import bpy  # first: importing bpy is what makes bmesh and mathutils available
import bmesh
from mathutils import Matrix

# Paths from this file, not the current directory, so the script works from anywhere.
# Build them with pathlib rather than gluing strings together, as Blender's gotchas advise:
# https://docs.blender.org/api/current/info_gotchas_file_paths_and_encoding.html
ART = Path(__file__).resolve().parent.parent / "art"
GLB = ART / "dragon_kit.glb"
BLEND = ART / "dragon_kit.blend"

VOXELS = 4  # voxels per cell edge

MATERIALS = []  # every material, in order; a face's material_index points into this list
PALETTE = {}  # voxel character -> index in MATERIALS; filled in by make_materials()


def reset_scene():
    """Start from an empty file, so nothing from Blender's default scene (cube, camera,
    light) or an earlier run leaks into the kit."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


# --- Materials ------------------------------------------------------------------


def pbr_material(name, color, metallic=0.0, roughness=0.5, emission=None, strength=1.0):
    """A Principled BSDF using only inputs glTF keeps. Returns its index in MATERIALS.
    Emission above about 1 blooms in the game, because the stage has glow switched on."""
    material = bpy.data.materials.new(name)
    if bpy.app.version < (5, 0):  # 4.x starts without nodes; 5.x always has them and deprecates use_nodes
        material.use_nodes = True
    # Find the node by type, not by its name, which a non-English Blender may translate:
    # https://terminalskills.io/skills/blender-scripting (section 9, Assign materials)
    bsdf = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = srgb(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:  # glTF keeps a color up to 1 plus a strength (KHR_materials_emissive_strength)
        bsdf.inputs["Emission Color"].default_value = srgb(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    material.diffuse_color = srgb(color)  # the viewport's solid color, for the GUI
    MATERIALS.append(material)
    return len(MATERIALS) - 1


def srgb(hex_code):
    """A hex color as Blender wants it: linear RGBA."""
    channels = [int(hex_code.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels) + (1.0,)


def make_materials():
    """One material per voxel character. Runs after reset_scene(), which would erase them."""
    PALETTE.update({
        "r": pbr_material("Rice", "#f5f0e1", roughness=0.85),
        "n": pbr_material("Nori", "#20382b", roughness=0.7),
        "s": pbr_material("Salmon", "#fa8067", roughness=0.35),
        "f": pbr_material("Salmon Stripe", "#ffd2b8", roughness=0.4),
        "e": pbr_material("Eye", "#171717", roughness=0.3),
        "w": pbr_material("Wood", "#c99a65", roughness=0.85),
        "g": pbr_material("Wood Grain", "#b88755", roughness=0.85),
        "b": pbr_material("Board Rim", "#795333", roughness=0.65),
        "o": pbr_material("Ingredient", "#ff6949", roughness=0.35),
    })


# --- Builders: each adds one piece's geometry to a bmesh ------------------------------
# bmesh builds meshes from data alone, with no edit mode or selection involved; Blender
# calls it the best way to create and edit faces:
# https://docs.blender.org/api/current/info_gotchas_meshes.html


def voxels(bm, layers, below_ground=0):
    """Add one cube per palette character. Each layer is a top-down view of the cell,
    from the ground up: the top row is the front (+Y), the bottom row is the back."""
    for z, layer in enumerate(layers):
        for row, line in enumerate(layer.split()):
            for column, char in enumerate(line):
                if char not in PALETTE:
                    continue
                center = (
                    (column + 0.5) / VOXELS - 0.5,
                    0.5 - (row + 0.5) / VOXELS,
                    (z - below_ground + 0.5) / VOXELS,
                )
                cube = bmesh.ops.create_cube(bm, size=1 / VOXELS, matrix=Matrix.Translation(center))
                for face in {f for v in cube["verts"] for f in v.link_faces}:
                    face.material_index = PALETTE[char]


def box(bm, material, center, dimensions):
    """A rectangular piece with explicit dimensions in grid-cell units."""
    transform = Matrix.Translation(center) @ Matrix.Diagonal((*dimensions, 1.0))
    cube = bmesh.ops.create_cube(bm, size=1.0, matrix=transform)
    for face in {f for v in cube["verts"] for f in v.link_faces}:
        face.material_index = PALETTE[material]


def sushi_segment(bm, openings, head=False, tail=False):
    """One nigiri per cell, with narrow nori links reaching the cell edges."""
    # The central block ends at +/- 0.36; connectors meet it exactly.
    box(bm, "r", (0, 0, 0.14), (0.72, 0.72, 0.28))
    box(bm, "s", (0, 0, 0.36), (0.72, 0.72, 0.16))
    # Salmon marbling, leaving the center clear for the nori belt.
    for y in (-0.26, 0.26):
        box(bm, "f", (0, y, 0.446), (0.64, 0.045, 0.012))
    # A continuous nori belt across the top and down both sides of the nigiri.
    # The three panels meet at their edges, with no buried overlapping volume.
    box(bm, "n", (0, 0, 0.452), (0.76, 0.19, 0.024))
    for x in (-0.37, 0.37):
        box(bm, "n", (x, 0, 0.22), (0.02, 0.19, 0.44))
    # A narrow seaweed link spans the gap between neighboring sushi blocks.
    # Each half-link stops at the cell edge; adjacent links touch, not overlap.
    for dx, dy in openings:
        if dx:
            # Split the link around the side belt so the central section meets it.
            box(bm, "n", (dx * 0.44, 0, 0.11), (0.12, 0.19, 0.22))
            for y in (-0.1225, 0.1225):
                box(bm, "n", (dx * 0.43, y, 0.11), (0.14, 0.055, 0.22))
        else:
            box(bm, "n", (0, dy * 0.43, 0.11), (0.30, 0.14, 0.22))
    if head:
        # Eyes are placed on the front half of the topping for top-down visibility.
        for x in (-0.23, 0.23):
            box(bm, "e", (x, 0.25, 0.475), (0.13, 0.13, 0.07))
    if tail:
        # A small nori cap marks the trailing end without extending beyond the cell.
        box(bm, "n", (0, -0.40, 0.11), (0.28, 0.08, 0.22))


def build_head(bm):
    sushi_segment(bm, [(0, -1)], head=True)


def build_straight(bm):
    sushi_segment(bm, [(0, -1), (0, 1)])


def build_turn(bm):
    sushi_segment(bm, [(0, -1), (1, 0)])


def build_tail(bm):
    sushi_segment(bm, [(0, 1)], tail=True)


def build_food(bm):
    voxels(bm, ["""
        ....
        .oo.
        .oo.
        ....
        """, """
        ....
        .of.
        .fo.
        ....
        """])


def build_floor(bm):
    voxels(bm, ["""
        wwww
        gggg
        wwww
        wwww
        """], below_ground=1)


def build_wall(bm):
    voxels(bm, ["""
        bbbb
        bbbb
        bbbb
        bbbb
        """, """
        wwww
        gggg
        wwww
        wwww
        """])


PIECES = {  # the dragon kit; the game finds each mesh by these names
    "head": build_head,
    "straight": build_straight,
    "turn": build_turn,
    "tail": build_tail,
}
TILES = {  # one entry per kind in core/board.gd's TILES; a new kind is one builder and one line
    "floor": build_floor,
    "wall": build_wall,
}


# --- Objects and layout ---------------------------------------------------------


def make_object(scene, name, build, location=(0, 0, 0)):
    """Run a builder on a fresh bmesh and turn the result into a mesh object called name.
    The game uses only the mesh; location just spreads the kit out for model viewers."""
    bm = bmesh.new()
    build(bm)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    # Keep only the materials this object uses, renumbering faces to match.
    used = sorted({p.material_index for p in mesh.polygons})
    mesh.polygons.foreach_set("material_index", [used.index(p.material_index) for p in mesh.polygons])
    for index in used:
        mesh.materials.append(MATERIALS[index])
    # bpy.data creates the object directly; bpy.ops.mesh.primitive_*_add would depend on
    # the active object and selection, which an operator reads from the context:
    # https://docs.blender.org/api/current/info_gotchas_operators.html
    obj = bpy.data.objects.new(name, mesh)
    # Blender quietly changes a name that is too long or already taken, and the game
    # finds pieces by name, so fail loudly instead:
    # https://docs.blender.org/api/current/info_gotchas_internal_data_and_python_objects.html
    if obj.name != name:
        raise ValueError(f"Blender renamed {name!r} to {obj.name!r}; pick a shorter, unique name")
    obj.location = location
    scene.collection.objects.link(obj)


def lay_out_kit(scene):
    """One row per registry, so a GLB viewer shows a tidy catalog instead of every piece
    stacked on the origin. Each mesh is still modeled around its own cell's center."""
    spacing = 1.5
    for row, registry in enumerate([PIECES, TILES]):
        for column, (name, build) in enumerate(registry.items()):
            make_object(scene, name, build, location=(column * spacing, -row * spacing, 0))
    make_object(scene, "food", build_food, location=(2 * spacing, -spacing, 0))


# --- Export ---------------------------------------------------------------------


def export():
    """Write the .glb the game loads, then the .blend for the Blender app.
    glTF export has no data API, only an operator, so every option that could depend
    on what is selected or active is spelled out. These match the steps in the docstring.
    Enum values such as 'GLB' get single quotes, Blender's own style:
    https://docs.blender.org/api/current/info_best_practice.html"""
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    # No art/dragon_kit.blend1 backup: the script is the backup, and the next run rewrites this.
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


def main():
    reset_scene()
    make_materials()
    lay_out_kit(bpy.context.scene)
    export()
    print(f"Built {GLB.name} and {BLEND.name} with Blender {bpy.app.version_string}")


# Run only as a script, not when another file imports this one for its builders:
# https://docs.python.org/3/library/__main__.html
if __name__ == "__main__":
    main()
