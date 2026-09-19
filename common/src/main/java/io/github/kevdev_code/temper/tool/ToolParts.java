package io.github.kevdev_code.temper.tool;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.Identifier;

import java.util.Optional;

/**
 * What a tool is made of: one material per part slot. This is the tool's identity, and everything
 * else about it is derived from these ids at assembly time.
 *
 * <p>There is deliberately no way to ask for a material by layer index. See {@link PartSlot}.
 */
public record ToolParts(Identifier handle, Identifier head, Identifier binding,
                        Optional<Identifier> reinforcement) {

    public static final Codec<ToolParts> CODEC = RecordCodecBuilder.create(i -> i.group(
            Identifier.CODEC.fieldOf("handle").forGetter(ToolParts::handle),
            Identifier.CODEC.fieldOf("head").forGetter(ToolParts::head),
            Identifier.CODEC.fieldOf("binding").forGetter(ToolParts::binding),
            Identifier.CODEC.optionalFieldOf("reinforcement").forGetter(ToolParts::reinforcement)
    ).apply(i, ToolParts::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, ToolParts> STREAM_CODEC = StreamCodec.composite(
            Identifier.STREAM_CODEC, ToolParts::handle,
            Identifier.STREAM_CODEC, ToolParts::head,
            Identifier.STREAM_CODEC, ToolParts::binding,
            ByteBufCodecs.optional(Identifier.STREAM_CODEC), ToolParts::reinforcement,
            ToolParts::new);

    /** Empty only for the reinforcement, and only when the tool was assembled without one. */
    public Optional<Identifier> get(final PartSlot slot) {
        return switch (slot) {
            case HANDLE -> Optional.of(handle);
            case HEAD -> Optional.of(head);
            case BINDING -> Optional.of(binding);
            case REINFORCEMENT -> reinforcement;
        };
    }
}
