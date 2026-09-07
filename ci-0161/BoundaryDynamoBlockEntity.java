package dev.futurae.veilbound.block.entity;

import dev.futurae.veilbound.registry.VeilboundBlockEntities;
import dev.futurae.veilbound.registry.VeilboundBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.transfer.ResourceHandler;
import net.neoforged.neoforge.transfer.access.ItemAccess;
import net.neoforged.neoforge.transfer.energy.EnergyHandler;
import net.neoforged.neoforge.transfer.energy.SimpleEnergyHandler;
import net.neoforged.neoforge.transfer.item.ItemResource;
import net.neoforged.neoforge.transfer.item.VanillaContainerWrapper;
import net.neoforged.neoforge.transfer.transaction.Transaction;

/**
 * Early self-contained FE generator.
 *
 * <p>Slot 0 accepts normal furnace fuels. Slot 1 is a dedicated one-item charging slot and accepts
 * any item exposing NeoForge's item energy capability, including the Spatial Generator. The other
 * seven slots exist only because the vanilla 9x1 container screen is intentionally reused; they are
 * hard-disabled for insertion.</p>
 */
public final class BoundaryDynamoBlockEntity extends BaseContainerBlockEntity {
    public static final int INVENTORY_SIZE = 9;
    public static final int FUEL_SLOT = 0;
    public static final int CHARGE_SLOT = 1;

    public static final int FE_CAPACITY = 500_000;
    public static final int FE_PER_BURN_TICK = 80;
    public static final int MAX_FE_OUTPUT = 5_000;
    public static final int CHARGE_RATE = 5_000;

    private NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
    private final DynamoEnergyHandler energy = new DynamoEnergyHandler();
    private final ResourceHandler<ItemResource> itemHandler = VanillaContainerWrapper.of(this);
    private int burnTicks;
    private int totalBurnTicks;

    public BoundaryDynamoBlockEntity(BlockPos pos, BlockState state) {
        super(VeilboundBlockEntities.BOUNDARY_DYNAMO.get(), pos, state);
    }

    public EnergyHandler energyHandler(Direction side) {
        return energy;
    }

    public ResourceHandler<ItemResource> itemHandler(Direction side) {
        return itemHandler;
    }

    public int storedForgeEnergy() { return energy.getAmountAsInt(); }
    public int forgeEnergyCapacity() { return FE_CAPACITY; }
    public int burnTicks() { return burnTicks; }
    public int totalBurnTicks() { return totalBurnTicks; }

    public static void tick(Level level, BlockPos pos, BlockState state, BoundaryDynamoBlockEntity dynamo) {
        if (level.isClientSide()) return;

        boolean changed = false;
        if (dynamo.energy.getAmountAsInt() < FE_CAPACITY) {
            if (dynamo.burnTicks <= 0) changed |= dynamo.tryStartFuel(level);
            if (dynamo.burnTicks > 0) {
                dynamo.burnTicks--;
                int generated = Math.min(FE_PER_BURN_TICK, FE_CAPACITY - dynamo.energy.getAmountAsInt());
                if (generated > 0) {
                    dynamo.energy.addGenerated(generated);
                    changed = true;
                }
            }
        }

        if (dynamo.tryChargeInstalledItem()) changed = true;
        if (changed) dynamo.setChanged();
    }

    private boolean tryStartFuel(Level level) {
        ItemStack fuel = items.get(FUEL_SLOT);
        if (fuel.isEmpty()) return false;
        int duration = fuel.getBurnTime(null, level.fuelValues());
        if (duration <= 0) return false;

        ItemStackTemplate remainderTemplate = fuel.getCraftingRemainder();
        ItemStack remainder = remainderTemplate == null ? ItemStack.EMPTY : remainderTemplate.create();
        fuel.shrink(1);
        if (fuel.isEmpty()) items.set(FUEL_SLOT, remainder);
        burnTicks = duration;
        totalBurnTicks = duration;
        return true;
    }

    private boolean tryChargeInstalledItem() {
        if (energy.getAmountAsInt() <= 0) return false;
        ItemStack chargeStack = items.get(CHARGE_SLOT);
        if (chargeStack.isEmpty()) return false;

        ItemAccess access = ItemAccess.forStack(chargeStack);
        EnergyHandler target = access.getCapability(Capabilities.Energy.ITEM);
        if (target == null) return false;

        int request = Math.min(CHARGE_RATE, energy.getAmountAsInt());
        if (request <= 0) return false;
        try (Transaction transaction = Transaction.openRoot()) {
            int inserted = target.insert(request, transaction);
            if (inserted <= 0) return false;
            int extracted = energy.extract(inserted, transaction);
            if (extracted != inserted) return false;
            transaction.commit();
            return true;
        }
    }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        if (slot == FUEL_SLOT) {
            return level != null && stack.getBurnTime(null, level.fuelValues()) > 0;
        }
        if (slot == CHARGE_SLOT) {
            return ItemAccess.forStack(stack).getCapability(Capabilities.Energy.ITEM) != null;
        }
        return false;
    }

    @Override
    public void setItem(int slot, ItemStack stack) {
        if (slot == CHARGE_SLOT && stack.getCount() > 1) stack = stack.copyWithCount(1);
        super.setItem(slot, stack);
    }

    @Override
    public boolean stillValid(Player player) {
        if (level == null || level.getBlockEntity(worldPosition) != this) return false;
        if (!level.getBlockState(worldPosition).is(VeilboundBlocks.BOUNDARY_DYNAMO.get())) return false;
        return player.distanceToSqr(
                worldPosition.getX() + 0.5,
                worldPosition.getY() + 0.5,
                worldPosition.getZ() + 0.5) <= 64.0;
    }

    @Override
    public int getContainerSize() {
        return INVENTORY_SIZE;
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> items) {
        this.items = items;
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("container.veilbound.boundary_dynamo");
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        // Minecraft 26.2 replacement for ChestMenu.oneRow: bind the one-row screen to this container.
        return new ChestMenu(MenuType.GENERIC_9x1, containerId, inventory, this, 1);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        output.putInt("forge_energy", energy.getAmountAsInt());
        output.putInt("burn_ticks", burnTicks);
        output.putInt("burn_total", totalBurnTicks);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        energy.setStored(Math.max(0, Math.min(FE_CAPACITY, input.getIntOr("forge_energy", 0))));
        burnTicks = Math.max(0, input.getIntOr("burn_ticks", 0));
        totalBurnTicks = Math.max(burnTicks, input.getIntOr("burn_total", burnTicks));
    }

    private final class DynamoEnergyHandler extends SimpleEnergyHandler {
        private DynamoEnergyHandler() {
            super(FE_CAPACITY, 0, MAX_FE_OUTPUT);
        }

        private void addGenerated(int amount) {
            if (amount <= 0) return;
            set(Math.min(FE_CAPACITY, getAmountAsInt() + amount));
        }

        private void setStored(int amount) {
            set(Math.max(0, Math.min(FE_CAPACITY, amount)));
        }

        @Override
        protected void onEnergyChanged(int previousAmount) {
            BoundaryDynamoBlockEntity.this.setChanged();
        }
    }
}
