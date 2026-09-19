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
    blade fill 76..100%, metal fill 46..68%, each with a dark outline, as before. The grip is drawn
    in grey too and multiplied by LEATHER at render time, exactly like a material tint but with a
    fixed colour, so all three textures stay grayscale and one authoring rule holds.
"""

import argparse
import os

SIZE = 16
TRANSPARENT = (0, 0, 0, 0)

# How far each arm of the guard reaches from the blade's axis, in v, the same on both sides. The
# blade ends at |v| = 2; 7 is vanilla's reach and makes the cross read as its own piece.
GUARD_REACH = 7

# Boxes of (u range, v range) per zone. Tip first.
ZONES = {
    "blade":  [((-2, 15), (-2, 2))],
    "guard":  [((-5, -3), (-GUARD_REACH, GUARD_REACH)),   # the bar, symmetric about the axis
               ((-6, -6), (-1, 1))],                       # its underside narrows into the grip
    "grip":   [((-10, -7), (-2, 1))],    # four wide, offset toward the lit side (negative v)
    "pommel": [((-15, -11), (-3, 3))],
}

# Who carries the dark seam: the lower rank does. Grip highest so it stays leather to its edges.
RANK = {"grip": 4, "blade": 3, "guard": 2, "pommel": 1}

# Zone -> tint layer. Phase 2 change: "guard": "binding".
LAYER = {
    "blade": "head",
    "guard": "handle",
    "grip": "grip",
    "pommel": "handle",
}

# Grey ladders per layer: (lit, body, shade, edge, seam). The edge is the outer silhouette and
# stays near black; a seam is the line between two zones and only needs to separate them, so it
# sits at 33..40%, still dark by the brief but leaving the small metal zones some colour.
TONES = {
    "head":   (0xFF, 0xE0, 0xC2, 0x33, 0x66),    # 100 / 88 / 76 / 20 / 40 %
    "handle": (0xAD, 0x8F, 0x75, 0x2E, 0x55),    #  68 / 56 / 46 / 18 / 33 %
    "grip":   (0xFF, 0xCC, 0xA6, 0x66, 0x8A),    # 100 / 80 / 65 / 40 / 54 %, then multiplied by LEATHER
}
LEATHER = 0x8B5E3C                          # the constant grip colour; a shade off oak so wood/wood still reads
MATERIALS = {"wood": 0xA0763F, "iron": 0xD8D8D8, "diamond": 0x4AEDD9}


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


def tinted(pixels, zones, head_rgb, handle_rgb, binding_rgb=None):
    """What the game shows: each layer's grey multiplied by its colour; the grip by LEATHER."""
    colour = {"head": head_rgb, "handle": handle_rgb, "binding": binding_rgb or handle_rgb, "grip": LEATHER}
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
    ranges = {"head": (0.75, 1.0), "handle": (0.45, 0.70)}
    for layer, (lo, hi) in ranges.items():
        fills = {pixels[y][x][0] for y in range(SIZE) for x in range(SIZE)
                 if zones[y][x] and LAYER[zones[y][x]] == layer and not OUTLINE_MASK[y][x]}
        if fills and not (lo <= min(fills) / 255 and max(fills) / 255 <= hi):
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
    chars, marks = "@%+=-:#", {"blade": "B", "guard": "G", "grip": "g", "pommel": "P"}
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


def export_layers(out_dir):
    """
    Splits the approved sprite into the game's textures by the zone map alone: every pixel keeps
    its grey value and lands in the file of its LAYER. Nothing is redrawn. Also prints the constant
    the item model definition needs for the grip layer.
    """
    from PIL import Image

    pixels, zones = build()
    files = {"head": "sword_head.png", "handle": "sword_handle.png", "grip": "sword_grip.png"}
    os.makedirs(out_dir, exist_ok=True)
    for layer, name in files.items():
        im = Image.new("RGBA", (SIZE, SIZE))
        im.putdata([pixels[y][x] if zones[y][x] and LAYER[zones[y][x]] == layer else TRANSPARENT
                    for y in range(SIZE) for x in range(SIZE)])
        im.save(os.path.join(out_dir, name))
        n = sum(1 for y in range(SIZE) for x in range(SIZE) if zones[y][x] and LAYER[zones[y][x]] == layer)
        print(f"  {name:<18} {n:2d} px  <- zones " + ", ".join(z for z in ZONES if LAYER[z] == layer))
    print(f"  grip constant tint: {LEATHER} (#{LEATHER:06X}), for minecraft:constant \"value\"")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--guard-compare", action="store_true", help="short against long upper arm")
    parser.add_argument("--export", action="store_true", help="write the three layer textures into the mod assets")
    parser.add_argument("--out", default=os.path.join(root, "build", "texture-drafts", "sword-hilt.png"))
    args = parser.parse_args()
    if args.export:
        export_layers(os.path.join(root, "common", "src", "main", "resources", "assets", "temper", "textures", "item"))
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
