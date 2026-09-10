package dev.futurae.veilbound.block.entity;

import dev.futurae.veilbound.Veilbound;
import dev.futurae.veilbound.block.DimensionalTransducerBlock;
import dev.futurae.veilbound.domain.DomainRecord;
import dev.futurae.veilbound.energy.MatterTransductionService;
import dev.futurae.veilbound.energy.TransducerMatterInputService;
import dev.futurae.veilbound.energy.TransducerTier;
import dev.futurae.veilbound.energy.TransductionRuntimePolicy;
import dev.futurae.veilbound.menu.DimensionalTransducerMenu;
import dev.futurae.veilbound.registry.VeilboundBlockEntities;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.neoforged.neoforge.transfer.ResourceHandler;
import net.neoforged.neoforge.transfer.TransferPreconditions;
import net.neoforged.neoforge.transfer.energy.EnergyHandler;
import net.neoforged.neoforge.transfer.energy.SimpleEnergyHandler;
import net.neoforged.neoforge.transfer.item.ItemResource;
import net.neoforged.neoforge.transfer.transaction.SnapshotJournal;
import net.neoforged.neoforge.transfer.transaction.TransactionContext;
import org.jspecify.annotations.Nullable;

/** Owner-bound Matter + FE machine that converts both into the owner's Core DE reservoir. */
public final class DimensionalTransducerBlockEntity extends BaseContainerBlockEntity {
    public static final int INVENTORY_SIZE = 1;
    public static final int MATTER_INPUT_SLOT = 0;

    private UUID ownerId;
    private long storedMatter;
    private NonNullList<ItemStack> items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
    private final ConfigurableEnergyHandler energy = new ConfigurableEnergyHandler();
    private final ResourceHandler<ItemResource> matterInput = new MatterInputHandler();

    private final ContainerData menuData = new ContainerData() {
        @Override
        public int get(int index) {
            long matterCap = matterCapacity();
            DomainRecord record = ownerId == null ? null : Veilbound.runtime().domains().getRecord(ownerId).orElse(null);
            long de = record == null ? 0L : record.state().dimensionalEnergy();
            long deCap = record == null ? 1L : record.state().coreTier().dimensionalEnergyCapacity();
            return switch (index) {
                case 0 -> low(storedMatter);
                case 1 -> high(storedMatter);
                case 2 -> low(matterCap);
                case 3 -> high(matterCap);
                case 4 -> energy.getAmountAsInt();
                case 5 -> (int) Math.min(Integer.MAX_VALUE, energy.getCapacityAsLong());
                case 6 -> low(de);
                case 7 -> high(de);
                case 8 -> low(deCap);
                case 9 -> high(deCap);
                case 10 -> tier().level();
                default -> 0;
            };
        }

        @Override public void set(int index, int value) { }
        @Override public int getCount() { return DimensionalTransducerMenu.DATA_COUNT; }
    };

    public DimensionalTransducerBlockEntity(BlockPos pos, BlockState state) {
        super(VeilboundBlockEntities.DIMENSIONAL_TRANSDUCER.get(), pos, state);
    }

    private static int low(long value) { return (int) value; }
    private static int high(long value) { return (int) (value >>> 32); }

    public void bindOwner(UUID ownerId) {
        if (this.ownerId == null) {
            this.ownerId = java.util.Objects.requireNonNull(ownerId, "ownerId");
            setChanged();
        }
    }

    public @Nullable UUID ownerId() { return ownerId; }
    public ContainerData menuData() { return menuData; }
    public EnergyHandler energyHandler(Direction side) {
        energy.applyPolicy(Veilbound.runtime().transductionPolicy().policy());
        return energy;
    }
    public ResourceHandler<ItemResource> matterInputHandler(Direction side) { return matterInput; }
    public long storedForgeEnergy() { return energy.getAmountAsLong(); }
    public long forgeEnergyCapacity() { return energy.getCapacityAsLong(); }
    public long storedMatter() { return storedMatter; }
    public long matterCapacity() { return Veilbound.runtime().transductionPolicy().policy().matterCapacity(); }
    public TransducerTier tier() {
        return getBlockState().getBlock() instanceof DimensionalTransducerBlock block ? block.tier() : TransducerTier.DIMENSIONAL;
    }

    /** Player-facing direct feed path used by the GUI input slot and automation. */
    public int absorbMatterItems(ItemStack stack) {
        if (stack == null || stack.isEmpty() || ownerId == null
                || Veilbound.runtime().domains().getRecord(ownerId).isEmpty()) return 0;
        String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        var plan = TransducerMatterInputService.plan(
                Veilbound.runtime().matter(), itemId, stack.getCount(), storedMatter, matterCapacity());
        if (!plan.accepted()) return 0;
        storedMatter = Math.addExact(storedMatter, plan.matterAdded());
        stack.shrink(plan.itemsConsumed());
        setChanged();
        return plan.itemsConsumed();
    }

    public static void tick(Level level, BlockPos pos, BlockState state, DimensionalTransducerBlockEntity blockEntity) {
        if (!(level instanceof ServerLevel serverLevel)) return;
        blockEntity.absorbMatterItems(blockEntity.items.get(MATTER_INPUT_SLOT));
        TransductionRuntimePolicy runtimePolicy = Veilbound.runtime().transductionPolicy().policy();
        blockEntity.energy.applyPolicy(runtimePolicy);
        if (serverLevel.getGameTime() % runtimePolicy.cycleTicks() != 0L) return;
        blockEntity.runCycle(runtimePolicy);
    }

    private void runCycle(TransductionRuntimePolicy runtimePolicy) {
        if (ownerId == null || energy.getAmountAsLong() <= 0 || storedMatter <= 0) return;
        DomainRecord record = Veilbound.runtime().domains().getRecord(ownerId).orElse(null);
        if (record == null) return;
        long maxDe = tier().maxDimensionalEnergyPerCycle();
        long maxMatter = saturatedMultiply(maxDe, runtimePolicy.conversion().matterPerDimensionalEnergy());
        long offeredMatter = Math.min(storedMatter, maxMatter);
        MatterTransductionService.Result result = MatterTransductionService.transduce(
                record.state(), offeredMatter, energy.getAmountAsLong(), runtimePolicy.conversion(), true);
        if (!result.converted()) return;

        long remainingMatter = storedMatter - result.matterConsumed();
        long remainingFe = energy.getAmountAsLong() - result.forgeEnergyConsumed();
        if (remainingMatter < 0 || remainingFe < 0 || remainingFe > Integer.MAX_VALUE) {
            throw new IllegalStateException("Invalid Dimensional Transducer local-buffer commit");
        }
        storedMatter = remainingMatter;
        energy.setStored((int) remainingFe);
        setChanged();
    }

    private static long saturatedMultiply(long a, long b) {
        if (a <= 0 || b <= 0) return 0L;
        return a > Long.MAX_VALUE / b ? Long.MAX_VALUE : a * b;
    }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        if (slot != MATTER_INPUT_SLOT || stack == null || stack.isEmpty() || ownerId == null) return false;
        if (Veilbound.runtime().domains().getRecord(ownerId).isEmpty()) return false;
        String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        var value = Veilbound.runtime().matter().amount(itemId);
        return value.isPresent() && value.getAsLong() > 0L && storedMatter < matterCapacity();
    }

    @Override
    public boolean stillValid(Player player) {
        if (level == null || level.getBlockEntity(worldPosition) != this) return false;
        if (!(level.getBlockState(worldPosition).getBlock() instanceof DimensionalTransducerBlock)) return false;
        if (ownerId != null && !ownerId.equals(player.getUUID())) return false;
        return player.distanceToSqr(worldPosition.getX() + 0.5, worldPosition.getY() + 0.5, worldPosition.getZ() + 0.5) <= 64.0;
    }

    @Override public int getContainerSize() { return INVENTORY_SIZE; }
    @Override protected NonNullList<ItemStack> getItems() { return items; }
    @Override protected void setItems(NonNullList<ItemStack> items) { this.items = items; }

    @Override
    protected Component getDefaultName() {
        return Component.translatable(switch (tier()) {
            case DIMENSIONAL -> "block.veilbound.dimensional_transducer";
            case RESONANT -> "block.veilbound.resonant_transducer";
            case PHASE -> "block.veilbound.phase_transducer";
            case CAUSAL -> "block.veilbound.causal_transducer";
        });
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return new DimensionalTransducerMenu(containerId, inventory, this);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        if (ownerId != null) output.putString("owner", ownerId.toString());
        output.putInt("forge_energy", (int) Math.min(Integer.MAX_VALUE, energy.getAmountAsLong()));
        output.putString("transducer_matter", Long.toString(storedMatter));
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(INVENTORY_SIZE, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        ownerId = input.getString("owner").flatMap(raw -> {
            try { return java.util.Optional.of(UUID.fromString(raw)); }
            catch (IllegalArgumentException ignored) { return java.util.Optional.empty(); }
        }).orElse(null);
        energy.setStored(Math.max(0, input.getIntOr("forge_energy", 0)));
        storedMatter = input.getString("transducer_matter").map(raw -> {
            try { return Math.max(0L, Long.parseLong(raw)); }
            catch (NumberFormatException ignored) { return 0L; }
        }).orElse(0L);
    }

    private final class ConfigurableEnergyHandler extends SimpleEnergyHandler {
        private ConfigurableEnergyHandler() {
            super(TransductionRuntimePolicy.DEVELOPMENT_DEFAULT.forgeEnergyCapacity(),
                    TransductionRuntimePolicy.DEVELOPMENT_DEFAULT.maxForgeEnergyInput(), 0);
        }

        private void applyPolicy(TransductionRuntimePolicy policy) {
            this.capacity = policy.forgeEnergyCapacity();
            this.maxInsert = policy.maxForgeEnergyInput();
            this.maxExtract = 0;
        }

        private void setStored(int amount) { set(Math.max(0, Math.min(capacity, amount))); }

        @Override
        protected void onEnergyChanged(int previousAmount) {
            DimensionalTransducerBlockEntity.this.setChanged();
        }
    }

    /** Insert-only automation endpoint that reduces accepted items directly into machine Matter. */
    private final class MatterInputHandler extends SnapshotJournal<Long> implements ResourceHandler<ItemResource> {
        @Override public int size() { return 1; }
        @Override public ItemResource getResource(int index) { return ItemResource.EMPTY; }
        @Override public long getAmountAsLong(int index) { return 0L; }

        @Override
        public long getCapacityAsLong(int index, ItemResource resource) {
            if (ownerId == null || Veilbound.runtime().domains().getRecord(ownerId).isEmpty()) return 0L;
            if (index != 0 || resource == null || resource.isEmpty()) return 0L;
            String itemId = BuiltInRegistries.ITEM.getKey(resource.getItem()).toString();
            var value = Veilbound.runtime().matter().amount(itemId);
            if (value.isEmpty() || value.getAsLong() <= 0) return 0L;
            long room = Math.max(0L, matterCapacity() - storedMatter);
            return room / value.getAsLong();
        }

        @Override
        public boolean isValid(int index, ItemResource resource) {
            if (ownerId == null || Veilbound.runtime().domains().getRecord(ownerId).isEmpty()) return false;
            if (index != 0 || resource == null || resource.isEmpty()) return false;
            String itemId = BuiltInRegistries.ITEM.getKey(resource.getItem()).toString();
            return Veilbound.runtime().matter().amount(itemId).isPresent();
        }

        @Override
        public int insert(int index, ItemResource resource, int amount, TransactionContext transaction) {
            TransferPreconditions.checkNonEmptyNonNegative(resource, amount);
            if (ownerId == null || Veilbound.runtime().domains().getRecord(ownerId).isEmpty()) return 0;
            if (index != 0 || amount == 0) return 0;
            String itemId = BuiltInRegistries.ITEM.getKey(resource.getItem()).toString();
            var plan = TransducerMatterInputService.plan(
                    Veilbound.runtime().matter(), itemId, amount, storedMatter, matterCapacity());
            if (!plan.accepted()) return 0;
            updateSnapshots(transaction);
            storedMatter = Math.addExact(storedMatter, plan.matterAdded());
            setChanged();
            return plan.itemsConsumed();
        }

        @Override
        public int extract(int index, ItemResource resource, int amount, TransactionContext transaction) {
            TransferPreconditions.checkNonEmptyNonNegative(resource, amount);
            return 0;
        }

        @Override public int insert(ItemResource resource, int amount, TransactionContext transaction) { return insert(0, resource, amount, transaction); }
        @Override public int extract(ItemResource resource, int amount, TransactionContext transaction) { TransferPreconditions.checkNonEmptyNonNegative(resource, amount); return 0; }
        @Override protected Long createSnapshot() { return storedMatter; }
        @Override protected void revertToSnapshot(Long snapshot) { storedMatter = snapshot; setChanged(); }
    }
}
