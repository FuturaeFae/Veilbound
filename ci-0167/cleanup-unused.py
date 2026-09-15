from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
java = root / 'src/main/java'
res = root / 'src/main/resources'


def rewrite(rel, transform):
    path = root / rel
    text = path.read_text(encoding='utf-8')
    updated = transform(text)
    if updated != text:
        path.write_text(updated, encoding='utf-8')


def strip_deprecated_null_fields(text):
    return '\n'.join(
        line for line in text.splitlines()
        if '@Deprecated public static final' not in line
    ) + '\n'


# Registries contain actual runtime entries only. The old null aliases existed solely to let
# disconnected development-era source compile and caused real world-load crashes when stale code
# dereferenced them.
for rel in (
    'src/main/java/dev/futurae/veilbound/registry/VeilboundBlocks.java',
    'src/main/java/dev/futurae/veilbound/registry/VeilboundItems.java',
    'src/main/java/dev/futurae/veilbound/registry/VeilboundBlockEntities.java',
):
    rewrite(rel, strip_deprecated_null_fields)

rewrite(
    'src/main/java/dev/futurae/veilbound/registry/VeilboundBlocks.java',
    lambda text: text.replace(
        '/** First-release physical registry. Legacy source fields remain null only so dormant old classes compile. */',
        '/** Physical block registrations used by the current Veilbound release. */'))

# No custom item data components are registered by the current runtime.
data_components = java / 'dev/futurae/veilbound/registry/VeilboundDataComponents.java'
if data_components.exists():
    data_components.unlink()


# Remove the compile-only Threshold portal compatibility hook from the mod root.
def clean_mod_root(text):
    text = text.replace(
        'import dev.futurae.veilbound.platform.neoforge.threshold.NeoForgeThresholdPortalTransit;\n', '')
    text = re.sub(
        r'\n    /\*\* Compile-time compatibility for the dormant legacy ThresholdPortalBlock source\. \*/\n'
        r'    @Deprecated\n'
        r'    public static NeoForgeThresholdPortalTransit thresholdPortalTransit\(\) \{\n'
        r'        throw new UnsupportedOperationException\("Threshold portals are not part of the first Veilbound release"\);\n'
        r'    \}\n',
        '\n', text)
    text = text.replace(
        ' * one Overworld shard family, rare Domain accretions, and four transducer levels. Legacy source\n'
        ' * remains in-tree temporarily for migration/reference purposes but is not registered or event-wired.</p>',
        ' * one Overworld shard family, rare Domain accretions, and four transducer levels.</p>')
    return text


rewrite('src/main/java/dev/futurae/veilbound/Veilbound.java', clean_mod_root)

# Remove source-only aliases/constructors with no callers.
rewrite(
    'src/main/java/dev/futurae/veilbound/domain/StarterPocketLayout.java',
    lambda text: re.sub(
        r'\n    /\*\* Legacy alias retained for dormant source compatibility; no starter Void Anchor is placed\. \*/\n'
        r'    @Deprecated public static final DomainPosition VOID_ANCHOR_FLOOR = new DomainPosition\(0, -2, 0\);\n',
        '\n', text))
rewrite(
    'src/main/java/dev/futurae/veilbound/block/DimensionalTransducerBlock.java',
    lambda text: re.sub(
        r'\n    /\*\* Legacy source constructor maps to the first-release Level I machine\. \*/\n'
        r'    public DimensionalTransducerBlock\(Properties properties\) \{ this\(TransducerTier\.DIMENSIONAL, properties\); \}\n',
        '\n', text))


# The current Core is the only oversized physical object that needs the out-of-cell collision scan.
# Replace the old shared monument/lance supplement with a Core-only implementation.
core_collision = java / 'dev/futurae/veilbound/block/DimensionalCoreCollisionState.java'
core_collision.parent.mkdir(parents=True, exist_ok=True)
core_collision.write_text('''package dev.futurae.veilbound.block;

import dev.futurae.veilbound.registry.VeilboundBlocks;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** Supplies collision for Dimensional Core geometry that extends beyond its anchor cell. */
public final class DimensionalCoreCollisionState {
    private static final double HORIZONTAL_REACH = 2.60D;
    private static final double DOWNWARD_ANCHOR_REACH = 3.15D;
    private static final double UPWARD_ANCHOR_REACH = 1.35D;
    private static final double EPSILON = 1.0E-7D;

    private DimensionalCoreCollisionState() {}

    public static List<VoxelShape> collisionShapes(Entity entity, Level level, AABB queryBox) {
        if (entity == null || entity.isSpectator()) return List.of();

        int minX = Mth.floor(queryBox.minX - HORIZONTAL_REACH);
        int maxX = Mth.floor(queryBox.maxX + HORIZONTAL_REACH);
        int minY = Mth.floor(queryBox.minY - DOWNWARD_ANCHOR_REACH);
        int maxY = Mth.floor(queryBox.maxY + UPWARD_ANCHOR_REACH + EPSILON);
        int minZ = Mth.floor(queryBox.minZ - HORIZONTAL_REACH);
        int maxZ = Mth.floor(queryBox.maxZ + HORIZONTAL_REACH);

        AABB expandedQuery = queryBox.inflate(EPSILON);
        AABB entityBox = entity.getBoundingBox();
        List<VoxelShape> result = new ArrayList<>();
        BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

        for (int y = minY; y <= maxY; y++) {
            for (int x = minX; x <= maxX; x++) {
                for (int z = minZ; z <= maxZ; z++) {
                    cursor.set(x, y, z);
                    BlockState state = level.getBlockState(cursor);
                    if (state.getBlock() != VeilboundBlocks.DIMENSIONAL_CORE.get()) continue;
                    for (AABB local : DimensionalCoreBlock.collisionBoxes(level)) {
                        AABB world = new AABB(
                                local.minX + x, local.minY + y, local.minZ + z,
                                local.maxX + x, local.maxY + y, local.maxZ + z);
                        if (!world.intersects(expandedQuery) || world.intersects(entityBox)) continue;
                        result.add(Shapes.create(world));
                    }
                }
            }
        }
        return result;
    }
}
''', encoding='utf-8')

old_collision = java / 'dev/futurae/veilbound/block/EngineeringMonumentCollisionState.java'
if old_collision.exists():
    old_collision.unlink()


def clean_collision_mixin(text):
    text = text.replace(
        'import dev.futurae.veilbound.block.EngineeringMonumentCollisionState;',
        'import dev.futurae.veilbound.block.DimensionalCoreCollisionState;')
    text = text.replace(
        'Adds Veilbound mathematical boundary and oversized monument collision',
        'Adds Veilbound mathematical boundary and oversized Dimensional Core collision')
    text = text.replace(
        'List<VoxelShape> monuments = EngineeringMonumentCollisionState.collisionShapes(entity, level, testArea);\n'
        '        if (boundary.isEmpty() && monuments.isEmpty()) return;\n\n'
        '        List<VoxelShape> combined = new ArrayList<>(cir.getReturnValue());\n'
        '        combined.addAll(boundary);\n'
        '        combined.addAll(monuments);',
        'List<VoxelShape> core = DimensionalCoreCollisionState.collisionShapes(entity, level, testArea);\n'
        '        if (boundary.isEmpty() && core.isEmpty()) return;\n\n'
        '        List<VoxelShape> combined = new ArrayList<>(cir.getReturnValue());\n'
        '        combined.addAll(boundary);\n'
        '        combined.addAll(core);')
    return text


rewrite(
    'src/main/java/dev/futurae/veilbound/platform/neoforge/mixin/EntityVeilBoundaryCollisionMixin.java',
    clean_collision_mixin)


# The capability registrar is active, but the old class name referred to the removed Veil Interface.
old_capabilities = java / 'dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInterfaceCapabilities.java'
new_capabilities = java / 'dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeMachineCapabilities.java'
if old_capabilities.exists():
    text = old_capabilities.read_text(encoding='utf-8')
    text = text.replace(
        'public final class NeoForgeVeilInterfaceCapabilities',
        'public final class NeoForgeMachineCapabilities')
    text = text.replace(
        'private NeoForgeVeilInterfaceCapabilities()',
        'private NeoForgeMachineCapabilities()')
    new_capabilities.write_text(text, encoding='utf-8')
    old_capabilities.unlink()

rewrite(
    'src/main/java/dev/futurae/veilbound/Veilbound.java',
    lambda text: text.replace(
        'import dev.futurae.veilbound.platform.neoforge.inventory.NeoForgeVeilInterfaceCapabilities;',
        'import dev.futurae.veilbound.platform.neoforge.inventory.NeoForgeMachineCapabilities;').replace(
        'modBus.addListener(NeoForgeVeilInterfaceCapabilities::register);',
        'modBus.addListener(NeoForgeMachineCapabilities::register);'))


# Remove composition-root subsystems that have no active event/network/runtime caller in this release.
def trim_runtime(text):
    for type_name in (
        'EngineeringRecipeRegistry', 'EngineeringMonumentFieldTracker', 'MilestoneRegistry',
        'OntologicalLoadTracker', 'OntologyPolicyRegistry', 'SpatialGeneratorPolicyRegistry',
        'StabilityPolicyRegistry', 'CoreUpgradeRegistry'):
        text = re.sub(r'^import .*\.' + type_name + r';\n', '', text, flags=re.M)

    for pattern in (
        r'    private final StabilityPolicyRegistry stabilityPolicy = new StabilityPolicyRegistry\(\);\n',
        r'    private final MilestoneRegistry milestones = new MilestoneRegistry\(\);\n',
        r'    private final SpatialGeneratorPolicyRegistry spatialGeneratorPolicy = new SpatialGeneratorPolicyRegistry\(\);\n',
        r'    private final CoreUpgradeRegistry coreUpgrades = new CoreUpgradeRegistry\(\);\n',
        r'    private final EngineeringRecipeRegistry engineeringRecipes = new EngineeringRecipeRegistry\(\);\n',
        r'    private final EngineeringMonumentFieldTracker monumentFields = new EngineeringMonumentFieldTracker\(\);\n',
        r'    private final OntologicalLoadTracker ontologicalLoads = new OntologicalLoadTracker\(\);\n',
        r'    private final OntologyPolicyRegistry ontologyPolicy = new OntologyPolicyRegistry\(\);\n'):
        text = re.sub(pattern, '', text)

    for pattern in (
        r'    public StabilityPolicyRegistry stabilityPolicy\(\) \{ return stabilityPolicy; \}\n',
        r'    public MilestoneRegistry milestones\(\) \{ return milestones; \}\n',
        r'    public SpatialGeneratorPolicyRegistry spatialGeneratorPolicy\(\) \{ return spatialGeneratorPolicy; \}\n',
        r'    public CoreUpgradeRegistry coreUpgrades\(\) \{ return coreUpgrades; \}\n',
        r'    public EngineeringRecipeRegistry engineeringRecipes\(\) \{ return engineeringRecipes; \}\n',
        r'    public EngineeringMonumentFieldTracker monumentFields\(\) \{ return monumentFields; \}\n',
        r'    public OntologicalLoadTracker ontologicalLoads\(\) \{ return ontologicalLoads; \}\n',
        r'    public OntologyPolicyRegistry ontologyPolicy\(\) \{ return ontologyPolicy; \}\n',
        r'    public VeilStoragePolicy veilStoragePolicy\(\) \{ return veilStoragePolicy; \}\n',
        r'    public LawEffectResolver lawEffectResolver\(\) \{ return lawEffects; \}\n'):
        text = re.sub(pattern, '', text)

    text = text.replace(
        '    private final VeilStoragePolicy veilStoragePolicy = new VeilStoragePolicy();\n'
        '    private final VeilInventoryAccessService veilInventoryAccess = new VeilInventoryAccessService(domains, veilStoragePolicy);',
        '    private final VeilInventoryAccessService veilInventoryAccess = new VeilInventoryAccessService(domains, new VeilStoragePolicy());')
    return text


rewrite('src/main/java/dev/futurae/veilbound/runtime/VeilboundRuntime.java', trim_runtime)


# Compute reachability from the real mod/client/mixin roots after compatibility stubs are gone.
# Disconnected source clusters are not loaded, registered, reflected, or referenced and are deleted.
files = list(java.rglob('*.java'))
texts = {path: path.read_text(encoding='utf-8', errors='ignore') for path in files}
name_to_file = {}
file_to_name = {}
for path, text in texts.items():
    match = re.search(
        r'\bpublic\s+(?:final\s+|abstract\s+|sealed\s+)?(?:class|interface|record|enum)\s+(\w+)',
        text)
    if match:
        name_to_file[match.group(1)] = path
        file_to_name[path] = match.group(1)

edges = {name: set() for name in name_to_file}
for path, text in texts.items():
    source = file_to_name.get(path)
    if source is None:
        continue
    for name, target in name_to_file.items():
        if target == path:
            continue
        if re.search(r'\b' + re.escape(name) + r'\b', text):
            edges[source].add(name)

roots = {
    'Veilbound', 'VeilboundClient',
    'MinecraftServerAccessor', 'EntityVeilBoundaryCollisionMixin', 'ClientLevelEnvironmentAccessor'
}
reachable = set(roots)
queue = list(roots)
while queue:
    source = queue.pop()
    for target in edges.get(source, ()):
        if target not in reachable:
            reachable.add(target)
            queue.append(target)

dead_types = {name for name in name_to_file if name not in reachable}
dead_files = {name_to_file[name] for name in dead_types}
for path in sorted(dead_files):
    path.unlink()

# Tests for removed source are no longer meaningful; active-feature tests remain.
test_root = root / 'src/test/java'
removed_tests = 0
if test_root.exists() and dead_types:
    token_pattern = re.compile(
        r'\b(?:' + '|'.join(map(re.escape, sorted(dead_types, key=len, reverse=True))) + r')\b')
    for path in list(test_root.rglob('*.java')):
        if token_pattern.search(path.read_text(encoding='utf-8', errors='ignore')):
            path.unlink()
            removed_tests += 1

# Orphaned renderer resources for the deleted monument system.
for rel in (
    'assets/veilbound/shaders/core/engineering_monument.vsh',
    'assets/veilbound/shaders/core/engineering_monument.fsh'):
    path = res / rel
    if path.exists():
        path.unlink()

# Prune empty folders left by deleted feature clusters.
for base in (java, test_root, res / 'assets/veilbound', res / 'data/veilbound'):
    if base.exists():
        for path in sorted(
                (entry for entry in base.rglob('*') if entry.is_dir()),
                key=lambda entry: len(entry.parts), reverse=True):
            try:
                path.rmdir()
            except OSError:
                pass

# Final source-level cleanup audit. Migration readers that are still executed are deliberately not
# forbidden: they are active compatibility code and protect existing worlds.
all_java = '\n'.join(
    path.read_text(encoding='utf-8', errors='ignore')
    for path in java.rglob('*.java'))
for forbidden in (
    'EngineeringMonumentBlock', 'EngineeringMonumentCollisionState', 'EngineeringMonumentRenderer',
    'VeilLanceBlock', 'VeilboundDataComponents', 'NeoForgeVeilInterfaceCapabilities',
    '@Deprecated public static final', 'VOID_ANCHOR_FLOOR'):
    if forbidden in all_java:
        raise SystemExit(f'legacy cleanup incomplete: {forbidden}')

resource_names = '\n'.join(
    str(path.relative_to(res)) for path in res.rglob('*') if path.is_file())
if 'engineering_monument' in resource_names:
    raise SystemExit('legacy engineering monument resource remained')

remaining_main = len(list(java.rglob('*.java')))
print(
    'VEILBOUND_0167_UNUSED_CLEANUP=PASS '
    f'removed_main_java={len(dead_files)} removed_types={len(dead_types)} '
    f'removed_tests={removed_tests} remaining_main_java={remaining_main}')
