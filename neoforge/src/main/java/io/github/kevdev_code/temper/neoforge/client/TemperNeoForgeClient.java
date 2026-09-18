package io.github.kevdev_code.temper.neoforge.client;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;

import io.github.kevdev_code.temper.Temper;
import io.github.kevdev_code.temper.client.TemperClient;

@Mod(value = Temper.MOD_ID, dist = Dist.CLIENT)
public final class TemperNeoForgeClient {
    public TemperNeoForgeClient() {
        TemperClient.init();
    }
}
