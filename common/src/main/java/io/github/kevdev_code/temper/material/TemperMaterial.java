package io.github.kevdev_code.temper.material;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;

import io.github.kevdev_code.temper.tool.PartSlot;
import io.github.kevdev_code.temper.tool.ToolKind;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * One row of the material table. Everything here comes from {@code temper/materials.json}; adding a
 * material is a new entry in that file, never a new class.
 *
 * <p>The head numbers are vanilla's own {@code ToolMaterial} constants for 26.1.2, so a tool whose
 * head is material X lands on vanilla's tier for X. The handle multipliers and the binding numbers
 * are Temper's own. Each block is named for the slot it applies through: a material's personality
 * reaches the tool only via the part it occupies, which is what makes the combination space
 * interesting rather than merely large.
 */
public record TemperMaterial(int color, String ingredient, Head head, Handle handle, Binding binding,
                             List<PartSlot> validParts) {

    /**
     * Absolute values. PLAN.md section 5: the head contributes these, the handle scales them. The
     * mining speed and the drops tag are what vanilla's {@code ToolMaterial} carries as {@code speed}
     * and {@code incorrectBlocksForDrops}; a tool that does not mine ignores them.
     */
    public record Head(int durability, float attackDamageBonus, float miningSpeed, String incorrectForDrops,
                       Map<ToolKind, Attack> attack) {
        public static final Codec<Head> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.INT.fieldOf("durability").forGetter(Head::durability),
                Codec.FLOAT.fieldOf("attack_damage_bonus").forGetter(Head::attackDamageBonus),
                Codec.FLOAT.fieldOf("mining_speed").forGetter(Head::miningSpeed),
                Codec.STRING.fieldOf("incorrect_for_drops").forGetter(Head::incorrectForDrops),
                Codec.unboundedMap(ToolKind.CODEC, Attack.CODEC).fieldOf("attack").forGetter(Head::attack)
        ).apply(i, Head::new));

        /** Empty when vanilla makes no such tool of this material, which then cannot head one either. */
        public Optional<Attack> attack(final ToolKind kind) {
            return Optional.ofNullable(attack.get(kind));
        }

        /** The blocks this head mines without dropping anything, vanilla's mining level in tag form. */
        public TagKey<Block> incorrectForDropsTag() {
            return TagKey.create(Registries.BLOCK, Identifier.parse(incorrectForDrops));
        }
    }

    /**
     * What vanilla's {@code Items} gives a tool of this material and kind, as
     * {@code [attackDamageBaseline, attackSpeedBaseline]}: the head's bonus is added to the first, the
     * second is a modifier against the player's 4.0. Constant across materials for the sword, pickaxe
     * and shovel; hand tuned per material for the axe and the hoe, which is why they are data here and
     * not constants on the kind.
     */
    public record Attack(float damageBaseline, float speedBaseline) {
        public static final Codec<Attack> CODEC = Codec.FLOAT.listOf(2, 2).xmap(
                pair -> new Attack(pair.get(0), pair.get(1)),
                a -> List.of(a.damageBaseline(), a.speedBaseline()));
    }

    /** Multipliers, never absolutes, so four mediocre materials cannot sum into a good tool. */
    public record Handle(float durabilityMultiplier, float speedMultiplier) {
        public static final Codec<Handle> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.FLOAT.fieldOf("durability_multiplier").forGetter(Handle::durabilityMultiplier),
                Codec.FLOAT.fieldOf("speed_multiplier").forGetter(Handle::speedMultiplier)
        ).apply(i, Handle::new));
    }

    /**
     * How much the tool can be customised. Enchantability lives here rather than on the head, which
     * is what PLAN.md section 4 asks for, and the slot count is the trade that stops the binding
     * being the ignorable part Tinkers' made it: more slots usually means less enchantability.
     */
    public record Binding(int enchantmentValue, int modifierSlots) {
        public static final Codec<Binding> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.INT.fieldOf("enchantment_value").forGetter(Binding::enchantmentValue),
                Codec.INT.fieldOf("modifier_slots").forGetter(Binding::modifierSlots)
        ).apply(i, Binding::new));
    }

    private static final Codec<Integer> RGB_CODEC = Codec.STRING.xmap(
            text -> Integer.parseInt(text.startsWith("#") ? text.substring(1) : text, 16),
            value -> "#%06X".formatted(value));

    public static final Codec<TemperMaterial> CODEC = RecordCodecBuilder.create(i -> i.group(
            RGB_CODEC.fieldOf("color").forGetter(TemperMaterial::color),
            Codec.STRING.fieldOf("ingredient").forGetter(TemperMaterial::ingredient),
            Head.CODEC.fieldOf("head").forGetter(TemperMaterial::head),
            Handle.CODEC.fieldOf("handle").forGetter(TemperMaterial::handle),
            Binding.CODEC.fieldOf("binding").forGetter(TemperMaterial::binding),
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
