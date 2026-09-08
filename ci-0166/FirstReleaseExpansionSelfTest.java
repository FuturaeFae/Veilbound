package dev.futurae.veilbound.domain;

import java.util.UUID;

/** Regression for first-release Core-driven expansion with no physical Boundary Pylon. */
public final class FirstReleaseExpansionSelfTest {
    public static void main(String[] args) {
        DomainState state = new DomainState(UUID.randomUUID());
        state.initializeFirstReleaseCore();
        truth(state.bounds().equals(new DomainBounds(-1, -1, -1, 1, 1, 1)), "starter Domain is centered 3x3x3");
        truth(state.coreTier() == CoreTier.NASCENT, "starter Core is Nascent");

        // First release retains the old persisted direction-state record only as save compatibility.
        // A selected face must not require an online/placed Boundary Pylon.
        var directionState = state.pylons().get(AxisDirection.POSITIVE_X);
        truth(directionState != null && !directionState.online(), "no physical Pylon is online in first-release state");
        state.setPylon(directionState.withExpansionEnabled(true));
        state.setDimensionalEnergy(100L);

        ExpansionPolicy policy = new ExpansionPolicy(4L, 384, 0);
        var decision = ExpansionGovernor.planOneBlock(state, AxisDirection.POSITIVE_X, policy, true);
        truth(decision.allowed(), "Core-selected +X face expands without a physical Pylon");
        eq(36L, decision.dimensionalEnergyCost(), "3x3 exposed face costs 9 blocks x 4 DE");
        truth(ExpansionGovernor.apply(state, decision), "approved expansion applies atomically");
        truth(state.bounds().equals(new DomainBounds(-1, -1, -1, 2, 1, 1)), "+X grows by exactly one block");
        eq(64L, state.dimensionalEnergy(), "face expansion debits the exact DE cost");
        truth(state.coreTier() == CoreTier.NASCENT, "Core level remains size-derived after asymmetric growth");

        // The tier boundary itself is dimension-derived, not an item/command upgrade.
        state.setBounds(new DomainBounds(-4, -4, -4, 4, 4, 4));
        truth(state.coreTier() == CoreTier.ANCHORED, "9x9x9 derives Anchored Core level");

        System.out.println("FirstReleaseExpansionSelfTest: PASS");
    }

    private static void eq(long expected, long actual, String label) {
        if (expected != actual) throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
    }

    private static void truth(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }
}
