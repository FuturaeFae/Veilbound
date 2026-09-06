#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0144-black-boundary-fog.py <source-root>')
root = Path(sys.argv[1]).resolve()

# Version
p = root / 'gradle.properties'
s = p.read_text()
if 'mod_version=0.1.43-dev' not in s:
    raise SystemExit('Expected 0.1.43-dev version marker not found')
p.write_text(s.replace('mod_version=0.1.43-dev', 'mod_version=0.1.44-dev', 1))

# Opaque black wall pipeline.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderPipeline.java'
p.write_text(r'''package dev.futurae.veilbound.client.render;

import com.mojang.blaze3d.PrimitiveTopology;
import com.mojang.blaze3d.pipeline.DepthStencilState;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.platform.CompareOp;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import dev.futurae.veilbound.Veilbound;
import net.minecraft.client.renderer.BindGroupLayouts;
import net.minecraft.client.renderer.rendertype.RenderSetup;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.client.event.RegisterRenderPipelinesEvent;

/** Fully opaque, pure-black render pipeline for the physical personal-Domain shell. */
public final class VeilBoundaryRenderPipeline {
    public static final RenderPipeline PIPELINE = RenderPipeline.builder()
            .withLocation(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "pipeline/veil_boundary"))
            .withVertexShader(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "core/veil_boundary"))
            .withFragmentShader(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "core/veil_boundary"))
            .withBindGroupLayout(BindGroupLayouts.MATRICES_PROJECTION)
            .withCull(false)
            .withDepthStencilState(new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, true, 0.0F, 0.0F))
            .withVertexBinding(0, DefaultVertexFormat.POSITION_TEX_COLOR)
            .withPrimitiveTopology(PrimitiveTopology.QUADS)
            .build();

    private static final RenderType TYPE = RenderType.create(
            "veilbound:veil_boundary",
            RenderSetup.builder(PIPELINE).createRenderSetup());

    private VeilBoundaryRenderPipeline() {}

    public static void register(RegisterRenderPipelinesEvent event) {
        event.registerPipeline(PIPELINE);
    }

    public static RenderType type() {
        return TYPE;
    }
}
''')

# Dedicated translucent volume-slice pipeline for fog emitted inward by every face.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryFogRenderPipeline.java'
p.write_text(r'''package dev.futurae.veilbound.client.render;

import com.mojang.blaze3d.PrimitiveTopology;
import com.mojang.blaze3d.pipeline.BlendFunction;
import com.mojang.blaze3d.pipeline.ColorTargetState;
import com.mojang.blaze3d.pipeline.DepthStencilState;
import com.mojang.blaze3d.pipeline.RenderPipeline;
import com.mojang.blaze3d.platform.CompareOp;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import dev.futurae.veilbound.Veilbound;
import net.minecraft.client.renderer.BindGroupLayouts;
import net.minecraft.client.renderer.rendertype.RenderSetup;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.resources.Identifier;
import net.neoforged.neoforge.client.event.RegisterRenderPipelinesEvent;

/** Translucent world-anchored slice pipeline used to build genuine spatial Veil fog volume. */
public final class VeilBoundaryFogRenderPipeline {
    public static final RenderPipeline PIPELINE = RenderPipeline.builder()
            .withLocation(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "pipeline/veil_boundary_fog"))
            .withVertexShader(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "core/veil_boundary_fog"))
            .withFragmentShader(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "core/veil_boundary_fog"))
            .withBindGroupLayout(BindGroupLayouts.MATRICES_PROJECTION)
            .withColorTargetState(new ColorTargetState(BlendFunction.TRANSLUCENT))
            .withCull(false)
            .withDepthStencilState(new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, false, 0.0F, 0.0F))
            .withVertexBinding(0, DefaultVertexFormat.POSITION_TEX_COLOR)
            .withPrimitiveTopology(PrimitiveTopology.QUADS)
            .build();

    private static final RenderType TYPE = RenderType.create(
            "veilbound:veil_boundary_fog",
            RenderSetup.builder(PIPELINE)
                    .sortOnUpload()
                    .createRenderSetup());

    private VeilBoundaryFogRenderPipeline() {}

    public static void register(RegisterRenderPipelinesEvent event) {
        event.registerPipeline(PIPELINE);
    }

    public static RenderType type() {
        return TYPE;
    }
}
''')

# Renderer: exact same density from all six walls, volumetric depth from stacked world-space slices,
# and deliberately extended face tangents so no microscopic corner/edge slit can show through.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java'
p.write_text(r'''package dev.futurae.veilbound.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.futurae.veilbound.Veilbound;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.BreachOpening;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.ShellBounds;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.Snapshot;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import net.minecraft.util.context.ContextKey;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.client.event.ExtractLevelRenderStateEvent;
import net.neoforged.neoforge.client.event.SubmitCustomGeometryEvent;

/**
 * Renders a sealed black Veil shell plus a real inward fog volume.
 *
 * <p>The shell itself is deliberately visually simple: pure black, fully opaque and incapable of
 * leaking sky/world pixels. Atmospheric depth is supplied by twenty world-anchored fog slices from
 * every face. Every face uses exactly the same depth, layer count and density curve. Face geometry
 * extends slightly beyond every tangential edge so adjacent faces overlap and cannot expose a
 * sub-pixel crack at corners.</p>
 */
public final class VeilBoundaryRenderer {
    private static final ContextKey<Snapshot> RENDER_STATE_KEY = new ContextKey<>(
            Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "veil_boundary_render_state"));
    private static final double SURFACE_EPSILON = 0.002D;
    /** Extra visual length past each edge, intentionally overlapping adjoining boundary faces. */
    private static final double EDGE_OVERLAP = 0.10D;
    private static final double FOG_DEPTH = 3.00D;
    private static final int FOG_LAYERS = 20;
    private static final float FOG_WALL_ALPHA = 0.105F;

    private VeilBoundaryRenderer() {}

    public static void onExtractLevelRenderState(ExtractLevelRenderStateEvent event) {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level == null) return;
        Snapshot snapshot = VeilBoundaryCollisionState.clientSnapshot(
                minecraft.level.dimension().identifier().toString());
        if (snapshot != null) event.getRenderState().setRenderData(RENDER_STATE_KEY, snapshot);
    }

    public static void onSubmitCustomGeometry(SubmitCustomGeometryEvent event) {
        Snapshot snapshot = event.getLevelRenderState().getRenderData(RENDER_STATE_KEY);
        if (snapshot == null) return;

        PoseStack poseStack = event.getPoseStack();
        Vec3 camera = event.getLevelRenderState().cameraRenderState.pos;
        ShellBounds shell = VeilBoundaryCollisionState.shellBounds(snapshot.bounds());
        float time = (float) ((System.nanoTime() % 240_000_000_000L) / 1_000_000_000.0D * 0.0125D);
        float fracture = (float) Math.min(1.0D, snapshot.fractureMeter() / 200.0D);

        poseStack.pushPose();
        poseStack.translate(-camera.x, -camera.y, -camera.z);
        var collector = event.getSubmitNodeCollector();

        collector.submitCustomGeometry(poseStack, VeilBoundaryRenderPipeline.type(), (pose, out) ->
                renderOpaqueShell(out, pose, shell));

        collector.submitCustomGeometry(poseStack, VeilBoundaryFogRenderPipeline.type(), (pose, out) ->
                renderFogVolume(out, pose, shell, time, fracture));

        if (!snapshot.openBreaches().isEmpty()) {
            collector.submitCustomGeometry(poseStack, VeilBoundaryFogRenderPipeline.type(), (pose, out) -> {
                for (BreachOpening breach : snapshot.openBreaches()) {
                    renderBreachMist(out, pose, breach, shell, time, fracture);
                }
            });
        }

        poseStack.popPose();
    }

    private static void renderOpaqueShell(VertexConsumer out, PoseStack.Pose pose, ShellBounds s) {
        double minX = s.minX();
        double maxX = s.maxX();
        double minY = s.minY();
        double maxY = s.maxY();
        double minZ = s.minZ();
        double maxZ = s.maxZ();
        int black = 0xFFFFFFFF;

        quadX(out, pose, minX + SURFACE_EPSILON, minY - EDGE_OVERLAP, maxY + EDGE_OVERLAP, minZ - EDGE_OVERLAP, maxZ + EDGE_OVERLAP, 0.0F, 0.0F, black, false);
        quadX(out, pose, maxX - SURFACE_EPSILON, minY - EDGE_OVERLAP, maxY + EDGE_OVERLAP, minZ - EDGE_OVERLAP, maxZ + EDGE_OVERLAP, 0.0F, 0.0F, black, true);
        quadY(out, pose, minY + SURFACE_EPSILON, minX - EDGE_OVERLAP, maxX + EDGE_OVERLAP, minZ - EDGE_OVERLAP, maxZ + EDGE_OVERLAP, 0.0F, 0.0F, black, true);
        quadY(out, pose, maxY - SURFACE_EPSILON, minX - EDGE_OVERLAP, maxX + EDGE_OVERLAP, minZ - EDGE_OVERLAP, maxZ + EDGE_OVERLAP, 0.0F, 0.0F, black, false);
        quadZ(out, pose, minZ + SURFACE_EPSILON, minX - EDGE_OVERLAP, maxX + EDGE_OVERLAP, minY - EDGE_OVERLAP, maxY + EDGE_OVERLAP, 0.0F, 0.0F, black, true);
        quadZ(out, pose, maxZ - SURFACE_EPSILON, minX - EDGE_OVERLAP, maxX + EDGE_OVERLAP, minY - EDGE_OVERLAP, maxY + EDGE_OVERLAP, 0.0F, 0.0F, black, false);
    }

    private static void renderFogVolume(VertexConsumer out, PoseStack.Pose pose, ShellBounds s, float time, float fracture) {
        for (int layer = 0; layer < FOG_LAYERS; layer++) {
            float depth01 = (layer + 0.5F) / FOG_LAYERS;
            double distance = 0.035D + depth01 * FOG_DEPTH;
            float falloff = (float) Math.pow(1.0F - depth01, 1.35D);
            float alpha = FOG_WALL_ALPHA * falloff;
            int control = rgba(fracture, 1.0F - depth01, 1.0F, alpha);

            fogQuadX(out, pose, s.minX() + distance, s.minY() - EDGE_OVERLAP, s.maxY() + EDGE_OVERLAP, s.minZ() - EDGE_OVERLAP, s.maxZ() + EDGE_OVERLAP, time, depth01, control, false);
            fogQuadX(out, pose, s.maxX() - distance, s.minY() - EDGE_OVERLAP, s.maxY() + EDGE_OVERLAP, s.minZ() - EDGE_OVERLAP, s.maxZ() + EDGE_OVERLAP, time, depth01, control, true);
            fogQuadY(out, pose, s.minY() + distance, s.minX() - EDGE_OVERLAP, s.maxX() + EDGE_OVERLAP, s.minZ() - EDGE_OVERLAP, s.maxZ() + EDGE_OVERLAP, time, depth01, control, true);
            fogQuadY(out, pose, s.maxY() - distance, s.minX() - EDGE_OVERLAP, s.maxX() + EDGE_OVERLAP, s.minZ() - EDGE_OVERLAP, s.maxZ() + EDGE_OVERLAP, time, depth01, control, false);
            fogQuadZ(out, pose, s.minZ() + distance, s.minX() - EDGE_OVERLAP, s.maxX() + EDGE_OVERLAP, s.minY() - EDGE_OVERLAP, s.maxY() + EDGE_OVERLAP, time, depth01, control, true);
            fogQuadZ(out, pose, s.maxZ() - distance, s.minX() - EDGE_OVERLAP, s.maxX() + EDGE_OVERLAP, s.minY() - EDGE_OVERLAP, s.maxY() + EDGE_OVERLAP, time, depth01, control, false);
        }
    }

    private static void renderBreachMist(VertexConsumer out, PoseStack.Pose pose, BreachOpening breach, ShellBounds shell, float time, float fracture) {
        double radius = switch (breach.severity()) {
            case MINOR -> 1.05D;
            case SEVERE -> 1.70D;
            case EXTREME -> 2.35D;
        };
        double x = breach.position().x() + 0.5D;
        double y = breach.position().y() + 0.5D;
        double z = breach.position().z() + 0.5D;
        int color = rgba(Math.max(fracture, 0.82F), 0.0F, 1.0F, 0.20F);
        switch (breach.face()) {
            case NEGATIVE_X -> fogQuadX(out, pose, shell.minX() + 0.045D, y - radius, y + radius, z - radius, z + radius, time, 0.0F, color, false);
            case POSITIVE_X -> fogQuadX(out, pose, shell.maxX() - 0.045D, y - radius, y + radius, z - radius, z + radius, time, 0.0F, color, true);
            case NEGATIVE_Y -> fogQuadY(out, pose, shell.minY() + 0.045D, x - radius, x + radius, z - radius, z + radius, time, 0.0F, color, true);
            case POSITIVE_Y -> fogQuadY(out, pose, shell.maxY() - 0.045D, x - radius, x + radius, z - radius, z + radius, time, 0.0F, color, false);
            case NEGATIVE_Z -> fogQuadZ(out, pose, shell.minZ() + 0.045D, x - radius, x + radius, y - radius, y + radius, time, 0.0F, color, true);
            case POSITIVE_Z -> fogQuadZ(out, pose, shell.maxZ() - 0.045D, x - radius, x + radius, y - radius, y + radius, time, 0.0F, color, false);
        }
    }

    private static void fogQuadX(VertexConsumer out, PoseStack.Pose pose, double x, double minY, double maxY, double minZ, double maxZ, float time, float depth, int color, boolean flip) { quadX(out, pose, x, minY, maxY, minZ, maxZ, time, depth, color, flip); }
    private static void fogQuadY(VertexConsumer out, PoseStack.Pose pose, double y, double minX, double maxX, double minZ, double maxZ, float time, float depth, int color, boolean flip) { quadY(out, pose, y, minX, maxX, minZ, maxZ, time, depth, color, flip); }
    private static void fogQuadZ(VertexConsumer out, PoseStack.Pose pose, double z, double minX, double maxX, double minY, double maxY, float time, float depth, int color, boolean flip) { quadZ(out, pose, z, minX, maxX, minY, maxY, time, depth, color, flip); }

    private static void quadX(VertexConsumer out, PoseStack.Pose pose, double x, double minY, double maxY, double minZ, double maxZ, float u, float v, int color, boolean flip) {
        if (flip) {
            vertex(out, pose, x, minY, minZ, u, v, color); vertex(out, pose, x, minY, maxZ, u, v, color); vertex(out, pose, x, maxY, maxZ, u, v, color); vertex(out, pose, x, maxY, minZ, u, v, color);
        } else {
            vertex(out, pose, x, minY, maxZ, u, v, color); vertex(out, pose, x, minY, minZ, u, v, color); vertex(out, pose, x, maxY, minZ, u, v, color); vertex(out, pose, x, maxY, maxZ, u, v, color);
        }
    }
    private static void quadY(VertexConsumer out, PoseStack.Pose pose, double y, double minX, double maxX, double minZ, double maxZ, float u, float v, int color, boolean flip) {
        if (flip) {
            vertex(out, pose, minX, y, maxZ, u, v, color); vertex(out, pose, maxX, y, maxZ, u, v, color); vertex(out, pose, maxX, y, minZ, u, v, color); vertex(out, pose, minX, y, minZ, u, v, color);
        } else {
            vertex(out, pose, minX, y, minZ, u, v, color); vertex(out, pose, maxX, y, minZ, u, v, color); vertex(out, pose, maxX, y, maxZ, u, v, color); vertex(out, pose, minX, y, maxZ, u, v, color);
        }
    }
    private static void quadZ(VertexConsumer out, PoseStack.Pose pose, double z, double minX, double maxX, double minY, double maxY, float u, float v, int color, boolean flip) {
        if (flip) {
            vertex(out, pose, maxX, minY, z, u, v, color); vertex(out, pose, minX, minY, z, u, v, color); vertex(out, pose, minX, maxY, z, u, v, color); vertex(out, pose, maxX, maxY, z, u, v, color);
        } else {
            vertex(out, pose, minX, minY, z, u, v, color); vertex(out, pose, maxX, minY, z, u, v, color); vertex(out, pose, maxX, maxY, z, u, v, color); vertex(out, pose, minX, maxY, z, u, v, color);
        }
    }
    private static void vertex(VertexConsumer out, PoseStack.Pose pose, double x, double y, double z, float u, float v, int color) { out.addVertex(pose, (float) x, (float) y, (float) z).setUv(u, v).setColor(color); }
    private static int rgba(float r, float g, float b, float a) {
        int ai = Math.round(clamp01(a) * 255.0F); int ri = Math.round(clamp01(r) * 255.0F); int gi = Math.round(clamp01(g) * 255.0F); int bi = Math.round(clamp01(b) * 255.0F);
        return (ai << 24) | (ri << 16) | (gi << 8) | bi;
    }
    private static float clamp01(float value) { return Math.max(0.0F, Math.min(1.0F, value)); }
}
''')

# Pure-black fully opaque boundary shader.
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary.vsh'
p.write_text(r'''#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:projection.glsl>

in vec3 Position;
in vec2 UV0;
in vec4 Color;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
}
''')
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary.fsh'
p.write_text(r'''#version 330

out vec4 fragColor;

void main() {
    fragColor = vec4(0.0, 0.0, 0.0, 1.0);
}
''')

# Fog vertex + fragment shaders. World-position noise remains anchored while the camera moves.
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.vsh'
p.write_text(r'''#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:projection.glsl>

in vec3 Position;
in vec2 UV0;
in vec4 Color;
out vec3 fogWorldPos;
out vec2 fogControl;
out vec4 fogColor;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    fogWorldPos = Position;
    fogControl = UV0;
    fogColor = Color;
}
''')
p = root / 'src/main/resources/assets/veilbound/shaders/core/veil_boundary_fog.fsh'
p.write_text(r'''#version 330

in vec3 fogWorldPos;
in vec2 fogControl;
in vec4 fogColor;
out vec4 fragColor;

float hash13(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}
float noise3(vec3 p) {
    vec3 i = floor(p); vec3 f = fract(p); f = f * f * (3.0 - 2.0 * f);
    float n000 = hash13(i + vec3(0,0,0)); float n100 = hash13(i + vec3(1,0,0));
    float n010 = hash13(i + vec3(0,1,0)); float n110 = hash13(i + vec3(1,1,0));
    float n001 = hash13(i + vec3(0,0,1)); float n101 = hash13(i + vec3(1,0,1));
    float n011 = hash13(i + vec3(0,1,1)); float n111 = hash13(i + vec3(1,1,1));
    float nx00 = mix(n000, n100, f.x); float nx10 = mix(n010, n110, f.x);
    float nx01 = mix(n001, n101, f.x); float nx11 = mix(n011, n111, f.x);
    return mix(mix(nx00, nx10, f.y), mix(nx01, nx11, f.y), f.z);
}
float fbm(vec3 p) {
    float sum = 0.0; float amp = 0.52;
    for (int i = 0; i < 5; ++i) { sum += noise3(p) * amp; p = p * 2.07 + vec3(7.13, -4.91, 9.77); amp *= 0.48; }
    return sum;
}
void main() {
    float time = fogControl.x;
    float depth01 = clamp(fogControl.y, 0.0, 1.0);
    vec3 p = fogWorldPos * 0.34;
    vec3 drift = vec3(time * 0.31, -time * 0.17, time * 0.23);
    float broad = fbm(p + drift);
    float detail = fbm(p * 1.85 - drift * 0.57 + vec3(13.2, -7.8, 3.4));
    float wisps = fbm(p * 3.25 + drift * 0.29 + vec3(-5.1, 8.7, 11.6));
    float smoke = smoothstep(0.30, 0.82, broad * 0.56 + detail * 0.31 + wisps * 0.13);
    float fracture = fogColor.r;
    float wallFalloff = pow(1.0 - depth01, 1.25);
    float alpha = fogColor.a * wallFalloff * (0.28 + smoke * 0.92);
    vec3 base = vec3(0.006, 0.005, 0.010);
    vec3 violet = vec3(0.045, 0.016, 0.065);
    vec3 color = mix(base, violet, smoke * (0.55 + fracture * 0.20));
    alpha = clamp(alpha, 0.0, 0.24);
    fragColor = vec4(color, alpha);
}
''')

# Register the fog pipeline beside the solid shell pipeline.
p = root / 'src/main/java/dev/futurae/veilbound/client/VeilboundClient.java'
s = p.read_text()
if 'VeilBoundaryFogRenderPipeline' not in s:
    s = s.replace('import dev.futurae.veilbound.client.render.VeilBoundaryRenderPipeline;\n', 'import dev.futurae.veilbound.client.render.VeilBoundaryRenderPipeline;\nimport dev.futurae.veilbound.client.render.VeilBoundaryFogRenderPipeline;\n', 1)
if 'VeilBoundaryFogRenderPipeline::register' not in s:
    s = s.replace('        modBus.addListener(VeilBoundaryRenderPipeline::register);\n', '        modBus.addListener(VeilBoundaryRenderPipeline::register);\n        modBus.addListener(VeilBoundaryFogRenderPipeline::register);\n', 1)
p.write_text(s)

# Document visual contract.
p = root / 'README.md'
s = p.read_text()
marker = '## 0.1.44-dev — Opaque Veil shell and boundary fog\n'
if marker not in s:
    s += r'''

## 0.1.44-dev — Opaque Veil shell and boundary fog

- The personal-Domain boundary is now a completely opaque pure-black shell. Outside sky/world pixels cannot show through it.
- Atmospheric depth is separated from the wall itself: twenty translucent world-anchored slices occupy three blocks of inward depth and create rolling Veil fog with actual spatial parallax.
- Every one of the six faces emits exactly the same fog depth, layer count and baseline density curve.
- Visual boundary faces extend 0.10 blocks beyond every tangential edge so adjoining faces intentionally overlap; this removes tiny corner slits and rasterization gaps without changing physical collision bounds.
- Fog motion is time-driven in stable world coordinates rather than camera-relative coordinates, avoiding the prior motion-sickness-inducing swimming effect.
- Vanilla Domain clouds remain permanently disabled and environment Memories remain independent of the sealed Veil shell/fog system.
'''
p.write_text(s)

print('Applied 0.1.44 opaque black Veil shell, edge overlap, and uniform inward fog volume')