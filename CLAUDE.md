# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Temper is a Minecraft mod (mod id `temper`) that replaces vanilla tool progression with a four-part
crafting system. Design, scope, phases and open questions live in `docs/PLAN.md` — read it before
adding any gameplay feature. This file covers only how the repo works.

Targets Minecraft **26.1.2**, Java **25**, Gradle 9.5.1, built with Architectury Loom for both
**Fabric** and **NeoForge**. Base package is `io.github.kevdev_code.temper`.

State: PLAN.md Phase 1 (the vertical slice) is in. One sword item, two part slots, three materials,
assembled in the vanilla crafting table. Phase 0's spike lives on branch `phase-0/tint-spike`; nothing
from it is needed any more.

## Version context

Minecraft 26.1 uses calver (`year.release.patch`) on quarterly drops. Anything written
for `1.20.x` or `1.21.x` describes a different API, not an older patch of this one.

Since 26.1 the game ships unobfuscated — real class, field, method and parameter names,
no mappings, no remap step.

Architectury's 20.x line targets Minecraft 26.1.2 (21.x is for 26.2, 22.x for 26.3).
Compile against the newest 20.x; declare the minimum you actually use in the loader
metadata. These are different numbers and they are allowed to differ. An Architectury bump can
raise the NeoForge floor (20.1.14 needs NeoForge ≥ 26.1.2.99): read the `neoforge.mods.toml` inside
`architectury-neoforge-<ver>.jar` in the Gradle cache and move `neoforge_version` with it.

## Working rules

**Don't invent API signatures.** The 26.1 API is recent and differs substantially from the
1.21 material that dominates search results. If unsure whether a class, method or signature
exists, say so and ask for the decompiled source or the versioned docs
(`docs.fabricmc.net/26.1.2`) instead of guessing.

**Verify by compiling, on both platforms.** `common` compiles fine in cases where a platform
module won't.

**The jar outranks the docs.** `docs.fabricmc.net/26.1.2` shows `ItemTintSources.ID_MAPPER.put(...)`;
in vanilla that field is private and only Fabric API's access widener opens it, so the same line
cannot compile in `common` or on NeoForge. `javap -p -cp <jar> <class>` (JDK 25 at
`C:\Program Files\Java\jdk-25.0.4.1\bin`) on the Minecraft jars under
`~/.gradle/caches/fabric-loom/minecraftMaven/` and the project's `.gradle/loom-cache/minecraftMaven/`
(the latter has the access-widened variant used by `fabric/`) settles such questions in seconds.
NeoForge and FML sources jars are in `~/.gradle/caches/modules-2/` and readable with `unzip -p`.

## Commands

Use `./gradlew` from bash or `gradlew.bat` from PowerShell. Add `--offline` once deps are cached.

```
./gradlew build                     # builds all three modules; ships jars land in fabric/build/libs and neoforge/build/libs
./gradlew :fabric:runClient         # launch Fabric dev client
./gradlew :neoforge:runClient       # launch NeoForge dev client
./gradlew :fabric:runServer         # dev server (also :neoforge:runServer)
./gradlew :fabric:genSources        # decompile Minecraft for IDE navigation (also :neoforge:, :common:)
```

There is no test suite yet; `./gradlew test` runs nothing. Per `docs/PLAN.md`, a feature is not
done until it is visually verified in-game on **both** loaders — compiling is not evidence.

`genSources` matters more than usual here: PLAN.md requires stat calibration values to be read
from the game's own `ToolMaterial` constants in 26.1.2, not from memory or 1.21-era tables.

## Verifying in-game

**Visual check.** `scripts/visual-check.sh <fabric|neoforge> [world] [out-dir]` launches the client
straight into a world, screenshots it and shuts it down, leaving a PNG and a filtered log under
`build/visual-check/`. It generates the world on first use and reuses it after. To get the item under
test into the player's hands, point `TEMPER_DATAPACK` at a datapack directory; it is copied into the
save, and worlds load their own datapacks without prompting. A `#minecraft:tick` function that gives
the item with its components needs no typing in-game:

```
execute as @a unless items entity @s hotbar.* temper:<item> run give @s temper:<item>[temper:<component>=[...]]
```

For 26.1.2 a datapack `pack.mcmeta` needs `"min_format": [101, 1], "max_format": 101`; copy the current
numbers from `data/minecraft/datapacks/*/pack.mcmeta` in the game jar when the version changes.

**Checking the result.** `scripts/verify-swords.py` reads the screenshots left in `build/visual-check/`
and checks every sword in them pixel by pixel against the sprite, exiting non-zero if any of the nine
head and handle pairings is missing or mistinted. The comparison can be exact because the GUI draws
icons unlit, so each pixel is its layer's grey times its material colour and nothing else. Do not
verify by counting colours in a slot: the hotbar frame and the world behind it produce greys that pass
for iron. The world in the shot is expendable; delete `<platform>/run/saves/<world>` and the next run
regenerates it.

**Load check without a screenshot.** For NeoForge set `NEOFORGE_CLIENT_SELFTEST=<path of a file that
must not exist yet>` before `:neoforge:runClient`; the client stops itself after the loading overlay and
creates the file. `NEOFORGE_DEDICATED_SERVER_SELFTEST` does the same for `:neoforge:runServer`, after one
tick, which is how the test world gets generated. Fabric has no equivalent: watch the log for
`Temper client init` and `Sound engine started`, then stop the java process whose command line contains
`architectury.main.class` and the project path.

Everything the clients write lives under `<platform>/run/`, which is gitignored.

## Module layout (Architectury)

- `common/` — all gameplay code and all resources (`assets/temper/`, `data/temper/`, `temper.mixins.json`).
  `Temper.init()` runs on both sides. `client.TemperClient.init(registrar)` runs client-only and
  registers `client.LayerTintSource` under `temper:layer` through the `put` each loader passes in,
  because vanilla keeps `ItemTintSources.ID_MAPPER` private: Fabric API widens it, NeoForge exposes it
  via `RegisterColorHandlersEvent.ItemTintSources` on the mod bus. Depends on `fabric-loader` **only**
  for the `@Environment` annotations, which Architectury remaps per platform; do not use other Fabric
  Loader classes here. Mixins go in package `io.github.kevdev_code.temper.mixin`.
- `fabric/` — `TemperFabric` (main) and `client.TemperFabricClient` (client), both declared as
  entrypoints in `fabric.mod.json`.
- `neoforge/` — `TemperNeoForge` (`@Mod`) and `client.TemperNeoForgeClient`
  (`@Mod(value = MOD_ID, dist = Dist.CLIENT)`, constructor takes the mod `IEventBus`). NeoForge discovers
  `@Mod` classes by annotation; `neoforge.mods.toml` does not reference classes.

Client-only code (`ItemTintSource`, screens, renderers) is reached only from the two client
entrypoints, never from `Temper.init()`, or a dedicated server crashes on class load. Shared logic
that must differ per loader goes through Architectury's `@ExpectPlatform` or its API. Do **not** mark mod
classes `@Environment(EnvType.CLIENT)` (Architectury turns it into `@OnlyIn`): NeoForge no longer strips
`@OnlyIn` members, and in dev it logs ERRORs and shows a load-warning screen for any mod class carrying
it. Keep client code client-only by reachability.

Registration notes. Items, data component types, recipe serializers and creative tabs go through
Architectury's `DeferredRegister`, registered from `Temper.init()`. A 26.1 item needs
`Item.Properties().setId(ResourceKey)`. Do not resolve one `RegistrySupplier` inside another's register
lambda (a component type used as an item default, say): registry event order differs per loader.

**Never build an `ItemStack` during `init()`.** It throws `NullPointerException: Components not bound
yet`, because the item registry has not bound its component maps at that point. Anything that needs a
stack waits for a later moment, such as creative tab population or a recipe being matched.

## How a tool is built

`temper/materials.json` in the mod jar is the material table, loaded once on both sides by
`TemperMaterials`, so the client has the colours and the server has the stats with nothing to sync. The
head numbers are vanilla's own `ToolMaterial` constants; the handle multipliers are Temper's and
straddle 1.0. Adding a material is one entry there and nothing else: its combinations, its recipes and
its creative tab entries all follow.

`SwordAssembly` is PLAN.md section 5 in code. It runs once per assembly and writes the result into the
stack's components, never recomputing per tick. The stack carries `temper:parts`, which is the tool's
identity, plus the derived `max_damage`, `attribute_modifiers` and `enchantable`.

`SwordAssemblyRecipe` is a `CustomRecipe` in the ordinary crafting table, in vanilla's own sword shape:
two head cells over one handle cell. It reads the materials from the table rather than from the recipe,
so there is one recipe file no matter how many materials exist. `CraftingInput` arrives cropped to its
filled cells, so the shape check is `width() == 1 && height() == 3`.

The first time the creative tab is built it logs the whole calibration table, one line per combination.
That log is the artefact PLAN.md's definition of done gets checked against: a sword with an iron head
and an iron handle must land exactly on the vanilla iron sword.

Item appearance takes two files per item. `assets/temper/items/<item>.json` is the client item model
definition and carries the tints, one per model layer, in layer order:

```json
{ "model": { "type": "minecraft:model", "model": "temper:item/<item>",
             "tints": [ { "type": "temper:layer", "layer": 0 },
                        { "type": "temper:layer", "layer": 1 },
                        { "type": "minecraft:constant", "value": 9133628 } ] } }
```

Tints multiply, so a material's colour is not the colour you see: it is the colour that makes the
blade body (90% grey) land on the vanilla item's main tone after multiplying. Vanilla's iron blade
body is pure white, so iron is `#FFFFFF`; copying a tone off a source texture comes out dull. A
material that is dark to begin with, like wood, gets dragged under vanilla by the 55% shade floor,
so its colour is raised until the per-zone means match instead of the body.
`scripts/sword-sprite.py --calibrate` renders ours beside the vanilla swords extracted to
`build/texture-drafts/ref/` to check a new material against the real thing.

The grip's constant is one colour for every sword on purpose: it is what ties the set together.
It sits darker and redder than oak because in Temper, unlike vanilla, a wood blade can sit on a
wood handle, and that pairing has to keep reading as two pieces.

`assets/temper/models/item/<item>.json` with parent `minecraft:item/handheld` maps each `layerN`
texture to tint index `N`. The `layer` field of `temper:layer` is the **part slot** (0 handle,
1 head, per `PartSlot`), which happens to equal the model layer today and will not once more layers
exist. Textures are authored grayscale; all colour comes from the tint.

The sword's three textures are not hand-drawn. `scripts/sword-sprite.py` holds the approved sprite as
zones (blade, guard, grip, pommel) on one diagonal axis, computes outlines and seams, and `--export`
splits it by zone into `sword_head.png` (blade, tinted by the head material), `sword_handle.png`
(guard and pommel, tinted by the handle material) and `sword_grip.png` (the grip, tinted by a fixed
leather colour: a grip is never solid diamond). Edit the script and re-export; never edit the PNGs.
Moving the guard to the binding layer in Phase 2 is one line of its `LAYER` map.

## Build quirks worth knowing

- **No remapping.** 26.1 Minecraft is unobfuscated, so the root build uses `loom-no-remap` and there
  is no `remapJar`. The **shadow jar** (no classifier) is the shippable artifact; the plain `jar`
  task produces a `-dev` jar that is not usable in a real game.
- **Common is bundled, not depended on.** Each platform pulls `common` in via the `shadowBundle`
  configuration (`transformProductionFabric` / `transformProductionNeoForge`) and shades it. Common
  never ships as its own mod.
- **Versions are centralized** in the root `gradle.properties` (`mod_version`, `minecraft_version`,
  `fabric_api_version`, `neoforge_version`, `architectury_api_version`). `processResources` expands
  `${version}` into `fabric.mod.json` and `neoforge.mods.toml`; the Architectury and loader ranges in
  those two files are the minimum the code actually needs, not the compile version, so they change on
  purpose, not on every bump.
- `neoforge/gradle.properties` sets `loom.platform = neoforge`; that line is what makes the module
  a NeoForge build.
- Loom's run tasks accept Gradle's `--args="..."`; Loom passes its own launch arguments through
  DevLaunchInjector (`.gradle/loom-cache/projects/<platform>/launch.cfg`), so `--args` adds to them.

## Design constraints that shape code (from docs/PLAN.md)

- Rendering is built first and decides viability: grayscale part textures tinted at runtime through
  a custom `ItemTintSource` reading a material from a data component. One model layer per part.
- Materials and their stats are **data (JSON)**, not code. Adding a material must be a new entry, not
  a new class.
- Tool identity lives in data components (material per slot, cached stats, modifiers, decaying max
  durability). Stats are computed on assembly, never per tick.
- Temper tools must not exceed vanilla's power ceiling; vanilla enchanting stays untouched.
