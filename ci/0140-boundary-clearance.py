#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0140-boundary-clearance.py <Veilbound source root>')
root = Path(sys.argv[1]).resolve()

# Version bump.
gp = root / 'gradle.properties'
s = gp.read_text()
if 'mod_version=0.1.39-dev' not in s:
    raise SystemExit('Expected 0.1.39 version marker not found')
gp.write_text(s.replace('mod_version=0.1.39-dev', 'mod_version=0.1.40-dev', 1))

# Shared collision/render shell geometry. The buildable Domain remains exactly the same; the
# membrane gets enough body/head clearance that a 1x1x2 starter pocket is actually inhabitable.
p = root / 'src/main/java/dev/futurae/veilbound/boundary/VeilBoundaryCollisionState.java'
s = p.read_text()
s = s.replace(
    '    private static final double WALL_THICKNESS = 1.0D;\n',
    '    private static final double WALL_THICKNESS = 0.25D;\n'
    '    /** Half a vanilla player width: lets the player center traverse the full starter block. */\n'
    '    public static final double HORIZONTAL_BODY_CLEARANCE = 0.30D;\n'
    '    /** Enough extra ceiling room for a normal jump inside the two-block starter pocket. */\n'
    '    public static final double TOP_HEADROOM_CLEARANCE = 0.40D;\n')
old = '''    public static List<AABB> wallBoxes(DomainBounds b) {\n        double minX = b.minX();\n        double maxX = b.maxX() + 1.0D;\n        double minY = b.minY();\n        double maxY = b.maxY() + 1.0D;\n        double minZ = b.minZ();\n        double maxZ = b.maxZ() + 1.0D;\n        return List.of(\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, minX, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(maxX, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, minY, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, maxY, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, minZ),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, maxZ, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS));\n    }\n'''
new = '''    public static ShellBounds shellBounds(DomainBounds b) {\n        return new ShellBounds(\n                b.minX() - HORIZONTAL_BODY_CLEARANCE,\n                b.minY(),\n                b.minZ() - HORIZONTAL_BODY_CLEARANCE,\n                b.maxX() + 1.0D + HORIZONTAL_BODY_CLEARANCE,\n                b.maxY() + 1.0D + TOP_HEADROOM_CLEARANCE,\n                b.maxZ() + 1.0D + HORIZONTAL_BODY_CLEARANCE);\n    }\n\n    public static List<AABB> wallBoxes(DomainBounds b) {\n        ShellBounds shell = shellBounds(b);\n        double minX = shell.minX();\n        double maxX = shell.maxX();\n        double minY = shell.minY();\n        double maxY = shell.maxY();\n        double minZ = shell.minZ();\n        double maxZ = shell.maxZ();\n        return List.of(\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, minX, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(maxX, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, minY, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, maxY, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, minZ - WALL_THICKNESS, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, minZ),\n                new AABB(minX - WALL_THICKNESS, minY - WALL_THICKNESS, maxZ, maxX + WALL_THICKNESS, maxY + WALL_THICKNESS, maxZ + WALL_THICKNESS));\n    }\n'''
if old not in s:
    raise SystemExit('Expected 0.1.39 wallBoxes implementation not found')
s = s.replace(old, new, 1)
s = s.replace('        AABB expandedQuery = queryBox.inflate(2.0D);\n', '        AABB expandedQuery = queryBox.inflate(1.0E-7D);\n', 1)
insert = '''\n    /** Physical/visual membrane coordinates around the integer buildable Domain cells. */\n    public record ShellBounds(double minX, double minY, double minZ, double maxX, double maxY, double maxZ) {}\n'''
needle = '    private record FaceShape(AxisDirection face, AABB box) {}\n'
if needle not in s:
    raise SystemExit('Expected FaceShape marker not found')
s = s.replace(needle, insert + '\n' + needle, 1)
p.write_text(s)

# Render exactly the same padded shell used by collision so visual and physical faces remain aligned.
p = root / 'src/main/java/dev/futurae/veilbound/client/render/VeilBoundaryRenderer.java'
s = p.read_text()
s = s.replace(
    'import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.Snapshot;\n',
    'import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.ShellBounds;\n'
    'import dev.futurae.veilbound.boundary.VeilBoundaryCollisionState.Snapshot;\n')
s = s.replace('import dev.futurae.veilbound.domain.DomainBounds;\n', '')
s = s.replace(
    '        DomainBounds b = snapshot.bounds();\n',
    '        ShellBounds shell = VeilBoundaryCollisionState.shellBounds(snapshot.bounds());\n', 1)
s = s.replace('                renderShaderFallback(out, pose, b));\n', '                renderShaderFallback(out, pose, shell));\n', 1)
old_coords = '''            double minX = b.minX();\n            double maxX = b.maxX() + 1.0D;\n            double minY = b.minY();\n            double maxY = b.maxY() + 1.0D;\n            double minZ = b.minZ();\n            double maxZ = b.maxZ() + 1.0D;\n'''
new_coords = '''            double minX = shell.minX();\n            double maxX = shell.maxX();\n            double minY = shell.minY();\n            double maxY = shell.maxY();\n            double minZ = shell.minZ();\n            double maxZ = shell.maxZ();\n'''
if old_coords not in s:
    raise SystemExit('Expected custom membrane coordinate block not found')
s = s.replace(old_coords, new_coords, 1)
old_fallback = '''    private static void renderShaderFallback(VertexConsumer out, PoseStack.Pose pose, DomainBounds b) {\n        double minX = b.minX();\n        double maxX = b.maxX() + 1.0D;\n        double minY = b.minY();\n        double maxY = b.maxY() + 1.0D;\n        double minZ = b.minZ();\n        double maxZ = b.maxZ() + 1.0D;\n'''
new_fallback = '''    private static void renderShaderFallback(VertexConsumer out, PoseStack.Pose pose, ShellBounds shell) {\n        double minX = shell.minX();\n        double maxX = shell.maxX();\n        double minY = shell.minY();\n        double maxY = shell.maxY();\n        double minZ = shell.minZ();\n        double maxZ = shell.maxZ();\n'''
if old_fallback not in s:
    raise SystemExit('Expected fallback coordinate block not found')
s = s.replace(old_fallback, new_fallback, 1)
s = s.replace(
    '                renderBreachPulse(out, pose, breach, phase, fracture);\n',
    '                renderBreachPulse(out, pose, breach, shell, phase, fracture);\n', 1)
s = s.replace(
    '    private static void renderBreachPulse(VertexConsumer out, PoseStack.Pose pose, BreachOpening breach, double phase, float fracture) {\n',
    '    private static void renderBreachPulse(VertexConsumer out, PoseStack.Pose pose, BreachOpening breach, ShellBounds shell, double phase, float fracture) {\n', 1)
old_switch = '''        switch (breach.face()) {\n            case NEGATIVE_X, POSITIVE_X -> quadX(out, pose, x, y - radius, y + radius, z - radius, z + radius, uv, color, breach.face() == AxisDirection.POSITIVE_X);\n            case NEGATIVE_Y, POSITIVE_Y -> quadY(out, pose, y, x - radius, x + radius, z - radius, z + radius, uv, color, breach.face() == AxisDirection.NEGATIVE_Y);\n            case NEGATIVE_Z, POSITIVE_Z -> quadZ(out, pose, z, x - radius, x + radius, y - radius, y + radius, uv, color, breach.face() == AxisDirection.NEGATIVE_Z);\n        }\n'''
new_switch = '''        switch (breach.face()) {\n            case NEGATIVE_X -> quadX(out, pose, shell.minX() + SURFACE_EPSILON, y - radius, y + radius, z - radius, z + radius, uv, color, false);\n            case POSITIVE_X -> quadX(out, pose, shell.maxX() - SURFACE_EPSILON, y - radius, y + radius, z - radius, z + radius, uv, color, true);\n            case NEGATIVE_Y -> quadY(out, pose, shell.minY() + SURFACE_EPSILON, x - radius, x + radius, z - radius, z + radius, uv, color, true);\n            case POSITIVE_Y -> quadY(out, pose, shell.maxY() - SURFACE_EPSILON, x - radius, x + radius, z - radius, z + radius, uv, color, false);\n            case NEGATIVE_Z -> quadZ(out, pose, shell.minZ() + SURFACE_EPSILON, x - radius, x + radius, y - radius, y + radius, uv, color, true);\n            case POSITIVE_Z -> quadZ(out, pose, shell.maxZ() - SURFACE_EPSILON, x - radius, x + radius, y - radius, y + radius, uv, color, false);\n        }\n'''
if old_switch not in s:
    raise SystemExit('Expected breach render switch not found')
s = s.replace(old_switch, new_switch, 1)
p.write_text(s)

# Strengthen starter-pocket regression: standing, full-block center travel and normal jump headroom.
p = root / 'src/test/java/dev/futurae/veilbound/network/VeilBoundarySnapshotPayloadSelfTest.java'
s = p.read_text()
old_test = '''        List<AABB> walls = VeilBoundaryCollisionState.wallBoxes(starterPayload.bounds());\n        eq(2.0D, walls.get(3).minY, "starter positive-Y wall begins above the two-block pocket");\n        eq(1.0D, walls.get(1).minX, "starter positive-X wall begins outside usable X cell");\n        eq(1.0D, walls.get(5).minZ, "starter positive-Z wall begins outside usable Z cell");\n'''
new_test = '''        var shell = VeilBoundaryCollisionState.shellBounds(starterPayload.bounds());\n        eq(-0.30D, shell.minX(), "starter shell gives half-player clearance on -X");\n        eq(1.30D, shell.maxX(), "starter shell gives half-player clearance on +X");\n        eq(-0.30D, shell.minZ(), "starter shell gives half-player clearance on -Z");\n        eq(1.30D, shell.maxZ(), "starter shell gives half-player clearance on +Z");\n        eq(2.40D, shell.maxY(), "starter shell gives normal jump headroom");\n\n        List<AABB> walls = VeilBoundaryCollisionState.wallBoxes(starterPayload.bounds());\n        eq(2.40D, walls.get(3).minY, "starter positive-Y wall begins above jump headroom");\n        eq(1.30D, walls.get(1).minX, "starter positive-X wall is body-clear of build cell");\n        eq(1.30D, walls.get(5).minZ, "starter positive-Z wall is body-clear of build cell");\n\n        AABB westEdgePlayer = new AABB(-0.30D, 0.0D, 0.20D, 0.30D, 1.8D, 0.80D);\n        AABB eastEdgePlayer = new AABB(0.70D, 0.0D, 0.20D, 1.30D, 1.8D, 0.80D);\n        AABB jumpingPlayer = new AABB(0.20D, 0.42D, 0.20D, 0.80D, 2.22D, 0.80D);\n        truth(!walls.get(0).intersects(westEdgePlayer), "player center must be able to reach west edge of starter block");\n        truth(!walls.get(1).intersects(eastEdgePlayer), "player center must be able to reach east edge of starter block");\n        truth(!walls.get(3).intersects(jumpingPlayer), "normal jump must fit below starter ceiling membrane");\n'''
if old_test not in s:
    raise SystemExit('Expected 0.1.39 starter wall assertions not found')
s = s.replace(old_test, new_test, 1)
p.write_text(s)

print('Applied 0.1.40 inhabitable starter-boundary clearance and shared render/collision shell geometry')
