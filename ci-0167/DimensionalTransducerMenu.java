package dev.futurae.veilbound.menu;

import dev.futurae.veilbound.block.entity.DimensionalTransducerBlockEntity;
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

/** One-slot transducer menu with live Matter, DE and FE telemetry. */
public final class DimensionalTransducerMenu extends AbstractContainerMenu {
    public static final int DATA_COUNT = 11;
    private static final int MACHINE_SLOT_COUNT = 1;
    private static final int PLAYER_INV_START = MACHINE_SLOT_COUNT;
    private static final int PLAYER_INV_END = PLAYER_INV_START + 27;
    private static final int HOTBAR_END = PLAYER_INV_END + 9;

    private final Container machine;
    private final ContainerData data;

    public DimensionalTransducerMenu(int containerId, Inventory playerInventory, FriendlyByteBuf ignored) {
        this(containerId, playerInventory, new SimpleContainer(MACHINE_SLOT_COUNT), new SimpleContainerData(DATA_COUNT));
    }

    public DimensionalTransducerMenu(int containerId, Inventory playerInventory, DimensionalTransducerBlockEntity transducer) {
        this(containerId, playerInventory, transducer, transducer.menuData());
    }

    private DimensionalTransducerMenu(int containerId, Inventory playerInventory, Container machine, ContainerData data) {
        super(VeilboundMenus.DIMENSIONAL_TRANSDUCER.get(), containerId);
        checkContainerSize(machine, MACHINE_SLOT_COUNT);
        checkContainerDataCount(data, DATA_COUNT);
        this.machine = machine;
        this.data = data;
        machine.startOpen(playerInventory.player);

        addSlot(new Slot(machine, DimensionalTransducerBlockEntity.MATTER_INPUT_SLOT, 58, 60) {
            @Override public boolean mayPlace(ItemStack stack) { return machine.canPlaceItem(index, stack); }
        });

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

    private long longData(int lowIndex) {
        return Integer.toUnsignedLong(data.get(lowIndex)) | ((long) data.get(lowIndex + 1) << 32);
    }

    public long storedMatter() { return longData(0); }
    public long matterCapacity() { return longData(2); }
    public int storedForgeEnergy() { return Math.max(0, data.get(4)); }
    public int forgeEnergyCapacity() { return Math.max(1, data.get(5)); }
    public long dimensionalEnergy() { return longData(6); }
    public long dimensionalEnergyCapacity() { return longData(8); }
    public int tierLevel() { return Math.max(1, Math.min(4, data.get(10))); }

    public int matterPercent() { return percent(storedMatter(), matterCapacity()); }
    public int energyPercent() { return percent(storedForgeEnergy(), forgeEnergyCapacity()); }
    public int dePercent() { return percent(dimensionalEnergy(), dimensionalEnergyCapacity()); }

    private static int percent(long value, long capacity) {
        if (capacity <= 0L || value <= 0L) return 0;
        return Math.max(0, Math.min(100, (int) Math.min(100L, value * 100L / capacity)));
    }

    @Override public boolean stillValid(Player player) { return machine.stillValid(player); }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        Slot slot = slots.get(index);
        if (!slot.hasItem()) return ItemStack.EMPTY;
        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();

        if (index < MACHINE_SLOT_COUNT) {
            if (!moveItemStackTo(stack, PLAYER_INV_START, HOTBAR_END, true)) return ItemStack.EMPTY;
        } else {
            Slot input = slots.get(DimensionalTransducerBlockEntity.MATTER_INPUT_SLOT);
            if (input.mayPlace(stack)) {
                if (!moveItemStackTo(stack, 0, 1, false)) return ItemStack.EMPTY;
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
}
