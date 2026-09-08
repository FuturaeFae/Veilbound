from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
java = root / 'src/main/java'

payload_path = java / 'dev/futurae/veilbound/network/DomainVisualEffectPayload.java'
payload_path.parent.mkdir(parents=True, exist_ok=True)
payload_path.write_text(r'''package dev.futurae.veilbound.network;

import dev.futurae.veilbound.Veilbound;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

/** Server-authoritative client visual cue for Domain travel and first binding. */
public record DomainVisualEffectPayload(Effect effect) implements CustomPacketPayload {
    public enum Effect { ENTER, EXIT, BIND }

    public static final Type<DomainVisualEffectPayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "domain_visual_effect"));
    public static final StreamCodec<RegistryFriendlyByteBuf, DomainVisualEffectPayload> STREAM_CODEC = new StreamCodec<>() {
        @Override public DomainVisualEffectPayload decode(RegistryFriendlyByteBuf buffer) {
            int ordinal = buffer.readUnsignedByte();
            Effect[] values = Effect.values();
            return new DomainVisualEffectPayload(values[Math.min(ordinal, values.length - 1)]);
        }
        @Override public void encode(RegistryFriendlyByteBuf buffer, DomainVisualEffectPayload payload) {
            buffer.writeByte(payload.effect().ordinal());
        }
    };

    public DomainVisualEffectPayload {
        effect = effect == null ? Effect.ENTER : effect;
    }

    public static DomainVisualEffectPayload enter() { return new DomainVisualEffectPayload(Effect.ENTER); }
    public static DomainVisualEffectPayload exit() { return new DomainVisualEffectPayload(Effect.EXIT); }
    public static DomainVisualEffectPayload bind() { return new DomainVisualEffectPayload(Effect.BIND); }

    @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
}
''', encoding='utf-8')

overlay_path = java / 'dev/futurae/veilbound/client/render/DomainTransitionOverlay.java'
overlay_path.parent.mkdir(parents=True, exist_ok=True)
overlay_path.write_text(r'''package dev.futurae.veilbound.client.render;

import dev.futurae.veilbound.network.DomainVisualEffectPayload;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;

/**
 * Full-screen Veil transition. It intentionally uses only Minecraft's GUI extraction pipeline so
 * the effect works with both the OpenGL and Vulkan render backends in 26.2.
 */
public final class DomainTransitionOverlay {
    private static final long TRAVEL_DURATION_NANOS = 950_000_000L;
    private static final long BIND_DURATION_NANOS = 2_150_000_000L;
    private static final int BLACK = 0x000000;
    private static final int DEEP_PURPLE = 0x240046;
    private static final int VEIL_PURPLE = 0x5A189A;
    private static final int BRIGHT_PURPLE = 0x9D4EDD;

    private static DomainVisualEffectPayload.Effect active;
    private static long startedNanos;

    private DomainTransitionOverlay() {}

    public static void start(DomainVisualEffectPayload.Effect effect) {
        active = effect == null ? DomainVisualEffectPayload.Effect.ENTER : effect;
        startedNanos = System.nanoTime();
    }

    public static void clear() {
        active = null;
        startedNanos = 0L;
    }

    public static boolean active() { return active != null; }

    public static void render(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
        DomainVisualEffectPayload.Effect effect = active;
        if (effect == null) return;

        long duration = effect == DomainVisualEffectPayload.Effect.BIND ? BIND_DURATION_NANOS : TRAVEL_DURATION_NANOS;
        double progress = (System.nanoTime() - startedNanos) / (double) duration;
        if (progress >= 1.0D) {
            clear();
            return;
        }
        if (progress < 0.0D) progress = 0.0D;

        Minecraft minecraft = Minecraft.getInstance();
        int width = minecraft.getWindow().getGuiScaledWidth();
        int height = minecraft.getWindow().getGuiScaledHeight();
        if (width <= 0 || height <= 0) return;

        float t = (float) progress;
        float envelope = (float) Math.pow(Math.sin(Math.PI * t), effect == DomainVisualEffectPayload.Effect.BIND ? 0.72D : 0.62D);
        float cx = width * 0.5F;
        float cy = height * 0.5F;
        int radius = (int) Math.ceil(Math.hypot(width, height)) + 48;

        // Dark veil first: strongest around the actual transition, but never a hard flash.
        int blackAlpha = clampAlpha((effect == DomainVisualEffectPayload.Effect.BIND ? 210F : 226F) * envelope);
        graphics.fill(0, 0, width, height, argb(blackAlpha, BLACK));

        drawEdgeVignette(graphics, width, height, envelope, effect == DomainVisualEffectPayload.Effect.BIND);
        drawVortex(graphics, cx, cy, radius, t, envelope, effect);

        if (effect == DomainVisualEffectPayload.Effect.BIND) {
            drawBindingCollapse(graphics, cx, cy, radius, t, envelope);
        } else {
            drawTravelIris(graphics, cx, cy, radius, t, envelope, effect == DomainVisualEffectPayload.Effect.ENTER);
        }
    }

    private static void drawVortex(
            GuiGraphicsExtractor graphics,
            float cx,
            float cy,
            int radius,
            float t,
            float envelope,
            DomainVisualEffectPayload.Effect effect) {
        float direction = effect == DomainVisualEffectPayload.Effect.EXIT ? -1.0F : 1.0F;
        float spin = direction * (0.45F + t * (effect == DomainVisualEffectPayload.Effect.BIND ? 5.4F : 4.1F));
        int ribbons = effect == DomainVisualEffectPayload.Effect.BIND ? 24 : 18;

        var pose = graphics.pose();
        for (int i = 0; i < ribbons; i++) {
            float phase = i / (float) ribbons;
            float wave = (float) Math.sin((phase * Math.PI * 2.0) + t * 8.0F);
            float angle = spin + phase * (float) (Math.PI * 2.0);
            int thickness = Math.max(2, Math.round((3.0F + 7.0F * envelope) * (0.72F + 0.28F * wave)));
            int alpha = clampAlpha((effect == DomainVisualEffectPayload.Effect.BIND ? 104F : 124F)
                    * envelope * (0.55F + 0.45F * (1.0F - phase)));
            int rgb = (i % 3 == 0) ? BRIGHT_PURPLE : (i % 2 == 0 ? VEIL_PURPLE : DEEP_PURPLE);

            pose.pushMatrix();
            pose.translate(cx, cy);
            pose.rotate(angle);
            float breathing = 0.82F + 0.18F * (float) Math.sin(t * Math.PI * 2.0F + phase * 4.0F);
            pose.scale(1.0F, breathing);
            graphics.fill(-radius, -thickness, radius, thickness, argb(alpha, rgb));
            pose.popMatrix();
        }
    }

    private static void drawTravelIris(
            GuiGraphicsExtractor graphics, float cx, float cy, int radius, float t, float envelope, boolean entering) {
        // Concentric rotating square-rings make the screen feel as though it is being pulled through
        // the Veil instead of merely fading to a color.
        var pose = graphics.pose();
        for (int ring = 0; ring < 7; ring++) {
            float offset = ring / 7.0F;
            float motion = entering ? (1.0F - t) : t;
            float scale = 0.16F + ((offset + motion * 0.72F) % 1.0F) * 1.28F;
            int half = Math.max(10, Math.round(radius * scale));
            int thickness = Math.max(2, Math.round(4.0F + 8.0F * envelope * (1.0F - offset)));
            int alpha = clampAlpha(112F * envelope * (1.0F - offset * 0.55F));
            float angle = (entering ? 1.0F : -1.0F) * (t * 2.4F + ring * 0.19F);

            pose.pushMatrix();
            pose.translate(cx, cy);
            pose.rotate(angle);
            int color = argb(alpha, ring % 2 == 0 ? VEIL_PURPLE : DEEP_PURPLE);
            graphics.fill(-half, -half, half, -half + thickness, color);
            graphics.fill(-half, half - thickness, half, half, color);
            graphics.fill(-half, -half + thickness, -half + thickness, half - thickness, color);
            graphics.fill(half - thickness, -half + thickness, half, half - thickness, color);
            pose.popMatrix();
        }
    }

    private static void drawBindingCollapse(
            GuiGraphicsExtractor graphics, float cx, float cy, int radius, float t, float envelope) {
        // Binding is deliberately distinct from travel: the Veil contracts into a dense center,
        // holds for an instant, then releases outward as the new Domain identity settles.
        float collapse;
        if (t < 0.58F) collapse = 1.0F - smooth(t / 0.58F);
        else collapse = smooth((t - 0.58F) / 0.42F);

        var pose = graphics.pose();
        for (int ring = 0; ring < 9; ring++) {
            float local = Math.min(1.0F, collapse + ring * 0.065F);
            int half = Math.max(5, Math.round(radius * (0.055F + local * 0.72F)));
            int thickness = Math.max(2, 9 - ring / 2);
            int alpha = clampAlpha((150F - ring * 10F) * envelope);
            pose.pushMatrix();
            pose.translate(cx, cy);
            pose.rotate(t * 5.6F + ring * 0.27F);
            int color = argb(alpha, ring % 3 == 0 ? BRIGHT_PURPLE : VEIL_PURPLE);
            graphics.fill(-half, -half, half, -half + thickness, color);
            graphics.fill(-half, half - thickness, half, half, color);
            graphics.fill(-half, -half, -half + thickness, half, color);
            graphics.fill(half - thickness, -half, half, half, color);
            pose.popMatrix();
        }

        int coreRadius = Math.max(3, Math.round((10F + 38F * envelope) * (1.0F - Math.abs(t - 0.58F))));
        int coreAlpha = clampAlpha(188F * envelope);
        graphics.fill(Math.round(cx) - coreRadius, Math.round(cy) - coreRadius,
                Math.round(cx) + coreRadius, Math.round(cy) + coreRadius, argb(coreAlpha, DEEP_PURPLE));
        int inner = Math.max(2, coreRadius / 3);
        graphics.fill(Math.round(cx) - inner, Math.round(cy) - inner,
                Math.round(cx) + inner, Math.round(cy) + inner, argb(clampAlpha(210F * envelope), BRIGHT_PURPLE));
    }

    private static void drawEdgeVignette(
            GuiGraphicsExtractor graphics, int width, int height, float envelope, boolean binding) {
        int layers = 7;
        for (int i = 0; i < layers; i++) {
            float p = (i + 1) / (float) layers;
            int insetX = Math.round(width * 0.045F * i);
            int insetY = Math.round(height * 0.045F * i);
            int thicknessX = Math.max(4, Math.round(width * 0.055F));
            int thicknessY = Math.max(4, Math.round(height * 0.055F));
            int alpha = clampAlpha((binding ? 44F : 52F) * envelope * (1.0F - p * 0.45F));
            int color = argb(alpha, i % 2 == 0 ? BLACK : DEEP_PURPLE);
            graphics.fill(insetX, insetY, Math.min(width, insetX + thicknessX), height - insetY, color);
            graphics.fill(Math.max(0, width - insetX - thicknessX), insetY, width - insetX, height - insetY, color);
            graphics.fill(insetX, insetY, width - insetX, Math.min(height, insetY + thicknessY), color);
            graphics.fill(insetX, Math.max(0, height - insetY - thicknessY), width - insetX, height - insetY, color);
        }
    }

    private static float smooth(float value) {
        float x = Math.max(0.0F, Math.min(1.0F, value));
        return x * x * (3.0F - 2.0F * x);
    }

    private static int clampAlpha(float alpha) {
        return Math.max(0, Math.min(255, Math.round(alpha)));
    }

    private static int argb(int alpha, int rgb) {
        return (alpha << 24) | (rgb & 0x00FFFFFF);
    }
}
''', encoding='utf-8')

client = java / 'dev/futurae/veilbound/client/VeilboundClient.java'
text = client.read_text(encoding='utf-8')
if 'import dev.futurae.veilbound.client.render.DomainTransitionOverlay;' not in text:
    text = text.replace('import dev.futurae.veilbound.client.render.DimensionalCoreRenderer;\n',
                        'import dev.futurae.veilbound.client.render.DimensionalCoreRenderer;\nimport dev.futurae.veilbound.client.render.DomainTransitionOverlay;\n', 1)
if 'import net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;' not in text:
    text = text.replace('import net.neoforged.neoforge.client.event.RegisterCustomEnvironmentEffectRendererEvent;\n',
                        'import net.neoforged.neoforge.client.event.RegisterCustomEnvironmentEffectRendererEvent;\nimport net.neoforged.neoforge.client.event.RegisterGuiLayersEvent;\n', 1)
if 'modBus.addListener(VeilboundClient::registerGuiLayers);' not in text:
    text = text.replace('        modBus.addListener(VeilboundClient::registerEnvironmentRenderers);\n',
                        '        modBus.addListener(VeilboundClient::registerEnvironmentRenderers);\n        modBus.addListener(VeilboundClient::registerGuiLayers);\n', 1)
method_marker = '    private static void registerEnvironmentRenderers(RegisterCustomEnvironmentEffectRendererEvent event) {\n'
if 'private static void registerGuiLayers(RegisterGuiLayersEvent event)' not in text:
    method = '''    private static void registerGuiLayers(RegisterGuiLayersEvent event) {\n        event.registerAboveAll(Identifier.fromNamespaceAndPath(Veilbound.MOD_ID, "domain_transition"), DomainTransitionOverlay::render);\n    }\n\n'''
    text = text.replace(method_marker, method + method_marker, 1)
clear_marker = '            if (minecraft.getConnection() == null) MatterTooltipClientState.clear();\n'
if 'DomainTransitionOverlay.clear();' not in text:
    text = text.replace(clear_marker, clear_marker + '            if (minecraft.getConnection() == null) DomainTransitionOverlay.clear();\n', 1)
handler_marker = '    public static void handleDomainEnvironmentSnapshot(DomainEnvironmentSnapshotPayload snapshot) {\n'
if 'handleDomainVisualEffect(DomainVisualEffectPayload payload)' not in text:
    handler = '''    public static void handleDomainVisualEffect(DomainVisualEffectPayload payload) {\n        DomainTransitionOverlay.start(payload.effect());\n    }\n\n'''
    text = text.replace(handler_marker, handler + handler_marker, 1)
client.write_text(text, encoding='utf-8')

networking = java / 'dev/futurae/veilbound/platform/neoforge/network/NeoForgeNetworking.java'
text = networking.read_text(encoding='utf-8')
text = text.replace('private static final String PROTOCOL = "20";', 'private static final String PROTOCOL = "21";')
reg_marker = '        registrar.playToServer(DomainTravelRequestPayload.TYPE, DomainTravelRequestPayload.STREAM_CODEC, NeoForgeNetworking::handleDomainTravel);\n'
if 'DomainVisualEffectPayload.TYPE' not in text:
    text = text.replace(reg_marker, reg_marker + '        registrar.playToClient(DomainVisualEffectPayload.TYPE, DomainVisualEffectPayload.STREAM_CODEC, NeoForgeNetworking::handleDomainVisualEffect);\n', 1)
handler_marker = '    private static void handleDomainEnvironmentSnapshot(DomainEnvironmentSnapshotPayload payload, IPayloadContext context) {\n'
if 'handleDomainVisualEffect(DomainVisualEffectPayload payload' not in text:
    handler = '''    private static void handleDomainVisualEffect(DomainVisualEffectPayload payload, IPayloadContext context) {\n        context.enqueueWork(() -> VeilboundClient.handleDomainVisualEffect(payload));\n    }\n'''
    text = text.replace(handler_marker, handler + handler_marker, 1)
networking.write_text(text, encoding='utf-8')

genesis = java / 'dev/futurae/veilbound/platform/neoforge/NeoForgeGenesisSeedCoordinator.java'
text = genesis.read_text(encoding='utf-8')
if 'import dev.futurae.veilbound.network.DomainVisualEffectPayload;' not in text:
    text = text.replace('import dev.futurae.veilbound.domain.DomainIdentity;\n',
                        'import dev.futurae.veilbound.domain.DomainIdentity;\nimport dev.futurae.veilbound.network.DomainVisualEffectPayload;\n', 1)
if 'import net.neoforged.neoforge.network.PacketDistributor;' not in text:
    text = text.replace('import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;\n',
                        'import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;\nimport net.neoforged.neoforge.network.PacketDistributor;\n', 1)
old = '        player.sendSystemMessage(Component.translatable("message.veilbound.genesis_seed.bound"), false);\n        finish.accept(InteractionResult.SUCCESS);'
new = '        PacketDistributor.sendToPlayer(player, DomainVisualEffectPayload.bind());\n        finish.accept(InteractionResult.SUCCESS);'
if old in text:
    text = text.replace(old, new, 1)
elif 'DomainVisualEffectPayload.bind()' not in text:
    raise SystemExit('could not replace Genesis Seed success text with binding animation')
genesis.write_text(text, encoding='utf-8')

travel = java / 'dev/futurae/veilbound/platform/neoforge/travel/NeoForgeDomainTravelExecutor.java'
text = travel.read_text(encoding='utf-8')
if 'import dev.futurae.veilbound.network.DomainVisualEffectPayload;' not in text:
    text = text.replace('import dev.futurae.veilbound.domain.StarterPocketLayout;\n',
                        'import dev.futurae.veilbound.domain.StarterPocketLayout;\nimport dev.futurae.veilbound.network.DomainVisualEffectPayload;\n', 1)
if 'import net.neoforged.neoforge.network.PacketDistributor;' not in text:
    text = text.replace('import net.minecraft.world.entity.Relative;\n',
                        'import net.minecraft.world.entity.Relative;\nimport net.neoforged.neoforge.network.PacketDistributor;\n', 1)
enter_marker = '        boolean moved = NeoForgeTransitGuard.run(ownerId, () -> owner.teleportTo(\n'
if 'PacketDistributor.sendToPlayer(owner, DomainVisualEffectPayload.enter());' not in text:
    text = text.replace(enter_marker,
                        '        PacketDistributor.sendToPlayer(owner, DomainVisualEffectPayload.enter());\n' + enter_marker, 1)
guest_marker = '                if (!teleport(guest, destination)) {\n                    return TravelResult.denied("guest_evacuation_failed:" + session.guestId());\n                }'
animated_guest_marker = '                PacketDistributor.sendToPlayer(guest, DomainVisualEffectPayload.exit());\n' + guest_marker
if animated_guest_marker not in text:
    text = text.replace(guest_marker, animated_guest_marker)
owner_marker = '            if (!teleport(owner, ownerDestination)) return TravelResult.denied("owner_exit_teleport_failed");'
if 'PacketDistributor.sendToPlayer(owner, DomainVisualEffectPayload.exit());' not in text:
    text = text.replace(owner_marker,
                        '            PacketDistributor.sendToPlayer(owner, DomainVisualEffectPayload.exit());\n' + owner_marker, 1)
direct_guest_marker = '            if (!teleport(guest, destination)) return TravelResult.denied("guest_exit_teleport_failed");'
animated_direct_guest = '            PacketDistributor.sendToPlayer(guest, DomainVisualEffectPayload.exit());\n' + direct_guest_marker
if direct_guest_marker in text and animated_direct_guest not in text:
    text = text.replace(direct_guest_marker, animated_direct_guest, 1)
travel.write_text(text, encoding='utf-8')

client_text = client.read_text(encoding='utf-8')
network_text = networking.read_text(encoding='utf-8')
genesis_text = genesis.read_text(encoding='utf-8')
travel_text = travel.read_text(encoding='utf-8')
for marker in ('registerGuiLayers', 'DomainTransitionOverlay::render', 'handleDomainVisualEffect'):
    if marker not in client_text:
        raise SystemExit(f'missing client transition marker: {marker}')
for marker in ('DomainVisualEffectPayload.TYPE', 'PROTOCOL = "21"', 'handleDomainVisualEffect'):
    if marker not in network_text:
        raise SystemExit(f'missing transition networking marker: {marker}')
if 'message.veilbound.genesis_seed.bound' in genesis_text:
    raise SystemExit('Genesis Seed binding still emits success text')
if 'DomainVisualEffectPayload.bind()' not in genesis_text:
    raise SystemExit('Genesis Seed binding animation missing')
if 'DomainVisualEffectPayload.enter()' not in travel_text or travel_text.count('DomainVisualEffectPayload.exit()') < 3:
    raise SystemExit('Domain travel animation hooks incomplete')

print('VEILBOUND_0167_DOMAIN_TRANSITIONS=PASS travel=black_purple_vortex enter_exit=opposed_swirl binding=singularity no_binding_success_text=PASS renderer=gui_extraction')
