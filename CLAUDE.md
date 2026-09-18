# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Temper is a Minecraft mod (mod id `temper`) that replaces vanilla tool progression with a four-part
crafting system. Design, scope, phases and open questions live in `docs/PLAN.md` — read it before
adding any gameplay feature. This file covers only how the repo works.

Targets Minecraft **26.1.2**, Java **25**, Gradle 9.5.1, built with Architectury Loom for both
**Fabric** and **NeoForge**. Base package is `io.github.kevdev_code.temper`. The mod metadata in
`fabric.mod.json` / `neoforge.mods.toml` still carries template placeholders (authors, description,
license, contact).

## Version context

Minecraft 26.1 uses calver (`year.release.patch`) on quarterly drops. Anything written
for `1.20.x` or `1.21.x` describes a different API, not an older patch of this one.

Since 26.1 the game ships unobfuscated — real class, field, method and parameter names,
no mappings, no remap step.

Architectury version lines are per Minecraft drop: **20.1.x for 26.1.2**. The 21.x line
is for 26.2 and 22.x for 26.3. Do not bump to a higher number just because it exists.

## Working rules

**Don't invent API signatures.** The 26.1 API is recent and differs substantially from the
1.21 material that dominates search results. If unsure whether a class, method or signature
exists, say so and ask for the decompiled source or the versioned docs
(`docs.fabricmc.net/26.1.2`) instead of guessing.

**Verify by compiling, on both platforms.** `common` compiles fine in cases where a platform
module won't.

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
Sources jars for NeoForge and FML also sit in the Gradle cache (`~/.gradle/caches/modules-2/`)
and can be read with `unzip -p` when a loader API signature is in doubt.

To confirm a client loads without babysitting it: for NeoForge, set `NEOFORGE_CLIENT_SELFTEST=<path to a
file that must not exist yet>` before `:neoforge:runClient`; the client stops itself after the loading
overlay and creates that file. Fabric has no equivalent: watch the log for `Temper client init` and
`Sound engine started`, then stop the java process whose command line contains `architectury.main.class`
and `Temper\fabric`.

## Module layout (Architectury)

- `common/` — all gameplay code and all resources (`assets/temper/`, `data/temper/`, `temper.mixins.json`).
  Entry points are `Temper.init()` (both sides) and `client.TemperClient.init()` (client only).
  Depends on `fabric-loader` **only** for the `@Environment` annotations, which Architectury remaps per
  platform; do not use other Fabric Loader classes here.
  Mixins go in package `io.github.kevdev_code.temper.mixin`.
- `fabric/` — `TemperFabric` (main) and `client.TemperFabricClient` (client), both declared as
  entrypoints in `fabric.mod.json`.
- `neoforge/` — `TemperNeoForge` (`@Mod`) and `client.TemperNeoForgeClient`
  (`@Mod(value = MOD_ID, dist = Dist.CLIENT)`). NeoForge discovers `@Mod` classes by annotation;
  `neoforge.mods.toml` does not reference classes.

Client-only code (`ItemTintSource`, screens, renderers) is reached only from the two client
entrypoints, never from `Temper.init()`, or a dedicated server crashes on class load. Shared logic
that must differ per loader goes through Architectury's `@ExpectPlatform` or its API. Do **not** mark mod
classes `@Environment(EnvType.CLIENT)` (Architectury turns it into `@OnlyIn`): NeoForge no longer strips `@OnlyIn`
members, and in dev it logs ERRORs and shows a load-warning screen for any mod class carrying it. Keep client code client-only by reachability.

## Build quirks worth knowing

- **No remapping.** 26.1 Minecraft is unobfuscated, so the root build uses `loom-no-remap` and there
  is no `remapJar`. The **shadow jar** (no classifier) is the shippable artifact; the plain `jar`
  task produces a `-dev` jar that is not usable in a real game.
- **Common is bundled, not depended on.** Each platform pulls `common` in via the `shadowBundle`
  configuration (`transformProductionFabric` / `transformProductionNeoForge`) and shades it. Common
  never ships as its own mod.
- **Versions are centralized** in the root `gradle.properties` (`mod_version`, `minecraft_version`,
  `fabric_api_version`, `neoforge_version`, `architectury_api_version`). `processResources` expands
  `${version}` into `fabric.mod.json` and `neoforge.mods.toml`; keep dependency version ranges in
  those two files in sync with `gradle.properties` by hand.
- `neoforge/gradle.properties` sets `loom.platform = neoforge`; that line is what makes the module
  a NeoForge build.
- `warning: unknown enum constant EnvType.CLIENT` when compiling `neoforge/` is expected and harmless: that
  module compiles against the untransformed `common` classes, where the Fabric annotation is absent.

## Design constraints that shape code (from docs/PLAN.md)

- Rendering is built first and decides viability: grayscale part textures tinted at runtime through
  a custom `ItemTintSource` reading a material from a data component. One model layer per part.
- Materials and their stats are **data (JSON)**, not code. Adding a material must be a new entry, not
  a new class.
- Tool identity lives in data components (material per slot, cached stats, modifiers, decaying max
  durability). Stats are computed on assembly, never per tick.
- Temper tools must not exceed vanilla's power ceiling; vanilla enchanting stays untouched.
