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

- The tool's item model has one layer per part: `layer0` handle, `layer1` head,
  `layer2` binding, `layer3` reinforcement — each carrying its own `tintindex`.
- The items model definition lists one tint source per index.
- A custom `ItemTintSource` implements `calculate(ItemStack, level, entity)`, reads
  the part material from the stack's data component, and returns that material's RGB.
- Registered via `ItemTintSources.ID_MAPPER`.

Reference: `docs.fabricmc.net/26.1.2/develop/items/item-appearance`.

**The leverage this buys:**

| Parts              | Materials | Textures authored | Resulting variants |
| ------------------ | --------- | ----------------- | ------------------ |
| 2                  | 10        | 2                 | 100                |
| 4                  | 10        | 4                 | 10,000             |
| 4 (× 5 tool types) | 10        | 20                | 50,000             |

Twenty grayscale textures produce a five-figure combination space. This ratio is the
entire argument for the mod's architecture.

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

### Phase 3 — Stations

Part Forge, then Assembly Bench with tabs. First `MenuType`, screen and networking
work in the project.

### Phase 4 — Tool coverage

Pickaxe, axe, shovel, hoe. Required for the replacement doctrine to hold.

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

- Does a tool with an empty reinforcement slot render a fourth layer at all, or is the
  layer omitted?
- What happens to existing vanilla tools in a world where Temper is installed —
  coexist silently, or is there a conversion path?
- Do parts stack? A stack of identical iron sword heads is convenient but complicates
  the component model.
- Mining level: reuse vanilla's block tags, or introduce a numeric level?
