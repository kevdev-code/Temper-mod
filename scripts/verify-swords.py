#!/usr/bin/env python3
"""
Checks the Temper swords in a visual-check screenshot, pixel by pixel, against the sprite that
scripts/sword-sprite.py draws.

    python scripts/verify-swords.py                     # both screenshots under build/visual-check/
    python scripts/verify-swords.py shot.png [more...]  # specific ones

Why it can be exact rather than approximate: the GUI draws item icons unlit, and each tint layer is
its material colour multiplied by the texture's grey, so every fill pixel has one predictable value.
A sword is located by its blade's lit diagonal, which is unambiguous per head material; its handle
material is whichever one makes every guard and pommel pixel match; the grip must be the constant
leather. Counting colours in a slot does not work: the hotbar frame and the world behind it produce
greys that pass for iron.

Position and order are ignored, so the check survives the creative screen opening on its own, and a
sword found anywhere in the image counts. It passes when all nine head/handle pairs are present and
complete. Colours and tones come from sword-sprite.py, which reads them from temper/materials.json,
so this cannot drift from what the game renders.
"""

import importlib.util
import os
import sys

from PIL import Image

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)
TOL = 4          # the renderer rounds; anything larger would start accepting a neighbouring tone

_spec = importlib.util.spec_from_file_location("sword_sprite", os.path.join(SCRIPTS, "sword-sprite.py"))
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


def rgb(packed):
    return ((packed >> 16) & 255, (packed >> 8) & 255, packed & 255)


MATERIALS = {name: rgb(c) for name, c in sp.MATERIALS.items()}
LEATHER = rgb(sp.LEATHER)

MASTER, ZONES = sp.build()
OUTLINE = sp.OUTLINE_MASK
FILL = {z: [(x, y) for y in range(sp.SIZE) for x in range(sp.SIZE)
            if ZONES[y][x] == z and not OUTLINE[y][x]] for z in sp.ZONES}
BLADE_LIT = [(x, y) for (x, y) in FILL["blade"] if MASTER[y][x][0] == sp.TONES["head"][0]]
TIP = max(BLADE_LIT, key=lambda p: p[0])


def mul(grey, colour):
    return tuple(round(grey * c / 255) for c in colour)


def near(a, b):
    return all(abs(p - q) <= TOL for p, q in zip(a, b))


def clusters(points, gap=6):
    """Groups nearby points. Each group is one sword's lit diagonal."""
    groups = []
    for p in sorted(points):
        for g in groups:
            if any(abs(p[0] - q[0]) <= gap and abs(p[1] - q[1]) <= gap for q in g[-12:]):
                g.append(p)
                break
        else:
            groups.append([p])
    return [g for g in groups if len(g) >= len(BLADE_LIT)]


def find_swords(image):
    """Maps (head, handle) to the places a complete, correctly tinted sword was found."""
    width, height = image.size
    px = image.load()
    found = {}
    for head, head_colour in MATERIALS.items():
        want = mul(sp.TONES["head"][0], head_colour)
        hits = [(x, y) for y in range(height) for x in range(width) if near(px[x, y], want)]
        for group in clusters(hits):
            scale = max(1, round((len(group) / len(BLADE_LIT)) ** 0.5))
            top, right = min(y for _, y in group), max(x for x, _ in group)
            ox, oy = right - (TIP[0] * scale + scale - 1), top - TIP[1] * scale

            def zone_matches(zone, colour):
                for (x, y) in FILL[zone]:
                    sx, sy = ox + x * scale + scale // 2, oy + y * scale + scale // 2
                    if not (0 <= sx < width and 0 <= sy < height):
                        return False
                    if not near(px[sx, sy], mul(MASTER[y][x][0], colour)):
                        return False
                return True

            if not zone_matches("blade", head_colour) or not zone_matches("grip", LEATHER):
                continue
            handles = [h for h, c in MATERIALS.items()
                       if zone_matches("guard", c) and zone_matches("pommel", c)]
            if len(handles) == 1:                      # ambiguous means the tint is not telling them apart
                found.setdefault((head, handles[0]), []).append((ox, oy, scale))
    return found


def check(path):
    found = find_swords(Image.open(path).convert("RGB"))
    print(f"\n{os.path.relpath(path, ROOT)}")
    print(f"  {'head/handle':<20}{'found':>6}   where (origin, scale)")
    ok = True
    for head in MATERIALS:
        for handle in MATERIALS:
            hits = found.get((head, handle), [])
            ok &= bool(hits)
            where = ", ".join(f"({x},{y})x{s}" for x, y, s in hits[:3]) + (" ..." if len(hits) > 3 else "")
            print(f"  {head + '/' + handle:<20}{len(hits):>6}   {where if hits else 'NOT FOUND'}")
    print("  all nine complete: blade, guard, pommel and grip exact" if ok else "  MISSING COMBINATIONS")
    return ok


def main():
    paths = sys.argv[1:]
    if not paths:
        shots = os.path.join(ROOT, "build", "visual-check")
        paths = [os.path.join(shots, f"{p}-test.png") for p in ("fabric", "neoforge")]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            sys.exit("no screenshots in build/visual-check/; run scripts/visual-check.sh first")
    sys.exit(0 if all([check(p) for p in paths]) else 1)


if __name__ == "__main__":
    main()
