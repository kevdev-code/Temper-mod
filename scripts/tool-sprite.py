#!/usr/bin/env python3
"""
Temper's tool sprites: vanilla's own PNG, pixel for pixel, plus three additions.

    python scripts/tool-sprite.py pickaxe --grid        # ours beside vanilla on a numbered grid
    python scripts/tool-sprite.py pickaxe --materials   # tinted, every material in every slot
    python scripts/tool-sprite.py pickaxe --layers      # the five textures, each alone
    python scripts/tool-sprite.py pickaxe --ascii       # zone map and audit in the terminal
    python scripts/tool-sprite.py pickaxe --export      # write the textures and both JSON files

THE METHOD
    The sword was drawn from a parametric model and took six rounds. The pickaxe was drawn the same
    way and failed eight times, because the geometry came out of formulas instead of the sprite the
    player already knows. So this file has no formulas. The base is the vanilla item's PNG, read out
    of the game jar at run time and never redrawn: its head and stick are told apart by the PNG's own
    colours, and every one of its pixels keeps its place. On that base, three additions only, each
    listed by hand on the 16 x 16 grid:

        blades   each arm of the head runs on past its point as a wedge      -> binding
        knob     a small ball on the butt of the haft                        -> reinforcement
        grip     a stretch of the haft, cut square across it                 -> grip, a fixed colour

    Everything else, the head's proportions, the haft's angle and thickness, where they cross, is
    vanilla's and stays vanilla's. The audit refuses an added pixel that lands on a vanilla one.

    The comparison sheets carry a numbered grid. It is what let the pickaxe close in two rounds
    after eight without it: a correction can name a cell.

TONES
    Vanilla's iron tools are drawn in pure grey, so the iron PNG's head pixels are the head texture
    as they stand: tinted with iron they give back the vanilla item exactly. The stick is the same
    brown in every vanilla tool, and it is our wood colour times four greys, 25 / 46 / 66 / 87 per
    cent; the handle texture maps those four onto the sword's hilt ladder (18 / 33 / 50 / 75), so the
    haft sits under the head in the grey the way the sword's hilt sits under its blade, and a wood
    handle lands a little darker than vanilla's stick, as the sword's does. The grip maps the same
    four onto the sword's grip ladder, times the same leather. Added pixels carry a grey each,
    written next to them.

LAYERS
    Five tint layers in the model's order: handle, head, grip, binding, reinforcement. Every pixel
    is in exactly one layer, and the audit refuses two layers sharing one. This is not tidiness:
    the reinforcement is optional and an empty slot is hidden by tinting its layer transparent, and
    in the GUI a layer hidden that way also hides whatever another layer drew beneath it. The knob
    was first drawn over the haft's last pixel with the handle drawing that pixel too, and a pickaxe
    without a reinforcement came up with a hole where the pixel should have been, measured off the
    screenshot. So the knob wraps the haft's end instead of covering it.
"""

import argparse
import glob
import io
import json
import os
import sys
import zipfile

SIZE = 16
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(ROOT, "build", "texture-drafts", "ref")
LAYER_ORDER = ["handle", "head", "grip", "binding", "reinforcement"]
LEATHER = 0x8B5E3C                  # the sword's constant, so the set reads as one set

# Vanilla's stick, as it appears in every tool PNG, and the grey each of its four tones becomes in
# the handle and grip textures. The stick is wood (#9E772D) times 25 / 46 / 66 / 87 per cent.
STICK_TO_HANDLE = {0x281E0B: 0x2E, 0x493615: 0x54, 0x684E1E: 0x80, 0x896727: 0xBF}
STICK_TO_GRIP = {0x281E0B: 0x66, 0x493615: 0xA6, 0x684E1E: 0xCC, 0x896727: 0xFF}

TOOLS = {
    "pickaxe": {
        "vanilla": "iron_pickaxe.png",
        # The blades: the inner edge continues the arm's inner row (or column) straight and the
        # outer edge cuts diagonally to the new point, so both points lean in toward the haft as a
        # real pick's do. Vanilla's own tip pixels, (5,3) and (13,11), join the blade and take the
        # arm's core grey, since the arm now runs on past them.
        "binding": {(5, 3): 0xC1, (4, 3): 0xC1, (3, 4): 0x44, (5, 4): 0x18, (4, 4): 0x18,
                    (13, 11): 0xC1, (13, 12): 0xC1, (12, 13): 0x44, (12, 11): 0x18, (12, 12): 0x18},
        # Three pixels cupping the haft's last pixel, (2,14), which stays haft: the stick is seen
        # entering the knob, as it enters the mace's pommel. Lit from the top left.
        "reinforcement": {(1, 14): 0xD9, (1, 15): 0x9B, (2, 15): 0x6B},
        # The stick between the diagonals x - y = -5 and -9: cut square across the haft, so the band
        # reaches equally far along both flanks. Cut by columns it sat a pixel askew.
        "grip": [(5, 10), (4, 11), (5, 11), (6, 11), (3, 12), (4, 12), (5, 12), (4, 13)],
    },
    "axe": {
        "vanilla": "iron_axe.png",
        # The blade: the bit's cutting edge moved one column out along its whole length, from the
        # toe at row 1 to the heel at row 6. The added column is the new outline, dark on top and
        # darker under the heel as vanilla's is, and vanilla's old outline just inside it becomes
        # the lit bevel, so the sharpened edge is two pixels wide and shows its material.
        "binding": {(8, 1): 0x44, (7, 2): 0x44, (6, 3): 0x44, (5, 4): 0x44, (5, 5): 0x18, (6, 6): 0x18,
                    (8, 2): 0xFF, (7, 3): 0xFF, (6, 4): 0xFF, (6, 5): 0xFF, (7, 6): 0xFF},
        # The stick is the pickaxe's stick, pixel for pixel, so the knob and the grip are the same.
        "reinforcement": {(1, 14): 0xD9, (1, 15): 0x9B, (2, 15): 0x6B},
        "grip": [(5, 10), (4, 11), (5, 11), (6, 11), (3, 12), (4, 12), (5, 12), (4, 13)],
    },
}


# ---------------------------------------------------------------- vanilla, from the jar

def vanilla_png(name):
    """The PNG's bytes, from build/texture-drafts/ref/ if it has been extracted, else from the jar."""
    local = os.path.join(REF_DIR, name)
    if os.path.exists(local):
        with open(local, "rb") as f:
            return f.read()
    pattern = os.path.expanduser("~/.gradle/caches/fabric-loom/minecraftMaven/net/minecraft/minecraft-merged-deobf/*/minecraft-merged-deobf-*.jar")
    jars = sorted(glob.glob(pattern))
    if not jars:
        raise SystemExit(f"neither {local} nor a Minecraft jar under the Gradle cache")
    with zipfile.ZipFile(jars[-1]) as jar:
        data = jar.read(f"assets/minecraft/textures/item/{name}")
    os.makedirs(REF_DIR, exist_ok=True)
    with open(local, "wb") as f:
        f.write(data)
    return data


def vanilla(tool):
    """(head, stick, rgb per pixel) straight off the PNG. Head and stick are the PNG's own colours."""
    from PIL import Image
    im = Image.open(io.BytesIO(vanilla_png(TOOLS[tool]["vanilla"]))).convert("RGBA")
    px = im.load()
    head, stick, rgb = {}, {}, {}
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            if not a:
                continue
            rgb[(x, y)] = (r, g, b)
            if r == g == b:
                head[(x, y)] = r                          # the iron PNG's head is pure grey
            else:
                stick[(x, y)] = r << 16 | g << 8 | b
    unknown = {v for v in stick.values() if v not in STICK_TO_HANDLE}
    if unknown:
        raise SystemExit(f"{tool}: stick tones not in the table: " + ", ".join(f"#{v:06X}" for v in unknown))
    return head, stick, rgb


# ---------------------------------------------------------------- the sprite

def layers(tool):
    """Layer -> {pixel: grey}."""
    spec = TOOLS[tool]
    head, stick, _ = vanilla(tool)
    binding = dict(spec["binding"])
    grip = set(spec["grip"])
    return {
        "handle": {p: STICK_TO_HANDLE[v] for p, v in stick.items() if p not in grip},
        "head": {p: g for p, g in head.items() if p not in binding},
        "grip": {p: STICK_TO_GRIP[stick[p]] for p in grip},
        "binding": binding,
        "reinforcement": dict(spec["reinforcement"]),
    }


def load_materials():
    """Colours from temper/materials.json, the same file the game reads, so nothing can drift."""
    path = os.path.join(ROOT, "common", "src", "main", "resources", "temper", "materials.json")
    with open(path, encoding="utf-8") as f:
        table = json.load(f)["materials"]
    return {name: int(entry["color"].lstrip("#"), 16) for name, entry in table.items()}


def audit(tool):
    """Everything the method promises, checked. Export refuses to run if any of it fails."""
    spec = TOOLS[tool]
    head, stick, _ = vanilla(tool)
    L = layers(tool)
    problems = []
    base = set(head) | set(stick)
    added = (set(spec["binding"]) | set(spec["reinforcement"])) - base
    for p in sorted(added & base):
        problems.append(f"added pixel {p} lands on vanilla")
    if not set(spec["grip"]) <= set(stick):
        problems.append("grip is not entirely stick: " + str(sorted(set(spec["grip"]) - set(stick))))
    for name, px in L.items():
        if len(px) < 3:
            problems.append(f"{name} has {len(px)} px, too few to read at 1:1")
    for a in LAYER_ORDER:
        for b in LAYER_ORDER:
            if a < b and set(L[a]) & set(L[b]):
                problems.append(f"{a} and {b} share pixels: {sorted(set(L[a]) & set(L[b]))}")
    bare = set(L["handle"]) | set(L["grip"]) | set(L["head"]) | set(L["binding"])
    if not base <= bare:
        problems.append("without a reinforcement the sprite loses vanilla pixels: " + str(sorted(base - bare)))
    if max(L["handle"].values()) > 0.75 * max(L["head"].values()) + 0.5:
        problems.append("haft core is not under three quarters of the head's; the two read as one piece")
    # Nothing floats: the whole sprite is one eight-connected blob.
    filled = set().union(*(set(px) for px in L.values()))
    seen, todo = set(), [min(filled)]
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        x, y = p
        todo += [q for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1),
                             (x - 1, y - 1), (x + 1, y + 1), (x - 1, y + 1), (x + 1, y - 1)) if q in filled]
    if seen != filled:
        problems.append(f"{len(filled - seen)} pixels float free of the rest")
    return problems


def composite(tool, materials=None, colours=None, reinforcement=True):
    """
    What the game shows: each layer's grey times its colour, in model order. materials maps slot to
    material name and colours maps name to 0xRRGGBB; with neither, white, which is the grey itself.
    The grip is leather either way, because it is never anything else.
    """
    from PIL import Image
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = im.load()
    for name in LAYER_ORDER:
        if name == "reinforcement" and not reinforcement:
            continue
        if name == "grip":
            colour = LEATHER
        else:
            colour = 0xFFFFFF if materials is None else colours[materials[name]]
        for (x, y), g in layers(tool)[name].items():
            px[x, y] = (round(g * (colour >> 16 & 255) / 255), round(g * (colour >> 8 & 255) / 255),
                        round(g * (colour & 255) / 255), 255)
    return im


# ---------------------------------------------------------------- sheets

def _sheet(width, height):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (width, height), (30, 30, 34))
    return im, ImageDraw.Draw(im), ImageFont.load_default(size=12), ImageFont.load_default(size=10)


def _place(out, draw, im, x, y, scale):
    """The sprite at a scale, over a checkerboard, so transparent pixels stay visible as such."""
    from PIL import Image
    k = max(scale, 2)
    for cy in range(0, SIZE * scale, k):
        for cx in range(0, SIZE * scale, k):
            draw.rectangle([x + cx, y + cy, x + cx + k - 1, y + cy + k - 1],
                           fill=(56, 56, 60) if ((cx // k + cy // k) % 2 == 0) else (46, 46, 50))
    up = im.resize((SIZE * scale, SIZE * scale), Image.NEAREST)
    out.paste(up, (x, y), up)


def _gridded(out, draw, small, im, x0, y0, scale):
    """The sprite at a scale with cell lines and numbered rows and columns."""
    _place(out, draw, im, x0, y0, scale)
    for k in range(SIZE + 1):
        draw.line([x0 + k * scale, y0, x0 + k * scale, y0 + SIZE * scale], fill=(18, 18, 22))
        draw.line([x0, y0 + k * scale, x0 + SIZE * scale, y0 + k * scale], fill=(18, 18, 22))
    for k in range(SIZE):
        draw.text((x0 + k * scale + scale / 2, y0 - 8), f"{k % 10}", font=small, fill=(190, 190, 198), anchor="mm")
        draw.text((x0 - 9, y0 + k * scale + scale / 2), f"{k}", font=small, fill=(190, 190, 198), anchor="mm")


def _strip(out, draw, im, x, y):
    _place(out, draw, im, x, y, 1)
    _place(out, draw, im, x + 24, y, 2)
    _place(out, draw, im, x + 64, y, 4)


def _vanilla_images(tool):
    from PIL import Image
    colour = Image.open(io.BytesIO(vanilla_png(TOOLS[tool]["vanilla"]))).convert("RGBA")
    grey = colour.copy()
    px = grey.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            if a:
                l = round(0.299 * r + 0.587 * g + 0.114 * b)
                px[x, y] = (l, l, l, 255)
    return colour, grey


def _zone_image(tool):
    from PIL import Image
    tint = {"head": (120, 130, 140), "handle": (120, 130, 140), "grip": (215, 170, 90),
            "binding": (90, 170, 255), "reinforcement": (255, 95, 95)}
    im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = im.load()
    for name in LAYER_ORDER:
        for (x, y) in layers(tool)[name]:
            px[x, y] = tint[name] + (255,)
    return im


def grid_sheet(tool, path):
    """Vanilla beside ours, grey only, on the numbered grid, plus the case with no reinforcement."""
    colour, grey = _vanilla_images(tool)
    panels = [("vanilla, color", colour), ("vanilla, gris", grey),
              ("Temper, gris (agarre en cuero)", composite(tool)),
              ("Temper, sin refuerzo", composite(tool, reinforcement=False)),
              ("zonas: azul binding, rojo refuerzo, ocre agarre", _zone_image(tool))]
    S, pad, top = 14, 30, 30
    cell = SIZE * S
    out, draw, font, small = _sheet(len(panels) * (cell + pad + 16) + pad, top + cell + pad + 95)
    for i, (name, im) in enumerate(panels):
        x0, y0 = pad + 16 + i * (cell + pad + 16), top
        _gridded(out, draw, small, im, x0, y0, S)
        draw.text((x0 - 16, y0 + cell + 8), name, font=font, fill=(232, 232, 238))
        draw.text((x0 - 16, y0 + cell + 28), "1:1  2x   4x", font=small, fill=(170, 170, 178))
        _strip(out, draw, im, x0 - 16, y0 + cell + 42)
    out.save(path)
    print(f"wrote {path}")


def layers_sheet(tool, path):
    from PIL import Image
    panels = []
    for name in LAYER_ORDER:
        im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        px = im.load()
        for (x, y), g in layers(tool)[name].items():
            px[x, y] = (g, g, g, 255)
        panels.append((f"{name}  ({len(layers(tool)[name])} px)", im))
    panels.append(("compuesto", composite(tool)))
    S, pad, top = 10, 30, 30
    cell = SIZE * S
    out, draw, font, small = _sheet(len(panels) * (cell + pad + 16) + pad, top + cell + pad + 30)
    for i, (name, im) in enumerate(panels):
        x0 = pad + 16 + i * (cell + pad + 16)
        _gridded(out, draw, small, im, x0, top, S)
        draw.text((x0 - 16, top + cell + 8), name, font=font, fill=(232, 232, 238))
    out.save(path)
    print(f"wrote {path}")


def materials_sheet(tool, path):
    """Three mixes that put every material in every slot, then each material in all four slots."""
    colours = load_materials()
    names = list(colours)
    es = {"wood": "madera", "iron": "hierro", "diamond": "diamante"}

    def mk(head, handle, binding, reinforcement):
        return {"head": head, "handle": handle, "binding": binding, "reinforcement": reinforcement}

    n = len(names)
    mixes = [mk(names[i % n], names[(i + 1) % n], names[(i + 2) % n], names[i % n]) for i in range(n)]
    uniform = [mk(m, m, m, m) for m in names]
    S, pad, top, cap = 14, 30, 30, 110
    cell = SIZE * S
    out, draw, font, small = _sheet(n * (cell + pad + 16) + pad, 2 * (top + cell + cap) + pad)
    for r, (title, group) in enumerate((("Mezclas: cada material en cada ranura", mixes),
                                        ("Un solo material en las cuatro ranuras", uniform))):
        y0 = pad + r * (top + cell + cap) + top
        draw.text((pad, y0 - top + 4), title, font=font, fill=(238, 238, 244))
        for c, m in enumerate(group):
            x0 = pad + 16 + c * (cell + pad + 16)
            im = composite(tool, m, colours)
            _gridded(out, draw, small, im, x0, y0, S)
            _strip(out, draw, im, x0 - 16, y0 + cell + 8)
            text = ("todo " + es.get(m["head"], m["head"]) if len(set(m.values())) == 1 else
                    "\n".join(f"{slot}: {es.get(m[slot], m[slot])}" for slot in ("head", "handle", "binding", "reinforcement")))
            draw.text((x0 - 16, y0 + cell + 30), text, font=small, fill=(206, 206, 214))
    out.save(path)
    print(f"wrote {path}")


def ascii_map(tool):
    L = layers(tool)
    marks = {"reinforcement": "R", "binding": "B", "grip": "G", "head": "H", "handle": "h"}
    lines = []
    for y in range(SIZE):
        row = ""
        for x in range(SIZE):
            row += next((marks[k] for k in marks if (x, y) in L[k]), ".")
        lines.append(f"{y:2d} {row}")
    return "\n".join(lines)


# ---------------------------------------------------------------- export

def export(tool):
    """
    Writes what the game loads: one grayscale texture per tint layer, the item model and the item
    model definition, all from LAYER_ORDER, so the layer a texture sits on, the layer its tint sits
    on and the part slot that tint reads cannot disagree.
    """
    from PIL import Image
    problems = audit(tool)
    for p in problems:
        print("  audit:", p)
    if problems:
        raise SystemExit("refusing to export a sprite that fails its own audit")
    assets = os.path.join(ROOT, "common", "src", "main", "resources", "assets", "temper")
    textures = os.path.join(assets, "textures", "item")
    os.makedirs(textures, exist_ok=True)
    for i, name in enumerate(LAYER_ORDER):
        im = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        px = im.load()
        for (x, y), g in layers(tool)[name].items():
            px[x, y] = (g, g, g, 255)
        im.save(os.path.join(textures, f"{tool}_{name}.png"))
        print(f"  layer {i}  {tool}_{name}.png  {len(layers(tool)[name]):2d} px")
    model = {"parent": "minecraft:item/handheld",
             "textures": {f"layer{i}": f"temper:item/{tool}_{name}" for i, name in enumerate(LAYER_ORDER)}}
    _write_json(os.path.join(assets, "models", "item", f"{tool}.json"), model)
    tints = [{"type": "minecraft:constant", "value": LEATHER} if name == "grip"
             else {"type": "temper:part", "slot": name} for name in LAYER_ORDER]
    _write_json(os.path.join(assets, "items", f"{tool}.json"),
                {"model": {"type": "minecraft:model", "model": f"temper:item/{tool}", "tints": tints}})


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"  wrote {os.path.basename(path)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("--grid", action="store_true")
    parser.add_argument("--materials", action="store_true")
    parser.add_argument("--layers", action="store_true")
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    drafts = os.path.join(ROOT, "build", "texture-drafts")
    os.makedirs(drafts, exist_ok=True)
    problems = audit(args.tool)
    for p in problems:
        print("audit:", p)
    if args.export:
        export(args.tool)
    if args.grid:
        grid_sheet(args.tool, os.path.join(drafts, f"{args.tool}-vs-vanilla.png"))
    if args.materials:
        materials_sheet(args.tool, os.path.join(drafts, f"{args.tool}-materials.png"))
    if args.layers:
        layers_sheet(args.tool, os.path.join(drafts, f"{args.tool}-layers.png"))
    if args.ascii or not (args.export or args.grid or args.materials or args.layers):
        print(ascii_map(args.tool))
        for name in LAYER_ORDER:
            px = layers(args.tool)[name]
            print(f"  {name:<14}{len(px):3d} px   grey {min(px.values())/255:.0%}..{max(px.values())/255:.0%}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
