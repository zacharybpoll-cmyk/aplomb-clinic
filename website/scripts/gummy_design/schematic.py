"""
Technical schematic PDF — bottle elevation + label dieline.

One page per bottle SKU. Two views per page:
  Top:   bottle elevation (front view) with all dimensions called out
  Bottom: label dieline flat with bleed/safety zones, panel divisions

Output: business documents/packaging/gummy/Aplomb_Calm_Gummy_Schematic.pdf
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Ellipse
from matplotlib.lines import Line2D

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")

# Page is 17 × 22" (tabloid Plus / B-size) for clean dimension callouts
PAGE_W_IN = 17.0
PAGE_H_IN = 22.0


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",
    })


def _make_page():
    fig = plt.figure(figsize=(PAGE_W_IN, PAGE_H_IN), dpi=300, facecolor=g.BG_HEX)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, PAGE_W_IN)
    ax.set_ylim(0, PAGE_H_IN)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def _header(ax, bottle: g.BottleSpec):
    ax.text(0.6, PAGE_H_IN - 0.7, "Aplomb.",
            family="Cormorant Garamond", fontsize=22,
            fontstyle="italic", color=g.AMBER_HEX)
    ax.text(PAGE_W_IN - 0.6, PAGE_H_IN - 0.7,
            "§ Outer packaging  ·  Technical schematic  ·  v1",
            family="IBM Plex Sans", fontsize=11,
            color=g.AMBER_HEX, ha="right")
    ax.plot([0.6, PAGE_W_IN - 0.6], [PAGE_H_IN - 0.95, PAGE_H_IN - 0.95],
            color=g.AMBER_HEX, linewidth=0.5)
    ax.text(0.6, PAGE_H_IN - 1.5, bottle.sku,
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=28, color=g.INK_HEX)
    ax.text(0.6, PAGE_H_IN - 1.95,
            f"{bottle.count}-count ginger gummies  ·  "
            f"{bottle.mg_ginger} mg ginger root extract + "
            f"{bottle.mg_b6} mg vitamin B6 per gummy  ·  "
            f"SUNI OEM stock 180 cc HDPE bottle",
            family="IBM Plex Sans", fontsize=11, color=g.MUTED_HEX)


def _legend(ax, x, y):
    items = [
        ("cut line",       g.INK_HEX, "-",     1.4),
        ("bleed (3 mm)",   "#2E7B3F", "--",    1.0),
        ("safety (3 mm)",  g.MUTED_HEX, ":",   1.0),
        ("dimension",      g.AMBER_HEX, "-",   0.8),
        ("panel division", g.RULE_HEX, "-.",   0.8),
    ]
    for i, (label, color, ls, lw) in enumerate(items):
        yy = y - i * 0.20
        ax.add_line(Line2D([x, x + 0.25], [yy, yy],
                           color=color, linestyle=ls, linewidth=lw))
        ax.text(x + 0.32, yy, label, family="IBM Plex Sans",
                fontsize=8, color=g.INK_HEX, va="center")


# ----- Bottle elevation (top half of page) ---------------------------------

def _draw_bottle_elevation(ax, bottle: g.BottleSpec, *, cx, base_y, scale):
    """Draw bottle elevation: base → body → shoulder → neck → cap.
    All dimensions in mm; `scale` converts mm → inches on the page."""

    s = scale
    body_dia = bottle.body_dia_mm * s
    body_h = bottle.body_h_mm * s
    shoulder_h = bottle.shoulder_h_mm * s
    neck_dia = bottle.neck_dia_mm * s
    neck_h = bottle.neck_h_mm * s
    cap_dia = bottle.cap_dia_mm * s
    cap_h = bottle.cap_h_mm * s

    half_body = body_dia / 2
    half_neck = neck_dia / 2
    half_cap = cap_dia / 2

    # Body (rounded base + straight wall)
    body_left = cx - half_body
    body_bottom = base_y
    body_top = body_bottom + body_h
    ax.add_patch(FancyBboxPatch(
        (body_left, body_bottom), body_dia, body_h,
        boxstyle=f"round,pad=0,rounding_size={bottle.base_radius_mm * s}",
        facecolor="white", edgecolor=g.INK_HEX, linewidth=1.4, zorder=2,
    ))

    # Shoulder (curved transition body → neck)
    shoulder_top = body_top + shoulder_h
    # Approximate shoulder with a trapezoid + bezier-ish curve via two lines
    ax.plot([body_left, cx - half_neck],
            [body_top, shoulder_top],
            color=g.INK_HEX, linewidth=1.4, zorder=2)
    ax.plot([body_left + body_dia, cx + half_neck],
            [body_top, shoulder_top],
            color=g.INK_HEX, linewidth=1.4, zorder=2)
    # fill shoulder area
    ax.fill([body_left, cx - half_neck, cx + half_neck, body_left + body_dia],
            [body_top, shoulder_top, shoulder_top, body_top],
            color="white", zorder=1)

    # Neck (straight)
    neck_top = shoulder_top + neck_h
    ax.add_patch(Rectangle(
        (cx - half_neck, shoulder_top), neck_dia, neck_h,
        facecolor="white", edgecolor=g.INK_HEX, linewidth=1.4, zorder=2,
    ))
    # 38-400 thread hint (3 horizontal ticks)
    for i in range(3):
        yy = shoulder_top + neck_h * (0.25 + 0.25 * i)
        ax.plot([cx - half_neck + 0.04, cx + half_neck - 0.04], [yy, yy],
                color=g.MUTED_HEX, linewidth=0.4, zorder=3)

    # Cap (slightly wider than neck)
    cap_top = neck_top + cap_h
    ax.add_patch(FancyBboxPatch(
        (cx - half_cap, neck_top), cap_dia, cap_h,
        boxstyle="round,pad=0,rounding_size=0.04",
        facecolor=g.CAP_HEX, edgecolor=g.INK_HEX, linewidth=1.0, zorder=3,
    ))
    # Cap knurl ticks
    n_ticks = 18
    for i in range(n_ticks):
        xx = cx - half_cap + (i + 0.5) * (cap_dia / n_ticks)
        ax.plot([xx, xx], [neck_top + 0.04, cap_top - 0.04],
                color="#3A3024", linewidth=0.3, zorder=4)

    # ------- Label outline on bottle (shows where label sits) -------------
    label_h_p = bottle.label_h_mm * s
    label_y = body_bottom + bottle.label_y_offset_mm * s
    ax.add_patch(Rectangle(
        (body_left + 0.04, label_y), body_dia - 0.08, label_h_p,
        facecolor=g.BONE_HEX, edgecolor=g.AMBER_HEX,
        linestyle=(0, (4, 3)), linewidth=0.7, zorder=3,
    ))
    ax.text(cx, label_y + label_h_p / 2, "label area",
            family="IBM Plex Sans", fontsize=8, color=g.AMBER_HEX,
            ha="center", va="center", alpha=0.7, zorder=4)

    # ------- Dimension callouts -------------------------------------------
    # Total height (left side)
    dim_x = body_left - 0.55
    _vertical_dim(ax, dim_x, base_y, cap_top,
                  f"{bottle.total_h_mm:.0f} mm  ·  total height")
    # Body diameter (below)
    _horizontal_dim(ax, body_left, body_left + body_dia, base_y - 0.35,
                    f"{bottle.body_dia_mm:.0f} mm  ·  body Ø")
    # Cap diameter (above)
    _horizontal_dim(ax, cx - half_cap, cx + half_cap, cap_top + 0.40,
                    f"{bottle.cap_dia_mm:.0f} mm  ·  cap Ø")
    # Body height (right side)
    dim_x_r = body_left + body_dia + 0.45
    _vertical_dim(ax, dim_x_r, body_bottom, body_top,
                  f"{bottle.body_h_mm:.0f}  ·  body H", side="right")
    # Neck height
    _vertical_dim(ax, dim_x_r, shoulder_top, neck_top,
                  f"{bottle.neck_h_mm:.0f}  ·  neck H", side="right")
    # Cap height
    _vertical_dim(ax, dim_x_r, neck_top, cap_top,
                  f"{bottle.cap_h_mm:.0f}  ·  cap H", side="right")
    # Neck diameter (callout to top)
    ax.plot([cx, cx + 1.6], [shoulder_top + neck_h * 0.5,
                              shoulder_top + neck_h * 0.5 + 0.4],
            color=g.AMBER_HEX, linewidth=0.5, zorder=5)
    ax.text(cx + 1.65, shoulder_top + neck_h * 0.5 + 0.45,
            f"38-400 neck Ø {bottle.neck_dia_mm:.0f} mm  ·  CRC induction-seal",
            family="IBM Plex Sans", fontsize=8, color=g.AMBER_HEX, zorder=5)


def _vertical_dim(ax, x, y0, y1, text, *, side="left"):
    ax.plot([x, x], [y0, y1], color=g.AMBER_HEX, linewidth=0.6)
    ax.plot([x - 0.06, x + 0.06], [y0, y0], color=g.AMBER_HEX, linewidth=0.6)
    ax.plot([x - 0.06, x + 0.06], [y1, y1], color=g.AMBER_HEX, linewidth=0.6)
    if side == "left":
        ax.text(x - 0.10, (y0 + y1) / 2, text,
                family="IBM Plex Sans", fontsize=8, color=g.AMBER_HEX,
                ha="right", va="center", rotation=90)
    else:
        ax.text(x + 0.10, (y0 + y1) / 2, text,
                family="IBM Plex Sans", fontsize=8, color=g.AMBER_HEX,
                ha="left", va="center", rotation=90)


def _horizontal_dim(ax, x0, x1, y, text):
    ax.plot([x0, x1], [y, y], color=g.AMBER_HEX, linewidth=0.6)
    ax.plot([x0, x0], [y - 0.06, y + 0.06], color=g.AMBER_HEX, linewidth=0.6)
    ax.plot([x1, x1], [y - 0.06, y + 0.06], color=g.AMBER_HEX, linewidth=0.6)
    ax.text((x0 + x1) / 2, y - 0.18, text,
            family="IBM Plex Sans", fontsize=8, color=g.AMBER_HEX,
            ha="center", va="top")


# ----- Label dieline (bottom half of page) ---------------------------------

def _draw_label_dieline(ax, bottle: g.BottleSpec, *, x0, y0, scale):
    """Flat label rectangle with bleed, safety zone, and panel divisions."""
    s = scale
    w = bottle.label_flat_w_mm * s
    h = bottle.label_flat_h_mm * s
    bleed = g.BLEED_MM * s
    safe = g.SAFE_MM * s

    # Bleed rect (outermost, dashed green)
    ax.add_patch(Rectangle(
        (x0 - bleed, y0 - bleed), w + 2 * bleed, h + 2 * bleed,
        facecolor=g.BONE_HEX, edgecolor="#2E7B3F",
        linestyle=(0, (5, 3)), linewidth=0.8, zorder=1,
    ))
    # Cut line (solid black)
    ax.add_patch(Rectangle(
        (x0, y0), w, h,
        facecolor="none", edgecolor=g.INK_HEX, linewidth=1.4, zorder=3,
    ))
    # Safety zone (dotted gray)
    ax.add_patch(Rectangle(
        (x0 + safe, y0 + safe), w - 2 * safe, h - 2 * safe,
        facecolor="none", edgecolor=g.MUTED_HEX,
        linestyle=(0, (1, 2)), linewidth=0.6, zorder=4,
    ))

    # Panel divisions (dash-dot)
    pw = bottle.panel_widths_mm
    x_facts = x0
    x_front = x0 + pw["facts"] * s
    x_desc = x_front + pw["front"] * s
    x_end = x_desc + pw["description"] * s
    for xv in (x_front, x_desc):
        ax.plot([xv, xv], [y0, y0 + h],
                color=g.RULE_HEX, linestyle=(0, (5, 2, 1, 2)),
                linewidth=0.7, zorder=5)
    # Seam allowance (overlap on far right)
    overlap_x = x_end + bottle.label_overlap_mm * s
    if overlap_x > x_end:
        ax.add_patch(Rectangle(
            (x_end, y0), overlap_x - x_end, h,
            facecolor="none", edgecolor=g.AMBER_HEX,
            linestyle=(0, (2, 2)), linewidth=0.5,
            hatch="///", zorder=4,
        ))
        ax.text((x_end + overlap_x) / 2, y0 + h + 0.10,
                f"{bottle.label_overlap_mm:.0f} mm  overlap",
                family="IBM Plex Sans", fontsize=7,
                color=g.AMBER_HEX, ha="center", va="bottom")

    # Panel labels
    panels = [
        ("facts", "Supplement Facts panel", x_facts, pw["facts"]),
        ("front", "Front (hero) panel",     x_front, pw["front"]),
        ("description", "Description panel", x_desc, pw["description"]),
    ]
    for key, label, xstart, w_mm in panels:
        cx = xstart + w_mm * s / 2
        ax.text(cx, y0 + h - 0.18, label,
                family="IBM Plex Sans", fontsize=8,
                color=g.AMBER_HEX, ha="center", va="top",
                fontstyle="italic")
        ax.text(cx, y0 + 0.18,
                f"{w_mm:.1f} × {bottle.label_flat_h_mm:.1f} mm",
                family="IBM Plex Sans", fontsize=7,
                color=g.MUTED_HEX, ha="center", va="bottom")

    # Outer dimension callouts
    _horizontal_dim(ax, x0, x0 + w, y0 - 0.45,
                    f"{bottle.label_flat_w_mm:.1f} mm  ·  cut width")
    _vertical_dim(ax, x0 - 0.55, y0, y0 + h,
                  f"{bottle.label_flat_h_mm:.0f} mm  ·  cut height")
    # Bleed callout
    ax.text(x0 + w + 0.10, y0 + h + bleed,
            f"+{g.BLEED_MM:.0f} mm bleed all sides",
            family="IBM Plex Sans", fontsize=7,
            color="#2E7B3F", ha="left", va="center")


# ----- Main render ---------------------------------------------------------

def render(bottle: g.BottleSpec, out_path: Path):
    _set_style()
    fig, ax = _make_page()
    _header(ax, bottle)

    # Section A — bottle elevation
    ax.text(0.6, PAGE_H_IN - 3.0, "A  Bottle elevation",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=18, color=g.AMBER_HEX)
    ax.plot([0.6, 5.5], [PAGE_H_IN - 3.20, PAGE_H_IN - 3.20],
            color=g.AMBER_HEX, linewidth=0.4)
    # 1 mm = 0.06 in (so a 128mm bottle is ~7.7" tall on page)
    bottle_scale = 0.06
    base_y = PAGE_H_IN - 3.6 - bottle.total_h_mm * bottle_scale
    _draw_bottle_elevation(ax, bottle,
                           cx=PAGE_W_IN / 2,
                           base_y=base_y,
                           scale=bottle_scale)

    # Section B — label dieline
    sec_b_y = base_y - 1.5
    ax.text(0.6, sec_b_y, "B  Label dieline (flat)",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=18, color=g.AMBER_HEX)
    ax.plot([0.6, 5.5], [sec_b_y - 0.20, sec_b_y - 0.20],
            color=g.AMBER_HEX, linewidth=0.4)
    label_scale = 0.075   # 1 mm = 0.075 in → label ~15" wide, fits page
    label_w_in = bottle.label_flat_w_mm * label_scale
    label_h_in = bottle.label_flat_h_mm * label_scale
    label_x0 = (PAGE_W_IN - label_w_in) / 2
    label_y0 = sec_b_y - 1.0 - label_h_in
    _draw_label_dieline(ax, bottle,
                        x0=label_x0, y0=label_y0, scale=label_scale)

    # Legend (bottom-right)
    _legend(ax, PAGE_W_IN - 3.5, 2.0)

    # Footer
    ax.plot([0.6, PAGE_W_IN - 0.6], [1.1, 1.1],
            color=g.AMBER_HEX, linewidth=0.4)
    ax.text(0.6, 0.75, "Aplomb.",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=14, color=g.AMBER_HEX)
    ax.text(PAGE_W_IN - 0.6, 0.75,
            "All dims in mm. Bottle = SUNI 180 cc HDPE stock. "
            "Items marked [CONFIRM] in geometry.py to be locked on RFQ.",
            family="IBM Plex Sans", fontsize=8,
            color=g.MUTED_HEX, ha="right")

    fig.savefig(out_path, format="pdf",
                facecolor=g.BG_HEX, bbox_inches=None, pad_inches=0)
    plt.close(fig)
    kb = out_path.stat().st_size // 1024
    print(f"Wrote {out_path.name} ({kb} KB)")


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for bottle in g.ALL_BOTTLES:
        suffix = bottle.sku.replace("Aplomb. ", "").replace(" ", "_")
        render(bottle, OUT_DIR / f"Aplomb_{suffix}_Gummy_Schematic.pdf")


if __name__ == "__main__":
    render_all()
