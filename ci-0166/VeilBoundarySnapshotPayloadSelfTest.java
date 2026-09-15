package dev.futurae.veilbound.network;

import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState;
import dev.futurae.veilbound.domain.DomainBounds;
import dev.futurae.veilbound.domain.CoreTier;
import java.util.List;
import net.minecraft.world.phys.AABB;

/** Regression for snapshot axis order and the centered 3x3x3 first-release starter shell. */
public final class VeilBoundarySnapshotPayloadSelfTest {
    public static void main(String[] args) {
        DomainBounds starter = DomainBounds.initial();
        VeilBoundarySnapshotPayload starterPayload = payload(starter);
        eq(starter, starterPayload.bounds(), "starter snapshot must preserve X/Y/Z bound order");
        eq(3, starterPayload.bounds().sizeX(), "starter X size");
        eq(3, starterPayload.bounds().sizeY(), "starter Y size");
        eq(3, starterPayload.bounds().sizeZ(), "starter Z size");

        DomainBounds asymmetric = new DomainBounds(-7, -3, -11, 12, 19, 5);
        eq(asymmetric, payload(asymmetric).bounds(), "asymmetric bounds must round-trip without axis permutation");

        // First-release arrival is beside the Core at x=1.5, z=.5 with feet at y=-1,
        // standing on the lower Veil membrane. No side/ceiling wall may embed that player.
        AABB standingPlayer = new AABB(1.2D, -1.0D, 0.2D, 1.8D, 0.8D, 0.8D);
        for (AABB wall : VeilBoundaryCollisionState.wallBoxes(starterPayload.bounds())) {
            truth(!wall.intersects(standingPlayer), "starter player must not spawn embedded in wall " + wall);
        }

        var shell = VeilBoundaryCollisionState.shellBounds(starterPayload.bounds());
        eq(-1.30D, shell.minX(), "starter shell gives half-player clearance on -X");
        eq(2.30D, shell.maxX(), "starter shell gives half-player clearance on +X");
        eq(-1.30D, shell.minZ(), "starter shell gives half-player clearance on -Z");
        eq(2.30D, shell.maxZ(), "starter shell gives half-player clearance on +Z");
        eq(-1.0D, shell.minY(), "starter lower membrane matches the 3x3x3 floor boundary");
        eq(2.40D, shell.maxY(), "starter shell gives normal jump headroom");

        List<AABB> walls = VeilBoundaryCollisionState.wallBoxes(starterPayload.bounds());
        eq(2.40D, walls.get(3).minY, "starter positive-Y wall begins above jump headroom");
        eq(2.30D, walls.get(1).minX, "starter positive-X wall is body-clear of the outer build cell");
        eq(2.30D, walls.get(5).minZ, "starter positive-Z wall is body-clear of the outer build cell");

        AABB westEdgePlayer = new AABB(-1.30D, -1.0D, 0.20D, -0.70D, 0.8D, 0.80D);
        AABB eastEdgePlayer = new AABB(1.70D, -1.0D, 0.20D, 2.30D, 0.8D, 0.80D);
        AABB jumpingPlayer = new AABB(0.20D, 0.42D, 0.20D, 0.80D, 2.22D, 0.80D);
        truth(!walls.get(0).intersects(westEdgePlayer), "player center must be able to reach west edge of starter Domain");
        truth(!walls.get(1).intersects(eastEdgePlayer), "player center must be able to reach east edge of starter Domain");
        truth(!walls.get(3).intersects(jumpingPlayer), "normal jump must fit below starter ceiling membrane");
        System.out.println("VeilBoundarySnapshotPayloadSelfTest: PASS");
    }

    private static VeilBoundarySnapshotPayload payload(DomainBounds b) {
        return new VeilBoundarySnapshotPayload(
                "veilbound:domain/test",
                b.minX(), b.maxX(), b.minY(), b.maxY(), b.minZ(), b.maxZ(),
                0.0D, CoreTier.NASCENT, 1.0D, List.of());
    }

    private static void truth(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void eq(Object expected, Object actual, String message) {
        if (!expected.equals(actual)) throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
    }

    private static void eq(int expected, int actual, String message) {
        if (expected != actual) throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
    }

    private static void eq(double expected, double actual, String message) {
        if (Double.compare(expected, actual) != 0) throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
    }
}
