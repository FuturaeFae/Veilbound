package dev.futurae.veilbound.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.futurae.veilbound.block.entity.DimensionalCoreBlockEntity;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState;
import dev.futurae.veilbound.domain.CoreTier;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Physical floating-crystal renderer for the personal Domain Core.
 *
 * <p>The visual language intentionally stays constant through progression: the main body and every
 * orbiting fragment are the same prismatic crystal material. Core level changes scale, cluster
 * complexity, fragment count and orbit radius rather than swapping to unrelated monuments. The
 * Nascent Core is deliberately small enough for a 3x3x3 starter Domain; the Transcendent Core grows
 * into the large broken-crystal nexus silhouette used by the concept art.</p>
 */
public final class DimensionalCoreRenderer
        implements BlockEntityRenderer<DimensionalCoreBlockEntity, DimensionalCoreRenderer.RenderState> {

    private static final Color DEEP = new Color(0.20F, 0.055F, 0.43F, 1.0F);
    private static final Color VIOLET = new Color(0.48F, 0.15F, 0.86F, 1.0F);
    private static final Color BLUE = new Color(0.12F, 0.40F, 0.92F, 1.0F);
    private static final Color ICE = new Color(0.55F, 0.78F, 1.00F, 1.0F);
    private static final Color MAGENTA = new Color(0.84F, 0.20F, 0.96F, 1.0F);

    public static final class RenderState extends BlockEntityRenderState {
        private CoreTier tier = CoreTier.NASCENT;
        private long phaseSeed;
    }

    @Override
    public RenderState createRenderState() {
        return new RenderState();
    }

    @Override
    public AABB getRenderBoundingBox(DimensionalCoreBlockEntity blockEntity) {
        var pos = blockEntity.getBlockPos();
        return new AABB(
                pos.getX() - 2.05D, pos.getY() - 0.35D, pos.getZ() - 2.05D,
                pos.getX() + 3.05D, pos.getY() + 4.10D, pos.getZ() + 3.05D);
    }

    @Override
    public void extractRenderState(
            DimensionalCoreBlockEntity blockEntity,
            RenderState state,
            float partialTick,
            Vec3 cameraPos,
            ModelFeatureRenderer.@Nullable CrumblingOverlay crumblingOverlay) {
        BlockEntityRenderer.super.extractRenderState(blockEntity, state, partialTick, cameraPos, crumblingOverlay);
        var level = blockEntity.getLevel();
        if (level != null) {
            var snapshot = VeilBoundaryCollisionState.snapshotFor(level);
            state.tier = snapshot == null ? CoreTier.NASCENT : snapshot.coreTier();
        } else {
            state.tier = CoreTier.NASCENT;
        }
        state.phaseSeed = blockEntity.getBlockPos().asLong();
    }

    @Override
    public void submit(RenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState cameraState) {
        double time = System.nanoTime() / 1_000_000_000.0D;
        double seedPhase = ((state.phaseSeed ^ (state.phaseSeed >>> 32)) & 0xFFFFL) * 0.000091D;
        double phase = time + seedPhase;
        Stage stage = Stage.forTier(state.tier);

        collector.submitCustomGeometry(poseStack, DimensionalCoreRenderPipelines.crystal(), (pose, out) ->
                renderCrystal(out, pose, stage, phase));
        collector.order(1).submitCustomGeometry(poseStack, DimensionalCoreRenderPipelines.glow(), (pose, out) ->
                renderGlow(out, pose, stage, state.tier, phase));
    }

    private static void renderCrystal(VertexConsumer out, PoseStack.Pose pose, Stage stage, double t) {
        double bob = Math.sin(t * 0.78D) * stage.bobAmplitude;
        P center = new P(0.5D, stage.hoverY + stage.height * 0.50D + bob, 0.5D);
        double slowTurn = t * stage.bodySpin;

        V primaryAxis = normalized(new V(
                Math.sin(t * 0.21D) * stage.primaryLean,
                1.0D,
                Math.cos(t * 0.17D) * stage.primaryLean));
        crystalShard(out, pose, center, primaryAxis, stage.height, stage.radius, stage.primarySides,
                slowTurn, DEEP, 0);

        for (int i = 0; i < stage.clusterPieces; i++) {
            double a = slowTurn * 0.65D + i * GOLDEN_ANGLE + 0.55D;
            double radial = stage.radius * (0.38D + 0.10D * (i % 3));
            double vertical = stage.height * (-0.14D + 0.085D * (i % 4));
            P c = new P(
                    center.x + Math.cos(a) * radial,
                    center.y + vertical,
                    center.z + Math.sin(a) * radial);
            V axis = normalized(new V(
                    Math.cos(a) * (0.28D + 0.055D * (i % 2)),
                    1.0D,
                    Math.sin(a) * (0.28D + 0.055D * ((i + 1) % 2))));
            double length = stage.height * (0.46D + 0.055D * (i % 4));
            double radius = stage.radius * (0.35D + 0.035D * (i % 3));
            crystalShard(out, pose, c, axis, length, radius, Math.max(5, stage.primarySides - 1),
                    -slowTurn * 0.33D + i * 0.71D, palette(i + 1), i + 11);
        }

        // Real crystal floaters: same geometry and exact same material path as the central body.
        for (int i = 0; i < stage.fragmentCount; i++) {
            double a = t * stage.orbitSpeed + i * (Math.PI * 2.0D / stage.fragmentCount) + 0.31D;
            double ellipse = 0.90D + 0.10D * Math.sin(i * 1.73D);
            double x = center.x + Math.cos(a) * stage.orbitRadius * ellipse;
            double z = center.z + Math.sin(a) * stage.orbitRadius;
            double y = center.y + Math.sin(a * 1.55D + i * 0.91D) * stage.orbitVertical
                    + Math.cos(a * 0.73D + i) * stage.orbitVertical * 0.22D;
            double size = stage.fragmentLength * (0.76D + 0.10D * (i % 4));
            double spin = -t * (0.32D + 0.035D * (i % 5)) + i * 0.67D;
            V axis = normalized(new V(
                    Math.cos(spin) * (0.28D + 0.05D * (i % 3)),
                    1.0D,
                    Math.sin(spin) * (0.28D + 0.04D * ((i + 1) % 3))));
            crystalShard(out, pose, new P(x, y, z), axis, size,
                    size * (0.20D + 0.015D * (i % 3)), 5 + (i & 1), spin,
                    palette(i + stage.clusterPieces + 3), i + 37);
        }
    }

    private static void renderGlow(VertexConsumer out, PoseStack.Pose pose, Stage stage, CoreTier tier, double t) {
        double bob = Math.sin(t * 0.78D) * stage.bobAmplitude;
        P center = new P(0.5D, stage.hoverY + stage.height * 0.50D + bob, 0.5D);
        float pulse = clamp01(0.72F + 0.16F * (float) Math.sin(t * 1.18D));
        Color inner = new Color(0.70F, 0.19F, 1.00F, 0.64F * pulse);
        Color whiteHot = new Color(0.88F, 0.73F, 1.00F, 0.46F * pulse);

        crystalShard(out, pose, center, new V(0.0D, 1.0D, 0.0D),
                stage.height * 0.58D, stage.radius * 0.34D, 6, -t * 0.16D, inner, 101);
        crystalShard(out, pose, center.add(0.0D, stage.height * 0.035D, 0.0D),
                new V(0.08D, 1.0D, -0.06D), stage.height * 0.36D, stage.radius * 0.18D,
                5, t * 0.23D, whiteHot, 131);

        if (tier.ordinal() >= CoreTier.RESONANT.ordinal()) {
            arc(out, pose, center, stage.orbitRadius * 0.92D, stage.orbitVertical * 0.65D,
                    t * stage.orbitSpeed - 0.35D, 0.82D + 0.12D * tier.ordinal(), 18,
                    new Color(0.57F, 0.18F, 1.00F, 0.21F * pulse), 0.020D + 0.004D * tier.ordinal());
        }
        if (tier.ordinal() >= CoreTier.ASCENDANT.ordinal()) {
            arc(out, pose, center.add(0.0D, stage.height * 0.12D, 0.0D), stage.orbitRadius * 0.76D,
                    stage.orbitVertical * 0.88D, -t * stage.orbitSpeed * 0.72D + 1.7D,
                    1.16D, 22, new Color(0.22F, 0.50F, 1.00F, 0.16F * pulse), 0.018D);
        }
    }

    private static void crystalShard(VertexConsumer out, PoseStack.Pose pose, P center, V axis,
            double length, double radius, int sides, double roll, Color base, int seed) {
        V w = normalized(axis);
        V helper = Math.abs(w.y) < 0.92D ? new V(0.0D, 1.0D, 0.0D) : new V(1.0D, 0.0D, 0.0D);
        V u = normalized(cross(helper, w));
        V v = normalized(cross(w, u));

        P bottomTip = plus(center, scale(w, -length * 0.50D));
        P topTip = plus(center, scale(w, length * 0.50D));
        P lowCenter = plus(center, scale(w, -length * 0.12D));
        P highCenter = plus(center, scale(w, length * 0.17D));

        P[] low = new P[sides];
        P[] high = new P[sides];
        for (int i = 0; i < sides; i++) {
            double a0 = roll + i * (Math.PI * 2.0D / sides);
            double a1 = a0 + 0.13D + 0.025D * ((seed + i) % 3);
            double irregular0 = 0.82D + 0.055D * hashUnit(seed * 31 + i * 17);
            double irregular1 = 0.68D + 0.080D * hashUnit(seed * 47 + i * 29 + 9);
            low[i] = ringPoint(lowCenter, u, v, a0, radius * irregular0);
            high[i] = ringPoint(highCenter, u, v, a1, radius * irregular1);
        }

        for (int i = 0; i < sides; i++) {
            int n = (i + 1) % sides;
            Color face = facetColor(base, seed + i);
            quad(out, pose, bottomTip, low[n], low[i], bottomTip, face.scale(0.72F));
            quad(out, pose, low[i], low[n], high[n], high[i], face);
            quad(out, pose, high[i], high[n], topTip, topTip, face.scale(1.12F));
        }
    }

    private static P ringPoint(P center, V u, V v, double angle, double radius) {
        return new P(
                center.x + (u.x * Math.cos(angle) + v.x * Math.sin(angle)) * radius,
                center.y + (u.y * Math.cos(angle) + v.y * Math.sin(angle)) * radius,
                center.z + (u.z * Math.cos(angle) + v.z * Math.sin(angle)) * radius);
    }

    private static void arc(VertexConsumer out, PoseStack.Pose pose, P center, double radius,
            double vertical, double phase, double sweep, int segments, Color color, double halfWidth) {
        for (int i = 0; i < segments; i++) {
            double f0 = i / (double) segments;
            double f1 = (i + 1) / (double) segments;
            double a0 = phase + sweep * f0;
            double a1 = phase + sweep * f1;
            double fade = Math.sin(Math.PI * (f0 + f1) * 0.5D);
            Color c = color.alpha(color.a * (float) Math.max(0.12D, fade));
            P p0 = new P(center.x + Math.cos(a0) * radius,
                    center.y + Math.sin(a0 * 1.37D) * vertical,
                    center.z + Math.sin(a0) * radius);
            P p1 = new P(center.x + Math.cos(a1) * radius,
                    center.y + Math.sin(a1 * 1.37D) * vertical,
                    center.z + Math.sin(a1) * radius);
            ribbon(out, pose, p0, p1, halfWidth, c);
        }
    }

    private static void ribbon(VertexConsumer out, PoseStack.Pose pose, P a, P b, double half, Color color) {
        double dx = b.x - a.x;
        double dz = b.z - a.z;
        double inv = 1.0D / Math.max(1.0E-6D, Math.sqrt(dx * dx + dz * dz));
        double nx = -dz * inv * half;
        double nz = dx * inv * half;
        quad(out, pose,
                new P(a.x + nx, a.y, a.z + nz),
                new P(b.x + nx, b.y, b.z + nz),
                new P(b.x - nx, b.y, b.z - nz),
                new P(a.x - nx, a.y, a.z - nz), color);
    }

    private static Color facetColor(Color base, int index) {
        Color accent = palette(index);
        float mix = 0.18F + 0.07F * (index % 4);
        return base.mix(accent, mix).scale(0.86F + 0.08F * (index % 3));
    }

    private static Color palette(int index) {
        return switch (Math.floorMod(index, 5)) {
            case 0 -> DEEP;
            case 1 -> VIOLET;
            case 2 -> BLUE;
            case 3 -> ICE;
            default -> MAGENTA;
        };
    }

    private static double hashUnit(int value) {
        int x = value;
        x ^= x >>> 16;
        x *= 0x7feb352d;
        x ^= x >>> 15;
        x *= 0x846ca68b;
        x ^= x >>> 16;
        return (x & 0xFFFF) / 65535.0D;
    }

    private static V cross(V a, V b) {
        return new V(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
    }

    private static V normalized(V v) {
        double len = Math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
        if (len < 1.0E-7D) return new V(0.0D, 1.0D, 0.0D);
        return new V(v.x / len, v.y / len, v.z / len);
    }

    private static V scale(V v, double s) { return new V(v.x * s, v.y * s, v.z * s); }
    private static P plus(P p, V v) { return new P(p.x + v.x, p.y + v.y, p.z + v.z); }

    private static void quad(VertexConsumer out, PoseStack.Pose pose, P a, P b, P c, P d, Color color) {
        vertex(out, pose, a, color); vertex(out, pose, b, color); vertex(out, pose, c, color); vertex(out, pose, d, color);
    }

    private static void vertex(VertexConsumer out, PoseStack.Pose pose, P p, Color color) {
        out.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
                .setUv((float) (p.x * 0.71D + p.z * 0.43D), (float) (p.y * 0.66D + p.x * 0.21D - p.z * 0.17D))
                .setColor(color.r, color.g, color.b, color.a);
    }

    private static float clamp01(float value) { return Math.max(0.0F, Math.min(1.0F, value)); }

    private static final double GOLDEN_ANGLE = Math.PI * (3.0D - Math.sqrt(5.0D));

    private record P(double x, double y, double z) {
        P add(double dx, double dy, double dz) { return new P(x + dx, y + dy, z + dz); }
    }
    private record V(double x, double y, double z) {}
    private record Color(float r, float g, float b, float a) {
        Color scale(float factor) { return new Color(clamp01(r * factor), clamp01(g * factor), clamp01(b * factor), a); }
        Color alpha(float next) { return new Color(r, g, b, clamp01(next)); }
        Color mix(Color other, float amount) {
            float t = clamp01(amount);
            return new Color(r + (other.r - r) * t, g + (other.g - g) * t, b + (other.b - b) * t, a + (other.a - a) * t);
        }
    }

    private record Stage(
            double hoverY,
            double height,
            double radius,
            int primarySides,
            int clusterPieces,
            int fragmentCount,
            double fragmentLength,
            double orbitRadius,
            double orbitVertical,
            double orbitSpeed,
            double bodySpin,
            double bobAmplitude,
            double primaryLean) {
        static Stage forTier(CoreTier tier) {
            return switch (tier) {
                case NASCENT -> new Stage(0.27D, 0.78D, 0.22D, 6, 2, 3, 0.15D,
                        0.38D, 0.13D, 0.38D, 0.085D, 0.025D, 0.035D);
                case ANCHORED -> new Stage(0.23D, 1.16D, 0.31D, 7, 3, 5, 0.24D,
                        0.56D, 0.22D, 0.34D, 0.075D, 0.030D, 0.045D);
                case RESONANT -> new Stage(0.19D, 1.68D, 0.43D, 7, 5, 7, 0.34D,
                        0.78D, 0.34D, 0.30D, 0.064D, 0.035D, 0.055D);
                case ASCENDANT -> new Stage(0.15D, 2.24D, 0.57D, 8, 7, 9, 0.48D,
                        1.05D, 0.49D, 0.27D, 0.055D, 0.040D, 0.065D);
                case TRANSCENDENT -> new Stage(0.11D, 3.02D, 0.73D, 9, 9, 12, 0.62D,
                        1.39D, 0.68D, 0.24D, 0.047D, 0.045D, 0.075D);
            };
        }
    }
}
