#!/usr/bin/env python3
"""
Checks Temper swords in a visual-check screenshot, pixel by pixel, against the sprite that
scripts/sword-sprite.py draws.

    python scripts/verify-swords.py                     # both screenshots under build/visual-check/
    python scripts/verify-swords.py shot.png [more...]  # specific ones
    python scripts/verify-swords.py --give <dir>        # write the datapack that hands them out

Why it can be exact rather than approximate: the GUI draws item icons unlit, and each tint layer is
its material colour multiplied by the texture's grey, so every fill pixel has one predictable value.
A sword is located by its blade's lit diagonal, then every zone is read at its exact offset from
that. Counting colours in a slot does not work: the hotbar frame and the world behind it produce
greys that pass for iron.

WHAT IS CHECKED, AND WHY THIS SUBSET
    Four slots and three materials, with the reinforcement optional, is 108 combinations. Nine are
    enough to catch what can actually go wrong:

    - Three where every slot holds a different material, chosen so that each of the four slots sees
      each material once and no two slots hold the same material in every row. That last property is
      the one that matters: a layer wired to the wrong slot swaps two materials, and it can only hide
      if the two slots happen to agree everywhere they are compared.
    - The same three with no reinforcement, which is the only way to catch the empty slot failing to
      disappear.
    - Three where all four slots share one material, the hardest case for the zones to stay apart.

    Colours, tones and the zone map all come from sword-sprite.py, which reads its materials from
    temper/materials.json, so this cannot drift from what the game renders.
"""

import importlib.util
import json
import os
import sys

from PIL import Image

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)
TOL = 4          # the renderer rounds; anything larger would start accepting a neighbouring tone

_spec = importlib.util.spec_from_file_location("sword_sprite", os.path.join(SCRIPTS, "sword-sprite.py"))
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)

WOOD, IRON, DIAMOND = "wood", "iron", "diamond"

# (handle, head, binding, reinforcement). Each column is a different permutation of the three
# materials, which is what makes every pair of slots disagree somewhere.
EXPECTED = [
    (WOOD, IRON, DIAMOND, WOOD),
    (IRON, DIAMOND, WOOD, DIAMOND),
    (DIAMOND, WOOD, IRON, IRON),
    (WOOD, IRON, DIAMOND, None),
    (IRON, DIAMOND, WOOD, None),
    (DIAMOND, WOOD, IRON, None),
    (WOOD, WOOD, WOOD, None),
    (IRON, IRON, IRON, None),
    (DIAMOND, DIAMOND, DIAMOND, None),
]


def rgb(packed):
    return ((packed >> 16) & 255, (packed >> 8) & 255, packed & 255)


MATERIALS = {name: rgb(c) for name, c in sp.MATERIALS.items()}
LEATHER = rgb(sp.LEATHER)

MASTER, ZONES = sp.build()
OUTLINE = sp.OUTLINE_MASK
FILL = {z: [(x, y) for y in range(sp.SIZE) for x in range(sp.SIZE)
            if ZONES[y][x] == z and not OUTLINE[y][x]] for z in sp.ZONES}
ZONE_OF_LAYER = {layer: [z for z in sp.ZONES if sp.LAYER[z] == layer] for layer in set(sp.LAYER.values())}
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


def placements(image, head):
    """Where a sword with this head material might sit: origin and scale, from the blade alone."""
    width, height = image.size
    px = image.load()
    want = mul(sp.TONES["head"][0], MATERIALS[head])
    hits = [(x, y) for y in range(height) for x in range(width) if near(px[x, y], want)]
    found = []
    for group in clusters(hits):
        scale = max(1, round((len(group) / len(BLADE_LIT)) ** 0.5))
        top, right = min(y for _, y in group), max(x for x, _ in group)
        found.append((right - (TIP[0] * scale + scale - 1), top - TIP[1] * scale, scale))
    return found


def zone_matches(image, origin, zone, colour):
    ox, oy, scale = origin
    width, height = image.size
    px = image.load()
    for (x, y) in FILL[zone]:
        sx, sy = ox + x * scale + scale // 2, oy + y * scale + scale // 2
        if not (0 <= sx < width and 0 <= sy < height):
            return False
        if not near(px[sx, sy], mul(MASTER[y][x][0], colour)):
            return False
    return True


def sword_at(image, origin, handle, head, binding, reinforcement):
    layers = {"handle": handle, "head": head, "binding": binding}
    for layer, material in layers.items():
        for zone in ZONE_OF_LAYER[layer]:
            if not zone_matches(image, origin, zone, MATERIALS[material]):
                return False
    for zone in ZONE_OF_LAYER["grip"]:
        if not zone_matches(image, origin, zone, LEATHER):
            return False
    for zone in ZONE_OF_LAYER["reinforcement"]:
        if reinforcement is None:
            # The layer must be drawing nothing, so the zone cannot read as any material.
            if any(zone_matches(image, origin, zone, c) for c in MATERIALS.values()):
                return False
        elif not zone_matches(image, origin, zone, MATERIALS[reinforcement]):
            return False
    return True


def label(handle, head, binding, reinforcement):
    return f"{head}/{handle}/{binding}/{reinforcement or '-'}"


def check(path):
    image = Image.open(path).convert("RGB")
    print(f"\n{os.path.relpath(path, ROOT)}")
    print(f"  {'head/handle/binding/reinf':<34}{'found':>6}   where")
    ok = True
    for handle, head, binding, reinforcement in EXPECTED:
        hits = [o for o in placements(image, head)
                if sword_at(image, o, handle, head, binding, reinforcement)]
        ok &= bool(hits)
        where = ", ".join(f"({x},{y})x{s}" for x, y, s in hits[:2]) or "NOT FOUND"
        print(f"  {label(handle, head, binding, reinforcement):<34}{len(hits):>6}   {where}")
    print("  all nine present and exact in every zone" if ok else "  MISSING OR MISTINTED")
    return ok


def write_datapack(directory):
    """The same nine, as the datapack visual-check.sh hands to the player. One source, no drift."""
    functions = os.path.join(directory, "data", "temper_test", "function")
    tags = os.path.join(directory, "data", "minecraft", "tags", "function")
    os.makedirs(functions, exist_ok=True)
    os.makedirs(tags, exist_ok=True)

    def put(name, text):
        with open(name, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    pack = {"pack": {"description": "the swords verify-swords.py checks",
                     "min_format": [101, 1], "max_format": 101}}
    put(os.path.join(directory, "pack.mcmeta"), json.dumps(pack, indent=2) + "\n")
    put(os.path.join(tags, "tick.json"), json.dumps({"values": ["temper_test:tick"]}) + "\n")

    # Guarded on the inventory, not on a scoreboard. A scoreboard needs an objective created from
    # #minecraft:load, and when that lost the race with the first tick the function re-ran every
    # tick, clearing and re-giving, so the client only ever saw the last give land.
    put(os.path.join(functions, "tick.mcfunction"),
        "execute as @a unless items entity @s hotbar.* temper:sword run function temper_test:give\n")

    lines = []
    for handle, head, binding, reinforcement in EXPECTED:
        parts = ['handle:"temper:%s"' % handle, 'head:"temper:%s"' % head, 'binding:"temper:%s"' % binding]
        if reinforcement:
            parts.append('reinforcement:"temper:%s"' % reinforcement)
        lines.append("give @s temper:sword[temper:parts={" + ",".join(parts) + "}]")
    put(os.path.join(functions, "give.mcfunction"), "\n".join(lines) + "\n")
    print("wrote %d gives into %s" % (len(EXPECTED), directory))


def main():
    args = sys.argv[1:]
    if args and args[0] == "--give":
        write_datapack(args[1])
        return
    paths = args
    if not paths:
        shots = os.path.join(ROOT, "build", "visual-check")
        paths = [os.path.join(shots, f"{p}-test.png") for p in ("fabric", "neoforge")]
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            sys.exit("no screenshots in build/visual-check/; run scripts/visual-check.sh first")
    sys.exit(0 if all([check(p) for p in paths]) else 1)


if __name__ == "__main__":
    main()
