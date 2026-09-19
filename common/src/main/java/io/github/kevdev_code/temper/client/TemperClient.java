package io.github.kevdev_code.temper.client;

import com.mojang.serialization.MapCodec;
import net.minecraft.client.color.item.ItemTintSource;
import net.minecraft.resources.Identifier;

import io.github.kevdev_code.temper.Temper;

import java.util.function.BiConsumer;

// Client-only by reachability: called from the two client entrypoints, never from Temper.init().
public final class TemperClient {
    /**
     * Vanilla keeps {@code ItemTintSources.ID_MAPPER} private. Fabric widens it, NeoForge wraps it in an
     * event, so each loader hands in its own "put" and this decides what gets registered.
     */
    public static void init(BiConsumer<Identifier, MapCodec<? extends ItemTintSource>> registerTintSource) {
        registerTintSource.accept(PartTintSource.ID, PartTintSource.MAP_CODEC);
        Temper.LOGGER.info("Temper client init");
    }
}
