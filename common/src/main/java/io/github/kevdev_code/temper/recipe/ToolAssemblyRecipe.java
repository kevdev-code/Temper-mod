package io.github.kevdev_code.temper.recipe;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CustomRecipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

import io.github.kevdev_code.temper.Temper;
import io.github.kevdev_code.temper.material.TemperMaterials;
import io.github.kevdev_code.temper.tool.PartSlot;
import io.github.kevdev_code.temper.tool.ToolAssembly;
import io.github.kevdev_code.temper.tool.ToolKind;
import io.github.kevdev_code.temper.tool.ToolParts;

import java.util.Optional;

/**
 * Assembles a tool in the ordinary crafting table, in the shape its {@link ToolKind} declares: vanilla's
 * own layout for the head and handle, with the binding and the reinforcement hung off the left.
 *
 * <pre>
 *     sword        pickaxe
 *     . H          H H H      H  head, every cell the same material
 *     B H          B G .      B  binding        G  handle
 *     R G          R G .      R  reinforcement, optional; a dot must be empty
 * </pre>
 *
 * The materials come from the table rather than from the recipe, so a new material in
 * {@code materials.json} adds all of its combinations without a new recipe file, and a new tool is one
 * more shape on the enum plus a one-line recipe file naming it.
 */
public class ToolAssemblyRecipe extends CustomRecipe {
    public static final MapCodec<ToolAssemblyRecipe> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            ToolKind.CODEC.fieldOf("tool").forGetter(r -> r.kind)
    ).apply(i, ToolAssemblyRecipe::new));
    public static final StreamCodec<RegistryFriendlyByteBuf, ToolAssemblyRecipe> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.STRING_UTF8, r -> r.kind.getSerializedName(),
            name -> new ToolAssemblyRecipe(ToolKind.byName(name)));

    private final ToolKind kind;

    public ToolAssemblyRecipe(final ToolKind kind) {
        this.kind = kind;
    }

    @Override
    public boolean matches(final CraftingInput input, final Level level) {
        return resolve(input).isPresent();
    }

    @Override
    public ItemStack assemble(final CraftingInput input) {
        return resolve(input).flatMap(parts -> ToolAssembly.assemble(kind, parts)).orElse(ItemStack.EMPTY);
    }

    /**
     * The input arrives cropped to its filled cells. Both the four and five ingredient forms crop to
     * the same box, because the binding holds the left column open either way.
     */
    private Optional<ToolParts> resolve(final CraftingInput input) {
        var shape = kind.shape();
        if (input.height() != shape.size() || input.width() != shape.getFirst().length()) {
            return Optional.empty();
        }
        Optional<Identifier> head = Optional.empty(), handle = Optional.empty(),
                binding = Optional.empty(), reinforcement = Optional.empty();
        for (int y = 0; y < shape.size(); y++) {
            for (int x = 0; x < shape.get(y).length(); x++) {
                char cell = shape.get(y).charAt(x);
                ItemStack stack = input.getItem(x, y);
                if (cell == '.') {
                    if (!stack.isEmpty()) {
                        return Optional.empty();
                    }
                    continue;
                }
                if (cell == 'R' && stack.isEmpty()) {
                    continue;                                   // the one slot that may stay empty
                }
                PartSlot slot = switch (cell) {
                    case 'H' -> PartSlot.HEAD;
                    case 'G' -> PartSlot.HANDLE;
                    case 'B' -> PartSlot.BINDING;
                    case 'R' -> PartSlot.REINFORCEMENT;
                    default -> throw new IllegalStateException("bad shape cell " + cell);
                };
                Optional<Identifier> found = material(stack, slot);
                if (found.isEmpty()) {
                    return Optional.empty();
                }
                switch (slot) {
                    case HEAD -> {
                        if (head.isPresent() && !head.get().equals(found.get())) {
                            return Optional.empty();
                        }
                        head = found;
                    }
                    case HANDLE -> {
                        if (handle.isPresent() && !handle.get().equals(found.get())) {
                            return Optional.empty();
                        }
                        handle = found;
                    }
                    case BINDING -> binding = found;
                    case REINFORCEMENT -> reinforcement = found;
                }
            }
        }
        if (head.isEmpty() || handle.isEmpty() || binding.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new ToolParts(handle.get(), head.get(), binding.get(), reinforcement));
    }

    private static Optional<Identifier> material(final ItemStack stack, final PartSlot slot) {
        return TemperMaterials.byIngredient(stack)
                .filter(id -> TemperMaterials.get(id).map(m -> m.allows(slot)).orElse(false));
    }

    @Override
    public RecipeSerializer<ToolAssemblyRecipe> getSerializer() {
        return Temper.TOOL_ASSEMBLY.get();
    }
}
