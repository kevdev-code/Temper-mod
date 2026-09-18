package io.github.kevdev_code.temper.tool;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.Identifier;

import org.jetbrains.annotations.Nullable;

/**
 * What a tool is made of: one material per part slot. This is the tool's identity, and everything else
 * about it is derived from these two ids at assembly time.
 */
public record ToolParts(Identifier handle, Identifier head) {

    public static final Codec<ToolParts> CODEC = RecordCodecBuilder.create(i -> i.group(
            Identifier.CODEC.fieldOf("handle").forGetter(ToolParts::handle),
            Identifier.CODEC.fieldOf("head").forGetter(ToolParts::head)
    ).apply(i, ToolParts::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, ToolParts> STREAM_CODEC = StreamCodec.composite(
            Identifier.STREAM_CODEC, ToolParts::handle,
            Identifier.STREAM_CODEC, ToolParts::head,
            ToolParts::new);

    public Identifier get(final PartSlot slot) {
        return switch (slot) {
            case HANDLE -> handle;
            case HEAD -> head;
        };
    }

    /** The material drawn by a model layer, or null when the layer is beyond this tool's parts. */
    @Nullable
    public Identifier atLayer(final int layer) {
        PartSlot[] slots = PartSlot.values();
        return layer >= 0 && layer < slots.length ? get(slots[layer]) : null;
    }
}
