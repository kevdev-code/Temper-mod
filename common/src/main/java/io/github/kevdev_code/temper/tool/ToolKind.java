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
 * <p>The two baselines are vanilla 26.1.2's own, read off {@code Items}: every {@code *_sword} is
 * {@code Properties.sword(material, 3.0f, -2.4f)} and every {@code *_pickaxe} is
 * {@code Properties.pickaxe(material, 1.0f, -2.8f)}, every {@code *_axe} is
 * {@code new AxeItem(material, 6.0f, -3.1f, p)}, every {@code *_shovel} is
 * {@code new ShovelItem(material, 1.5f, -3.0f, p)}. The head's {@code attackDamageBonus} is added to
 * the first. A tool that mines names the block tag it mines efficiently; the sword names none.
 *
 * <p>The shape is the crafting grid, read after vanilla crops it to its filled cells: {@code H} head,
 * {@code B} binding, {@code G} handle, {@code R} reinforcement (optional), {@code .} must be empty.
 * Every head cell must hold the same material, and every handle cell likewise.
 */
public enum ToolKind implements StringRepresentable {
    SWORD("sword", 3.0F, -2.4F, null,
            ".H",
            "BH",
            "RG"),
    PICKAXE("pickaxe", 1.0F, -2.8F, BlockTags.MINEABLE_WITH_PICKAXE,
            "HHH",
            "BG.",
            "RG."),
    AXE("axe", 6.0F, -3.1F, BlockTags.MINEABLE_WITH_AXE,
            ".HH",
            "BHG",
            "R.G"),
    // Not the sword's box with one head fewer. A material is one ingredient whatever slot it fills,
    // so an all-iron column with iron fittings would fit both a sword and such a shovel, and
    // mirroring makes it worse. This shape's empty cell never lands where the sword's does in either
    // orientation; ShapeMatch's self check crosses the two.
    SHOVEL("shovel", 1.5F, -3.0F, BlockTags.MINEABLE_WITH_SHOVEL,
            "HB",
            "G.",
            "GR");

    public static final Codec<ToolKind> CODEC = StringRepresentable.fromEnum(ToolKind::values);

    private final String serializedName;
    private final float attackDamageBaseline;
    private final float attackSpeedBaseline;
    private final TagKey<Block> minesEfficiently;
    private final List<String> shape;

    ToolKind(final String serializedName, final float attackDamageBaseline, final float attackSpeedBaseline,
             final TagKey<Block> minesEfficiently, final String... shape) {
        this.serializedName = serializedName;
        this.attackDamageBaseline = attackDamageBaseline;
        this.attackSpeedBaseline = attackSpeedBaseline;
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
        };
    }

    public float attackDamageBaseline() {
        return attackDamageBaseline;
    }

    public float attackSpeedBaseline() {
        return attackSpeedBaseline;
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
