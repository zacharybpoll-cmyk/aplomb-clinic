"""
Embed brand SVG logos (aplomb-logo.svg, aplomb-wordmark.svg) into a
matplotlib axes as native vector PathPatches.

The canonical SVGs are outlined paths (no font dependency). Their path
data uses only M / L / H / V / Q / Z commands with absolute coordinates,
and transforms are `translate(x,y)` and `scale(sx[,sy])` only.
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

SVG_NS = "{http://www.w3.org/2000/svg}"


# ---------- transform parser -------------------------------------------------

_TRANSFORM_RE = re.compile(r"(translate|scale)\s*\(([^)]*)\)")


def _parse_transform(s):
    """Parse a transform string into a 3×3 affine matrix (homogeneous)."""
    M = np.eye(3)
    if not s:
        return M
    for fn, args in _TRANSFORM_RE.findall(s):
        nums = [float(t) for t in re.split(r"[,\s]+", args.strip()) if t]
        T = np.eye(3)
        if fn == "translate":
            tx = nums[0]
            ty = nums[1] if len(nums) > 1 else 0.0
            T[0, 2] = tx
            T[1, 2] = ty
        elif fn == "scale":
            sx = nums[0]
            sy = nums[1] if len(nums) > 1 else sx
            T[0, 0] = sx
            T[1, 1] = sy
        M = M @ T
    return M


def _apply(M, x, y):
    v = M @ np.array([x, y, 1.0])
    return v[0], v[1]


# ---------- SVG path data parser --------------------------------------------

_TOKEN_RE = re.compile(r"[MmLlHhVvQqTtCcSsZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _parse_path_d(d):
    """Parse SVG `d=...` into a list of (cmd, [x, y]) operations in absolute
    coordinates. Returns ([(x,y), ...], [code, ...]) ready for mpl Path."""
    tokens = _TOKEN_RE.findall(d)
    i = 0
    cur_x = cur_y = 0.0
    start_x = start_y = 0.0
    verts = []
    codes = []
    cmd = None
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
        # absolute coords only (canonical SVGs use uppercase). Handle
        # lowercase gracefully by treating same-as-uppercase if no current
        # point relative use is expected.
        u = cmd.upper() if cmd else None
        rel = cmd.islower() if cmd else False

        def num():
            nonlocal i
            v = float(tokens[i])
            i += 1
            return v

        if u == "M":
            x = num(); y = num()
            if rel: x += cur_x; y += cur_y
            verts.append((x, y))
            codes.append(MplPath.MOVETO)
            cur_x, cur_y = x, y
            start_x, start_y = x, y
            # Subsequent coord pairs after M are treated as L
            cmd = "L" if cmd == "M" else "l"
        elif u == "L":
            x = num(); y = num()
            if rel: x += cur_x; y += cur_y
            verts.append((x, y))
            codes.append(MplPath.LINETO)
            cur_x, cur_y = x, y
        elif u == "H":
            x = num()
            if rel: x += cur_x
            verts.append((x, cur_y))
            codes.append(MplPath.LINETO)
            cur_x = x
        elif u == "V":
            y = num()
            if rel: y += cur_y
            verts.append((cur_x, y))
            codes.append(MplPath.LINETO)
            cur_y = y
        elif u == "Q":
            cx = num(); cy = num(); x = num(); y = num()
            if rel:
                cx += cur_x; cy += cur_y
                x += cur_x;  y += cur_y
            verts.append((cx, cy))
            codes.append(MplPath.CURVE3)
            verts.append((x, y))
            codes.append(MplPath.CURVE3)
            cur_x, cur_y = x, y
        elif u == "C":
            c1x = num(); c1y = num()
            c2x = num(); c2y = num()
            x = num(); y = num()
            if rel:
                c1x += cur_x; c1y += cur_y
                c2x += cur_x; c2y += cur_y
                x += cur_x;   y += cur_y
            verts.append((c1x, c1y)); codes.append(MplPath.CURVE4)
            verts.append((c2x, c2y)); codes.append(MplPath.CURVE4)
            verts.append((x, y));     codes.append(MplPath.CURVE4)
            cur_x, cur_y = x, y
        elif u == "Z":
            verts.append((start_x, start_y))
            codes.append(MplPath.CLOSEPOLY)
            cur_x, cur_y = start_x, start_y
        else:
            raise ValueError(f"Unsupported SVG path command: {cmd!r} at token {i}")
    return verts, codes


# ---------- main entry point -------------------------------------------------

def _collect_paths(elem, M_parent):
    """Walk the SVG tree, accumulating (verts_transformed, codes, fill)
    tuples in viewBox coordinate space."""
    out = []
    M_self = M_parent @ _parse_transform(elem.attrib.get("transform", ""))
    fill_self = elem.attrib.get("fill")
    tag = elem.tag.replace(SVG_NS, "")
    if tag == "path":
        d = elem.attrib["d"]
        verts, codes = _parse_path_d(d)
        # transform each vertex into viewBox space
        verts_xy = np.array([_apply(M_self, x, y) for x, y in verts])
        out.append((verts_xy, codes, fill_self))
    else:
        # inherit fill from group if path has none
        for child in elem:
            child_fill = child.attrib.get("fill")
            if not child_fill and fill_self:
                child.attrib["fill"] = fill_self
            out.extend(_collect_paths(child, M_self))
    return out


def draw_svg_logo(ax, svg_path, *, anchor_xy, target_height_in,
                  ha="center", va="center", zorder=10,
                  fill_override=None):
    """Draw an outlined-path SVG logo onto a matplotlib axes.

    Args:
        ax: matplotlib axes (in inches, y-up).
        svg_path: path to the SVG file.
        anchor_xy: (x, y) in axes coordinates (inches) where the logo
            is anchored, per ha/va.
        target_height_in: uniform-scale the logo so the SVG viewBox
            height maps to this many axes-inches.
        ha: "left" | "center" | "right" — horizontal anchor on the
            logo's bounding box.
        va: "bottom" | "center" | "top" — vertical anchor.
        zorder: matplotlib zorder for the PathPatches.
        fill_override: if set, every path is filled with this color
            (otherwise the SVG's `fill="#..."` attributes are honored).
    """
    tree = ET.parse(str(svg_path))
    root = tree.getroot()

    vb = root.attrib.get("viewBox")
    if not vb:
        raise ValueError(f"SVG missing viewBox: {svg_path}")
    vb_x, vb_y, vb_w, vb_h = (float(t) for t in re.split(r"[,\s]+", vb.strip()))

    paths = _collect_paths(root, np.eye(3))

    # uniform scale to fit target height; logo will keep its aspect ratio.
    scale = target_height_in / vb_h
    width_in = vb_w * scale

    # anchor offsets within the logo's bounding box (in inches)
    if ha == "left":
        ax_x = anchor_xy[0]
    elif ha == "right":
        ax_x = anchor_xy[0] - width_in
    else:
        ax_x = anchor_xy[0] - width_in / 2

    if va == "bottom":
        ay_y = anchor_xy[1]
    elif va == "top":
        ay_y = anchor_xy[1] - target_height_in
    else:
        ay_y = anchor_xy[1] - target_height_in / 2

    for verts_vb, codes, fill in paths:
        # viewBox coords → canvas inches.
        # SVG y grows downward; matplotlib y grows upward → flip:
        #   y_canvas = (vb_h - (y_svg - vb_y)) * scale + ay_y
        # x:  x_canvas = (x_svg - vb_x) * scale + ax_x
        xs = (verts_vb[:, 0] - vb_x) * scale + ax_x
        ys = (vb_h - (verts_vb[:, 1] - vb_y)) * scale + ay_y
        pts = np.column_stack([xs, ys])
        mpath = MplPath(pts, codes)
        color = fill_override or fill or "#000000"
        ax.add_patch(PathPatch(
            mpath, facecolor=color, edgecolor="none",
            linewidth=0, zorder=zorder,
        ))
