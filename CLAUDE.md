# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Temper is a Minecraft mod (mod id `temper`) that replaces vanilla tool progression with a four-part
crafting system. Design, scope, phases and open questions live in `docs/PLAN.md` — read it before
adding any gameplay feature. This file covers only how the repo works.

Targets Minecraft **26.1.2**, Java **25**, Gradle 9.5.1, built with Architectury Loom for both
**Fabric** and **NeoForge**. Base package is `io.github.kevdev_code.temper`.

State: PLAN.md Phase 0 (rendering spike) is done and verified on both loaders. It left a throwaway
`temper:tint_test` item, a `temper:tint_colors` component (`List<Integer>`, one RGB per model layer)
and the `temper:layer` tint source. Phase 1 replaces the item, keeps the mechanism.

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

**Load check, no babysitting.** For NeoForge set `NEOFORGE_CLIENT_SELFTEST=<path of a file that must not
exist yet>` before `:neoforge:runClient`; the client stops itself after the loading overlay and creates
the file (`NEOFORGE_DEDICATED_SERVER_SELFTEST` does the same for `:neoforge:runServer`, after one tick).
Fabric has no equivalent: watch the log for `Temper client init` and `Sound engine started`, then stop
the java process whose command line contains `architectury.main.class` and `Temper\fabric`.

**Visual check** (everything lives under `<platform>/run/`, outside the repo):

1. Generate a world once with the NeoForge dedicated server: write `neoforge/run/eula.txt` (`eula=true`)
   and `neoforge/run/server.properties` (`level-type=minecraft:flat`, `difficulty=peaceful`,
   `gamemode=creative`, `online-mode=false`), run `:neoforge:runServer` with the self-test variable set.
   Copy `neoforge/run/world` to `fabric/run/saves/test` and `neoforge/run/saves/test`.
2. Put a datapack inside the save (`saves/test/datapacks/<name>/`) that hands the player what to look at.
   Worlds load their own datapacks automatically. For 26.1.2 `pack.mcmeta` needs
   `"min_format": [101, 1], "max_format": 101` (copy from `data/minecraft/datapacks/*/pack.mcmeta` in the
   game jar when the version changes). A `#minecraft:tick` function such as
   `execute as @a unless items entity @s hotbar.* temper:tint_test run give @s temper:tint_test[temper:tint_colors=[16728128,4227327]]`
   gives the item once, with its components, no typing needed.
3. Launch straight into it: `./gradlew :fabric:runClient --args="--quickPlaySingleplayer test"` (same for
   `:neoforge:`). Wait for `joined the game` in the log, give it ~10 s, then screenshot the window titled
   `Minecraft*` (PowerShell: `GetWindowRect` + `Graphics.CopyFromScreen`, save PNG) and read the PNG.
   Kill the client as above.

## Module layout (Architectury)

- `common/` — all gameplay code and all resources (`assets/temper/`, `data/temper/`, `temper.mixins.json`).
  `Temper.init()` runs on both sides and registers the Architectury `DeferredRegister`s (items, data
  component types). `client.TemperClient.init(registrar)` runs client-only and registers
  `client.LayerTintSource` under `temper:layer` through the `put` each loader passes in, because vanilla
  keeps `ItemTintSources.ID_MAPPER` private: Fabric API widens it, NeoForge exposes it via
  `RegisterColorHandlersEvent.ItemTintSources` on the mod bus. Depends on `fabric-loader` **only** for the
  `@Environment` annotations, which Architectury remaps per platform; do not use other Fabric Loader
  classes here. Mixins go in package `io.github.kevdev_code.temper.mixin`.
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

Registration notes: 26.1 items need `Item.Properties().setId(ResourceKey)`. Do not resolve one
`RegistrySupplier` inside another's register lambda (e.g. a component type as an item default): registry
event order differs per loader. Per-stack data goes on the stack (`/give ...[component=...]`, or set on
assembly), which is also what PLAN.md wants.

Item appearance files: `assets/temper/items/<item>.json` is the client item model definition
(`"type": "minecraft:model"`, `"tints": [{"type": "temper:layer", "layer": N}, ...]`), and
`assets/temper/models/item/<item>.json` with parent `minecraft:item/generated` maps `layerN` textures to
tint index `N`. Textures are grayscale; colour comes only from the tint source.

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
