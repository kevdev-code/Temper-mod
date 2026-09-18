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

        // ponytail: one dump of the calibration table per run, which is what PLAN.md's definition of
        // done gets checked against. Drop it once the combination count outgrows a readable log.
        LifecycleEvent.SERVER_STARTED.register(server ->
                everySword().forEach(stack -> LOGGER.info("sword {}", SwordAssembly.describe(stack))));

        LOGGER.info("Temper common init");
    }

    /**
     * Every head and handle pairing the material table allows, in a stable order.
     *
     * <p>This cannot run during {@link #init()}: building an {@link ItemStack} before the item registry
     * binds its components throws "Components not bound yet". Server start and creative tab population
     * are both late enough.
     */
    private static List<ItemStack> everySword() {
        return TemperMaterials.ids().stream()
                .flatMap(head -> TemperMaterials.ids().stream()
                        .flatMap(handle -> SwordAssembly.assemble(handle, head).stream()))
                .toList();
    }
}
