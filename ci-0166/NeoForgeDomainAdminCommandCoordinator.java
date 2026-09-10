package dev.futurae.veilbound.platform.neoforge;

import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.exceptions.DynamicCommandExceptionType;
import dev.futurae.veilbound.domain.AxisDirection;
import dev.futurae.veilbound.domain.DomainBounds;
import dev.futurae.veilbound.domain.DomainPosition;
import dev.futurae.veilbound.domain.DomainRecord;
import dev.futurae.veilbound.domain.DomainState;
import dev.futurae.veilbound.ritual.GenesisSeedService;
import dev.futurae.veilbound.runtime.VeilboundRuntime;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.NameAndId;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * Administrative pre-test commands for the compact first-release Domain loop.
 *
 * <p>This command surface intentionally omits legacy awakening, forced Core tiers, sovereignty,
 * Memory, milestone, fracture and removed-feature mutation. Those systems are not part of the
 * playable first release and exposing them here makes acceptance testing ambiguous.</p>
 */
public final class NeoForgeDomainAdminCommandCoordinator {
    private static final DynamicCommandExceptionType TARGET_NOT_FOUND = new DynamicCommandExceptionType(
            value -> Component.literal("Unknown player/UUID: " + value));
    private static final DynamicCommandExceptionType DOMAIN_NOT_FOUND = new DynamicCommandExceptionType(
            value -> Component.literal("No Veilbound Domain exists for " + value));

    private final VeilboundRuntime runtime;

    public NeoForgeDomainAdminCommandCoordinator(VeilboundRuntime runtime) {
        this.runtime = Objects.requireNonNull(runtime, "runtime");
    }

    public void onRegisterCommands(RegisterCommandsEvent event) {
        LiteralArgumentBuilder<CommandSourceStack> domain = Commands.literal("domain")
                .requires(Commands.hasPermission(Commands.LEVEL_ADMINS));

        domain.then(Commands.literal("info")
                .then(targetArgument().executes(ctx -> info(ctx.getSource(), existing(ctx)))));
        domain.then(Commands.literal("create")
                .then(targetArgument().executes(ctx -> create(ctx.getSource(), identity(ctx)))));

        domain.then(Commands.literal("bounds")
                .then(Commands.literal("set")
                        .then(targetArgument()
                                .then(Commands.argument("minX", IntegerArgumentType.integer())
                                        .then(Commands.argument("minY", IntegerArgumentType.integer())
                                                .then(Commands.argument("minZ", IntegerArgumentType.integer())
                                                        .then(Commands.argument("maxX", IntegerArgumentType.integer())
                                                                .then(Commands.argument("maxY", IntegerArgumentType.integer())
                                                                        .then(Commands.argument("maxZ", IntegerArgumentType.integer())
                                                                                .executes(this::setBounds))))))))));

        domain.then(Commands.literal("size")
                .then(Commands.literal("set")
                        .then(targetArgument()
                                .then(Commands.argument("sizeX", IntegerArgumentType.integer(3))
                                        .then(Commands.argument("sizeY", IntegerArgumentType.integer(3))
                                                .then(Commands.argument("sizeZ", IntegerArgumentType.integer(3))
                                                        .executes(this::setSize)))))));

        LiteralArgumentBuilder<CommandSourceStack> core = Commands.literal("core");
        core.then(Commands.literal("energy")
                .then(Commands.literal("set")
                        .then(targetArgument()
                                .then(Commands.argument("amount", LongArgumentType.longArg(0L))
                                        .executes(ctx -> setEnergy(
                                                ctx.getSource(), existing(ctx), LongArgumentType.getLong(ctx, "amount"))))))
                .then(Commands.literal("add")
                        .then(targetArgument()
                                .then(Commands.argument("amount", LongArgumentType.longArg(0L))
                                        .executes(ctx -> addEnergy(
                                                ctx.getSource(), existing(ctx), LongArgumentType.getLong(ctx, "amount")))))));
        domain.then(core);

        domain.then(Commands.literal("expansion")
                .then(Commands.literal("set")
                        .then(targetArgument()
                                .then(Commands.argument("value", BoolArgumentType.bool())
                                        .executes(ctx -> setExpansion(
                                                ctx.getSource(), existing(ctx), BoolArgumentType.getBool(ctx, "value")))))));

        event.getDispatcher().register(domain);
    }

    private static com.mojang.brigadier.builder.RequiredArgumentBuilder<CommandSourceStack, String> targetArgument() {
        return Commands.argument("target", StringArgumentType.word());
    }

    private ResolvedTarget identity(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        return resolveIdentity(ctx.getSource(), StringArgumentType.getString(ctx, "target"));
    }

    private ResolvedDomain existing(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ResolvedTarget target = identity(ctx);
        DomainRecord record = runtime.domains().getRecord(target.ownerId())
                .orElseThrow(() -> DOMAIN_NOT_FOUND.create(target.label()));
        return new ResolvedDomain(target, record);
    }

    private ResolvedTarget resolveIdentity(CommandSourceStack source, String token) throws CommandSyntaxException {
        MinecraftServer server = source.getServer();
        UUID uuid = tryUuid(token);
        if (uuid != null) {
            ServerPlayer online = server.getPlayerList().getPlayer(uuid);
            String cachedName = server.services().nameToIdCache().get(uuid).map(NameAndId::name).orElse(null);
            String label = online != null ? online.nameAndId().name() : cachedName != null ? cachedName : uuid.toString();
            return new ResolvedTarget(uuid, label);
        }

        ServerPlayer online = server.getPlayerList().getPlayerByName(token);
        if (online != null) return new ResolvedTarget(online.getUUID(), online.nameAndId().name());

        NameAndId cached = server.services().nameToIdCache().get(token).orElse(null);
        if (cached != null) {
            String label = cached.name() == null || cached.name().isBlank() ? cached.id().toString() : cached.name();
            return new ResolvedTarget(cached.id(), label);
        }
        throw TARGET_NOT_FOUND.create(token);
    }

    private int info(CommandSourceStack source, ResolvedDomain target) {
        source.sendSuccess(() -> Component.literal(summary(target)), false);
        return 1;
    }

    private int create(CommandSourceStack source, ResolvedTarget target) {
        GenesisSeedService.BindResult result = GenesisSeedService.bind(runtime.domains(), target.ownerId());
        if (!result.bound()) {
            source.sendFailure(Component.literal(target.label() + " already has a Domain."));
            return 0;
        }
        ResolvedDomain created = new ResolvedDomain(target, result.domain());
        source.sendSuccess(() -> Component.literal(
                "Created first-release Domain for " + target.label() + ". " + summary(created)), true);
        return 1;
    }

    private int setBounds(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ResolvedDomain target = existing(ctx);
        DomainBounds bounds = new DomainBounds(
                IntegerArgumentType.getInteger(ctx, "minX"),
                IntegerArgumentType.getInteger(ctx, "minY"),
                IntegerArgumentType.getInteger(ctx, "minZ"),
                IntegerArgumentType.getInteger(ctx, "maxX"),
                IntegerArgumentType.getInteger(ctx, "maxY"),
                IntegerArgumentType.getInteger(ctx, "maxZ"));
        if (bounds.sizeX() < 3 || bounds.sizeY() < 3 || bounds.sizeZ() < 3) {
            ctx.getSource().sendFailure(Component.literal("First-release Domains may not be smaller than 3x3x3."));
            return 0;
        }
        target.record().state().setBounds(bounds);
        ctx.getSource().sendSuccess(() -> Component.literal(
                "Set Domain bounds for " + target.label() + " to " + format(bounds)
                        + "; Core level is now " + target.record().state().coreTier().name() + "."), true);
        return 1;
    }

    private int setSize(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ResolvedDomain target = existing(ctx);
        DomainState state = target.record().state();
        int sx = IntegerArgumentType.getInteger(ctx, "sizeX");
        int sy = IntegerArgumentType.getInteger(ctx, "sizeY");
        int sz = IntegerArgumentType.getInteger(ctx, "sizeZ");
        state.setBounds(centeredBounds(state.corePosition(), sx, sy, sz));
        ctx.getSource().sendSuccess(() -> Component.literal(
                "Resized Domain for " + target.label() + " to " + sx + "x" + sy + "x" + sz
                        + "; Core level is now " + state.coreTier().name() + "."), true);
        return 1;
    }

    private int setEnergy(CommandSourceStack source, ResolvedDomain target, long amount) {
        long clamped = Math.min(amount, target.record().state().coreTier().dimensionalEnergyCapacity());
        target.record().state().setDimensionalEnergy(clamped);
        source.sendSuccess(() -> Component.literal(
                "Set Dimensional Energy for " + target.label() + " to " + clamped
                        + " / " + target.record().state().coreTier().dimensionalEnergyCapacity() + "."), true);
        return 1;
    }

    private int addEnergy(CommandSourceStack source, ResolvedDomain target, long amount) {
        long accepted = target.record().state().insertDimensionalEnergy(amount);
        source.sendSuccess(() -> Component.literal(
                "Added " + accepted + " Dimensional Energy to " + target.label() + "."), true);
        return 1;
    }

    private int setExpansion(CommandSourceStack source, ResolvedDomain target, boolean value) {
        target.record().state().setGlobalExpansionEnabled(value);
        source.sendSuccess(() -> Component.literal(
                "Set global expansion for " + target.label() + " to " + value + "."), true);
        return 1;
    }

    private static UUID tryUuid(String value) {
        try { return UUID.fromString(value); }
        catch (IllegalArgumentException ignored) { return null; }
    }

    private static DomainBounds centeredBounds(DomainPosition center, int sx, int sy, int sz) {
        int minX = center.x() - (sx - 1) / 2;
        int maxX = center.x() + sx / 2;
        int minY = center.y() - (sy - 1) / 2;
        int maxY = center.y() + sy / 2;
        int minZ = center.z() - (sz - 1) / 2;
        int maxZ = center.z() + sz / 2;
        return new DomainBounds(minX, minY, minZ, maxX, maxY, maxZ);
    }

    private static String format(DomainBounds b) {
        return "[" + b.minX() + "," + b.minY() + "," + b.minZ() + " -> "
                + b.maxX() + "," + b.maxY() + "," + b.maxZ() + "]";
    }

    private static String summary(ResolvedDomain target) {
        DomainRecord record = target.record();
        DomainState state = record.state();
        String directions = state.pylons().values().stream()
                .filter(p -> p.expansionEnabled())
                .map(p -> shortDirection(p.direction()))
                .sorted()
                .collect(Collectors.joining(","));
        if (directions.isBlank()) directions = "none";
        return "Domain{" + target.label()
                + ", dimension=" + record.identity().dimensionId()
                + ", size=" + state.bounds().sizeX() + "x" + state.bounds().sizeY() + "x" + state.bounds().sizeZ()
                + ", core=" + state.coreTier().name()
                + ", DE=" + state.dimensionalEnergy() + "/" + state.coreTier().dimensionalEnergyCapacity()
                + ", expansion=" + state.globalExpansionEnabled()
                + ", directions=" + directions
                + ", terminalItems=" + record.veilInventory().totalItems()
                + ", terminalTypes=" + record.veilInventory().distinctTypes()
                + ", Matter=" + record.matterTransmutation().storedMatter()
                + ", patterns=" + record.matterTransmutation().learnedItemIds().size()
                + ", physicalCore=" + record.starterPocketInitialized()
                + "}";
    }

    private static String shortDirection(AxisDirection direction) {
        return switch (direction) {
            case POSITIVE_X -> "+X";
            case NEGATIVE_X -> "-X";
            case POSITIVE_Y -> "+Y";
            case NEGATIVE_Y -> "-Y";
            case POSITIVE_Z -> "+Z";
            case NEGATIVE_Z -> "-Z";
        };
    }

    private record ResolvedTarget(UUID ownerId, String label) {}
    private record ResolvedDomain(ResolvedTarget target, DomainRecord record) {
        UUID ownerId() { return target.ownerId(); }
        String label() { return target.label(); }
    }
}
