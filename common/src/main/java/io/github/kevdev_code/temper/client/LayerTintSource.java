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

import java.util.List;

/** Tints model layer {@code layer} with the matching entry of the stack's {@code temper:tint_colors} component. */
public record LayerTintSource(int layer) implements ItemTintSource {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Temper.MOD_ID, "layer");
    public static final MapCodec<LayerTintSource> MAP_CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.INT.fieldOf("layer").forGetter(LayerTintSource::layer)
    ).apply(instance, LayerTintSource::new));

    @Override
    public int calculate(ItemStack stack, ClientLevel level, LivingEntity entity) {
        List<Integer> colors = stack.get(Temper.TINT_COLORS.get());
        // ponytail: missing component or layer = untinted white, so a broken wiring is visible on sight
        return colors != null && layer < colors.size() ? ARGB.opaque(colors.get(layer)) : ARGB.opaque(0xFFFFFF);
    }

    @Override
    public MapCodec<? extends ItemTintSource> type() {
        return MAP_CODEC;
    }
}
