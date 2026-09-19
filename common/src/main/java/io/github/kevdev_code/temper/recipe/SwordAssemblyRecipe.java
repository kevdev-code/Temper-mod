package io.github.kevdev_code.temper.recipe;

import com.mojang.serialization.MapCodec;
import net.minecraft.network.RegistryFriendlyByteBuf;
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
import io.github.kevdev_code.temper.tool.SwordAssembly;
import io.github.kevdev_code.temper.tool.ToolParts;

import java.util.Optional;

/**
 * Assembles a sword in the ordinary crafting table. The shape keeps vanilla's blade over grip and
 * hangs the fittings off its left:
 *
 * <pre>
 *     . H      H  head material, twice, as vanilla's sword does
 *     B H      B  binding
 *     R G      R  reinforcement, optional; G  handle
 * </pre>
 *
 * The materials come from the table rather than from the recipe, so a new material in
 * {@code materials.json} adds all of its combinations without a new recipe file.
 */
public class SwordAssemblyRecipe extends CustomRecipe {
    public static final MapCodec<SwordAssemblyRecipe> MAP_CODEC = MapCodec.unit(SwordAssemblyRecipe::new);
    public static final StreamCodec<RegistryFriendlyByteBuf, SwordAssemblyRecipe> STREAM_CODEC =
            StreamCodec.unit(new SwordAssemblyRecipe());

    @Override
    public boolean matches(final CraftingInput input, final Level level) {
        return resolve(input).isPresent();
    }

    @Override
    public ItemStack assemble(final CraftingInput input) {
        return resolve(input).flatMap(SwordAssembly::assemble).orElse(ItemStack.EMPTY);
    }

    /**
     * The input arrives cropped to its filled cells. Both the four and five ingredient forms crop to
     * the same two by three box, because the binding holds the left column open either way.
     */
    private Optional<ToolParts> resolve(final CraftingInput input) {
        if (input.width() != 2 || input.height() != 3) {
            return Optional.empty();
        }
        if (!input.getItem(0, 0).isEmpty()) {
            return Optional.empty();
        }
        Optional<Identifier> upper = material(input, 1, 0, PartSlot.HEAD);
        Optional<Identifier> lower = material(input, 1, 1, PartSlot.HEAD);
        Optional<Identifier> binding = material(input, 0, 1, PartSlot.BINDING);
        Optional<Identifier> handle = material(input, 1, 2, PartSlot.HANDLE);
        if (upper.isEmpty() || lower.isEmpty() || binding.isEmpty() || handle.isEmpty()
                || !upper.get().equals(lower.get())) {
            return Optional.empty();
        }
        ItemStack reinforcementSlot = input.getItem(0, 2);
        Optional<Identifier> reinforcement = Optional.empty();
        if (!reinforcementSlot.isEmpty()) {
            reinforcement = material(input, 0, 2, PartSlot.REINFORCEMENT);
            if (reinforcement.isEmpty()) {
                return Optional.empty();       // something is there, but it is not a valid reinforcement
            }
        }
        return Optional.of(new ToolParts(handle.get(), upper.get(), binding.get(), reinforcement));
    }

    private Optional<Identifier> material(final CraftingInput input, final int x, final int y, final PartSlot slot) {
        return TemperMaterials.byIngredient(input.getItem(x, y))
                .filter(id -> TemperMaterials.get(id).map(m -> m.allows(slot)).orElse(false));
    }

    @Override
    public RecipeSerializer<SwordAssemblyRecipe> getSerializer() {
        return Temper.SWORD_ASSEMBLY.get();
    }
}
