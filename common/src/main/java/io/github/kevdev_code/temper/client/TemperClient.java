package io.github.kevdev_code.temper.client;

import io.github.kevdev_code.temper.Temper;

// Client-only by reachability: called from the two client entrypoints, never from Temper.init().
public final class TemperClient {
    public static void init() {
        Temper.LOGGER.info("Temper client init");
    }
}
