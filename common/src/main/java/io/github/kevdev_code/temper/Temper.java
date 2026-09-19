package io.github.kevdev_code.temper;

import dev.architectury.event.events.common.LifecycleEvent;
import dev.architectury.registry.CreativeTabRegistry;
import dev.architectury.registry.registries.DeferredRegister;
import dev.architectury.registry.registries.RegistrySupplier;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.Weapon;
import net.minecraft.world.item.crafting.RecipeSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import io.github.kevdev_code.temper.material.TemperMaterials;
import io.github.kevdev_code.temper.recipe.SwordAssemblyRecipe;
import io.github.kevdev_code.temper.tool.SwordAssembly;
import io.github.kevdev_code.temper.tool.ToolParts;

import java.util.LinkedHashSet;
import java.util.Optional;
import java.util.Set;

import java.util.List;

public final class Temper {
    public static final String MOD_ID = "temper";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static final DeferredRegister<DataComponentType<?>> COMPONENTS =
            DeferredRegister.create(MOD_ID, Registries.DATA_COMPONENT_TYPE);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(MOD_ID, Registries.ITEM);
    public static final DeferredRegister<RecipeSerializer<?>> RECIPE_SERIALIZERS =
            DeferredRegister.create(MOD_ID, Registries.RECIPE_SERIALIZER);
    public static final DeferredRegister<CreativeModeTab> CREATIVE_TABS =
            DeferredRegister.create(MOD_ID, Registries.CREATIVE_MODE_TAB);

    /** The material in each part slot. Everything else about a tool is derived from this. */
    public static final RegistrySupplier<DataComponentType<ToolParts>> TOOL_PARTS = COMPONENTS.register("parts",
            () -> DataComponentType.<ToolParts>builder()
                    .persistent(ToolParts.CODEC)
                    .networkSynchronized(ToolParts.STREAM_CODEC)
                    .build());

    /**
     * One sword item for every combination. Durability, damage, speed and enchantability are per-stack
     * components written at assembly, so the item itself carries only what all Temper swords share.
     */
    public static final RegistrySupplier<Item> SWORD = ITEMS.register("sword",
            () -> new Item(new Item.Properties()
                    .setId(ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(MOD_ID, "sword")))
                    .durability(1)
                    .component(DataComponents.WEAPON, new Weapon(1))));

    public static final RegistrySupplier<RecipeSerializer<SwordAssemblyRecipe>> SWORD_ASSEMBLY =
            RECIPE_SERIALIZERS.register("sword_assembly",
                    () -> new RecipeSerializer<>(SwordAssemblyRecipe.MAP_CODEC, SwordAssemblyRecipe.STREAM_CODEC));

    public static final RegistrySupplier<CreativeModeTab> TAB = CREATIVE_TABS.register("temper",
            () -> CreativeTabRegistry.create(builder -> builder
                    .title(Component.translatable("itemGroup.temper"))
                    .icon(() -> new ItemStack(SWORD.get()))
                    .displayItems((params, output) -> everySword().forEach(output::accept))));

    public static void init() {
        TemperMaterials.load();
        COMPONENTS.register();
        ITEMS.register();
        RECIPE_SERIALIZERS.register();
        CREATIVE_TABS.register();

        // ponytail: three lines, the tools whose every part is one material, which are exactly the
        // ones PLAN.md calibrates against vanilla. The full space is 108 combinations and does not
        // belong in a log; the tooltip carries the rest.
        LifecycleEvent.SERVER_STARTED.register(server -> TemperMaterials.ids().forEach(id ->
                SwordAssembly.assemble(new ToolParts(id, id, id, Optional.empty()))
                        .ifPresent(stack -> LOGGER.info("sword {}", SwordAssembly.describe(stack)))));

        LOGGER.info("Temper common init");
    }

    /**
     * What the creative tab offers. The full space is 108 combinations, which is not a menu, so this
     * is a spanning set: every head against every handle, then the binding and the reinforcement
     * varied on a fixed base so each material is shown in each of the four slots at least once.
     */
    private static List<ItemStack> everySword() {
        List<Identifier> ids = TemperMaterials.ids();
        Identifier base = ids.contains(Identifier.fromNamespaceAndPath(MOD_ID, "iron"))
                ? Identifier.fromNamespaceAndPath(MOD_ID, "iron") : ids.getFirst();
        // A set: the loops below overlap, and a creative tab throws on a repeated stack.
        Set<ToolParts> combinations = new LinkedHashSet<>();
        for (Identifier head : ids) {
            for (Identifier handle : ids) {
                combinations.add(new ToolParts(handle, head, handle, Optional.empty()));
            }
        }
        for (Identifier binding : ids) {
            combinations.add(new ToolParts(base, base, binding, Optional.empty()));
        }
        for (Identifier reinforcement : ids) {
            combinations.add(new ToolParts(base, base, base, Optional.of(reinforcement)));
        }
        return combinations.stream().flatMap(parts -> SwordAssembly.assemble(parts).stream()).toList();
    }
}
