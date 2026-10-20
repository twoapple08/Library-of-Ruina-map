"""Rebuild the reference's rectangular X-braced table with Blender 4.5.3.

Run from the repo using the isolated Blender Python environment. Blender is an
authoring dependency only; normal world builds load the committed bbmodel.
"""
import base64
import io
import json
import math
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy
from mathutils import Vector
from tools import form_textures as T
from tools import forms as F


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    objects = []

    def box(name, lo, hi, bevel=.012):
        # Minecraft (x,y,z) -> Blender (x,-z,y), a proper rotation.
        lo, hi = Vector(lo), Vector(hi)
        c = (lo + hi) * .5
        bpy.ops.mesh.primitive_cube_add(size=1, location=(c.x, -c.z, c.y))
        obj = bpy.context.object
        obj.name = name
        delta = hi - lo
        obj.dimensions = (delta.x, delta.z, delta.y)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mod = obj.modifiers.new("edge chamfer", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
        objects.append(obj)
        return obj

    def brace(name, a, b):
        a, b = Vector(a), Vector(b)
        length = (b-a).length
        obj = box(name, (-.055, -.055, -length/2), (.055, .055, length/2), .008)
        direction = Vector((b.x-a.x, -(b.z-a.z), b.y-a.y))
        obj.rotation_euler = direction.to_track_quat("Y", "Z").to_euler()
        c = (a+b)*.5
        obj.location = (c.x, -c.z, c.y)

    # Keep the original table's width and height envelope; replace the circular
    # silhouette with the rectangular top and visible crossed trestles in ART.
    box("solid tabletop", (-1.3, .89, -.54), (1.3, 1, .54), .025)
    box("recessed apron", (-1.16, .76, -.43), (1.16, .89, .43))
    for z in (-.35, .35):
        box(f"foot {z}", (-.96, 0, z-.09), (.96, .10, z+.09))
        brace(f"cross left {z}", (-.83, .10, z), (.75, .77, z))
        brace(f"cross right {z}", (.83, .10, z), (-.75, .77, z))
    box("longitudinal stretcher", (-.10, .19, -.41), (.10, .29, .41))
    bpy.context.view_layer.update()

    sprite = T.wood("table_editor_preview", (110, 70, 30), (210, 160, 90), seed=163)
    image = F.TEXTURES[sprite.removeprefix("ruina:block/form/")]
    image = image.resize((64, 64))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    elements = []
    for obj in objects:
        mesh = obj.data
        # Bevel creates n-gons at the old cube faces. Triangulate only n-gons;
        # preserve planar quads and their simple explicit UVs.
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bm.to_mesh(mesh)
        bm.free()
        vertices = {}
        for v in mesh.vertices:
            p = obj.matrix_world @ v.co
            vertices[str(v.index)] = [round(p.x*16, 7), round(p.z*16, 7), round(-p.y*16, 7)]
        faces = {}
        for f in mesh.polygons:
            keys = [str(i) for i in f.vertices]
            coords = [(0, 0), (64, 0), (64, 64), (0, 64)][:len(keys)]
            faces[str(f.index)] = {"vertices": keys, "uv": dict(zip(keys, coords)), "texture": 0}
        elements.append({"type": "mesh", "name": obj.name,
                         "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "ruina/tiphereth/"+obj.name)),
                         "origin": [0, 0, 0], "rotation": [0, 0, 0],
                         "vertices": vertices, "faces": faces})
    data = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": "Tiphereth reference X-braced table", "resolution": {"width": 64, "height": 64},
            "elements": elements, "outliner": [e["uuid"] for e in elements],
            "textures": [{"name": "table_wood.png", "id": "0", "uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "ruina/table_wood")),
                          "width": 64, "height": 64, "uv_width": 64, "uv_height": 64,
                          "source": "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()}]}
    path = ROOT / "design/models/tiphereth_table.bbmodel"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"))+"\n", encoding="utf-8")
    print(f"Blender {bpy.app.version_string}: {len(elements)} parts, {sum(len(e['faces']) for e in elements)} faces -> {path}")


if __name__ == "__main__":
    main()
