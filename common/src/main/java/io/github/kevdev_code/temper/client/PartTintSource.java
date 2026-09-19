package io.github.kevdev_code.temper.client;

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
import io.github.kevdev_code.temper.tool.PartSlot;
import io.github.kevdev_code.temper.tool.ToolParts;

/**
 * Colours one model layer with the material filling a part slot. This is the whole reason the
 * textures are grayscale: one texture per part, every material for free.
 *
 * <p>It names the slot, never a layer number, because the two stopped agreeing in Phase 2 and a
 * mix-up would paint a part with a neighbour's colour without any error. See {@link PartSlot}.
 */
public record PartTintSource(PartSlot slot) implements ItemTintSource {
    public static final Identifier ID = Identifier.fromNamespaceAndPath(Temper.MOD_ID, "part");
    public static final MapCodec<PartTintSource> MAP_CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            PartSlot.CODEC.fieldOf("slot").forGetter(PartTintSource::slot)
    ).apply(instance, PartTintSource::new));

    /** Alpha zero: the layer draws nothing. This is how an empty reinforcement slot disappears. */
    private static final int ABSENT = 0x00000000;

    /** Opaque white leaves the grayscale untouched, so a malformed stack looks wrong rather than invisible. */
    private static final int NO_COMPONENT = 0xFFFFFFFF;

    @Override
    public int calculate(final ItemStack stack, final ClientLevel level, final LivingEntity entity) {
        ToolParts parts = stack.get(Temper.TOOL_PARTS.get());
        if (parts == null) {
            return NO_COMPONENT;
        }
        return parts.get(slot)
                .flatMap(TemperMaterials::get)
                .map(TemperMaterial::color)
                .map(ARGB::opaque)
                .orElse(ABSENT);
    }

    @Override
    public MapCodec<? extends ItemTintSource> type() {
        return MAP_CODEC;
    }
}
