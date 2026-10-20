"""Import baked static Blockbench Generic meshes into the existing form renderer.

Deliberately strict: no runtime texture downloads, scripts, animation, cubes,
unbaked transforms, n-gons, or UV wrapping. Export/bake those first. Texture
indices are explicitly bound to existing form materials by the caller.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools import forms as F


def load_bbmodel(path, materials, *, units_per_block=16.0):
    """Positions use Minecraft X/Y-up/Z; UVs are Blockbench pixel coordinates.

    Textures embedded in bbmodel are editor previews only; rendering uses the
    supplied {texture_index: form_material_id} bindings. Collision is separate.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("meta", {}).get("model_format") != "free":
        raise ValueError("Only Blockbench Generic (free) meshes are supported")
    if data.get("animations"):
        raise ValueError("Animated models require a separate mover/rig workflow")
    if not np.isfinite(units_per_block) or units_per_block <= 0:
        raise ValueError("units_per_block must be positive and finite")
    resolution = data.get("resolution", {})
    size = np.array([resolution.get("width", 0), resolution.get("height", 0)], float)
    if not np.isfinite(size).all() or np.any(size <= 0):
        raise ValueError("Invalid texture resolution")
    elements = data.get("elements", [])
    ids = [e.get("uuid") for e in elements]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Missing/duplicate element UUID")
    refs = []

    def check_transform(node):
        for key, default in (("rotation", [0, 0, 0]), ("scale", [1, 1, 1])):
            value = np.asarray(node.get(key, default), float)
            if value.shape != (3,) or not np.isfinite(value).all() or not np.allclose(value, default):
                raise ValueError(f"Bake {key} before importing")

    def walk(nodes):
        for node in nodes:
            if isinstance(node, str):
                refs.append(node)
            elif isinstance(node, dict):
                check_transform(node)
                if node.get("visibility", True) is False or node.get("export", True) is False:
                    raise ValueError("Hidden/disabled groups must be removed before importing")
                walk(node.get("children", []))
            else:
                raise ValueError("Invalid outliner node")

    walk(data.get("outliner", []))
    if sorted(refs) != sorted(ids):
        raise ValueError("Outliner must reference every element exactly once")
    bindings = {str(k): v for k, v in materials.items()}
    points, uvs, mats = [], [], []
    for e in elements:
        if e.get("type") != "mesh":
            raise ValueError("Convert all elements to meshes before importing")
        check_transform(e)
        if e.get("visibility", True) is False or e.get("export", True) is False:
            raise ValueError("Hidden/disabled elements must be removed before importing")
        vertices = e.get("vertices", {})
        for face in e.get("faces", {}).values():
            keys = face.get("vertices", [])
            if len(keys) not in (3, 4) or len(set(keys)) != len(keys):
                raise ValueError("Faces must have 3 or 4 distinct vertices")
            try:
                p = np.asarray([vertices[k] for k in keys], float) / units_per_block
                uv = np.asarray([face["uv"][k] for k in keys], float) / size
                material = bindings[str(face["texture"])]
            except (KeyError, TypeError) as exc:
                raise ValueError("Missing vertex/UV/texture binding") from exc
            if p.shape != (len(keys), 3) or uv.shape != (len(keys), 2):
                raise ValueError("Invalid vertex/UV dimensions")
            if not np.isfinite(p).all() or not np.isfinite(uv).all():
                raise ValueError("Nonfinite geometry/UV")
            if np.any(uv < 0) or np.any(uv > 1):
                raise ValueError("UV wrapping is unsupported; bake into an atlas first")
            normal = np.cross(p[1] - p[0], p[2] - p[0])
            length = np.linalg.norm(normal)
            if length < 1e-10:
                raise ValueError("Degenerate face")
            if len(keys) == 4:
                if abs(np.dot(normal / length, p[3] - p[0])) > 1e-6:
                    raise ValueError("Triangulate nonplanar quads before importing")
                # Reject concave/bow-tie quads instead of letting the renderer
                # choose a different triangulation from the editor.
                edges = np.roll(p, -1, axis=0) - p
                turns = np.cross(edges, np.roll(edges, -1, axis=0)) @ normal
                if np.any(turns <= 1e-14):
                    raise ValueError("Triangulate concave/degenerate quads first")
            if not isinstance(material, (int, np.integer)) or not 0 <= material < len(F.MATERIALS):
                raise ValueError("Unknown form material")
            if len(keys) == 3:
                p = np.concatenate([p, p[-1:]])
                uv = np.concatenate([uv, uv[-1:]])
            points.append(p)
            uvs.append(uv)
            mats.append(material)
    if not points:
        raise ValueError("Empty model")
    return F.Quads(points, uvs, M=mats)
