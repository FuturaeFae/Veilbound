package dev.futurae.veilbound.breach;

/** Reloadable combat identity for Breach-linked fauna. */
public record BreachCombatPolicy(
        int crawlerSnareTicks,
        int crawlerMiningFatigueTicks,
        int stalkerDarknessTicks,
        int stalkerWeaknessTicks,
        long wraithDimensionalEnergyDrain,
        double wraithFractureShock,
        int wraithWeaknessTicks) {
    public BreachCombatPolicy {
        if (crawlerSnareTicks < 0 || crawlerMiningFatigueTicks < 0 || stalkerDarknessTicks < 0
                || stalkerWeaknessTicks < 0 || wraithWeaknessTicks < 0) {
            throw new IllegalArgumentException("Breach combat effect durations must be >= 0");
        }
        if (wraithDimensionalEnergyDrain < 0) throw new IllegalArgumentException("Wraith DE drain must be >= 0");
        if (!Double.isFinite(wraithFractureShock) || wraithFractureShock < 0.0) {
            throw new IllegalArgumentException("Wraith fracture shock must be finite and >= 0");
        }
    }
    public static BreachCombatPolicy developmentDefault() {
        return new BreachCombatPolicy(80, 60, 80, 80, 5_000L, 4.0, 100);
    }
}
