"""
Production label artwork — flat dieline at exact dimensions with bleed.

One label per bottle SKU. Three zones along the wrap:
  Facts panel — Supplement Facts (FDA-compliant 21 CFR 101.36 layout)
  Front panel — Hero: wordmark + product name + plumb mark + tagline
  Description panel — One-paragraph description + dosing + URL

Outputs:  ..._Label.pdf  +  ..._Label.svg
The SVG is Illustrator-importable; designer drops onto SUNI's official
label dieline if minor positional tweaks are needed at proof stage.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from . import geometry as g

OUT_DIR = Path("/Users/zacharypoll/Desktop/Documents/Claude Code/"
               "aplomb.clinic/business documents/packaging/gummy")


def _set_style():
    plt.rcParams.update({
        "font.family": "IBM Plex Sans",
        "pdf.fonttype": 3,
        "ps.fonttype": 3,
        "svg.fonttype": "path",   # outline glyphs in SVG
    })


def _make_canvas(bottle: g.BottleSpec):
    """Figure sized to label cut + 3mm bleed each side, in mm.
    Matplotlib uses inches internally; we use a 1mm = 0.05 inch scale."""
    SCALE = 0.05  # 1 mm → 0.05 in ⇒ 200.9mm wrap = ~10" wide
    w_in = bottle.label_total_w_mm * SCALE
    h_in = bottle.label_total_h_mm * SCALE
    fig = plt.figure(figsize=(w_in, h_in), dpi=300, facecolor=g.BONE_HEX)
    ax = fig.add_axes([0, 0, 1, 1])
    # Coordinates in MM, with origin at bottom-left of CUT line
    ax.set_xlim(-g.BLEED_MM, bottle.label_flat_w_mm + g.BLEED_MM)
    ax.set_ylim(-g.BLEED_MM, bottle.label_flat_h_mm + g.BLEED_MM)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def _bone_fill(ax, bottle: g.BottleSpec):
    """Fill entire label + bleed with bone."""
    ax.add_patch(Rectangle(
        (-g.BLEED_MM, -g.BLEED_MM),
        bottle.label_flat_w_mm + 2 * g.BLEED_MM,
        bottle.label_flat_h_mm + 2 * g.BLEED_MM,
        facecolor=g.BONE_HEX, edgecolor="none", zorder=0,
    ))


def _plumb_mark(ax, cx, top_y, height, color):
    line_h = height * 0.58
    diamond_h = height * 0.42
    line_top = top_y
    line_bottom = top_y - line_h
    ax.plot([cx, cx], [line_bottom, line_top],
            color=color, linewidth=1.5, zorder=10,
            solid_capstyle="butt")
    half_w = diamond_h * 0.18
    diamond_top = line_bottom
    diamond_bottom = diamond_top - diamond_h
    diamond_mid_y = diamond_top - diamond_h * 0.35
    ax.fill(
        [cx, cx - half_w, cx, cx + half_w],
        [diamond_top, diamond_mid_y, diamond_bottom, diamond_mid_y],
        color=color, zorder=10,
    )


def _draw_facts_panel(ax, bottle: g.BottleSpec, x0, w):
    """Supplement Facts panel — black-on-white box per 21 CFR 101.36."""
    h = bottle.label_flat_h_mm
    # Section header
    cx = x0 + w / 2
    # Use a bordered rectangle (the FDA-required panel) inside the wrap
    safe = g.SAFE_MM
    panel_x = x0 + safe + 1.5
    panel_y = safe + 1.5
    panel_w = w - 2 * safe - 3.0
    panel_h = h - 2 * safe - 3.0
    ax.add_patch(Rectangle(
        (panel_x, panel_y), panel_w, panel_h,
        facecolor="white", edgecolor=g.INK_HEX, linewidth=0.8, zorder=2,
    ))
    # Header rule + "Supplement Facts"
    header_y = panel_y + panel_h - 5.5
    ax.text(panel_x + 1.5, header_y + 2.0, "Supplement Facts",
            family="IBM Plex Sans", fontweight="bold",
            fontsize=8.5, color=g.INK_HEX, zorder=3)
    ax.plot([panel_x + 1.0, panel_x + panel_w - 1.0],
            [header_y, header_y],
            color=g.INK_HEX, linewidth=0.8, zorder=3)
    # Serving info
    sy = header_y - 1.5
    ax.text(panel_x + 1.5, sy, "Serving Size  2 gummies",
            family="IBM Plex Sans", fontsize=5.5, color=g.INK_HEX,
            zorder=3)
    sy -= 1.6
    ax.text(panel_x + 1.5, sy, f"Servings Per Container  {bottle.count // 2}",
            family="IBM Plex Sans", fontsize=5.5, color=g.INK_HEX,
            zorder=3)
    sy -= 1.4
    ax.plot([panel_x + 1.0, panel_x + panel_w - 1.0],
            [sy, sy], color=g.INK_HEX, linewidth=0.4, zorder=3)
    # Column headers
    sy -= 1.6
    ax.text(panel_x + panel_w - 1.5, sy, "Amount\nPer Serving  % DV",
            family="IBM Plex Sans", fontsize=4.5, color=g.INK_HEX,
            zorder=3, ha="right", va="bottom",
            fontweight="bold")
    sy -= 1.6
    ax.plot([panel_x + 1.0, panel_x + panel_w - 1.0],
            [sy, sy], color=g.INK_HEX, linewidth=0.4, zorder=3)
    # Rows
    rows = [
        ("Vitamin B6 (as Pyridoxal-5-Phosphate)",
         f"{bottle.mg_b6 * 2:.0f} mg",  "294%"),
        ("Ginger Root Extract (5% gingerols)",
         f"{bottle.mg_ginger * 2:.0f} mg", "†"),
    ]
    for label, amount, dv in rows:
        sy -= 1.7
        ax.text(panel_x + 1.5, sy, label,
                family="IBM Plex Sans", fontsize=5.0,
                color=g.INK_HEX, zorder=3, va="bottom")
        ax.text(panel_x + panel_w - 8.0, sy, amount,
                family="IBM Plex Sans", fontsize=5.0,
                color=g.INK_HEX, zorder=3, va="bottom",
                ha="right")
        ax.text(panel_x + panel_w - 1.5, sy, dv,
                family="IBM Plex Sans", fontsize=5.0,
                color=g.INK_HEX, zorder=3, va="bottom",
                ha="right")
        sy -= 0.4
        ax.plot([panel_x + 1.0, panel_x + panel_w - 1.0],
                [sy, sy], color=g.INK_HEX, linewidth=0.3, zorder=3)
    # Footer note
    sy -= 1.4
    ax.text(panel_x + 1.5, sy, "† Daily Value not established.",
            family="IBM Plex Sans", fontsize=4.3,
            fontstyle="italic", color=g.INK_HEX, zorder=3, va="bottom")
    sy -= 1.4
    ax.text(panel_x + 1.5, sy,
            "Other ingredients: Tapioca syrup, cane sugar,\n"
            "pectin, citric acid, natural ginger flavor,\n"
            "natural color (carrot juice).",
            family="IBM Plex Sans", fontsize=4.3,
            color=g.INK_HEX, zorder=3, va="top",
            linespacing=1.2)


def _draw_front_panel(ax, bottle: g.BottleSpec, x0, w):
    """Hero panel: wordmark · plumb mark · product name · tagline."""
    h = bottle.label_flat_h_mm
    cx = x0 + w / 2

    # Wordmark "Aplomb." at top
    ax.text(cx - 0.4, h - 9.5, "Aplomb",
            ha="right", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="medium",
            fontsize=22, color=g.AMBER_HEX, zorder=10)
    ax.text(cx - 0.4, h - 9.5, ".",
            ha="left", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontweight="bold",
            fontsize=22, color=g.AMBER_HEX, zorder=10)

    # Plumb mark (centered, below wordmark)
    _plumb_mark(ax, cx, h - 13.5, 7.0, g.AMBER_HEX)

    # Product name "Calm" — large
    ax.text(cx, h - 27.0, "Calm.",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=44,
            color=g.INK_HEX, zorder=10)

    # Tiny rule
    ax.plot([cx - 9.0, cx + 9.0], [h - 35.5, h - 35.5],
            color=g.AMBER_HEX, linewidth=0.5, zorder=10)

    # Tagline
    ax.text(cx, h - 39.0, "For nausea, on the drug.",
            ha="center", va="center", family="Cormorant Garamond",
            fontstyle="italic", fontsize=10,
            color=g.AMBER_HEX, zorder=10)

    # Form factor + count (bottom)
    ax.text(cx, h - 47.5,
            f"GINGER GUMMIES   ·   {bottle.count} ct",
            ha="center", va="center", family="IBM Plex Sans",
            fontsize=7, color=g.MUTED_HEX, zorder=10)
    ax.plot([cx - 16.0, cx + 16.0], [h - 50.0, h - 50.0],
            color=g.RULE_HEX, linewidth=0.4, zorder=10)
    ax.text(cx, h - 53.0,
            f"{bottle.mg_ginger} MG GINGER + B6   ·   30-DAY SUPPLY",
            ha="center", va="center", family="IBM Plex Sans",
            fontsize=6.5, color=g.MUTED_HEX, zorder=10)


def _draw_description_panel(ax, bottle: g.BottleSpec, x0, w):
    """Description panel: paragraph + dosing + URL + barcode block."""
    h = bottle.label_flat_h_mm
    cx = x0 + w / 2
    safe = g.SAFE_MM

    # Section heading
    ax.text(x0 + safe + 1.5, h - safe - 4.0,
            "What this is",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=10, color=g.AMBER_HEX, zorder=10)
    ax.plot([x0 + safe + 1.5, x0 + safe + 14.0],
            [h - safe - 5.5, h - safe - 5.5],
            color=g.AMBER_HEX, linewidth=0.4, zorder=10)

    # Description body
    body = ("Ginger root extract and bioavailable B6, "
            "dosed for the nausea that GLP-1 medications "
            "produce in the first weeks of treatment "
            "and after every dose increase. Two gummies, "
            "morning of injection day. Cinnamon-ginger "
            "flavor — easier than capsules when food is "
            "the last thing you want.")
    # Use a manually wrapped narrow column so the text fits the panel
    import textwrap
    lines = textwrap.wrap(body, width=24)
    sy = h - safe - 8.5
    for line in lines:
        ax.text(x0 + safe + 1.5, sy, line,
                family="IBM Plex Sans", fontsize=5.5,
                color=g.INK_HEX, zorder=10, va="top")
        sy -= 1.9

    # Dosing
    sy -= 1.5
    ax.text(x0 + safe + 1.5, sy, "Dose",
            family="Cormorant Garamond", fontstyle="italic",
            fontsize=9, color=g.AMBER_HEX, zorder=10, va="top")
    sy -= 2.4
    ax.text(x0 + safe + 1.5, sy,
            "Two (2) gummies on injection\nmorning. May add a third\nbefore evening meal if needed.",
            family="IBM Plex Sans", fontsize=5.5,
            color=g.INK_HEX, zorder=10, va="top",
            linespacing=1.3)

    # URL + made-in line
    ax.text(cx, safe + 4.8, "aplomb.clinic",
            family="IBM Plex Sans", fontsize=6.5,
            color=g.AMBER_HEX, zorder=10, ha="center",
            va="center", fontweight="medium")
    ax.text(cx, safe + 2.8,
            "Made in USA from imported ingredients · Store cool & dry",
            family="IBM Plex Sans", fontsize=4.0,
            color=g.MUTED_HEX, zorder=10, ha="center",
            va="center")


def render(bottle: g.BottleSpec, out_base: Path):
    _set_style()
    fig, ax = _make_canvas(bottle)
    _bone_fill(ax, bottle)

    pw = bottle.panel_widths_mm
    x_facts = 0.0
    x_front = pw["facts"]
    x_desc = x_front + pw["front"]

    # Hairline panel-divider rules (very subtle)
    h = bottle.label_flat_h_mm
    for xv in (x_front, x_desc):
        ax.plot([xv, xv], [h * 0.10, h * 0.90],
                color=g.RULE_HEX, linewidth=0.3, zorder=5)

    _draw_facts_panel(ax, bottle, x_facts, pw["facts"])
    _draw_front_panel(ax, bottle, x_front, pw["front"])
    _draw_description_panel(ax, bottle, x_desc, pw["description"])

    pdf_path = out_base.with_suffix(".pdf")
    svg_path = out_base.with_suffix(".svg")
    fig.savefig(pdf_path, format="pdf", facecolor=g.BONE_HEX,
                bbox_inches=None, pad_inches=0)
    fig.savefig(svg_path, format="svg", facecolor=g.BONE_HEX,
                bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Wrote {pdf_path.name} "
          f"({pdf_path.stat().st_size // 1024} KB) + "
          f"{svg_path.name} ({svg_path.stat().st_size // 1024} KB)")


def render_all():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for bottle in g.ALL_BOTTLES:
        suffix = bottle.sku.replace("Aplomb. ", "").replace(" ", "_")
        render(bottle, OUT_DIR / f"Aplomb_{suffix}_Gummy_Label")


if __name__ == "__main__":
    render_all()
