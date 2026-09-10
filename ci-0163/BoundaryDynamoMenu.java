package dev.futurae.veilbound.menu;

import dev.futurae.veilbound.block.entity.BoundaryDynamoBlockEntity;
import dev.futurae.veilbound.registry.VeilboundMenus;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/** Two-slot Boundary Dynamo menu with live machine telemetry synchronized through container data. */
public final class BoundaryDynamoMenu extends AbstractContainerMenu {
    public static final int DATA_COUNT = 4;
    private static final int MACHINE_SLOT_COUNT = 2;
    private static final int PLAYER_INV_START = MACHINE_SLOT_COUNT;
    private static final int PLAYER_INV_END = PLAYER_INV_START + 27;
    private static final int HOTBAR_END = PLAYER_INV_END + 9;

    private final Container machine;
    private final ContainerData data;

    /** Client-side constructor used by MenuType. Slot contents/data arrive over normal menu sync packets. */
    public BoundaryDynamoMenu(int containerId, Inventory playerInventory, FriendlyByteBuf ignored) {
        this(containerId, playerInventory, new SimpleContainer(MACHINE_SLOT_COUNT), new SimpleContainerData(DATA_COUNT));
    }

    /** Server-side constructor bound to the actual block entity. */
    public BoundaryDynamoMenu(int containerId, Inventory playerInventory, BoundaryDynamoBlockEntity dynamo) {
        this(containerId, playerInventory, dynamo, dynamo.menuData());
    }

    private BoundaryDynamoMenu(int containerId, Inventory playerInventory, Container machine, ContainerData data) {
        super(VeilboundMenus.BOUNDARY_DYNAMO.get(), containerId);
        checkContainerSize(machine, MACHINE_SLOT_COUNT);
        checkContainerDataCount(data, DATA_COUNT);
        this.machine = machine;
        this.data = data;
        machine.startOpen(playerInventory.player);

        addSlot(new DynamoSlot(machine, BoundaryDynamoBlockEntity.FUEL_SLOT, 43, 68));
        addSlot(new DynamoSlot(machine, BoundaryDynamoBlockEntity.CHARGE_SLOT, 87, 68));

        // Player inventory: 3 rows + hotbar.
        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 9; column++) {
                addSlot(new Slot(playerInventory, column + row * 9 + 9, 37 + column * 18, 112 + row * 18));
            }
        }
        for (int column = 0; column < 9; column++) {
            addSlot(new Slot(playerInventory, column, 37 + column * 18, 170));
        }
        addDataSlots(data);
    }

    public int storedForgeEnergy() { return data.get(0); }
    public int burnTicks() { return data.get(1); }
    public int totalBurnTicks() { return data.get(2); }
    public int lastChargeTransfer() { return data.get(3); }

    public int energyPercent() {
        return Math.max(0, Math.min(100, (int) ((long) storedForgeEnergy() * 100L / BoundaryDynamoBlockEntity.FE_CAPACITY)));
    }

    public int burnPercent() {
        int total = totalBurnTicks();
        if (total <= 0) return 0;
        return Math.max(0, Math.min(100, (int) ((long) burnTicks() * 100L / total)));
    }

    public ItemStack chargeStack() {
        return machine.getItem(BoundaryDynamoBlockEntity.CHARGE_SLOT);
    }

    @Override
    public boolean stillValid(Player player) {
        return machine.stillValid(player);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();

        if (index < MACHINE_SLOT_COUNT) {
            if (!moveItemStackTo(stack, PLAYER_INV_START, HOTBAR_END, true)) return ItemStack.EMPTY;
        } else {
            Slot fuel = slots.get(BoundaryDynamoBlockEntity.FUEL_SLOT);
            Slot charge = slots.get(BoundaryDynamoBlockEntity.CHARGE_SLOT);
            if (fuel.mayPlace(stack)) {
                if (!moveItemStackTo(stack, BoundaryDynamoBlockEntity.FUEL_SLOT, BoundaryDynamoBlockEntity.FUEL_SLOT + 1, false)) {
                    return ItemStack.EMPTY;
                }
            } else if (charge.mayPlace(stack)) {
                if (!moveItemStackTo(stack, BoundaryDynamoBlockEntity.CHARGE_SLOT, BoundaryDynamoBlockEntity.CHARGE_SLOT + 1, false)) {
                    return ItemStack.EMPTY;
                }
            } else if (index < PLAYER_INV_END) {
                if (!moveItemStackTo(stack, PLAYER_INV_END, HOTBAR_END, false)) return ItemStack.EMPTY;
            } else if (!moveItemStackTo(stack, PLAYER_INV_START, PLAYER_INV_END, false)) {
                return ItemStack.EMPTY;
            }
        }

        if (stack.isEmpty()) slot.set(ItemStack.EMPTY);
        else slot.setChanged();
        if (stack.getCount() == original.getCount()) return ItemStack.EMPTY;
        slot.onTake(player, stack);
        return original;
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        machine.stopOpen(player);
    }

    private static final class DynamoSlot extends Slot {
        private DynamoSlot(Container container, int slot, int x, int y) {
            super(container, slot, x, y);
        }

        @Override
        public boolean mayPlace(ItemStack stack) {
            return container.canPlaceItem(getContainerSlot(), stack);
        }
    }
}
