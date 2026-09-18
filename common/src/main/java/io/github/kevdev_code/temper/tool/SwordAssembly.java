package io.github.kevdev_code.temper.tool;

import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.enchantment.Enchantable;

import io.github.kevdev_code.temper.Temper;
import io.github.kevdev_code.temper.material.TemperMaterial;
import io.github.kevdev_code.temper.material.TemperMaterials;

import java.util.Optional;

/**
 * Turns two materials into a finished sword. This is PLAN.md section 5 in code, and it runs once per
 * assembly, never per tick: every number it derives is baked into the stack's components.
 */
public final class SwordAssembly {

    /**
     * What the sword tool type contributes, read off vanilla 26.1.2: every {@code *_sword} in
     * {@code Items} calls {@code Properties.sword(material, 3.0f, -2.4f)}, and the material's
     * {@code attackDamageBonus} is added to the first of those.
     */
    public static final float BASE_ATTACK_DAMAGE = 3.0F;
    public static final float BASE_ATTACK_SPEED_MODIFIER = -2.4F;

    /** A player swings at 4.0 per second and punches for 1.0 before any item modifier applies. */
    private static final double PLAYER_BASE_ATTACK_SPEED = 4.0;
    private static final double PLAYER_BASE_ATTACK_DAMAGE = 1.0;

    private SwordAssembly() {
    }

    /** Empty when either id is unknown or the material is not allowed in that slot. */
    public static Optional<ItemStack> assemble(final Identifier handleId, final Identifier headId) {
        Optional<TemperMaterial> handle = TemperMaterials.get(handleId).filter(m -> m.allows(PartSlot.HANDLE));
        Optional<TemperMaterial> head = TemperMaterials.get(headId).filter(m -> m.allows(PartSlot.HEAD));
        if (handle.isEmpty() || head.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(build(handleId, handle.get(), headId, head.get()));
    }

    private static ItemStack build(final Identifier handleId, final TemperMaterial handle,
                                   final Identifier headId, final TemperMaterial head) {
        ItemStack stack = new ItemStack(Temper.SWORD.get());
        stack.set(Temper.TOOL_PARTS.get(), new ToolParts(handleId, headId));

        // durability = head.baseDurability * handle.durabilityMultiplier
        int durability = Math.max(1, Math.round(head.head().durability() * handle.handle().durabilityMultiplier()));
        stack.set(DataComponents.MAX_DAMAGE, durability);

        // attackDamage = head.attackDamage. The handle owns nimbleness, never raw damage.
        double attackDamage = BASE_ATTACK_DAMAGE + head.head().attackDamageBonus();

        // attackSpeed = head.baseSpeed * handle.speedMultiplier, worked in swings per second so that a
        // multiplier above 1.0 means faster. Vanilla stores it as a modifier against the player's 4.0,
        // so it converts back on the way out.
        double swingsPerSecond = (PLAYER_BASE_ATTACK_SPEED + BASE_ATTACK_SPEED_MODIFIER) * handle.handle().speedMultiplier();
        double attackSpeedModifier = swingsPerSecond - PLAYER_BASE_ATTACK_SPEED;

        stack.set(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.builder()
                .add(Attributes.ATTACK_DAMAGE,
                        new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID, attackDamage, AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .add(Attributes.ATTACK_SPEED,
                        new AttributeModifier(Item.BASE_ATTACK_SPEED_ID, attackSpeedModifier, AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .build());

        // ponytail: enchantability comes off the head because Phase 1 has no binding. PLAN.md section 4
        // gives it to the binding, so Phase 2 moves this one line and the rest stands.
        stack.set(DataComponents.ENCHANTABLE, new Enchantable(head.head().enchantmentValue()));

        stack.set(DataComponents.ITEM_NAME, Component.translatable("item.temper.sword.assembled",
                Component.translatable(materialKey(headId)),
                Component.translatable(materialKey(handleId))));
        return stack;
    }

    public static String materialKey(final Identifier material) {
        return "material." + material.getNamespace() + "." + material.getPath();
    }

    /**
     * Reads the finished numbers back off the stack, so what gets reported is what was actually written
     * rather than the arithmetic repeated. PLAN.md wants these checked against vanilla's tiers: a sword
     * with an iron head and an iron handle should land exactly on the vanilla iron sword.
     */
    public static String describe(final ItemStack stack) {
        ToolParts parts = stack.get(Temper.TOOL_PARTS.get());
        ItemAttributeModifiers attributes = stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
        Enchantable enchantable = stack.get(DataComponents.ENCHANTABLE);
        return "%s head / %s handle: durability %d, damage %.1f, speed %.2f/s, enchantability %d".formatted(
                parts == null ? "?" : parts.head().getPath(),
                parts == null ? "?" : parts.handle().getPath(),
                stack.getOrDefault(DataComponents.MAX_DAMAGE, 0),
                attributes.compute(Attributes.ATTACK_DAMAGE, PLAYER_BASE_ATTACK_DAMAGE, EquipmentSlot.MAINHAND),
                attributes.compute(Attributes.ATTACK_SPEED, PLAYER_BASE_ATTACK_SPEED, EquipmentSlot.MAINHAND),
                enchantable == null ? 0 : enchantable.value());
    }
}
