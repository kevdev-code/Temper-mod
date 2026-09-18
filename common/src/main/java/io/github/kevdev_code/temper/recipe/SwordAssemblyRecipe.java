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

import io.github.kevdev_code.temper.material.TemperMaterials;
import io.github.kevdev_code.temper.tool.PartSlot;
import io.github.kevdev_code.temper.tool.SwordAssembly;

import java.util.Optional;

/**
 * Assembles a sword in the ordinary crafting table, in vanilla's own sword shape: two head cells above
 * one handle cell. The materials come from the table rather than the recipe, so a new material in
 * {@code materials.json} adds its combinations with no new recipe file.
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
        return resolve(input)
                .flatMap(parts -> SwordAssembly.assemble(parts.handle(), parts.head()))
                .orElse(ItemStack.EMPTY);
    }

    /**
     * The input arrives cropped to its filled cells, so a valid sword is exactly one column of three:
     * the same head material twice over a handle material.
     */
    private Optional<Parts> resolve(final CraftingInput input) {
        if (input.width() != 1 || input.height() != 3 || input.ingredientCount() != 3) {
            return Optional.empty();
        }
        Optional<Identifier> upper = material(input, 0, PartSlot.HEAD);
        Optional<Identifier> lower = material(input, 1, PartSlot.HEAD);
        Optional<Identifier> handle = material(input, 2, PartSlot.HANDLE);
        if (upper.isEmpty() || lower.isEmpty() || handle.isEmpty() || !upper.get().equals(lower.get())) {
            return Optional.empty();
        }
        return Optional.of(new Parts(handle.get(), upper.get()));
    }

    private Optional<Identifier> material(final CraftingInput input, final int index, final PartSlot slot) {
        return TemperMaterials.byIngredient(input.getItem(index))
                .filter(id -> TemperMaterials.get(id).map(m -> m.allows(slot)).orElse(false));
    }

    @Override
    public RecipeSerializer<SwordAssemblyRecipe> getSerializer() {
        return io.github.kevdev_code.temper.Temper.SWORD_ASSEMBLY.get();
    }

    private record Parts(Identifier handle, Identifier head) {
    }
}
