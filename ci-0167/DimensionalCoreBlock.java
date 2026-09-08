package dev.futurae.veilbound.block;

import com.mojang.serialization.MapCodec;
import dev.futurae.veilbound.block.entity.DimensionalCoreBlockEntity;
import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState;
import dev.futurae.veilbound.domain.CoreTier;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Invisible logical anchor for the floating crystalline Domain Core.
 *
 * <p>Only the main crystal body is collidable/selectable. Orbiting shards are visual pieces and do
 * not create moving collision. The stacked boxes approximate the pointed crystal silhouette and,
 * importantly, leave air below the model so the Core actually reads as floating rather than as a
 * disguised full block.</p>
 */
public final class DimensionalCoreBlock extends BaseEntityBlock {
    private static final List<AABB> NASCENT = List.of(
            coreBox(0.39, 0.27, 0.39, 0.61, 0.38, 0.61),
            coreBox(0.31, 0.38, 0.31, 0.69, 0.84, 0.69),
            coreBox(0.40, 0.84, 0.40, 0.60, 1.05, 0.60));
    private static final List<AABB> ANCHORED = List.of(
            coreBox(0.38, 0.23, 0.38, 0.62, 0.38, 0.62),
            coreBox(0.25, 0.38, 0.25, 0.75, 1.12, 0.75),
            coreBox(0.36, 1.12, 0.36, 0.64, 1.39, 0.64));
    private static final List<AABB> RESONANT = List.of(
            coreBox(0.36, 0.19, 0.36, 0.64, 0.42, 0.64),
            coreBox(0.17, 0.42, 0.17, 0.83, 1.52, 0.83),
            coreBox(0.31, 1.52, 0.31, 0.69, 1.87, 0.69));
    private static final List<AABB> ASCENDANT = List.of(
            coreBox(0.33, 0.15, 0.33, 0.67, 0.45, 0.67),
            coreBox(0.08, 0.45, 0.08, 0.92, 2.02, 0.92),
            coreBox(0.27, 2.02, 0.27, 0.73, 2.39, 0.73));
    private static final List<AABB> TRANSCENDENT = List.of(
            coreBox(0.30, 0.11, 0.30, 0.70, 0.52, 0.70),
            coreBox(-0.02, 0.52, -0.02, 1.02, 2.70, 1.02),
            coreBox(0.22, 2.70, 0.22, 0.78, 3.13, 0.78));

    public DimensionalCoreBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return simpleCodec(DimensionalCoreBlock::new);
    }

    @Override
    public RenderShape getRenderShape(BlockState state) {
        return RenderShape.INVISIBLE;
    }

    @Override
    public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape(collisionBoxes(level));
    }

    @Override
    public VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        return shape(collisionBoxes(level));
    }

    @Override
    public @Nullable BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new DimensionalCoreBlockEntity(pos, state);
    }

    public static List<AABB> collisionBoxes(BlockGetter level) {
        CoreTier tier = CoreTier.NASCENT;
        if (level instanceof Level world) {
            var snapshot = VeilBoundaryCollisionState.snapshotFor(world);
            if (snapshot != null) tier = snapshot.coreTier();
        }
        return collisionBoxes(tier);
    }

    public static List<AABB> collisionBoxes(CoreTier tier) {
        return switch (tier) {
            case NASCENT -> NASCENT;
            case ANCHORED -> ANCHORED;
            case RESONANT -> RESONANT;
            case ASCENDANT -> ASCENDANT;
            case TRANSCENDENT -> TRANSCENDENT;
        };
    }

    private static VoxelShape shape(List<AABB> boxes) {
        VoxelShape result = Shapes.empty();
        for (AABB box : boxes) result = Shapes.or(result, Shapes.create(box));
        return result;
    }

    private static AABB coreBox(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {
        return new AABB(minX, minY, minZ, maxX, maxY, maxZ);
    }
}
