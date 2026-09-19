#!/usr/bin/env bash
#
# Launches a dev client straight into a test world, screenshots it, shuts it down.
# PLAN.md requires every part and tool to be seen on both loaders; this is that loop.
#
#   scripts/visual-check.sh <fabric|neoforge> [world] [out-dir]
#
# The world is generated on first use (flat, peaceful, creative) and reused after that.
# To put the item under test in the player's hands, point TEMPER_DATAPACK at a datapack
# directory; it is copied into the save, and a #minecraft:tick function in it can `give`
# the item with its components. Worlds load their own datapacks with no prompt.
#
# Windows only: the screenshot goes through PowerShell.
#
set -uo pipefail

PLATFORM=${1:-}
WORLD=${2:-test}
OUT_DIR=${3:-build/visual-check}

case "$PLATFORM" in
    fabric|neoforge) ;;
    *) echo "usage: $0 <fabric|neoforge> [world] [out-dir]" >&2; exit 2 ;;
esac

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT" || exit 1
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/$PLATFORM-$WORLD.log"
SHOT="$OUT_DIR/$PLATFORM-$WORLD.png"
SAVE="$PLATFORM/run/saves/$WORLD"
WIN_ROOT=$(cygpath -w "$ROOT")

# The NeoForge dedicated server halts itself once this file can be written, which makes
# world generation a task that ends on its own instead of one that has to be killed.
generate_world() {
    echo "==> generating world (one-off)"
    local marker="$ROOT/$OUT_DIR/.server-selftest"
    rm -f "$marker"
    mkdir -p neoforge/run
    echo 'eula=true' > neoforge/run/eula.txt
    cat > neoforge/run/server.properties <<'PROPS'
level-type=minecraft:flat
level-name=world
difficulty=peaceful
gamemode=creative
online-mode=false
generate-structures=false
spawn-monsters=false
view-distance=6
PROPS
    NEOFORGE_DEDICATED_SERVER_SELFTEST=$(cygpath -w "$marker") \
        ./gradlew :neoforge:runServer --offline > "$OUT_DIR/worldgen.log" 2>&1
    if [ ! -d neoforge/run/world ]; then
        echo "world generation failed, see $OUT_DIR/worldgen.log" >&2
        return 1
    fi
}

kill_client() {
    powershell -NoProfile -Command "
        Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" |
            Where-Object { \$_.CommandLine -like '*architectury.main.class*' -and \$_.CommandLine -like '*${WIN_ROOT}\\${PLATFORM}*' } |
            ForEach-Object { Stop-Process -Id \$_.ProcessId -Force; 'stopped client pid ' + \$_.ProcessId }"
}

if [ ! -d "$SAVE" ]; then
    [ -d neoforge/run/world ] || generate_world || exit 1
    mkdir -p "$(dirname "$SAVE")"
    cp -r neoforge/run/world "$SAVE"
fi

if [ -n "${TEMPER_DATAPACK:-}" ]; then
    mkdir -p "$SAVE/datapacks"
    cp -r "$TEMPER_DATAPACK" "$SAVE/datapacks/"
    echo "==> datapack $(basename "$TEMPER_DATAPACK") copied into $SAVE"
fi

echo "==> launching $PLATFORM client into world '$WORLD'"
rm -f "$LOG" "$SHOT"
./gradlew ":$PLATFORM:runClient" --args="--quickPlaySingleplayer $WORLD" --offline > "$LOG" 2>&1 &
GRADLE_PID=$!

# "joined the game" is the first line that means the world is actually on screen. The failure
# alternatives matter as much: without them a crash looks exactly like a slow start.
for _ in $(seq 1 150); do
    grep -qE "joined the game|FAILURE:|Exception in|Crash Report" "$LOG" 2>/dev/null && break
    kill -0 "$GRADLE_PID" 2>/dev/null || break   # gradle died without a marker we recognise
    sleep 2
done
sleep 12

# Capture the client this script launched, by id. Matching on the window title alone can pick a
# different Minecraft window, such as one an earlier run left at the menu, and screenshot that.
CLIENT_PID=$(powershell -NoProfile -Command "
    Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" |
        Where-Object { \$_.CommandLine -like '*architectury.main.class*' -and \$_.CommandLine -like '*${WIN_ROOT}\\${PLATFORM}*' } |
        Select-Object -First 1 -ExpandProperty ProcessId" | tr -d '[:space:]')
echo "==> client pid ${CLIENT_PID:-unknown}"
# Capture the client this script launched, by id. Matching on the window title alone can pick a
# different Minecraft window, such as one an earlier run left at the menu, and screenshot that.
CLIENT_PID=$(powershell -NoProfile -Command "
    Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" |
        Where-Object { \$_.CommandLine -like '*architectury.main.class*' -and \$_.CommandLine -like '*${WIN_ROOT}\\${PLATFORM}*' } |
        Select-Object -First 1 -ExpandProperty ProcessId" | tr -d '[:space:]')
echo "==> client pid ${CLIENT_PID:-unknown}"

# Three shots a few seconds apart. The creative screen opens by itself now and then and its
# tooltip hides a slot or two, which says nothing about the sprite; verify-swords.py unions the
# shots, so one clean view of each sword is enough. Steadier than fighting the screen.
SHOTS=""
for n in 1 2 3; do
    shot="${SHOT%.png}-$n.png"
    rm -f "$shot"
    powershell -NoProfile -ExecutionPolicy Bypass -File "$ROOT/scripts/screenshot-window.ps1" \
        -Out "$(cygpath -w "$ROOT/$shot")" -ProcessId "${CLIENT_PID:-0}" -TitleLike 'Minecraft*' || true
    [ -f "$shot" ] && SHOTS="$SHOTS $shot"
    [ "$n" = 3 ] || sleep 4
done
first=$(echo $SHOTS | awk '{print $1}')
[ -n "$first" ] && cp "$first" "$SHOT"
echo "==> log evidence"
grep -nE "Temper (common|client) init|- temper |Temper 1\.[0-9.]+ \(temper\)|joined the game|FAILURE:|Exception in|Crash Report|/ERROR" "$LOG" |
    grep -viE "Realms|SignedJWT|CancellationException" | cut -c1-200 | head -20

kill_client
wait $GRADLE_PID 2>/dev/null
echo "==> screenshots:${SHOTS:- none}"
