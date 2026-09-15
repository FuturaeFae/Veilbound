package dev.futurae.veilbound.platform.neoforge;

import dev.futurae.veilbound.block.entity.DimensionalTransducerBlockEntity;
import dev.futurae.veilbound.block.DimensionalTransducerBlock;
import dev.futurae.veilbound.domain.DomainRecord;
import dev.futurae.veilbound.runtime.VeilboundRuntime;
import java.util.Objects;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/** Owner-safe interaction bridge for the transducer machine screen. */
public final class NeoForgeTransducerCoordinator {
    private final VeilboundRuntime runtime;

    public NeoForgeTransducerCoordinator(VeilboundRuntime runtime) {
        this.runtime = Objects.requireNonNull(runtime, "runtime");
    }

    public void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || event.getLevel().isClientSide()) return;
        if (!(event.getLevel().getBlockState(event.getPos()).getBlock() instanceof DimensionalTransducerBlock)) return;
        if (!(event.getLevel().getBlockEntity(event.getPos()) instanceof DimensionalTransducerBlockEntity transducer)) return;

        if (transducer.ownerId() == null || !transducer.ownerId().equals(player.getUUID())) {
            player.sendSystemMessage(Component.translatable("message.veilbound.transducer.not_owner"), true);
            consume(event, InteractionResult.FAIL);
            return;
        }
        DomainRecord record = runtime.domains().getRecord(player.getUUID()).orElse(null);
        if (record == null) {
            player.sendSystemMessage(Component.translatable("message.veilbound.transducer.no_domain"), true);
            consume(event, InteractionResult.FAIL);
            return;
        }

        // The transducer behaves like a normal machine: right-click opens the panel.
        // Matter enters through the dedicated GUI slot or insert-only automation capability.
        player.openMenu(transducer);
        consume(event, InteractionResult.SUCCESS);
    }

    private static void consume(PlayerInteractEvent.RightClickBlock event, InteractionResult result) {
        event.setCancellationResult(result);
        event.setCanceled(true);
    }
}
