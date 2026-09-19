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
 * Both orientations match, as they do for every asymmetric shaped recipe in vanilla; the mirroring
 * lives in {@link ShapeMatch}, which has no Minecraft types in it and carries its own runnable check.
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
     * The input arrives cropped to its filled cells. Each cell is resolved to a material id first,
     * then {@link ShapeMatch} fits the grid to the kind's shape or its mirror image, and only then is
     * each material checked against the slot the shape gave it.
     */
    private Optional<ToolParts> resolve(final CraftingInput input) {
        String[][] grid = new String[input.height()][input.width()];
        for (int y = 0; y < input.height(); y++) {
            for (int x = 0; x < input.width(); x++) {
                ItemStack stack = input.getItem(x, y);
                if (stack.isEmpty()) {
                    continue;
                }
                Optional<Identifier> id = TemperMaterials.byIngredient(stack);
                if (id.isEmpty()) {
                    return Optional.empty();                   // something is there that is no material
                }
                grid[y][x] = id.get().toString();
            }
        }
        ShapeMatch.Parts found = ShapeMatch.match(kind.shape(), grid);
        if (found == null) {
            return Optional.empty();
        }
        Optional<Identifier> head = allowed(found.head(), PartSlot.HEAD);
        Optional<Identifier> handle = allowed(found.handle(), PartSlot.HANDLE);
        Optional<Identifier> binding = allowed(found.binding(), PartSlot.BINDING);
        if (head.isEmpty() || handle.isEmpty() || binding.isEmpty()) {
            return Optional.empty();
        }
        Optional<Identifier> reinforcement = Optional.empty();
        if (found.reinforcement() != null) {
            reinforcement = allowed(found.reinforcement(), PartSlot.REINFORCEMENT);
            if (reinforcement.isEmpty()) {
                return Optional.empty();                       // something is there, but it may not reinforce
            }
        }
        return Optional.of(new ToolParts(handle.get(), head.get(), binding.get(), reinforcement));
    }

    /** The material, if it may occupy that slot. */
    private static Optional<Identifier> allowed(final String id, final PartSlot slot) {
        Identifier material = Identifier.parse(id);
        return TemperMaterials.get(material).filter(m -> m.allows(slot)).map(m -> material);
    }

    @Override
    public RecipeSerializer<ToolAssemblyRecipe> getSerializer() {
        return Temper.TOOL_ASSEMBLY.get();
    }
}
