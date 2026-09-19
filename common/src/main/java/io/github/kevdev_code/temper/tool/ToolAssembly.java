package io.github.kevdev_code.temper.tool;

import net.minecraft.ChatFormatting;
import net.minecraft.core.HolderSet;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.component.Tool;
import net.minecraft.world.item.enchantment.Enchantable;
import net.minecraft.world.level.block.Block;

import io.github.kevdev_code.temper.Temper;
import io.github.kevdev_code.temper.material.TemperMaterial;
import io.github.kevdev_code.temper.material.TemperMaterials;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Turns a set of materials into a finished tool. This is PLAN.md section 5 in code, and it runs once
 * per assembly, never per tick: every number it derives is baked into the stack's components.
 */
public final class ToolAssembly {

    /** A player swings at 4.0 per second and punches for 1.0 before any item modifier applies. */
    private static final double PLAYER_BASE_ATTACK_SPEED = 4.0;
    private static final double PLAYER_BASE_ATTACK_DAMAGE = 1.0;

    private ToolAssembly() {
    }

    /** Empty when a material is unknown or is not allowed in the slot it was given. */
    public static Optional<ItemStack> assemble(final ToolKind kind, final ToolParts parts) {
        for (PartSlot slot : PartSlot.values()) {
            Optional<Identifier> id = parts.get(slot);
            if (id.isEmpty()) {
                if (!slot.isOptional()) {
                    return Optional.empty();
                }
                continue;
            }
            if (TemperMaterials.get(id.get()).filter(m -> m.allows(slot)).isEmpty()) {
                return Optional.empty();
            }
        }
        if (material(parts, PartSlot.HEAD).head().attack(kind).isEmpty()) {
            return Optional.empty();                        // vanilla makes no such tool of that material
        }
        return Optional.of(build(kind, parts));
    }

    private static TemperMaterial material(final ToolParts parts, final PartSlot slot) {
        return TemperMaterials.get(parts.get(slot).orElseThrow()).orElseThrow();
    }

    private static ItemStack build(final ToolKind kind, final ToolParts parts) {
        TemperMaterial head = material(parts, PartSlot.HEAD);
        TemperMaterial handle = material(parts, PartSlot.HANDLE);
        TemperMaterial binding = material(parts, PartSlot.BINDING);

        ItemStack stack = new ItemStack(kind.item());
        stack.set(Temper.TOOL_PARTS.get(), parts);

        // durability = head.baseDurability * handle.durabilityMultiplier
        int durability = Math.max(1, Math.round(head.head().durability() * handle.handle().durabilityMultiplier()));
        stack.set(DataComponents.MAX_DAMAGE, durability);

        // attackDamage = head.attackDamage: vanilla's baseline for this kind of tool in this material,
        // plus the material's bonus. The handle owns nimbleness, never raw damage.
        TemperMaterial.Attack attack = head.head().attack(kind).orElseThrow();
        double attackDamage = attack.damageBaseline() + head.head().attackDamageBonus();

        // attackSpeed = head.baseSpeed * handle.speedMultiplier, worked in swings per second so that a
        // multiplier above 1.0 means faster. Vanilla stores it as a modifier against the player's 4.0,
        // so it converts back on the way out.
        double swingsPerSecond = (PLAYER_BASE_ATTACK_SPEED + attack.speedBaseline()) * handle.handle().speedMultiplier();
        double attackSpeedModifier = swingsPerSecond - PLAYER_BASE_ATTACK_SPEED;

        stack.set(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.builder()
                .add(Attributes.ATTACK_DAMAGE,
                        new AttributeModifier(Item.BASE_ATTACK_DAMAGE_ID, attackDamage, AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .add(Attributes.ATTACK_SPEED,
                        new AttributeModifier(Item.BASE_ATTACK_SPEED_ID, attackSpeedModifier, AttributeModifier.Operation.ADD_VALUE),
                        EquipmentSlotGroup.MAINHAND)
                .build());

        // miningSpeed = head.miningSpeed, miningLevel = head.miningLevel: the head alone decides what the
        // tool digs and how fast, exactly as vanilla's ToolMaterial does through its two rules.
        if (kind.minesEfficiently() != null) {
            HolderSet<Block> incorrect = BuiltInRegistries.BLOCK.getOrThrow(head.head().incorrectForDropsTag());
            HolderSet<Block> mineable = BuiltInRegistries.BLOCK.getOrThrow(kind.minesEfficiently());
            stack.set(DataComponents.TOOL, new Tool(List.of(
                    Tool.Rule.deniesDrops(incorrect),
                    Tool.Rule.minesAndDrops(mineable, head.head().miningSpeed())), 1.0F, 1, true));
        }

        // enchantValue = binding.enchantability, as PLAN.md section 4 has it.
        stack.set(DataComponents.ENCHANTABLE, new Enchantable(binding.binding().enchantmentValue()));

        // A tool built on a vanilla item class carries that class's repair ingredient as a default.
        // Repair is PLAN.md section 8 and is not designed yet, so no Temper tool repairs in an anvil.
        stack.remove(DataComponents.REPAIRABLE);

        stack.set(DataComponents.ITEM_NAME, Component.translatable("item.temper." + kind.getSerializedName() + ".assembled",
                Component.translatable(materialKey(parts.head()))));
        stack.set(DataComponents.LORE, new ItemLore(lore(parts, binding)));
        return stack;
    }

    /**
     * The parts the name cannot carry, plus the modifier slots the binding grants. Those slots hold
     * nothing yet: modifiers arrive in Phase 6, and the reinforcement's behavioural trait with them.
     */
    private static List<Component> lore(final ToolParts parts, final TemperMaterial binding) {
        List<Component> lines = new ArrayList<>();
        lines.add(line("tooltip.temper.handle", Component.translatable(materialKey(parts.handle()))));
        lines.add(line("tooltip.temper.binding", Component.translatable(materialKey(parts.binding()))));
        lines.add(parts.reinforcement()
                .map(id -> line("tooltip.temper.reinforcement", Component.translatable(materialKey(id))))
                .orElseGet(() -> Component.translatable("tooltip.temper.reinforcement.none")
                        .withStyle(ChatFormatting.DARK_GRAY)));
        lines.add(line("tooltip.temper.modifier_slots", Component.literal(
                String.valueOf(binding.binding().modifierSlots()))));
        return List.copyOf(lines);
    }

    private static Component line(final String key, final Component value) {
        return Component.translatable(key, value).withStyle(ChatFormatting.GRAY);
    }

    public static String materialKey(final Identifier material) {
        return "material." + material.getNamespace() + "." + material.getPath();
    }

    /**
     * Reads the finished numbers back off the stack, so what gets reported is what was actually
     * written rather than the arithmetic repeated. PLAN.md wants these checked against vanilla's
     * tiers: a tool whose parts are all iron should land exactly on the vanilla iron tool.
     */
    public static String describe(final ItemStack stack) {
        ToolParts parts = stack.get(Temper.TOOL_PARTS.get());
        ItemAttributeModifiers attributes = stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
        Enchantable enchantable = stack.get(DataComponents.ENCHANTABLE);
        Tool tool = stack.get(DataComponents.TOOL);
        String mining = tool == null ? "" : ", mining speed %.1f, %d rule(s)".formatted(
                tool.rules().stream().flatMap(r -> r.speed().stream()).findFirst().orElse(0.0F), tool.rules().size());
        return "%s head / %s handle / %s binding: durability %d, damage %.1f, speed %.2f/s, enchantability %d%s".formatted(
                parts == null ? "?" : parts.head().getPath(),
                parts == null ? "?" : parts.handle().getPath(),
                parts == null ? "?" : parts.binding().getPath(),
                stack.getOrDefault(DataComponents.MAX_DAMAGE, 0),
                attributes.compute(Attributes.ATTACK_DAMAGE, PLAYER_BASE_ATTACK_DAMAGE, EquipmentSlot.MAINHAND),
                attributes.compute(Attributes.ATTACK_SPEED, PLAYER_BASE_ATTACK_SPEED, EquipmentSlot.MAINHAND),
                enchantable == null ? 0 : enchantable.value(),
                mining);
    }
}
