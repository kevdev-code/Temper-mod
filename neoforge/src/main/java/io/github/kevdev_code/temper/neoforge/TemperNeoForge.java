package io.github.kevdev_code.temper.neoforge;

import net.neoforged.fml.common.Mod;

import io.github.kevdev_code.temper.Temper;

@Mod(Temper.MOD_ID)
public final class TemperNeoForge {
    public TemperNeoForge() {
        Temper.init();
    }
}
