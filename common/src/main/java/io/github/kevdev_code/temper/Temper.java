package io.github.kevdev_code.temper;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class Temper {
    public static final String MOD_ID = "temper";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static void init() {
        LOGGER.info("Temper common init");
    }
}
