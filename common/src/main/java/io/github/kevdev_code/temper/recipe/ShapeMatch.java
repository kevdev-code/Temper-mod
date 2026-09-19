package io.github.kevdev_code.temper.recipe;

import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * Matches a crafting grid against a tool shape, free of Minecraft types so it can be run and checked
 * without the game: {@code java -cp common/build/classes/java/main io.github.kevdev_code.temper.recipe.ShapeMatch}.
 *
 * <p>The shape is rows of {@code H} head, {@code G} handle, {@code B} binding, {@code R} optional
 * reinforcement and {@code .} empty. The grid is what the player placed, already cropped to its
 * filled cells and resolved to material ids, null where a cell is empty. Both the shape and its
 * mirror image are tried, because that is what vanilla does with every asymmetric shaped recipe and a
 * player who has learned to build an axe either way round should get a Temper axe either way round.
 */
final class ShapeMatch {

    /** Material ids by slot; the reinforcement is null when its cell was left empty. */
    record Parts(String head, String handle, String binding, String reinforcement) {
    }

    private ShapeMatch() {
    }

    /** Null when the grid does not fit the shape in either orientation. */
    static Parts match(final List<String> shape, final String[][] grid) {
        Parts parts = matchExactly(shape, grid);
        return parts != null ? parts : matchExactly(mirror(shape), grid);
    }

    static List<String> mirror(final List<String> shape) {
        return shape.stream().map(row -> new StringBuilder(row).reverse().toString()).toList();
    }

    private static Parts matchExactly(final List<String> shape, final String[][] grid) {
        if (grid.length != shape.size() || grid[0].length != shape.getFirst().length()) {
            return null;
        }
        String head = null, handle = null, binding = null, reinforcement = null;
        for (int y = 0; y < shape.size(); y++) {
            for (int x = 0; x < shape.get(y).length(); x++) {
                char cell = shape.get(y).charAt(x);
                String id = grid[y][x];
                if (cell == '.') {
                    if (id != null) {
                        return null;
                    }
                    continue;
                }
                if (id == null) {
                    if (cell == 'R') {
                        continue;                              // the one cell that may stay empty
                    }
                    return null;
                }
                switch (cell) {
                    case 'H' -> {
                        if (head != null && !head.equals(id)) {
                            return null;                       // every head cell, one material
                        }
                        head = id;
                    }
                    case 'G' -> {
                        if (handle != null && !handle.equals(id)) {
                            return null;
                        }
                        handle = id;
                    }
                    case 'B' -> binding = id;
                    case 'R' -> reinforcement = id;
                    default -> throw new IllegalStateException("bad shape cell " + cell);
                }
            }
        }
        if (head == null || handle == null || binding == null) {
            return null;
        }
        return new Parts(head, handle, binding, reinforcement);
    }

    // ---------------------------------------------------------------- self check

    private static String[][] grid(final String... rows) {
        return Arrays.stream(rows).map(row -> Arrays.stream(row.split(" "))
                .map(cell -> cell.equals(".") ? null : cell).toArray(String[]::new)).toArray(String[][]::new);
    }

    public static void main(final String[] args) {
        List<String> axe = List.of(".HH", "BHG", "R.G");
        Parts want = new Parts("iron", "wood", "diamond", null);
        Parts withR = new Parts("iron", "wood", "diamond", "wood");

        check("axe as written", match(axe, grid(". iron iron", "diamond iron wood", ". . wood")), want);
        check("axe mirrored", match(axe, grid("iron iron .", "wood iron diamond", "wood . .")), want);
        check("axe with reinforcement", match(axe, grid(". iron iron", "diamond iron wood", "wood . wood")), withR);
        check("axe mirrored with reinforcement", match(axe, grid("iron iron .", "wood iron diamond", "wood . wood")), withR);
        check("vanilla axe, no fittings, does not match", match(axe, grid("iron iron", "iron wood", ". wood")), null);
        check("heads must agree", match(axe, grid(". iron diamond", "diamond iron wood", ". . wood")), null);
        check("an occupied empty cell fails", match(axe, grid("iron iron iron", "diamond iron wood", ". . wood")), null);

        List<String> sword = List.of(".H", "BH", "RG");
        check("sword as written", match(sword, grid(". iron", "diamond iron", ". wood")), want);
        check("sword mirrored", match(sword, grid("iron .", "iron diamond", "wood .")), want);
        List<String> pickaxe = List.of("HHH", "BG.", "RG.");
        check("pickaxe as written", match(pickaxe, grid("iron iron iron", "diamond wood .", ". wood .")), want);
        check("pickaxe mirrored", match(pickaxe, grid("iron iron iron", ". wood diamond", ". wood .")), want);

        // A material is one ingredient whatever slot it fills, so an all-iron grid is the case where
        // two tools sharing a box could both match. Of the three tools in a two wide box, exactly one
        // may fit any all-iron grid, with or without the reinforcement, in either orientation. The
        // pickaxe and the axe are left out on purpose: both fill three columns, so a cropped input
        // fits a two wide box or a three wide one, never both, and between the two of them the empty
        // cells never coincide in either orientation.
        List<String> shovel = List.of("HB", "G.", "GR");
        List<String> hoe = List.of("HH", "BG", "RG");
        Parts allIron = new Parts("iron", "iron", "iron", "iron");
        for (String[] rows : new String[][] {
                {". iron", "iron iron", "iron iron"}, {"iron .", "iron iron", "iron iron"},     // a sword, both ways
                {". iron", "iron iron", ". iron"}, {"iron .", "iron iron", "iron ."},
                {"iron iron", "iron .", "iron iron"}, {"iron iron", ". iron", "iron iron"},     // a shovel, both ways
                {"iron iron", "iron .", "iron ."}, {"iron iron", ". iron", ". iron"},
                {"iron iron", "iron iron", "iron iron"},                                        // a hoe, both ways
                {"iron iron", "iron iron", ". iron"}, {"iron iron", "iron iron", "iron ."}}) {
            int fits = 0;
            for (List<String> shape : List.of(sword, shovel, hoe)) {
                fits += match(shape, grid(rows)) != null ? 1 : 0;
            }
            if (fits != 1) {
                throw new AssertionError(fits + " tools fit " + Arrays.toString(rows));
            }
        }
        check("hoe as written", match(hoe, grid("iron iron", "diamond wood", ". wood")), want);
        check("hoe mirrored", match(hoe, grid("iron iron", "wood diamond", "wood .")), want);
        check("vanilla hoe, no fittings, does not match", match(hoe, grid("iron iron", ". wood", ". wood")), null);
        check("shovel as written", match(shovel, grid("iron iron", "iron .", "iron iron")), allIron);
        check("shovel mirrored, no reinforcement", match(shovel, grid("iron iron", ". iron", ". iron")), new Parts("iron", "iron", "iron", null));
        System.out.println("ShapeMatch: every check passed");
    }

    private static void check(final String name, final Parts got, final Parts want) {
        if (!Objects.equals(got, want)) {
            throw new AssertionError(name + ": got " + got + ", wanted " + want);
        }
    }
}
