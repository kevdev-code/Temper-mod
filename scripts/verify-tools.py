#!/usr/bin/env python3
"""
Checks a Temper tool in a visual-check screenshot, pixel by pixel, against the sprite that
scripts/tool-sprite.py draws. The sword has its own checker, verify-swords.py, because its sprite
comes from a different script.

    python scripts/verify-tools.py pickaxe                      # both loaders' shots under build/visual-check/
    python scripts/verify-tools.py pickaxe shot.png [more...]   # those, unioned as one set
    python scripts/verify-tools.py pickaxe --give <dir>         # write the datapack that hands them out

Why it can be exact rather than approximate: the GUI draws item icons unlit, and each tint layer is
its material colour multiplied by the texture's grey, so every pixel has one predictable value. A
tool is located by the brightest pixel of its head, then every layer is read at its exact offset
from that. Only pixels whose grey is half or more are compared: the dark ones land near black once
tinted, and the GUI has plenty of near black of its own.

The nine combinations are the sword's nine, for the same reasons verify-swords.py gives: three
where every pair of slots disagrees somewhere, the same three without a reinforcement, and the three
where all four slots share a material.
"""

import glob
import importlib.util
import json
import os
import sys

from PIL import Image

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)
TOL = 4                  # the renderer rounds; anything larger would start accepting a neighbouring tone
COMPARE_FROM = 0x80      # greys under this are skipped: tinted, they are too close to the GUI's darks

_spec = importlib.util.spec_from_file_location("tool_sprite", os.path.join(SCRIPTS, "tool-sprite.py"))
ts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ts)

WOOD, IRON, DIAMOND = "wood", "iron", "diamond"

# (handle, head, binding, reinforcement)
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


def mul(grey, colour):
    return tuple(round(grey * c / 255) for c in colour)


def near(a, b):
    return all(abs(p - q) <= TOL for p, q in zip(a, b))


class Sprite:
    def __init__(self, tool):
        self.tool = tool
        self.layers = ts.layers(tool)
        self.materials = {name: rgb(c) for name, c in ts.load_materials().items()}
        self.leather = rgb(ts.LEATHER)
        self.fill = {name: {p: g for p, g in px.items() if g >= COMPARE_FROM} for name, px in self.layers.items()}
        # The haft pixels the knob cups are dark, but they are the point of the no-reinforcement
        # case, so they are compared regardless: a hidden reinforcement layer must leave them drawn.
        knob = set(self.layers["reinforcement"])
        self.cupped = {p: g for p, g in self.layers["handle"].items()
                       if any(n in knob for n in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)))}
        brightest = max(self.layers["head"].values())
        self.anchor = min(p for p, g in self.layers["head"].items() if g == brightest)
        self.anchor_grey = brightest

    def placements(self, image, head):
        """Every origin and scale at which a tool with this head material could sit."""
        width, height = image.size
        px = image.load()
        want = mul(self.anchor_grey, self.materials[head])
        ax, ay = self.anchor
        origins = set()
        for y in range(height):
            for x in range(width):
                if near(px[x, y], want):
                    for scale in (1, 2, 3, 4):
                        origins.add((x - (ax * scale + scale // 2), y - (ay * scale + scale // 2), scale))
        return sorted(origins)

    def pixels_match(self, image, origin, pixels, colour):
        ox, oy, scale = origin
        width, height = image.size
        px = image.load()
        for (x, y), g in pixels.items():
            sx, sy = ox + x * scale + scale // 2, oy + y * scale + scale // 2
            if not (0 <= sx < width and 0 <= sy < height) or not near(px[sx, sy], mul(g, colour)):
                return False
        return True

    def tool_at(self, image, origin, handle, head, binding, reinforcement):
        for layer, material in (("handle", handle), ("head", head), ("binding", binding)):
            if not self.pixels_match(image, origin, self.fill[layer], self.materials[material]):
                return False
        if not self.pixels_match(image, origin, self.fill["grip"], self.leather):
            return False
        if not self.pixels_match(image, origin, self.cupped, self.materials[handle]):
            return False
        if reinforcement is None:
            # The layer draws nothing, so the knob's pixels cannot read as any material.
            return not any(self.pixels_match(image, origin, self.fill["reinforcement"], c) for c in self.materials.values())
        return self.pixels_match(image, origin, self.fill["reinforcement"], self.materials[reinforcement])


def label(handle, head, binding, reinforcement):
    return f"{head}/{handle}/{binding}/{reinforcement or '-'}"


def check(sprite, paths):
    """The images are one set: a tool only has to be readable in one of them."""
    found = {combo: [] for combo in EXPECTED}
    for path in paths:
        image = Image.open(path).convert("RGB")
        short = os.path.basename(path)
        for combo in EXPECTED:
            handle, head, binding, reinforcement = combo
            for origin in sprite.placements(image, head):
                if sprite.tool_at(image, origin, handle, head, binding, reinforcement):
                    found[combo].append((short, origin))
    print(f"\n{len(paths)} shot(s): " + ", ".join(os.path.basename(q) for q in paths))
    print(f"  {'head/handle/binding/reinf':<34}{'seen in':>8}   where")
    ok = True
    for combo in EXPECTED:
        hits = found[combo]
        ok &= bool(hits)
        where = ", ".join(f"{n} ({x},{y})x{k}" for n, (x, y, k) in hits[:2]) or "NOT FOUND"
        print(f"  {label(*combo):<34}{len(hits):>8}   {where}")
    print(f"  all nine {sprite.tool}s present and exact in every layer" if ok else "  MISSING OR MISTINTED")
    return ok


def write_datapack(tool, directory):
    """The same nine, as the datapack visual-check.sh hands to the player. One source, no drift."""
    functions = os.path.join(directory, "data", "temper_test", "function")
    tags = os.path.join(directory, "data", "minecraft", "tags", "function")
    os.makedirs(functions, exist_ok=True)
    os.makedirs(tags, exist_ok=True)

    def put(name, text):
        with open(name, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    pack = {"pack": {"description": f"the {tool}s verify-tools.py checks", "min_format": [101, 1], "max_format": 101}}
    put(os.path.join(directory, "pack.mcmeta"), json.dumps(pack, indent=2) + "\n")
    put(os.path.join(tags, "tick.json"), json.dumps({"values": ["temper_test:tick"]}) + "\n")
    put(os.path.join(functions, "tick.mcfunction"),
        f"execute as @a unless items entity @s hotbar.* temper:{tool} run function temper_test:give\n")
    lines = []
    for handle, head, binding, reinforcement in EXPECTED:
        parts = ['handle:"temper:%s"' % handle, 'head:"temper:%s"' % head, 'binding:"temper:%s"' % binding]
        if reinforcement:
            parts.append('reinforcement:"temper:%s"' % reinforcement)
        lines.append(f"give @s temper:{tool}[temper:parts={{" + ",".join(parts) + "}]")
    put(os.path.join(functions, "give.mcfunction"), "\n".join(lines) + "\n")
    print("wrote %d gives into %s" % (len(EXPECTED), directory))


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ts.TOOLS:
        sys.exit("usage: verify-tools.py <" + "|".join(sorted(ts.TOOLS)) + "> [--give <dir> | shot.png ...]")
    tool, rest = args[0], args[1:]
    if rest and rest[0] == "--give":
        write_datapack(tool, rest[1])
        return
    sprite = Sprite(tool)
    if rest:
        sys.exit(0 if check(sprite, rest) else 1)
    shots = os.path.join(ROOT, "build", "visual-check")
    ok, ran = True, False
    for platform in ("fabric", "neoforge"):
        paths = sorted(glob.glob(os.path.join(shots, f"{platform}-{tool}-*.png")))
        if not paths:
            continue
        ran = True
        print(f"\n== {platform}")
        ok &= check(sprite, paths)
    if not ran:
        sys.exit(f"no {tool} screenshots in build/visual-check/; run scripts/visual-check.sh <loader> {tool} first")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
