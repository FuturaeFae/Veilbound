package dev.futurae.veilbound.block;

import dev.futurae.veilbound.domain.CoreTier;

/** Regression for the floating, level-scaled physical Core hitbox. */
public final class DimensionalCoreVisualScaleSelfTest {
    public static void main(String[] args) {
        double previousHeight = 0.0D;
        for (CoreTier tier : CoreTier.values()) {
            var boxes = DimensionalCoreBlock.collisionBoxes(tier);
            truth(!boxes.isEmpty(), tier + " has a selectable main crystal");
            double minY = boxes.stream().mapToDouble(box -> box.minY).min().orElseThrow();
            double maxY = boxes.stream().mapToDouble(box -> box.maxY).max().orElseThrow();
            truth(minY > 0.0D, tier + " leaves real air below the floating crystal");
            truth(maxY > previousHeight, tier + " grows taller than the previous Core level");
            previousHeight = maxY;
        }
        truth(previousHeight >= 3.0D, "Transcendent Core reaches concept-art scale");
        System.out.println("DimensionalCoreVisualScaleSelfTest: PASS");
    }

    private static void truth(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }
}
