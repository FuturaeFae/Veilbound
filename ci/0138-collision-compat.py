#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: 0138-collision-compat.py <Veilbound source root>')

root = Path(sys.argv[1]).resolve()
p = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/mixin/EntityVeilBoundaryCollisionMixin.java'
old = p.read_text()
if 'method = "collectColliders"' not in old:
    raise SystemExit('Expected original private Entity.collectColliders mixin target was not found')

p.write_text('''package dev.futurae.veilbound.platform.neoforge.mixin;\n\nimport dev.futurae.veilbound.boundary.VeilBoundaryCollisionState;\nimport java.util.ArrayList;\nimport java.util.List;\nimport net.minecraft.world.entity.Entity;\nimport net.minecraft.world.level.EntityGetter;\nimport net.minecraft.world.level.Level;\nimport net.minecraft.world.phys.AABB;\nimport net.minecraft.world.phys.shapes.VoxelShape;\nimport org.spongepowered.asm.mixin.Mixin;\nimport org.spongepowered.asm.mixin.injection.At;\nimport org.spongepowered.asm.mixin.injection.Inject;\nimport org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;\n\n/**\n * Adds the mathematical Veil shell to Minecraft's shared entity-collider source.\n *\n * <p>Targeting EntityGetter#getEntityCollisions keeps the boundary in the same collider list\n * used by both the flat movement solve and Entity's step-up retry. This avoids the fragile\n * private Entity.collectColliders injection and prevents stepping over/through the Veil.\n */\n@Mixin(EntityGetter.class)\npublic abstract class EntityVeilBoundaryCollisionMixin {\n    @Inject(method = "getEntityCollisions", at = @At("RETURN"), cancellable = true)\n    private void veilbound$appendBoundaryCollision(\n            Entity entity,\n            AABB testArea,\n            CallbackInfoReturnable<List<VoxelShape>> cir) {\n        if (!((Object) this instanceof Level level)) return;\n\n        List<VoxelShape> boundary = VeilBoundaryCollisionState.collisionShapes(entity, level, testArea);\n        if (boundary.isEmpty()) return;\n\n        List<VoxelShape> combined = new ArrayList<>(cir.getReturnValue());\n        combined.addAll(boundary);\n        cir.setReturnValue(combined);\n    }\n}\n''')
print('Moved Veil boundary collision injection to EntityGetter#getEntityCollisions for Minecraft 26.2')
