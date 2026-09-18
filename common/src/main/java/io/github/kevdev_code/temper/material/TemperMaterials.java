package io.github.kevdev_code.temper.material;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

import io.github.kevdev_code.temper.Temper;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * The material table, read once at startup from {@code temper/materials.json} inside the mod jar.
 * Both sides load it, so the client has the colours and the server has the stats with nothing to sync.
 */
public final class TemperMaterials {
    private static final String PATH = "/temper/materials.json";

    /** Bare keys land in the mod's namespace; a key with a colon is taken as written. */
    private static final Codec<Identifier> KEY_CODEC = Codec.STRING.xmap(
            text -> text.indexOf(':') < 0 ? Identifier.fromNamespaceAndPath(Temper.MOD_ID, text) : Identifier.parse(text),
            Identifier::toString);

    /** Under a "materials" key so the file can carry sibling notes; JSON has no comments. */
    private static final Codec<Map<Identifier, TemperMaterial>> TABLE_CODEC =
            Codec.unboundedMap(KEY_CODEC, TemperMaterial.CODEC).fieldOf("materials").codec();

    // ponytail: loaded from the jar, so it is not datapack-overridable. Move it to a reload listener
    // the day players need to add materials without rebuilding; the callers below do not change.
    private static Map<Identifier, TemperMaterial> table = Map.of();

    private TemperMaterials() {
    }

    public static void load() {
        try (InputStream stream = TemperMaterials.class.getResourceAsStream(PATH)) {
            if (stream == null) {
                throw new IllegalStateException(PATH + " is missing from the mod jar");
            }
            JsonElement json = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            table = Map.copyOf(TABLE_CODEC.parse(JsonOps.INSTANCE, json).getOrThrow());
            Temper.LOGGER.info("Loaded {} Temper materials", table.size());
        } catch (Exception e) {
            throw new IllegalStateException("Could not read " + PATH, e);
        }
    }

    public static Optional<TemperMaterial> get(final Identifier id) {
        return Optional.ofNullable(table.get(id));
    }

    /** Resolves the raw item a player placed in the grid back to the material it stands for. */
    public static Optional<Identifier> byIngredient(final ItemStack stack) {
        return table.entrySet().stream()
                .filter(entry -> entry.getValue().matchesIngredient(stack))
                .map(Map.Entry::getKey)
                .findFirst();
    }

    /** Sorted so the creative tab and any generated output keep a stable order. */
    public static List<Identifier> ids() {
        return table.keySet().stream().sorted(Identifier::compareTo).toList();
    }
}
