#!/usr/bin/env python3
from pathlib import Path
import sys, json, zlib, struct, binascii, math

root = Path(sys.argv[1])

def patch(rel, old, new):
    p = root / rel
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'missing patch anchor: {rel}')
    p.write_text(s.replace(old, new, 1), encoding='utf-8')

def write(rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def png_rgba(width, height, pixels):
    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', binascii.crc32(t + data) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes(pixels[y*width*4:(y+1)*width*4]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')

patch('gradle.properties', 'mod_version=0.1.60-dev', 'mod_version=0.1.61-dev')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundBlocks.java',
      'import dev.futurae.veilbound.block.AxiomMonolithBlock;\n',
      'import dev.futurae.veilbound.block.AxiomMonolithBlock;\nimport dev.futurae.veilbound.block.BoundaryDynamoBlock;\n')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundBlocks.java',
      '    public static final DeferredBlock<DimensionalTransducerBlock> DIMENSIONAL_TRANSDUCER = BLOCKS.registerBlock(\n            "dimensional_transducer", DimensionalTransducerBlock::new, properties -> properties.strength(4.0F));\n',
      '    public static final DeferredBlock<DimensionalTransducerBlock> DIMENSIONAL_TRANSDUCER = BLOCKS.registerBlock(\n            "dimensional_transducer", DimensionalTransducerBlock::new, properties -> properties.strength(4.0F));\n    /** Pre-Core vanilla-fuel FE source that can directly charge the Spatial Generator. */\n    public static final DeferredBlock<BoundaryDynamoBlock> BOUNDARY_DYNAMO = BLOCKS.registerBlock(\n            "boundary_dynamo", BoundaryDynamoBlock::new, properties -> properties.strength(3.5F).explosionResistance(8.0F));\n')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundItems.java',
      '    public static final DeferredItem<BlockItem> DIMENSIONAL_TRANSDUCER = ITEMS.registerSimpleBlockItem(VeilboundBlocks.DIMENSIONAL_TRANSDUCER);\n',
      '    public static final DeferredItem<BlockItem> DIMENSIONAL_TRANSDUCER = ITEMS.registerSimpleBlockItem(VeilboundBlocks.DIMENSIONAL_TRANSDUCER);\n    public static final DeferredItem<BlockItem> BOUNDARY_DYNAMO = ITEMS.registerSimpleBlockItem(VeilboundBlocks.BOUNDARY_DYNAMO);\n')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundBlockEntities.java',
      'import dev.futurae.veilbound.block.entity.AxiomMonolithBlockEntity;\n',
      'import dev.futurae.veilbound.block.entity.AxiomMonolithBlockEntity;\nimport dev.futurae.veilbound.block.entity.BoundaryDynamoBlockEntity;\n')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundBlockEntities.java',
      '    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<EngineeringStationBlockEntity>> ENGINEERING_STATION =\n',
      '    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<BoundaryDynamoBlockEntity>> BOUNDARY_DYNAMO =\n            BLOCK_ENTITIES.register("boundary_dynamo", () -> new BlockEntityType<>(\n                    BoundaryDynamoBlockEntity::new,\n                    false,\n                    VeilboundBlocks.BOUNDARY_DYNAMO.get()));\n\n    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<EngineeringStationBlockEntity>> ENGINEERING_STATION =\n')
patch('src/main/java/dev/futurae/veilbound/registry/VeilboundCreativeTabs.java',
      '                        output.accept(VeilboundItems.DIMENSIONAL_TRANSDUCER.get());\n',
      '                        output.accept(VeilboundItems.DIMENSIONAL_TRANSDUCER.get());\n                        output.accept(VeilboundItems.BOUNDARY_DYNAMO.get());\n')
patch('src/main/java/dev/futurae/veilbound/platform/neoforge/inventory/NeoForgeVeilInterfaceCapabilities.java',
      '        event.registerBlockEntity(\n                Capabilities.Energy.BLOCK,\n                VeilboundBlockEntities.VEIL_LANCE.get(),\n',
      '        event.registerBlockEntity(\n                Capabilities.Energy.BLOCK,\n                VeilboundBlockEntities.BOUNDARY_DYNAMO.get(),\n                (blockEntity, side) -> blockEntity.energyHandler(side));\n        event.registerBlockEntity(\n                Capabilities.Item.BLOCK,\n                VeilboundBlockEntities.BOUNDARY_DYNAMO.get(),\n                (blockEntity, side) -> blockEntity.itemHandler(side));\n        event.registerBlockEntity(\n                Capabilities.Energy.BLOCK,\n                VeilboundBlockEntities.VEIL_LANCE.get(),\n')
patch('src/main/resources/assets/veilbound/lang/en_us.json',
      '  "message.veilbound.breach.wraith_core_drain": "A Null Wraith tore %s DE from your Dimensional Core."\n}',
      '  "message.veilbound.breach.wraith_core_drain": "A Null Wraith tore %s DE from your Dimensional Core.",\n  "block.veilbound.boundary_dynamo": "Boundary Dynamo",\n  "container.veilbound.boundary_dynamo": "Boundary Dynamo — Fuel | Charge",\n  "tooltip.veilbound.boundary_dynamo": "Pre-Core FE generator • Slot 1 Fuel • Slot 2 Charge"\n}')
patch('src/main/resources/data/minecraft/tags/block/mineable/pickaxe.json',
      '    "veilbound:deepslate_paradox_ore"\n',
      '    "veilbound:deepslate_paradox_ore",\n    "veilbound:boundary_dynamo"\n')

ci = Path(__file__).resolve().parent
for name, rel in [
    ('BoundaryDynamoBlock.java', 'src/main/java/dev/futurae/veilbound/block/BoundaryDynamoBlock.java'),
    ('BoundaryDynamoBlockEntity.java', 'src/main/java/dev/futurae/veilbound/block/entity/BoundaryDynamoBlockEntity.java')]:
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes((ci / name).read_bytes())

write('src/main/resources/assets/veilbound/blockstates/boundary_dynamo.json', '{\n  "variants": {\n    "": { "model": "veilbound:block/boundary_dynamo" }\n  }\n}\n')
write('src/main/resources/assets/veilbound/models/block/boundary_dynamo.json', '{\n  "parent": "minecraft:block/cube_all",\n  "textures": { "all": "veilbound:block/boundary_dynamo" }\n}\n')
write('src/main/resources/assets/veilbound/models/item/boundary_dynamo.json', '{\n  "parent": "veilbound:block/boundary_dynamo"\n}\n')
write('src/main/resources/assets/veilbound/items/boundary_dynamo.json', '{\n  "model": {\n    "type": "minecraft:model",\n    "model": "veilbound:item/boundary_dynamo"\n  }\n}\n')
write('src/main/resources/data/veilbound/recipe/boundary_dynamo.json', '''{
  "type": "minecraft:crafting_shaped",
  "category": "misc",
  "pattern": ["ECE", "RFR", "CRC"],
  "key": {"E":"minecraft:ender_eye","C":"minecraft:copper_block","R":"minecraft:redstone_block","F":"minecraft:blast_furnace"},
  "result": {"id":"veilbound:boundary_dynamo","count":1}
}\n''')
write('src/main/resources/data/veilbound/loot_table/blocks/boundary_dynamo.json', '''{
  "type": "minecraft:block",
  "pools": [{"rolls":1,"entries":[{"type":"minecraft:item","name":"veilbound:boundary_dynamo"}],"conditions":[{"condition":"minecraft:survives_explosion"}]}]
}\n''')
write('docs/0.1.61-validation.md', '''# Veilbound 0.1.61 development validation

## Pre-Core FE bootstrap
- Adds the Boundary Dynamo as a Veilbound-native pre-Core FE source.
- Craftable entirely from vanilla materials; no Core, DE, or external tech mod is required.
- Burns normal furnace fuel, stores 500,000 FE, generates 80 FE/t, and outputs up to 5,000 FE/t.
- Slot 1 is fuel. Slot 2 is a dedicated one-item charge slot accepting FE-capable items including the Spatial Generator.
- Charge items receive up to 5,000 FE/t transactionally. Fuel/item/energy/burn state persist.

## Ore texture rebuild
- Rebuilds all six ores in both stone and deepslate variants.
- Animated sheets use eight true vanilla-scale 16x16 frames (16x128 sheets), replacing the previous 32x32 logical pixel density.
- Stone/deepslate backgrounds use broad readable patches rather than high-frequency noise.
- Ore veins are spread across the face rather than concentrated in the center; animation changes luminance without moving veins.
''')

stone_palette=[(125,125,125),(132,132,132),(118,118,118),(107,107,107),(145,145,145)]
deep_palette=[(70,70,76),(76,76,82),(62,62,68),(84,84,90),(55,55,61)]
stone_base=[[1,1,1,0,0,0,0,1,1,1,0,0,1,1,1,0],[1,1,0,0,0,2,2,1,1,0,0,1,1,1,0,0],[0,0,0,2,2,2,1,1,0,0,1,1,0,0,0,1],[0,0,2,2,2,1,1,0,0,0,1,0,0,4,4,1],[0,2,2,2,1,1,0,0,0,1,1,0,4,4,1,1],[0,2,2,1,1,0,0,0,1,1,0,0,0,1,1,1],[0,0,1,1,0,0,3,3,1,0,0,0,1,1,1,0],[1,1,1,0,0,3,3,3,0,0,0,1,1,1,0,0],[1,1,0,0,3,3,3,0,0,0,1,1,0,0,0,1],[1,0,0,0,3,3,0,0,0,1,1,0,0,2,2,1],[0,0,0,1,1,0,0,0,1,1,0,0,2,2,1,1],[0,0,1,1,1,0,0,1,1,0,0,2,2,1,1,0],[0,1,1,1,0,0,1,1,0,0,2,2,1,1,0,0],[1,1,1,0,0,1,1,0,0,2,2,1,1,0,0,1],[1,1,0,0,1,1,0,0,2,2,1,1,0,0,1,1],[1,0,0,1,1,0,0,1,1,1,1,0,0,1,1,1]]
deep_base=[[1,1,0,0,2,2,2,1,1,0,0,3,3,1,1,0],[1,0,0,2,2,2,1,1,0,0,3,3,1,1,0,0],[0,0,2,2,2,1,1,0,0,3,3,1,1,0,0,4],[0,2,2,2,1,1,0,0,3,3,1,1,0,0,4,4],[2,2,2,1,1,0,0,3,3,1,1,0,0,4,4,1],[2,2,1,1,0,0,3,3,1,1,0,0,4,4,1,1],[2,1,1,0,0,3,3,1,1,0,0,4,4,1,1,0],[1,1,0,0,3,3,1,1,0,0,4,4,1,1,0,0],[1,0,0,3,3,1,1,0,0,4,4,1,1,0,0,2],[0,0,3,3,1,1,0,0,4,4,1,1,0,0,2,2],[0,3,3,1,1,0,0,4,4,1,1,0,0,2,2,1],[3,3,1,1,0,0,4,4,1,1,0,0,2,2,1,1],[3,1,1,0,0,4,4,1,1,0,0,2,2,1,1,0],[1,1,0,0,4,4,1,1,0,0,2,2,1,1,0,0],[1,0,0,4,4,1,1,0,0,2,2,1,1,0,0,3],[0,0,4,4,1,1,0,0,2,2,1,1,0,0,3,3]]
ore_palettes={'resonant':[(25,92,156),(39,128,198),(66,173,235),(128,220,255)],'phase':[(75,42,141),(105,63,183),(148,102,232),(210,176,255)],'mnemonic_crystal':[(82,41,141),(124,70,184),(88,205,197),(164,249,234)],'causalite':[(131,45,38),(178,68,48),(235,121,66),(255,202,112)],'axiomite':[(102,87,54),(150,130,78),(207,188,116),(255,238,168)],'paradox':[(113,23,104),(166,35,145),(220,69,190),(255,157,229)]}
clusters=[[(2,2),(3,2),(2,3),(4,3)],[(12,2),(13,3),(11,3),(12,4)],[(3,11),(4,12),(2,13),(5,13)],[(11,11),(12,11),(13,12),(11,13)],[(7,5),(8,5),(7,6)],[(8,9),(9,9),(8,10)]]
texroot=root/'src/main/resources/assets/veilbound/textures/block'
for ore, colors in ore_palettes.items():
  for deep in (False,True):
    pal,mat=(deep_palette,deep_base) if deep else (stone_palette,stone_base)
    px=[]
    for frame in range(8):
      framepx=[[list(pal[mat[y][x]])+[255] for x in range(16)] for y in range(16)]
      phase=0.5+0.5*math.sin(frame/8*2*math.pi)
      for ci,cluster in enumerate(clusters):
        for j,(x,y) in enumerate(cluster):
          idx=(ci+j+frame//2)%3; base=colors[3] if ((ci*3+j+frame)%7)==0 else colors[min(2,idx)]
          c=[min(255,v+int(8*phase)) for v in base]+[255]; framepx[y][x]=c
          if j==0 and x>0: framepx[y][x-1]=[max(0,int(v*.72)) for v in colors[0]]+[255]
      for row in framepx:
        for p in row: px.extend(p)
    name=('deepslate_' if deep else '')+ore+'_ore.png'
    (texroot/name).write_bytes(png_rgba(16,128,px))

px=[]
for y in range(16):
  for x in range(16):
    border=x in (0,15) or y in (0,15); ring=((x-7.5)**2+(y-7.5)**2)
    if border: c=(31,37,43,255)
    elif 18<ring<34: c=(50,118,137,255)
    elif ring<=10: c=(224,105,54,255)
    else: c=(42,48,55,255)
    px.extend(c)
(texroot/'boundary_dynamo.png').write_bytes(png_rgba(16,16,px))
print('VEILBOUND_0161_APPLY=PASS')
