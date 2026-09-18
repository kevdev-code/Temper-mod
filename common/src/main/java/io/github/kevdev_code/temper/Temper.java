package io.github.kevdev_code.temper;

import com.mojang.serialization.Codec;
import dev.architectury.registry.registries.DeferredRegister;
import dev.architectury.registry.registries.RegistrySupplier;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

public final class Temper {
    public static final String MOD_ID = "temper";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static final DeferredRegister<DataComponentType<?>> COMPONENTS = DeferredRegister.create(MOD_ID, Registries.DATA_COMPONENT_TYPE);
    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(MOD_ID, Registries.ITEM);

    /** One RGB colour per model layer, read on the client by {@code temper:layer} tint sources. */
    public static final RegistrySupplier<DataComponentType<List<Integer>>> TINT_COLORS = COMPONENTS.register("tint_colors",
            () -> DataComponentType.<List<Integer>>builder().persistent(Codec.INT.listOf()).build());

    // ponytail: Phase 0 throwaway item, two grayscale layers tinted from TINT_COLORS. Delete once real parts exist.
    public static final RegistrySupplier<Item> TINT_TEST = ITEMS.register("tint_test",
            () -> new Item(new Item.Properties().setId(ResourceKey.create(Registries.ITEM, Identifier.fromNamespaceAndPath(MOD_ID, "tint_test")))));

    public static void init() {
        COMPONENTS.register();
        ITEMS.register();
        LOGGER.info("Temper common init");
    }
}
