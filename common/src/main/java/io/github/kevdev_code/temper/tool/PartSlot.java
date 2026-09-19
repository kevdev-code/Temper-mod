package io.github.kevdev_code.temper.tool;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/**
 * The part slots a tool is assembled from, in the order PLAN.md section 4 lists them.
 *
 * <p><b>An ordinal here is not a model layer index.</b> The model draws five layers and only four of
 * them are parts: the grip sits between head and binding and belongs to no slot at all. Phase 1 could
 * get away with treating the two as one number because handle and head happened to be 0 and 1 in both;
 * from binding on they diverge, and the failure is silent, painting a part with another part's colour.
 * Nothing in this package indexes by layer for that reason: the tint source carries a {@code PartSlot},
 * and which layer it paints is decided once, in {@code scripts/sword-sprite.py}, which generates both
 * the model and its tint list from a single table.
 */
public enum PartSlot implements StringRepresentable {
    HANDLE("handle"),
    HEAD("head"),
    BINDING("binding"),
    REINFORCEMENT("reinforcement");

    public static final Codec<PartSlot> CODEC = StringRepresentable.fromEnum(PartSlot::values);

    private final String serializedName;

    PartSlot(final String serializedName) {
        this.serializedName = serializedName;
    }

    /** Only the reinforcement may be absent from a finished tool. */
    public boolean isOptional() {
        return this == REINFORCEMENT;
    }

    @Override
    public String getSerializedName() {
        return serializedName;
    }
}
