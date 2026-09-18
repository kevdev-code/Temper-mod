package io.github.kevdev_code.temper.client;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.client.color.item.ItemTintSource;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

import io.github.kevdev_code.temper.Temper;

/**
 * Tints one model layer of a Temper tool, registered under {@code temper:layer}. An item model
 * definition names this source once per layer, and {@code layer} says which part slot that layer draws.
 *
 * <p>The colour lookup is deliberately absent. Phase 0 proved the mechanism against a throwaway
 * component; Phase 1 replaces it with the real per-slot material, which is the only thing this class
 * still needs.
 */
public record LayerTintSource(int layer) implements ItemTintSource {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Temper.MOD_ID, "layer");
    public static final MapCodec<LayerTintSource> MAP_CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.INT.fieldOf("layer").forGetter(LayerTintSource::layer)
    ).apply(instance, LayerTintSource::new));

    @Override
    public int calculate(ItemStack stack, ClientLevel level, LivingEntity entity) {
        // ponytail: untinted until Phase 1 reads the part material off the stack. White is the honest
        // placeholder — a tool that renders grey cannot be mistaken for a working lookup.
        return ARGB.opaque(0xFFFFFF);
    }

    @Override
    public MapCodec<? extends ItemTintSource> type() {
        return MAP_CODEC;
    }
}
