package io.github.kevdev_code.temper.tool;

import com.mojang.serialization.Codec;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

import io.github.kevdev_code.temper.Temper;

import java.util.Arrays;
import java.util.List;

/**
 * The tool types Temper assembles, and what each contributes on top of its parts.
 *
 * <p>The attack baselines are not here: vanilla hand tunes them per material for the axe and the hoe
 * (a diamond axe deals 9 like an iron one, every hoe deals 1), so they live in {@code materials.json}
 * under each material's head, per kind, read off {@code Items}. A tool that mines names the block tag
 * it mines efficiently; the sword names none.
 *
 * <p>The shape is the crafting grid, read after vanilla crops it to its filled cells: {@code H} head,
 * {@code B} binding, {@code G} handle, {@code R} reinforcement (optional), {@code .} must be empty.
 * Every head cell must hold the same material, and every handle cell likewise.
 */
public enum ToolKind implements StringRepresentable {
    SWORD("sword", null,
            ".H",
            "BH",
            "RG"),
    PICKAXE("pickaxe", BlockTags.MINEABLE_WITH_PICKAXE,
            "HHH",
            "BG.",
            "RG."),
    AXE("axe", BlockTags.MINEABLE_WITH_AXE,
            ".HH",
            "BHG",
            "R.G"),
    // Not the sword's box with one head fewer. A material is one ingredient whatever slot it fills,
    // so an all-iron column with iron fittings would fit both a sword and such a shovel, and
    // mirroring makes it worse. This shape's empty cell never lands where the sword's does in either
    // orientation; ShapeMatch's self check crosses the two.
    SHOVEL("shovel", BlockTags.MINEABLE_WITH_SHOVEL,
            "HB",
            "G.",
            "GR"),
    // Vanilla's hoe is two heads over a stick; the fittings fill the column vanilla leaves empty, so
    // vanilla's own layout does not fit this and this does not fit vanilla's. Crossed against the
    // sword and the shovel, the other two-wide boxes, in ShapeMatch's self check.
    HOE("hoe", BlockTags.MINEABLE_WITH_HOE,
            "HH",
            "BG",
            "RG");

    public static final Codec<ToolKind> CODEC = StringRepresentable.fromEnum(ToolKind::values);

    private final String serializedName;
    private final TagKey<Block> minesEfficiently;
    private final List<String> shape;

    ToolKind(final String serializedName, final TagKey<Block> minesEfficiently, final String... shape) {
        this.serializedName = serializedName;
        this.minesEfficiently = minesEfficiently;
        this.shape = Arrays.asList(shape);
    }

    public static ToolKind byName(final String name) {
        return Arrays.stream(values()).filter(k -> k.serializedName.equals(name)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("no Temper tool called " + name));
    }

    public Item item() {
        return switch (this) {
            case SWORD -> Temper.SWORD.get();
            case PICKAXE -> Temper.PICKAXE.get();
            case AXE -> Temper.AXE.get();
            case SHOVEL -> Temper.SHOVEL.get();
            case HOE -> Temper.HOE.get();
        };
    }

    /** Null for a tool that does not mine. */
    public TagKey<Block> minesEfficiently() {
        return minesEfficiently;
    }

    public List<String> shape() {
        return shape;
    }

    @Override
    public String getSerializedName() {
        return serializedName;
    }
}
