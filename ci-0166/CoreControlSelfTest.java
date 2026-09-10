package dev.futurae.veilbound.domain;

import dev.futurae.veilbound.energy.MatterTransductionService;
import dev.futurae.veilbound.energy.TransductionPolicy;
import java.util.UUID;

/** First-release Core control and baseline Transducer conversion regression. */
public final class CoreControlSelfTest {
    public static void main(String[] args) {
        DomainState state = new DomainState(UUID.randomUUID());
        truth(!CoreControlService.toggleExpansion(state).toggled(), "pre-Core expansion control rejected");

        state.initializeFirstReleaseCore();
        truth(state.dimensionalEnergy() == 0L, "first-release Core starts empty");
        truth(state.globalExpansionEnabled(), "global expansion defaults on");

        var direction = state.pylons().get(AxisDirection.POSITIVE_X);
        state.setPylon(direction.withExpansionEnabled(true));
        var expansionOff = CoreControlService.toggleExpansion(state);
        truth(expansionOff.toggled() && !expansionOff.enabled(), "Core toggles global expansion off");
        var denied = ExpansionGovernor.planOneBlock(
                state, AxisDirection.POSITIVE_X, new ExpansionPolicy(1, 4, 0), true);
        truth(!denied.allowed() && "global_expansion_disabled".equals(denied.reason()),
                "global Core switch dominates directional enable");

        // First-release baseline balance: 3 FE per Matter and 32 Matter per DE.
        // The Transducer owns both input buffers; only produced DE is credited to the linked Core.
        var conversion = MatterTransductionService.transduce(
                state, 32L, 96L, new TransductionPolicy(3L, 32L), true);
        truth(conversion.converted(), "Transducer feeds the DE-only Core from its own Matter/FE buffers");
        truth(conversion.matterConsumed() == 32L, "baseline conversion consumes exactly 32 Matter");
        truth(conversion.forgeEnergyConsumed() == 96L, "baseline conversion consumes exactly 96 FE");
        truth(conversion.dimensionalEnergyProduced() == 1L && state.dimensionalEnergy() == 1L,
                "baseline conversion wirelessly credits exactly 1 DE to the Core");

        truth(CoreControlService.toggleExpansion(state).enabled(), "expansion can be re-enabled");
        System.out.println("CoreControlSelfTest: PASS");
    }

    private static void truth(boolean value, String label) {
        if (!value) throw new AssertionError(label);
    }
}
