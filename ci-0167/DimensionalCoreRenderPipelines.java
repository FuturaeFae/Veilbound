package dev.futurae.veilbound.client.render;

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

/** Dedicated physical-crystal material pipelines for the evolving Domain Core. */
public final class DimensionalCoreRenderPipelines {
    private static final Identifier SHADER = Identifier.fromNamespaceAndPath(
            Veilbound.MOD_ID, "core/dimensional_core");

    public static final RenderPipeline CRYSTAL_PIPELINE = RenderPipeline.builder()
            .withLocation(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "pipeline/dimensional_core_crystal"))
            .withVertexShader(SHADER)
            .withFragmentShader(SHADER)
            .withBindGroupLayout(BindGroupLayouts.MATRICES_PROJECTION)
            .withCull(false)
            .withDepthStencilState(new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, true, 0.0F, 0.0F))
            .withVertexBinding(0, DefaultVertexFormat.POSITION_TEX_COLOR)
            .withPrimitiveTopology(PrimitiveTopology.QUADS)
            .build();

    public static final RenderPipeline GLOW_PIPELINE = RenderPipeline.builder()
            .withLocation(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "pipeline/dimensional_core_glow"))
            .withVertexShader(SHADER)
            .withFragmentShader(SHADER)
            .withBindGroupLayout(BindGroupLayouts.MATRICES_PROJECTION)
            .withColorTargetState(new ColorTargetState(BlendFunction.TRANSLUCENT))
            .withCull(false)
            .withDepthStencilState(new DepthStencilState(CompareOp.GREATER_THAN_OR_EQUAL, false, 0.0F, 0.0F))
            .withVertexBinding(0, DefaultVertexFormat.POSITION_TEX_COLOR)
            .withPrimitiveTopology(PrimitiveTopology.QUADS)
            .build();

    private static final RenderType CRYSTAL = RenderType.create(
            "veilbound:dimensional_core_crystal",
            RenderSetup.builder(CRYSTAL_PIPELINE).createRenderSetup());
    private static final RenderType GLOW = RenderType.create(
            "veilbound:dimensional_core_glow",
            RenderSetup.builder(GLOW_PIPELINE).sortOnUpload().createRenderSetup());

    private DimensionalCoreRenderPipelines() {}

    public static void register(RegisterRenderPipelinesEvent event) {
        event.registerPipeline(CRYSTAL_PIPELINE);
        event.registerPipeline(GLOW_PIPELINE);
    }

    public static RenderType crystal() { return CRYSTAL; }
    public static RenderType glow() { return GLOW; }
}
