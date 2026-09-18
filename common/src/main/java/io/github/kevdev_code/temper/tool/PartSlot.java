package io.github.kevdev_code.temper.tool;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/**
 * The part slots a tool is assembled from. The ordinal is the model layer that part draws, which is
 * the layer order PLAN.md section 10 fixes: handle underneath, head on top.
 *
 * <p>Phase 1 has two. Binding and reinforcement join them in Phase 2, appended in layer order.
 */
public enum PartSlot implements StringRepresentable {
    HANDLE("handle"),
    HEAD("head");

    public static final Codec<PartSlot> CODEC = StringRepresentable.fromEnum(PartSlot::values);

    private final String serializedName;

    PartSlot(final String serializedName) {
        this.serializedName = serializedName;
    }

    public int layer() {
        return ordinal();
    }

    @Override
    public String getSerializedName() {
        return serializedName;
    }
}
