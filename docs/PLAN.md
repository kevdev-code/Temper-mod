# Temper — Master Plan

Design and scope document. `CLAUDE.md` covers the _how_ of the repo; this covers
the _what_ and the _why_.

---

## 1. Concept

**Temper** replaces Minecraft's tool progression with a part-based crafting system.
Instead of picking a tier, you forge a tool out of four separate parts, each made
from a different material, and each material contributes something different.

Spiritually a successor to Tinkers' Construct, redesigned around one principle that
Tinkers' never fully committed to: **every part must own a distinct decision.**

The name refers to tempering — the metallurgical step that gives steel its final
properties — and to the fact that every tool ends up with a character of its own.

## 2. Design pillars

**Combinatorics over content.** A dozen grayscale textures tinted at runtime produce
thousands of visually distinct tools. The mod's value is a _system_, not a catalogue.
Whenever a feature can be expressed as a new row in a data table instead of new code
or new art, it should be.

**Every part is a question.** If a player can equip a part without thinking, that part
is dead weight. This is the single biggest lesson from Tinkers': its binding slot was
widely ignored because it moved numbers nobody could feel.

**No dominant build.** For any combination, there should exist a situation where a
different combination is better. Strictly-superior options collapse the system into a
single correct answer.

**Vanilla enchanting stays.** Replacing the enchantment system means reimplementing
half the game for marginal gain.

## 3. The replacement doctrine

Temper replaces vanilla tools, but **replacement means role, not power.**

✓ **What it means:** Temper tools occupy the same progression slots vanilla tools do.
A wooden-headed Temper tool performs roughly like a vanilla wooden tool; a
netherite-headed one performs roughly like vanilla netherite. Players still need to
mine diamonds and still need to go to the Nether.

✗ **What it must not mean:** Temper tools having higher ceilings than vanilla. The
moment the best combination beats netherite outright, progression collapses and the
rest of the game stops mattering.

**The advantage is specialization, not magnitude.** Temper lets a player build a tool
vanilla could never produce — a fast, fragile, highly-enchantable pickaxe; a slow,
enormous-durability axe — but never one that is simply better at everything.

**Consequence of replacing:** since Temper tools _are_ the game's tools, the 1.0
release must cover every vanilla tool role — pickaxe, axe, shovel, sword, hoe — at
minimum. Shipping with only a sword is not an option for a replacement mod. This
does not change the vertical slice; it changes the 1.0 bar.

## 4. Tool anatomy

Four parts. Each owns a different _kind_ of decision, not a share of the same number.

| Part              | Owns                                         | The question it asks                     |
| ----------------- | -------------------------------------------- | ---------------------------------------- |
| **Head**          | Attack damage, mining speed, mining level    | How hard does it hit?                    |
| **Handle**        | Durability multiplier, attack speed          | How long does it last, how nimble is it? |
| **Binding**       | Enchantability, **number of modifier slots** | How much can I customize it?             |
| **Reinforcement** | One behavioural trait (no raw numbers)       | What makes it special?                   |

The binding is the deliberate fix to Tinkers' weakest slot. By owning modifier slot
count, it becomes a real trade: a gold binding might give fewer points of
enchantability but an extra slot, which changes how the whole tool is built.

The reinforcement is optional. A tool assembled without one is valid — it simply has
no trait.

**The handle colours the metal, not the whole hilt.** A hilt reads as three pieces: guard,
grip and pommel. The handle material tints the guard and the pommel; the grip, the band the
hand actually closes on, is a fixed colour that no material touches. Gripping solid iron or
diamond does not read as a tool, and vanilla answers the same problem the same way, with a
wooden handle that never changes whatever the head is made of. The grip being one constant
across every tool is a feature, not a limitation: it is what gives the set a common signature,
and it is what keeps a wood head on a wood handle — a pairing vanilla never has to draw —
from merging into a single brown mass.

## 5. Stat model

**Head contributes absolute values. Handle contributes multipliers.**

```
durability   = head.baseDurability * handle.durabilityMultiplier
attackDamage = head.attackDamage
attackSpeed  = head.baseSpeed * handle.speedMultiplier
miningSpeed  = head.miningSpeed
miningLevel  = head.miningLevel
enchantValue = binding.enchantability
modSlots     = binding.slots
```

Absolute-plus-multiplier prevents four mediocre materials from summing into a good
tool, which is what a straight average would do.

**Material traits are slot-scoped.** A material's personality applies only through the
part it occupies: gold's fragility affects durability when it's the handle, and its
enchantability when it's the binding. The same material feels different depending on
where you put it. This is what makes the combination space interesting rather than
merely large.

**Calibration targets.** Vanilla values are the anchor — a Temper tool whose head is
material X should land near vanilla's tier for X. Reference values (durability,
mining speed, attack damage bonus, enchantability) must be read from the game's own
`ToolMaterial` constants in 26.1.2 rather than from memory or from 1.21-era tables.

## 6. Materials

Start with vanilla-sourced materials only. Custom materials come after the system works.

Initial set: wood, stone, copper, iron, gold, diamond, netherite.

Each material defines:

- A display colour (drives the runtime tint)
- Head stats, handle multipliers, binding stats
- An optional trait, applied per slot
- Which part types it is valid for (stone makes a poor handle; that is a design
  statement, not an oversight)

Materials live in data, not code. Adding one should be a JSON entry.

## 7. Modifiers

**Limited and mutually exclusive.** Slot count comes from the binding. Choosing one
modifier means giving up another. Tinkers' unlimited modifier stacking is the single
most cited source of its balance problems.

Modifiers are additive to a working system and are not part of the core. They belong
in a later phase.

## 8. Repair and enchanting

**Repair** uses the head's material, at an increasing cost: each repair permanently
reduces maximum durability slightly. Tools are long-lived but not immortal. Tinkers'
free infinite repair is why its tools outlived the rest of the game.

**Enchanting** is vanilla, unchanged. Enchantability comes from the binding.

## 9. Stations

Two blocks, each with a GUI.

**Part Forge** — turns raw material into parts. Select a part type and a material,
consume the material, produce the part.

**Assembly Bench** — tabbed. Tab one assembles four parts into a finished tool. Tab
two applies and removes modifiers.

The **Smeltery** is on the roadmap, not in the backlog — but it is the final phase.
It is a multiblock with fluids, temperature, casting and molten-metal rendering, and
on its own it is larger than everything else in this document combined.

## 10. Rendering architecture

**This is the system that decides whether the mod exists.** It is built first.

Part textures are authored in **grayscale**. The game tints them at runtime from the
material stored on the item.

Mechanism (native in 26.1, no hacks required):

- The tool's item model has one layer per drawn piece, each carrying its own `tintindex`:
  the part slots, plus the fixed grip from section 4.
- The items model definition lists one tint source per index, in layer order.
- A custom `ItemTintSource` implements `calculate(ItemStack, level, entity)`, reads
  the part material from the stack's data component, and returns that material's RGB.
- Registration is the part that differs per loader. `ItemTintSources.ID_MAPPER` is private in
  vanilla: Fabric API opens it with an access widener that applies only to the Fabric module, and
  NeoForge exposes it through `RegisterColorHandlersEvent.ItemTintSources` on the mod bus. So
  `common` owns _what_ gets registered and each platform entrypoint passes in _how_: the shared
  init takes the registrar as an argument.

Reference: `docs.fabricmc.net/26.1.2/develop/items/item-appearance`, which shows the
`ID_MAPPER` call directly — correct on Fabric, uncompilable anywhere else.

**Client APIs are where multiloader diverges most, and one loader's documentation will present
as standard something that only works there.** Expect this again at the Assembly Bench in Phase 3
(menus, screens, networking) and at the Smeltery in Phase 7 (fluids and custom rendering): assume
the registration path differs and keep the decision in `common` behind an injected registrar.

**The leverage this buys:**

| Parts              | Materials | Textures authored | Resulting variants |
| ------------------ | --------- | ----------------- | ------------------ |
| 2                  | 10        | 2                 | 100                |
| 4                  | 10        | 4                 | 10,000             |
| 4 (× 5 tool types) | 10        | 20                | 50,000             |

Twenty grayscale textures produce a five-figure combination space. This ratio is the
entire argument for the mod's architecture. The grip costs one more texture per tool type
and contributes no variants at all, which is exactly what being constant means.

**A model layer index is not a part slot index.** The tint source is told which _part slot_
to read; the model decides which _layer_ that tint paints. In Phase 1 the two line up by
coincidence: handle is slot 0 and layer 0, head is slot 1 and layer 1. The coincidence is
already partial — layer 2 is the grip, which is no slot at all — and Phase 2 ends it, because
binding and reinforcement land on layers 3 and 4 while their slots are 2 and 3. Any code that
assumes `layer == slot` fails silently, tinting a part with another part's material rather
than raising anything.

**Layers never share a pixel.** This is a constraint of the renderer, not a design preference,
and it shapes the geometry of every sprite from Phase 4 on. An empty reinforcement is hidden by
tinting its layer fully transparent (section 15), and in the GUI a layer hidden that way also hides
whatever another layer drew beneath it. The case that revealed it: the pickaxe's knob sat over the
last pixel of the haft, and the handle layer drew that pixel too so that a pickaxe without a
reinforcement would keep its whole haft. In the screenshot it did not: that pixel showed the world
behind the hotbar, while the haft pixel next to it, under no other layer, was drawn. So two pieces
can never occupy the same cell, and an optional piece has to be an appendage that sits beside what
it attaches to, never a cap over it. The knob became three pixels cupping the haft's end instead of
four covering it. The sprite script refuses an overlap, and the checker compares the dark haft
pixels the knob cups on purpose, so the case stays verified rather than assumed.

## 11. Data model

A finished tool is a single item whose identity lives in data components:

- Which material occupies each of the four part slots
- Computed stats, cached so they are not recalculated per tick
- Applied modifiers
- Remaining durability and current maximum (which decays with repairs)

Stats are computed on assembly and on modifier change, not on use.

## 12. Phases

The riskiest system goes first. Nothing else is designed in detail until rendering
is proven.

**Phases 3 and 4 were swapped after Phase 2 shipped, and are listed here in the order they run.**
The numbers still belong to their content, so Phase 4 is still tool coverage. Tool coverage adds no
new API: it reuses the material table, the assembly and the recipe, all of which are proven; the
way sprites are drawn did change, and Phase 4 below says how. Stations bring the project's first menus, screens and networking, which is where
multiloader diverges most, and nothing else waits on them. Running coverage first also settles the
surface question in section 15 with five tool types of evidence rather than with one sprite.

The cost is accepted rather than overlooked: each tool type needs its own shape in the crafting
table until the Assembly Bench exists, so some of those recipes are throwaway.

### Phase 0 — Rendering spike

A throwaway item with two grayscale layers that tints from a hardcoded data component.
No materials, no parts, no stats. Two hours of work that determines whether the
project is viable.

### Phase 1 — Vertical slice

One tool type: **sword**. Two parts: head and handle. Three materials: wood, iron,
diamond. Assembled in the vanilla crafting table — **no GUI yet**. Stats derived from
part materials. Nine possible swords, each visually distinct.

If this works, everything after it is adding rows to tables.

### Phase 2 — Full anatomy

Binding and reinforcement. Four-layer rendering. Modifier slot count driven by binding.

### Phase 4 — Tool coverage

Pickaxe, axe, shovel, hoe. Required for the replacement doctrine to hold.

**The drawing method changed here.** The sword was drawn from a parametric model: zones as boxes
on a diagonal axis, outlines and seams computed. The pickaxe was tried the same way, as strokes
with a centreline and a width profile, and failed eight times: the geometry came out of formulas
instead of the sprite the player already knows, and each round fixed one thing and broke another.
From the pickaxe on, a sprite starts from the vanilla PNG of the matching tool type, read out of the
game jar and never redrawn, with head and stick told apart by the PNG's own colours. On that base
three things are added and nothing else, each listed pixel by pixel: blades at the head's points
(the binding), a small knob on the butt of the haft (the reinforcement), and a stretch of haft cut
square across it (the grip). The head's proportions, the haft's angle and thickness and where they
cross stay vanilla's. That is what makes a Temper pickaxe read as a pickaxe at 1:1 in a slot: the
silhouette is the one the player has seen ten thousand times, and the parts are what changes on it.

Every comparison sheet carries a numbered grid, rows down the side and columns across the top,
with ours beside vanilla at the same scale. It is what let the pickaxe close in two rounds after
eight without it: a correction names a cell, "(13,4) becomes grip, (15,3) goes", instead of
describing a shape, and the next sheet shows whether that cell changed. Keep it for the axe, the
shovel and the hoe.

### Phase 3 — Stations

Part Forge, then Assembly Bench with tabs. First `MenuType`, screen and networking
work in the project.

### Phase 5 — Materials and traits

Full material roster, per-slot traits, mining levels.

### Phase 6 — Modifiers

The modifier system proper.

### Phase 7 — Smeltery

Multiblock, fluids, casting.

## 13. Definition of done

A part or tool type is not finished until:

- [ ] Grayscale texture, one per part type per tool type
- [ ] Item model with correct layer order and tint indices
- [ ] Items model definition wired to the tint source
- [ ] Material data entry with all slot-relevant stats
- [ ] Stats verified in-game against the vanilla calibration target
- [ ] Recipe
- [ ] Localization in `en_us.json`
- [ ] Appears in the mod's creative tab
- [ ] **Visually verified on both Fabric and NeoForge**

Compiling is not evidence that it looks right.

## 14. Out of scope

Not in 1.0, not forgotten:

- Tools that level up with use
- Custom enchantment system
- Custom materials beyond vanilla sources
- Armour
- Ranged weapons
- Tool types with no vanilla equivalent (hammer, scythe, excavator)

## 15. Open questions

**Answered in Phase 2.** _Does a tool with an empty reinforcement slot render its layer at all?_
It draws nothing. The layer is always present in the model — there is one model, not two — and the
tint source returns a fully transparent colour when the slot is empty, so the layer contributes no
pixels. Two reasons. A part that is not there should not be drawn: any placeholder colour invents a
material the tool does not have and reads as a rendering fault, while an absent piece reads as an
empty slot, which is the truth and is useful feedback. And the alternative, a second model selected
by a condition, would mean maintaining two copies of the layer list, which is exactly the duplication
that lets a layer drift away from its slot.

- **How is surface split between the four parts?** Open until there are more tool types. As it
  stands the blade shows 24 interior pixels, the reinforcement 10, the binding 7 and the handle 3,
  and a part with three pixels of colour cannot be told apart by its material, which is the whole
  premise. The constraint is not arithmetic: a reallocation was measured that gave every part ten or
  more and kept the silhouette in one piece, but it only got there by growing the pommel from five
  rows to seven, and the sword stopped reading as the same weapon. Sixteen by sixteen does not hold
  four parts, an outline around each and a constant grip without the proportions going wrong
  somewhere. Two things worth keeping from the attempt: a part needs one contiguous block about
  three pixels thick, because the outline eats anything thinner, and splitting a part into two small
  zones makes it worse, not better — the handle dropped to a single interior pixel that way. Decide
  it once pickaxe, axe, shovel and hoe exist, where each tool type has its own proportions and the
  handle is not competing with a blade for the same diagonal.

- What happens to existing vanilla tools in a world where Temper is installed —
  coexist silently, or is there a conversion path?
- Do parts stack? A stack of identical iron sword heads is convenient but complicates
  the component model.
- Mining level: reuse vanilla's block tags, or introduce a numeric level?
