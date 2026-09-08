from pathlib import Path
import base64, io, json, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent
payload = ci / 'transducer-pass.tar.gz.b64'
if not payload.is_file():
    raise SystemExit('missing transducer pass payload')

archive_bytes = base64.b64decode(payload.read_text(encoding='ascii'))
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as archive:
    archive.extractall(root)

# Remove the old flat cube-all textures. The replacement models use a dynamo-inspired lower casing,
# inset side panel, and a raised animated tier core instead.
tex = root / 'src/main/resources/assets/veilbound/textures/block'
for kind in ('dimensional', 'resonant', 'phase', 'causal'):
    (tex / f'{kind}_transducer.png').unlink(missing_ok=True)

menus = root / 'src/main/java/dev/futurae/veilbound/registry/VeilboundMenus.java'
text = menus.read_text(encoding='utf-8')
if 'import dev.futurae.veilbound.menu.DimensionalTransducerMenu;' not in text:
    text = text.replace(
        'import dev.futurae.veilbound.menu.BoundaryDynamoMenu;\n',
        'import dev.futurae.veilbound.menu.BoundaryDynamoMenu;\n'
        'import dev.futurae.veilbound.menu.DimensionalTransducerMenu;\n', 1)
registration = '''\n    public static final DeferredHolder<MenuType<?>, MenuType<DimensionalTransducerMenu>> DIMENSIONAL_TRANSDUCER =\n            MENUS.register("dimensional_transducer", () -> IMenuTypeExtension.create(DimensionalTransducerMenu::new));\n'''
if 'MenuType<DimensionalTransducerMenu>> DIMENSIONAL_TRANSDUCER' not in text:
    marker = '''    public static final DeferredHolder<MenuType<?>, MenuType<BoundaryDynamoMenu>> BOUNDARY_DYNAMO =\n            MENUS.register("boundary_dynamo", () -> IMenuTypeExtension.create(BoundaryDynamoMenu::new));\n'''
    if marker not in text:
        raise SystemExit('could not locate Boundary Dynamo menu registration')
    text = text.replace(marker, marker + registration, 1)
menus.write_text(text, encoding='utf-8')

client = root / 'src/main/java/dev/futurae/veilbound/client/VeilboundClient.java'
text = client.read_text(encoding='utf-8')
if 'import dev.futurae.veilbound.client.screen.DimensionalTransducerScreen;' not in text:
    marker = 'import dev.futurae.veilbound.client.screen.DomainControlsScreen;\n'
    if marker not in text:
        raise SystemExit('could not locate client screen imports')
    text = text.replace(marker, marker + 'import dev.futurae.veilbound.client.screen.DimensionalTransducerScreen;\n', 1)
registration = '        event.register(VeilboundMenus.DIMENSIONAL_TRANSDUCER.get(), DimensionalTransducerScreen::new);\n'
if registration not in text:
    marker = '        event.register(VeilboundMenus.BOUNDARY_DYNAMO.get(), BoundaryDynamoScreen::new);\n'
    if marker not in text:
        raise SystemExit('could not locate menu-screen registration')
    text = text.replace(marker, marker + registration, 1)
client.write_text(text, encoding='utf-8')

lang = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
data = json.loads(lang.read_text(encoding='utf-8'))
data.update({
    'screen.veilbound.transducer.matter': 'Matter',
    'screen.veilbound.transducer.de': 'DE',
    'screen.veilbound.transducer.fe': 'FE',
    'screen.veilbound.transducer.input': 'Matter Input',
    'screen.veilbound.transducer.rate': 'Throughput: %s DE/cycle',
})
# These chat/status strings belonged to the old no-GUI interaction path.
data.pop('message.veilbound.transducer.status', None)
data.pop('message.veilbound.transducer.absorbed', None)
lang.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# Patch/reconstruction backup files are not runtime source and should never ship in a clean tree.
for path in (root / 'src').rglob('*.orig'):
    path.unlink()

required = [
    root / 'src/main/java/dev/futurae/veilbound/menu/DimensionalTransducerMenu.java',
    root / 'src/main/java/dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java',
    root / 'src/main/java/dev/futurae/veilbound/block/entity/DimensionalTransducerBlockEntity.java',
]
for kind in ('dimensional', 'resonant', 'phase', 'causal'):
    required.extend([
        root / f'src/main/resources/assets/veilbound/models/block/{kind}_transducer.json',
        root / f'src/main/resources/assets/veilbound/textures/block/{kind}_transducer_casing.png',
        root / f'src/main/resources/assets/veilbound/textures/block/{kind}_transducer_panel.png',
        root / f'src/main/resources/assets/veilbound/textures/block/{kind}_transducer_core.png',
        root / f'src/main/resources/assets/veilbound/textures/block/{kind}_transducer_core.png.mcmeta',
    ])
for path in required:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f'transducer pass missing: {path.relative_to(root)}')

be = (root / 'src/main/java/dev/futurae/veilbound/block/entity/DimensionalTransducerBlockEntity.java').read_text(encoding='utf-8')
screen = (root / 'src/main/java/dev/futurae/veilbound/client/screen/DimensionalTransducerScreen.java').read_text(encoding='utf-8')
if 'MATTER_INPUT_SLOT' not in be or 'Matter enters through the dedicated GUI slot' not in (root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeTransducerCoordinator.java').read_text(encoding='utf-8'):
    raise SystemExit('transducer interaction path did not apply')
for marker in ('menu.matterPercent()', 'menu.dePercent()', 'menu.energyPercent()'):
    if marker not in screen:
        raise SystemExit(f'transducer meter layout missing: {marker}')
if 'VeilboundMenus.DIMENSIONAL_TRANSDUCER' not in client.read_text(encoding='utf-8'):
    raise SystemExit('transducer screen registration missing')

print('VEILBOUND_0167_TRANSDUCER_PASS=PASS gui=matter_left_de_center_fe_right matter_slot=present tiers=4 raised_core=animated vanilla_style=PASS')
