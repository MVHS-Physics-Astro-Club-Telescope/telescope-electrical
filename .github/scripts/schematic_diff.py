#!/usr/bin/env python3
"""Draw what a pull request changed in the schematic, as pictures.

    schematic_diff.py SVG_DIR OUT_DIR --prefix pr4-ab12cd3 --url-base https://.../download/pr-previews/

SVG_DIR holds four folders made by `kicad-cli sch export svg`, one SVG per sheet in each:
    before/color  before/bw  after/color  after/bw      (bw = exported with --black-and-white)

For every sheet whose black-and-white drawing changed, OUT_DIR gets:
    <prefix>-<sheet>-changes.png   whole page: black = unchanged, red = removed, blue = added, yellow = where
    <prefix>-<sheet>-zoom.png      the same, cropped to the changed area (only when that area is small)
    <prefix>-<sheet>-before.png    the old page in colour
    <prefix>-<sheet>-after.png     the new page in colour
and OUT_DIR/comment.md is the pull-request comment that shows them (empty when nothing changed).
Needs rsvg-convert on PATH, plus Pillow and numpy.
"""
import argparse
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

WIDTH = 2400              # pixels across an A4 sheet: thin wires stay visible
INK = 128                 # grey level below which a pixel counts as drawn
HALO = 12                 # pixels of yellow around every change, so small edits are easy to find
UNCHANGED = (40, 40, 40)
REMOVED = (224, 49, 49)
ADDED = (25, 113, 194)
HALO_RGB = (255, 236, 153)
MARKER = "<!-- schematic-diff -->"


def raster(svg: Path, png: Path) -> Image.Image:
    subprocess.run(["rsvg-convert", "-w", str(WIDTH), "-b", "white", str(svg), "-o", str(png)], check=True)
    return Image.open(png)


def sheet_name(stem: str, project: str) -> str:
    if stem == project:
        return "Top page (sheet map)"
    return stem[len(project) + 1:] if stem.startswith(project + "-") else stem


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("svg_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--url-base", required=True)
    ap.add_argument("--project", default="mv-telescope-hat")
    ap.add_argument("--commit", default="")
    a = ap.parse_args()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    tmp = a.out_dir / "_raster"
    tmp.mkdir(exist_ok=True)

    stems = sorted({p.stem for side in ("before", "after") for p in (a.svg_dir / side / "bw").glob("*.svg")},
                   key=lambda s: (s != a.project, s))
    changed, unchanged = [], []
    for stem in stems:
        name = sheet_name(stem, a.project)
        base = f"{a.prefix}-{slug(name)}"
        pages = {}
        for side in ("before", "after"):
            svg = a.svg_dir / side / "bw" / f"{stem}.svg"
            pages[side] = raster(svg, tmp / f"{side}-{base}.png").convert("L") if svg.exists() else None
        size = (pages["after"] or pages["before"]).size
        arr = {}
        for side, img in pages.items():
            if img is None:                      # sheet added or deleted: compare against a blank page
                img = Image.new("L", size, 255)
            elif img.size != size:
                img = img.resize(size)
            arr[side] = np.asarray(img) < INK
        b, h = arr["before"], arr["after"]
        diff = b != h
        if not diff.any():
            unchanged.append(name)
            continue

        out = np.full(b.shape + (3,), 255, np.uint8)
        halo = np.asarray(Image.fromarray(diff.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * HALO + 1))) > 0
        out[halo] = HALO_RGB
        out[b & h] = UNCHANGED
        out[b & ~h] = REMOVED
        out[~b & h] = ADDED
        full = Image.fromarray(out)
        files = {"changes": f"{base}-changes.png"}
        full.save(a.out_dir / files["changes"], optimize=True)

        ys, xs = np.nonzero(halo)
        m = 80
        box = (max(xs.min() - m, 0), max(ys.min() - m, 0), min(xs.max() + m, size[0]), min(ys.max() + m, size[1]))
        if (box[2] - box[0]) * (box[3] - box[1]) < 0.6 * size[0] * size[1]:
            files["zoom"] = f"{base}-zoom.png"
            full.crop(box).save(a.out_dir / files["zoom"], optimize=True)

        for side in ("before", "after"):
            svg = a.svg_dir / side / "color" / f"{stem}.svg"
            if svg.exists():
                files[side] = f"{base}-{side}.png"
                raster(svg, a.out_dir / files[side])
        changed.append((name, files, int(diff.sum())))

    body = ""
    if changed:
        u = a.url_base.rstrip("/") + "/"
        lines = [MARKER, "### Schematic changes in this pull request", "",
                 "Compared with `main`. **Red** is only in the old version (removed), **blue** is only in the new "
                 "version (added), **black** is unchanged, and **yellow** marks every spot that changed. "
                 "Click a picture to open it full size.", ""]
        for name, files, _ in changed:
            lines.append(f"#### {name}")
            shown = files.get("zoom", files["changes"])
            lines.append(f'<a href="{u}{files["changes"]}"><img src="{u}{shown}" alt="Changes on {name}" width="100%"></a>')
            links = [f"[whole page]({u}{files['changes']})"]
            links += [f"[{side}]({u}{files[side]})" for side in ("before", "after") if side in files]
            lines += ["", " · ".join(links), ""]
        if unchanged:
            lines.append("No changes on: " + ", ".join(unchanged) + ".")
        if a.commit:
            lines += ["", f"<sub>Drawn by CI for commit {a.commit[:7]}.</sub>"]
        body = "\n".join(lines) + "\n"
    (a.out_dir / "comment.md").write_text(body)
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    print(f"changed: {[c[0] for c in changed]}  unchanged: {unchanged}")


if __name__ == "__main__":
    main()
