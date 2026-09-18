package io.github.kevdev_code.temper.fabric.client;

import net.fabricmc.api.ClientModInitializer;

import io.github.kevdev_code.temper.client.TemperClient;

public final class TemperFabricClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        TemperClient.init();
    }
}
