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
import io.github.kevdev_code.temper.material.TemperMaterial;
import io.github.kevdev_code.temper.material.TemperMaterials;
import io.github.kevdev_code.temper.tool.ToolParts;

/**
 * Tints one model layer with the colour of whatever material fills that part slot. This is the whole
 * reason the mod's textures are grayscale: one texture per part, every material for free.
 */
public record LayerTintSource(int layer) implements ItemTintSource {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Temper.MOD_ID, "layer");
    public static final MapCodec<LayerTintSource> MAP_CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.INT.fieldOf("layer").forGetter(LayerTintSource::layer)
    ).apply(instance, LayerTintSource::new));

    private static final int UNTINTED = 0xFFFFFF;

    @Override
    public int calculate(final ItemStack stack, final ClientLevel level, final LivingEntity entity) {
        ToolParts parts = stack.get(Temper.TOOL_PARTS.get());
        if (parts == null) {
            return ARGB.opaque(UNTINTED);
        }
        Identifier material = parts.atLayer(layer);
        if (material == null) {
            return ARGB.opaque(UNTINTED);
        }
        return ARGB.opaque(TemperMaterials.get(material).map(TemperMaterial::color).orElse(UNTINTED));
    }

    @Override
    public MapCodec<? extends ItemTintSource> type() {
        return MAP_CODEC;
    }
}
