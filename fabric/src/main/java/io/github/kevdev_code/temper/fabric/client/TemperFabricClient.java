package io.github.kevdev_code.temper.fabric.client;

import net.fabricmc.api.ClientModInitializer;
import net.minecraft.client.color.item.ItemTintSources;

import io.github.kevdev_code.temper.client.TemperClient;

public final class TemperFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        TemperClient.init(ItemTintSources.ID_MAPPER::put);
    }
}
