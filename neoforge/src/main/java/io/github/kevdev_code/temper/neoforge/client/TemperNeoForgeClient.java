package io.github.kevdev_code.temper.neoforge.client;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.RegisterColorHandlersEvent;

import io.github.kevdev_code.temper.Temper;
import io.github.kevdev_code.temper.client.TemperClient;

@Mod(value = Temper.MOD_ID, dist = Dist.CLIENT)
public final class TemperNeoForgeClient {
    public TemperNeoForgeClient(IEventBus modBus) {
        modBus.addListener((RegisterColorHandlersEvent.ItemTintSources event) -> TemperClient.init(event::register));
    }
}
