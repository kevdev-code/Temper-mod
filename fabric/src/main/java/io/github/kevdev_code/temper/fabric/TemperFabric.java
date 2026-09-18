package io.github.kevdev_code.temper.fabric;

import net.fabricmc.api.ModInitializer;

import io.github.kevdev_code.temper.Temper;

public final class TemperFabric implements ModInitializer {
    @Override
    public void onInitialize() {
        Temper.init();
    }
}
