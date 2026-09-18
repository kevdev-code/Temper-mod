package io.github.kevdev_code.temper.material;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import io.github.kevdev_code.temper.tool.PartSlot;

import java.util.List;

/**
 * One row of the material table. Everything here comes from {@code temper/materials.json}; adding a
 * material is a new entry in that file, never a new class.
 *
 * <p>The head numbers are vanilla's own {@code ToolMaterial} constants for 26.1.2, so a tool whose head
 * is material X lands on vanilla's tier for X. The handle multipliers are Temper's own and straddle
 * 1.0, which is what keeps the handle a real choice instead of a strictly better option.
 */
public record TemperMaterial(int color, String ingredient, Head head, Handle handle, List<PartSlot> validParts) {

    /** Absolute values. PLAN.md section 5: the head contributes these, the handle scales them. */
    public record Head(int durability, float attackDamageBonus, int enchantmentValue) {
        public static final Codec<Head> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.INT.fieldOf("durability").forGetter(Head::durability),
                Codec.FLOAT.fieldOf("attack_damage_bonus").forGetter(Head::attackDamageBonus),
                Codec.INT.fieldOf("enchantment_value").forGetter(Head::enchantmentValue)
        ).apply(i, Head::new));
    }

    /** Multipliers, never absolutes, so four mediocre materials cannot sum into a good tool. */
    public record Handle(float durabilityMultiplier, float speedMultiplier) {
        public static final Codec<Handle> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.FLOAT.fieldOf("durability_multiplier").forGetter(Handle::durabilityMultiplier),
                Codec.FLOAT.fieldOf("speed_multiplier").forGetter(Handle::speedMultiplier)
        ).apply(i, Handle::new));
    }

    private static final Codec<Integer> RGB_CODEC = Codec.STRING.xmap(
            text -> Integer.parseInt(text.startsWith("#") ? text.substring(1) : text, 16),
            value -> "#%06X".formatted(value));

    public static final Codec<TemperMaterial> CODEC = RecordCodecBuilder.create(i -> i.group(
            RGB_CODEC.fieldOf("color").forGetter(TemperMaterial::color),
            Codec.STRING.fieldOf("ingredient").forGetter(TemperMaterial::ingredient),
            Head.CODEC.fieldOf("head").forGetter(TemperMaterial::head),
            Handle.CODEC.fieldOf("handle").forGetter(TemperMaterial::handle),
            PartSlot.CODEC.listOf().fieldOf("valid_parts").forGetter(TemperMaterial::validParts)
    ).apply(i, TemperMaterial::new));

    /** True when this material may occupy that slot. Stone making a poor handle is a design statement. */
    public boolean allows(final PartSlot slot) {
        return validParts.contains(slot);
    }

    /** Matches the raw item the player puts in the grid, written as an item id or a {@code #tag}. */
    public boolean matchesIngredient(final ItemStack stack) {
        if (ingredient.startsWith("#")) {
            TagKey<Item> tag = TagKey.create(Registries.ITEM, Identifier.parse(ingredient.substring(1)));
            return stack.is((Holder<Item> holder) -> holder.is(tag));
        }
        Identifier id = Identifier.parse(ingredient);
        return stack.is((Holder<Item> holder) -> holder.is(id));
    }
}
