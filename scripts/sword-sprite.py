#!/usr/bin/env python3
"""
Temper's sword sprite: one drawing, four zones, three tint layers.

    python scripts/sword-sprite.py            # writes build/texture-drafts/sword-hilt.png
    python scripts/sword-sprite.py --ascii    # prints the sprite, its zone map and the audit

ZONES
    Every pixel is classified in a frame aligned with the sword: u runs along the blade (tip at +15,
    pommel corner at -15), v runs across it, and v = 0 is the corner-to-corner diagonal. Each zone is
    a range of u and a range of v, so the four of them share one axis by construction.

        blade    the tinted head, three pixels of body between its outline pixels
        guard    a bar across the blade with two equal arms, each reaching well past the blade's
                 edge the way vanilla's cross does; a short neck under it narrows into the grip
        grip     the hand's zone: narrower than either neighbour, and never tinted by a material
        pommel   a block, wider than the grip, squared off by the corner

    The grip is four wide, half a pixel toward the lit side. Even widths cannot sit centred on a
    diagonal, vanilla's stick has the same offset, and three wide left the grip a single pixel of
    fill between its edges.

SEAMS
    A zone's outline is computed: a pixel goes dark when a four-neighbour lies outside the sprite,
    or belongs to a zone of higher RANK. So every boundary between zones is a single dark line, and
    RANK decides which side carries it. The order copies what vanilla does with its stick: the grip
    is never dark, the metal around it is; the guard is dark where it meets the blade; the pommel
    is dark where it meets the grip.

LAYERS
    LAYER maps zones to the model's tint layers. Today: head (blade), handle (guard and pommel) and
    grip, which gets a constant leather colour instead of a material. Phase 2 will most likely hand
    the guard to the binding: that is the one line marked below, and nothing else moves, because the
    outlines come from zones, not layers.

TONES
    The game multiplies each layer's grey by its colour, so the grey ladder decides contrast and the
    material colour decides where the ladder lands. Both were calibrated against vanilla's own
    swords, measured from the game jar, not from their source textures: vanilla's iron blade is pure
    white in the body with a 59% shade, and its diamond blade sits on (51,235,203) with a 41% shade.
        blade fill   100 / 90 / 55 %   the 55% floor is vanilla's own shade depth
        metal fill    75 / 50 / 33 %   vanilla's hilt body runs at 42..47% of its blade body
        grip fill    100 / 80 / 65 %   times LEATHER, one constant for every sword: it is what ties
                                       the set together, and it sits darker and redder than oak so
                                       wood on wood, which vanilla never has, keeps its seams
    Material colours live in temper/materials.json and this script reads them from there, so the
    preview shows what the game shows. The rule for a new material: pick the colour that makes the
    blade body (90% grey) land on the vanilla item's main tone, and check the shade follows. For a
    material that is dark to begin with, like wood, the 55% floor drags the whole sprite under
    vanilla; there the colour is raised until the zone means match instead (wood sits 22% above
    its body-matched value for that reason).
"""

import argparse
import os

SIZE = 16
TRANSPARENT = (0, 0, 0, 0)

# How far each arm of the guard reaches from the blade's axis, in v, the same on both sides. The
# blade ends at |v| = 2; 7 is vanilla's reach and makes the cross read as its own piece.
GUARD_REACH = 7

# Boxes of (u range, v range) per zone, v signed. Tip first.
ZONES = {
    "blade":         [((-2, 15), (-2, 2))],
    "reinforcement": [((-2, 1), (3, 6)),                         # langets clasping the blade's base,
                      ((-2, 1), (-6, -3))],                      # one tab each side, mirrored
    "guard":         [((-5, -3), (-GUARD_REACH, GUARD_REACH)),   # the bar, symmetric about the axis
                      ((-6, -6), (-1, 1))],                      # its underside narrows into the grip
    "grip":          [((-10, -7), (-2, 1))],   # four wide, offset toward the lit side (negative v)
    "pommel":        [((-15, -11), (-3, 3))],
}

# Who carries the dark seam: the lower rank does. Grip highest so it stays leather to its edges;
# reinforcement highest, because it is applied on top of the blade: the blade takes the seam, which it
# was already drawing as its own edge there, so the small tabs keep their fill instead of going all dark.
RANK = {"reinforcement": 5, "grip": 4, "blade": 3, "guard": 2, "pommel": 1}

# Zone -> tint layer. This and LAYER_ORDER below are the only places the mapping exists, and the
# game's two JSON files are generated from them, so a layer can never drift from its slot.
LAYER = {
    "blade": "head",
    "guard": "binding",
    "grip": "grip",
    "pommel": "handle",
    "reinforcement": "reinforcement",
}

# Model layer index -> layer name. The index is the position in the item model's texture list and in
# its tint list; it is NOT a part slot index, and past layer 1 the two no longer agree. Every layer
# but the grip names a PartSlot; the grip is a constant colour.
LAYER_ORDER = ["handle", "head", "grip", "binding", "reinforcement"]

# Grey ladders per layer: (lit, body, shade, edge, seam). The edge is the outer silhouette and
# stays near black; a seam is the line between two zones and only needs to separate them, so it
# sits at 33..40%, still dark by the brief but leaving the small metal zones some colour.
TONES = {
    "head":          (0xFF, 0xE6, 0x8C, 0x33, 0x66),   # 100 / 90 / 55 / 20 / 40 %
    "handle":        (0xBF, 0x80, 0x54, 0x2E, 0x55),   #  75 / 50 / 33 / 18 / 33 %
    "binding":       (0xBF, 0x80, 0x54, 0x2E, 0x55),   # the same metal band; it never touches the handle
    "reinforcement": (0xD9, 0x9B, 0x6B, 0x2E, 0x55),   #  85 / 61 / 42 %, a touch brighter: it is the accent
    "grip":          (0xFF, 0xCC, 0xA6, 0x66, 0x8A),   # 100 / 80 / 65 / 40 / 54 %, then times LEATHER
}
LEATHER = 0x8B5E3C                          # darker and redder than oak, so a wood blade on a wood handle still reads as two pieces


def load_materials():
    """Colours from temper/materials.json, the same file the game reads, so nothing can drift."""
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "common", "src", "main", "resources", "temper", "materials.json")
    with open(path, encoding="utf-8") as f:
        table = json.load(f)["materials"]
    return {name: int(entry["color"].lstrip("#"), 16) for name, entry in table.items()}


MATERIALS = load_materials()

# The previous calibration, kept only so --calibrate can show the change against it.
BEFORE = dict(
    tones={"head": (0xFF, 0xE6, 0x8C, 0x33, 0x66), "handle": (0xBF, 0x80, 0x54, 0x2E, 0x55),
           "grip": (0xFF, 0xCC, 0xA6, 0x66, 0x8A)},
    materials={"wood": 0x826225, "iron": 0xFFFFFF, "diamond": 0x39FFE2},
    leather=0x826226,
)


def uv(x, y):
    return x - y, x + y - 15


def zone_at(x, y):
    u, v = uv(x, y)
    for name, boxes in ZONES.items():
        for (u0, u1), (v0, v1) in boxes:
            if u0 <= u <= u1 and v0 <= v <= v1:
                return name
    return None


def outline_kind(x, y, zone):
    """'edge' against the outside, 'seam' against a higher-ranked zone, None for fill."""
    kind = None
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if not (0 <= nx < SIZE and 0 <= ny < SIZE):
            return "edge"
        other = zone_at(nx, ny)
        if other is None:
            return "edge"
        if RANK[other] > RANK[zone]:
            kind = "seam"
    return kind


def fill_tone(zone, x, y):
    lit, body, shade = TONES[LAYER[zone]][:3]
    u, v = uv(x, y)
    if zone == "guard":                       # a bar across the blade: the face toward the blade is lit
        return lit if u >= -4 else shade
    if zone == "grip":                        # even width: the two core pixels are lit and shade
        return lit if v <= -1 else shade
    if zone == "reinforcement":               # two separate tabs; light each on its own upper edge
        return lit if abs(v) <= 4 else (body if abs(v) == 5 else shade)
    return lit if v < 0 else (body if v == 0 else shade)


OUTLINE_MASK = [[False] * SIZE for _ in range(SIZE)]


def build():
    """Grey RGBA pixels, plus the zone name per pixel. OUTLINE_MASK is refreshed as a side effect."""
    pixels = [[TRANSPARENT] * SIZE for _ in range(SIZE)]
    zones = [[None] * SIZE for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(SIZE):
            zone = zone_at(x, y)
            if zone is None:
                continue
            zones[y][x] = zone
            kind = outline_kind(x, y, zone)
            OUTLINE_MASK[y][x] = kind is not None
            ladder = TONES[LAYER[zone]]
            g = ladder[3] if kind == "edge" else (ladder[4] if kind == "seam" else fill_tone(zone, x, y))
            pixels[y][x] = (g, g, g, 255)
    return pixels, zones


def tinted(pixels, zones, head_rgb, handle_rgb, binding_rgb=None, reinforcement_rgb=None):
    """
    What the game shows: each layer's grey multiplied by its colour, the grip by LEATHER.
    Binding and reinforcement fall back to the handle, which is what a vanilla sword looks like:
    one material for the whole hilt.
    """
    colour = {"head": head_rgb, "handle": handle_rgb, "grip": LEATHER,
              "binding": binding_rgb if binding_rgb is not None else handle_rgb,
              "reinforcement": reinforcement_rgb if reinforcement_rgb is not None else handle_rgb}
    out = [[TRANSPARENT] * SIZE for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(SIZE):
            if not pixels[y][x][3]:
                continue
            g, rgb = pixels[y][x][0] / 255, colour[LAYER[zones[y][x]]]
            out[y][x] = (round(g * (rgb >> 16 & 255)), round(g * (rgb >> 8 & 255)), round(g * (rgb & 255)), 255)
    return out


def audit(pixels, zones):
    problems = []
    ranges = {"head": (0.55, 1.0), "handle": (0.33, 0.75),      # the calibrated ladders; the floor keeps fills off black
              "binding": (0.33, 0.75), "reinforcement": (0.33, 0.90)}
    for layer, (lo, hi) in ranges.items():
        fills = {pixels[y][x][0] for y in range(SIZE) for x in range(SIZE)
                 if zones[y][x] and LAYER[zones[y][x]] == layer and not OUTLINE_MASK[y][x]}
        if fills and not (lo <= round(min(fills) / 255, 2) and round(max(fills) / 255, 2) <= hi):
            problems.append(f"{layer} fill spans {min(fills)/255:.0%}..{max(fills)/255:.0%}, wanted {lo:.0%}..{hi:.0%}")
    for zone in ZONES:
        n = sum(1 for y in range(SIZE) for x in range(SIZE) if zones[y][x] == zone and not OUTLINE_MASK[y][x])
        if n == 0:
            problems.append(f"{zone} has no fill at all, only outline")
    filled = {(x, y) for y in range(SIZE) for x in range(SIZE) if pixels[y][x][3]}
    seen, todo = set(), [next(iter(filled))]
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        x, y = p
        todo += [q for q in ((x-1, y), (x+1, y), (x, y-1), (x, y+1), (x-1, y-1), (x+1, y+1), (x-1, y+1), (x+1, y-1)) if q in filled]
    if seen != filled:
        problems.append(f"{len(filled) - len(seen)} pixels float free of the rest")
    problems += guard_symmetry_problems(zones)
    for zone, boxes in ZONES.items():
        vs = [uv(x, y)[1] for y in range(SIZE) for x in range(SIZE) if zones[y][x] == zone]
        v0, v1 = boxes[0][1]
        allowed = 0.5 if (v1 - v0) % 2 == 0 else 0.75
        if abs(sum(vs) / len(vs)) > allowed:
            problems.append(f"{zone} is centred at v = {sum(vs)/len(vs):+.2f}, off the diagonal")
    return problems


def guard_arms(zones):
    """Reach of each guard arm from the blade's axis, measured, per row of the bar and overall."""
    bar_u = ZONES["guard"][0][0]
    rows = {}
    for y in range(SIZE):
        for x in range(SIZE):
            if zones[y][x] == "guard":
                u, v = uv(x, y)
                if bar_u[0] <= u <= bar_u[1]:
                    rows.setdefault(u, []).append(v)
    per_row = {u: (min(vs), max(vs)) for u, vs in sorted(rows.items())}
    left = sum(1 for vs in rows.values() for v in vs if v < 0)
    right = sum(1 for vs in rows.values() for v in vs if v > 0)
    reach = (min(v for vs in rows.values() for v in vs), max(v for vs in rows.values() for v in vs))
    return per_row, left, right, reach


def guard_symmetry_problems(zones):
    per_row, left, right, (lo, hi) = guard_arms(zones)
    problems = []
    if -lo != hi:
        problems.append(f"guard arms reach v = {lo} and v = +{hi}, not equal")
    if left != right:
        problems.append(f"guard has {left} pixels on one side of the axis and {right} on the other")
    for u, (a, b) in per_row.items():
        if -a != b:
            problems.append(f"guard row u = {u} spans v = {a}..{b}, not mirrored")
    return problems


def zone_fill_counts(pixels, zones):
    return {z: (sum(1 for y in range(SIZE) for x in range(SIZE) if zones[y][x] == z and not OUTLINE_MASK[y][x]),
                sum(1 for y in range(SIZE) for x in range(SIZE) if zones[y][x] == z)) for z in ZONES}


def as_text(pixels, zones=None):
    order = sorted({p[0] for row in pixels for p in row if p[3]}, reverse=True)
    chars = "@%+=-:#"
    marks = {"blade": "B", "guard": "G", "grip": "g", "pommel": "P", "reinforcement": "R"}
    return "\n".join(
        "".join("." if not pixels[y][x][3] else (marks[zones[y][x]] if zones else chars[min(order.index(pixels[y][x][0]), 6)])
                for x in range(SIZE))
        for y in range(SIZE))


def sheet(out_path, scale=8):
    from PIL import Image, ImageDraw, ImageFont

    pixels, zones = build()
    for p in audit(pixels, zones):
        print("  audit:", p)

    def to_image(px):
        im = Image.new("RGBA", (SIZE, SIZE))
        im.putdata([p for row in px for p in row])
        return im

    def up(im, s):
        return im.resize((SIZE * s, SIZE * s), Image.NEAREST)

    font, bold = ImageFont.load_default(size=12), ImageFont.load_default(size=14)
    cell, pad = SIZE * scale, 12
    names = list(MATERIALS)
    width = 3 * cell + 4 * pad
    height = pad + (cell + 30) + pad + (cell + 30) + pad + (SIZE + 30) + pad
    out = Image.new("RGB", (width, height), (34, 34, 38))
    draw = ImageDraw.Draw(out)

    def checker(x0, y0, w, h, s):
        for cy in range(0, h, s):
            for cx in range(0, w, s):
                shade = (58, 58, 62) if ((cx // s + cy // s) % 2 == 0) else (46, 46, 50)
                draw.rectangle([x0 + cx, y0 + cy, x0 + cx + s - 1, y0 + cy + s - 1], fill=shade)

    def place(im, x, y, s, label):
        checker(x, y, SIZE * s, SIZE * s, s if s > 1 else 2)
        out.paste(up(im, s), (x, y), up(im, s))
        if label:
            draw.text((x, y + SIZE * s + 6), label, font=font, fill=(215, 215, 222))

    # Row one: grey master, zone map, and the sprite with a leather grip but no material yet.
    y = pad
    place(to_image(pixels), pad, y, scale, "grey master, 8x")
    zone_rgb = {"blade": (90, 170, 255, 255), "guard": (255, 200, 60, 255), "grip": (200, 90, 200, 255), "pommel": (255, 130, 60, 255)}
    zone_img = [[zone_rgb[zones[yy][xx]] if zones[yy][xx] else TRANSPARENT for xx in range(SIZE)] for yy in range(SIZE)]
    place(to_image(zone_img), 2 * pad + cell, y, scale, "zones")
    neutral = tinted(pixels, zones, 0xFFFFFF, 0xFFFFFF)
    place(to_image(neutral), 3 * pad + 2 * cell, y, scale, "untinted (grip only)")

    # Row two: iron blade, handle in wood / iron / diamond, 8x.
    y += cell + 30 + pad
    for i, handle in enumerate(names):
        im = to_image(tinted(pixels, zones, MATERIALS["iron"], MATERIALS[handle]))
        place(im, pad + i * (cell + pad), y, scale, f"iron blade, {handle} handle")

    # Row three: the same at 1:1.
    y += cell + 30 + pad
    draw.text((pad, y + 2), "1:1", font=bold, fill=(230, 230, 236))
    x = pad + 40
    for handle in names:
        im = to_image(tinted(pixels, zones, MATERIALS["iron"], MATERIALS[handle]))
        place(im, x, y, 1, None)
        x += SIZE + 10

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.save(out_path)
    print(f"wrote {out_path}  ({width}x{height})")


def build_with_guard_reach(v_min, v_max=None):
    saved = ZONES["guard"][0]
    ZONES["guard"][0] = (saved[0], (v_min, saved[1][1] if v_max is None else v_max))
    try:
        return build()
    finally:
        ZONES["guard"][0] = saved


def compare_guard(out_path, scale=8):
    """Short upper arm (before) against the long one (after), grey and iron on iron, 8x and 1:1."""
    from PIL import Image, ImageDraw, ImageFont

    def to_image(px):
        im = Image.new("RGBA", (SIZE, SIZE))
        im.putdata([p for row in px for p in row])
        return im

    def up(im, s):
        return im.resize((SIZE * s, SIZE * s), Image.NEAREST)

    font, bold = ImageFont.load_default(size=12), ImageFont.load_default(size=14)
    cell, pad = SIZE * scale, 12
    versions = [("before: arms to v=-7 and v=+3", (-7, 3)), ("after: arms to v=-7 and v=+7", (-GUARD_REACH, GUARD_REACH))]
    width = 2 * (2 * cell + pad) + 3 * pad
    height = pad + 22 + cell + 26 + SIZE + 30 + pad
    out = Image.new("RGB", (width, height), (34, 34, 38))
    draw = ImageDraw.Draw(out)

    def checker(x0, y0, w, h, s):
        for cy in range(0, h, s):
            for cx in range(0, w, s):
                shade = (58, 58, 62) if ((cx // s + cy // s) % 2 == 0) else (46, 46, 50)
                draw.rectangle([x0 + cx, y0 + cy, x0 + cx + s - 1, y0 + cy + s - 1], fill=shade)

    def place(im, x, y, s):
        checker(x, y, SIZE * s, SIZE * s, s if s > 1 else 2)
        out.paste(up(im, s), (x, y), up(im, s))

    for col, (title, reach) in enumerate(versions):
        px, zn = build_with_guard_reach(*reach)
        x0 = pad + col * (2 * cell + 2 * pad)
        y = pad
        draw.text((x0, y), title, font=bold, fill=(230, 230, 236))
        y += 22
        grey, iron = to_image(px), to_image(tinted(px, zn, MATERIALS["iron"], MATERIALS["iron"]))
        place(grey, x0, y, scale)
        place(iron, x0 + cell + pad, y, scale)
        draw.text((x0, y + cell + 6), "grey", font=font, fill=(200, 200, 208))
        draw.text((x0 + cell + pad, y + cell + 6), "iron blade, iron handle", font=font, fill=(200, 200, 208))
        y += cell + 26
        draw.text((x0, y + 2), "1:1", font=font, fill=(200, 200, 208))
        place(grey, x0 + 30, y, 1)
        place(iron, x0 + 30 + SIZE + 8, y, 1)
        per_row, left, right, (lo, hi) = guard_arms(zn)
        print(f"  {title}: arms reach v={lo}..+{hi}, {left} px left of axis / {right} px right")
        for p in audit(px, zn):
            print(f"    audit:", p)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.save(out_path)
    print(f"wrote {out_path}  ({width}x{height})")


def export_layers(root):
    """
    Writes what the game loads: one grayscale texture per tint layer, plus the item model and the
    item model definition. Everything comes from LAYER_ORDER and LAYER, so the layer a texture sits
    on, the layer its tint sits on, and the part slot that tint reads can never disagree. Pixels are
    not redrawn: each keeps its grey and lands in the file of its layer.
    """
    import json

    from PIL import Image

    pixels, zones = build()
    problems = audit(pixels, zones)
    for problem in problems:
        print("  audit:", problem)
    if problems:
        raise SystemExit("refusing to export a sprite that fails its own audit")

    assets = os.path.join(root, "common", "src", "main", "resources", "assets", "temper")
    textures = os.path.join(assets, "textures", "item")
    os.makedirs(textures, exist_ok=True)
    for layer in LAYER_ORDER:
        image = Image.new("RGBA", (SIZE, SIZE))
        image.putdata([pixels[y][x] if zones[y][x] and LAYER[zones[y][x]] == layer else TRANSPARENT
                       for y in range(SIZE) for x in range(SIZE)])
        image.save(os.path.join(textures, f"sword_{layer}.png"))
        drawn = [z for z in ZONES if LAYER[z] == layer]
        n = sum(1 for y in range(SIZE) for x in range(SIZE) if zones[y][x] and LAYER[zones[y][x]] == layer)
        print(f"  layer {LAYER_ORDER.index(layer)}  sword_{layer}.png  {n:2d} px  <- " + ", ".join(drawn))

    model = {"parent": "minecraft:item/handheld",
             "textures": {f"layer{i}": f"temper:item/sword_{name}" for i, name in enumerate(LAYER_ORDER)}}
    write_json(os.path.join(assets, "models", "item", "sword.json"), model)

    # The grip is the only layer with no part behind it, so it is the only constant tint.
    tints = [{"type": "minecraft:constant", "value": LEATHER} if name == "grip"
             else {"type": "temper:part", "slot": name} for name in LAYER_ORDER]
    definition = {"model": {"type": "minecraft:model", "model": "temper:item/sword", "tints": tints}}
    write_json(os.path.join(assets, "items", "sword.json"), definition)
    print(f"  grip constant: {LEATHER} (#{LEATHER:06X})")
    print("  tint order: " + ", ".join(t.get("slot", "constant") for t in tints))


def write_json(path, data):
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"  wrote {os.path.basename(path)}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--guard-compare", action="store_true", help="short against long upper arm")
    parser.add_argument("--export", action="store_true", help="write the three layer textures into the mod assets")
    parser.add_argument("--calibrate", action="store_true", help="vanilla against ours, before and after, per material")
    parser.add_argument("--out", default=os.path.join(root, "build", "texture-drafts", "sword-hilt.png"))
    args = parser.parse_args()
    if args.calibrate:
        calibrate_sheet(os.path.join(root, "build", "texture-drafts", "calibration.png"),
                        os.path.join(root, "build", "texture-drafts", "ref"))
        return
    if args.export:
        export_layers(root)
        return
    if args.guard_compare:
        compare_guard(os.path.join(root, "build", "texture-drafts", "guard-arm-compare.png"))
        return
    pixels, zones = build()
    if args.ascii:
        print("tones (bright to dark):\n" + as_text(pixels))
        print("\nzones:\n" + as_text(pixels, zones))
        for z, (fill, total) in zone_fill_counts(pixels, zones).items():
            print(f"  {z:<7} {fill:2d} fill / {total:2d} px")
        per_row, left, right, (lo, hi) = guard_arms(zones)
        print(f"  guard arms: reach v = {lo} and +{hi}; {left} px left of the axis, {right} px right; per row " +
              ", ".join(f"u={u}: {a}..+{b}" for u, (a, b) in per_row.items()))
        for p in audit(pixels, zones):
            print("audit:", p)
        return
    sheet(args.out)


if __name__ == "__main__":
    main()
