from pathlib import Path
import base64, io, json, shutil, sys, tarfile

root = Path(sys.argv[1]).resolve()
ci = Path(__file__).resolve().parent
payload = ci / 'transducer-pass.tar.gz.b64'
if not payload.is_file():
    raise SystemExit('missing transducer pass payload')

archive_bytes = base64.b64decode(payload.read_text(encoding='ascii'))
with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as archive:
    archive.extractall(root)

# The menu source was added after the first compact bundle was cut. Stage it directly.
menu_payload = ci / 'DimensionalTransducerMenu.java'
menu_target = root / 'src/main/java/dev/futurae/veilbound/menu/DimensionalTransducerMenu.java'
if not menu_payload.is_file():
    raise SystemExit('missing direct transducer menu source payload')
menu_target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(menu_payload, menu_target)

# Deterministic 16px machine textures. Keep these inline rather than depending on an older archive:
# dark framed casing + tier material panel + animated raised core, based on the user's dynamo reference.
TEXTURES = {
    'causal_transducer_casing.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAyklEQVR4nO2SMQrCQBREX/zbpUuREyw2CymCpeAhLAVPIFh6vBSChYWFsI1ErMQrpPhLLCQxRYxCWn8zMMzMn2KiLMtrRpwBmC2PADxuBdfDlhACItKLi7VvtffT7hXQEADWWowxqGovdrVtgy5RluVgg2ny1gJEWZbXVVVhrf1qbtA5h/eeOI6ZAIQQMMb8ZBYRVBURAXgFdMlfQppnbcC/wbgGBmjnOU0KLvvNoHm+OgNQpx+m7Jz7OGNV/T5l7/1ggzrtmTIj7gmk8RyrPeUiJwAAAABJRU5ErkJggg==',
    'dimensional_transducer_casing.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAyElEQVR4nO2SMQrCQBREX/zb5QSC5RbCQhC9lWDpQQTBRhC8SC5gOheblIJY2ab4ixYxIWKMQlp/MzDMzM7CREkyvdPjDMBhMwYgza4s1hdCCIhIK572s1q73N7KgIoAsNZijEFVW7GprRs0iTzPOxuk2ejlC1GSTO9FUWCt/Wqu0DmH9544jhkAhBAwxvxkFhFUFREBKAOa5C8h1WN1wL9BvwYGaMxzxHx17jQfd5Ondtg+Zefcxxmr6vcpe+87G6TZ8H3K9LgHqpYdb/7j9yoAAAAASUVORK5CYII=',
    'phase_transducer_casing.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAu0lEQVR4nO2SMQrCQBREX/zb5RrbLWyR2wmWVoKVxE5JKXgCS9FOLLfLQVL8JRYhIUJMAmn9zcAwM3+KSbzPahacAciLGwDv14PjfkOMEREZxOL67LTnfNsEtASAtRZjDKo6iH1t16BPlGU52qCvBUi8z+qqqrDWTppbdM4RQiBNU1YAMUaMMbPMIoKqIiIATUCfnBPSPusC/g2WNTDA1zwPu/Wo+XS5j0/ZOfdzxqo6PeUQwmiDwSmz4D5Sth/Zm0RtugAAAABJRU5ErkJggg==',
    'resonant_transducer_casing.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAuElEQVR4nO2SMQrCQBREX/zb5RrbLWyRgwmiKDZ6MyUIYsBCkO1ykBR/iUVIiBCTQFp/MzDMzJ9iEu+zmgVnAC75A4BbfuWw3xBjREQGsXi+O+35dGwCWgLAWosxBlUdxL62a9AnyrIcbdDXAiTeZ3VVVVhrJ80tOucIIZCmKSuAGCPGmFlmEUFVERGAJqBPzglpn3UB/wbLGhjga5677XrUfC9e41N2zv2csapOTzmEMNpgcMosuA/yGB8ZD2N59gAAAABJRU5ErkJggg==',
    'causal_transducer_panel.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAArklEQVR4nGP08vL7z0ABYGFgYGB48uQJWZplZGQgBjAwMDB8fveWJM28QsIMDAwMDExkWY0EsBoQ2/KAMgMW1yhgVRzb8oDBMOIiihgLVpVYgGHERYZVM1rxuwDddGTxa0emMPx8Mpvh55PZuA24dmQKhiHImrEBFC/8fDKb4doRVJfg04xhALIhyHx8AGsgYtMU2/IAa+wQnZBwRS3FKRHuBVjaJssAGRkZsl0AAKlTPIBZNC+kAAAAAElFTkSuQmCC',
    'dimensional_transducer_panel.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAn0lEQVR4nGP08vL7z0ABYGFgYGB48uQJWZplZGQgBjAwMDB8fveWJM28QsIMDAwMDExkWY0EMAyQmXacQWbacbxsvAaQCljQBexWfWNYdsCZIcphLwMDFjbVXYBhwLIDzgxHHBYxZDE8xcqmugswwuBYjwYDA0Mbg1XJDaxshgNUdgGjl5ff/ydPnpCVEmVkZKgYBrC0TZYBMjIyZLsAAOAzPGeI/dTYAAAAAElFTkSuQmCC',
    'phase_transducer_panel.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAkUlEQVR4nGP08vL7z0ABYGFgYGB48uQJWZplZGQgBjAwMDB8fveWJM28QsIMDAwMDExkWY0EMAyYu2oHg4vNfKINYEEXSA7zgBu0fNJzhj1HEkkzgFSDMAxICj+Owj+6loFBTpofLj5vpSV+A6yDPxLldJwGDHwYkGoQQQPQDUIHFKdEuAtgaZssA2RkZMh2AQDVNzt9akHyVwAAAABJRU5ErkJggg==',
    'resonant_transducer_panel.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAr0lEQVR4nGP08vL7z0ABYGFgYGB48uQJWZplZGQgBjAwMDB8fveWJM28QsIMDAwMDEyk2vr83QcUPtEGrNm2l+H5uw8MkkIChA1Ys20vg4W9J4qYtYUxhmYGBgZEGCCDEC9nFD42m/G6gFjNBA14/u4DQ2BgJF4LcBoAs/nEwe2kG4DL2dgCF8MAfM4O8XLGcBGKAcQ6G6cB+EIbF4CnA1jaJssAGRkZsjQzMDAwAAAkQDZR0CWCzwAAAABJRU5ErkJggg==',
    'causal_transducer_core.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAABACAYAAAATffeWAAACK0lEQVR4nNVXMXLCQAwUHuhwwQfSky/Qe1JT+hfp3LiioeMXlNQMvb8APR9I446CFMwekk6yxWQyk6iDvZUlnbR3NynLxZ1+YFMPmM2XNH/7SL+/zruYg9l8SUQkyPz/W38R/xcRcn89ZmsyBxEy8MX7px0ByFXdUlW3Jhm4cKALBls3nUtGxIUOu6pbOmxXdNiuMjKMYyIFkPlCHoXGidg28ry8sDU5RYAmscI+7TcZiejZDxO0Mt/fyFbio6kG8PgKWTjgTqJkkYI23bLa+aiDqBXjS4bN1QM+MP31GE+BE0HmNqgHY2Q9ysJBhGytzYoILfDIGi+srxM9tUCTYegTsQt8XNdNZ4qMnsiUgp71034jvqhxOJ8SoWBtBvKwPYUqiB57iwUctLQAOIZK6EFklGGuHrxCFg44ECWLFLTpk8o7XP+4HvBavKwHXiF1LUw9iI6ycBAhA+eKnR2u1pHu4cmBLpg1ylpkEHGBsNZNl90LeNhElHAexaQsF3frYK3qlk77jXCu0/o672Qf2GG3JlnU4NZfBq8xFhn9YHYiz9ki84KnbYyMMnDe1lkrj91U9Ey446xb9h/qga5FOAV9N/L2H2a+FzyyHmXhIEK21iYH66Yzj3SQPTy9F7gji6wjE3pA9Oh7fZjysIFrYUl6YD06ENFhuzLxW3959MHQc0eTtaU+0KoMB15aGKqpBXpf1qMuIiCKPzr4SJvvhSg5i4CbrsmvvRe+AZ90fL3+DuKUAAAAAElFTkSuQmCC',
    'dimensional_transducer_core.png': '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',
    'phase_transducer_core.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAABACAYAAAATffeWAAACeklEQVR4nO2XQWvbMBTH/5ZlIXsUuk8weuxnSSgJhV1SCvsQO4yRUxk77LCPMCjrsayU9bPkWHbcLQxmCVm2dwhPkWwnWO06dugfAkn0/PeT9N7PcnJw8LLFI8R3DUxmCyRJAgBo2xZ3N1eDcUk3g+n8DMeHF7jXH8AYAwA0TYO6rlFVFb5/+7rb4O2bezfwk30ODKy1MMbAGIPb60sXx/w7+8rzHEVRoCgK5HkOKSWklBBCBLFuDbIs6xlwvhm21iJN02A6QQaT2cIFkKSULgO6c5Zl4JwjTVNMZottBkmSuPmShBCQUrrflAVjDIwxt0PhVQ8QBzb73DRNMGCMCb5ba1HXNZqmQdM0aNt2m8HdzVWwMACgtUZZlijLElprGGNQVZUzosJyu1BVVWCglHILS0VEdeDHujXoVphSymWglILW2mXixwaL+OnLEVbrJQC4i7smfhUCA71AenAzxerv1MGQHs0D0g/zcS8PgimcnJ4H9Q+g19Inp+fDBtP5Wa+ByGA0D4QQEEIAJjQYzQPOeQ8sUTxgjA2CBXhCHjBgy4Pu/AC4BhrFA2ttr62jeEBz7BqM5oExBlrrnsFoHtxeXw4aPPNg/xR6BtP5GbIsQ5qmOJLv3f/itRjPA3q0+4riAZn4iuIBBeJ3aACM5MEQmXbxgAF9HnDONxl4ogv/DQ/oROYrigdDXRnNg7qu4eOVWnkUD7TWUEoFGUTxgA4Xvp55EHk+IB7Qlr4S7wAAq/Uyjgf0IR0fXsTxoGsAII4H9L6AX6HBaB4MZTDqfEA8IKj4Rf207wv7eECK4gE9WH1F8YDOSy88gygeDGUQxYOuwWq9/A958AeIf6mBA4vSCwAAAABJRU5ErkJggg==',
    'resonant_transducer_core.png': 'iVBORw0KGgoAAAANSUhEUgAAABAAAABACAYAAAATffeWAAACM0lEQVR4nO1XwVLbQAx9krly6FcEGBJICNAO/z8d2iROiEnBfIulHooW7WY3MZND25loxjNe775nSWu9len09IviAONDwEUCUUXdtFAA+j4WzTt64gedCIgIq+c3TEZnYP7gV1WICFQVlXseERj45uo8AhsBAIhI3gNRDWAiAjODiKK3G6mIgN/nAoF32y5PYEB7Fry2bVQgAKuqCvcGFBF0XRfujebgbQwhqNsmVQ1x+7GfpzQHOWCaxJQoImCiAGTmre0yEr8DWQ/St6dzqgqUCCqX9TQE8xIJcUTgw/GWehOtLc70tH+UwOpfAdRNu1MPIoJOBKIa6mHZtJiMzkJtiCq6UjkDCGXMzJivfmF6fREKqpceePDd5BJVVQXwXj0wDwzcVw/YgxdPL5heX4CIonBs7NduEVjCPmtBkUQ1UqKcJnplyubgqAcfdtSDWA+sP6ibNkuQ7Q/8VwgAi6cXjIeDP6T7+oP0M54tN5EupB9YoPJ6YESz5Qb3N8PomSlT0QNb+GPR4NvtFZh5px6ceLCZB+eAWT0wM7f7WiBQ1aBIvqxzZay5HKye3zAeDqJS7qMH5FvddCe8HfWgbH+fIJsDK5ZsEnd5kPYHae9cN23//iDN/Gy5wXg4KFdjTg9s8eN8vSUqFk4UQnqsMzMe52t8nY6yx3xEkNY7EeH7zxUe7sf9+oPUDLzPsv8L5rbfxt7/C16FP90f1OvXLVHx5Dk9iASldLCkXhQPlv9TD34DO+AketR7RxAAAAAASUVORK5CYII='
}

tex = root / 'src/main/resources/assets/veilbound/textures/block'
tex.mkdir(parents=True, exist_ok=True)
for name, encoded in TEXTURES.items():
    (tex / name).write_bytes(base64.b64decode(encoded))
for kind in ('dimensional', 'resonant', 'phase', 'causal'):
    (tex / f'{kind}_transducer_core.png.mcmeta').write_text(
        json.dumps({'animation': {'frametime': 3, 'interpolate': True}}, indent=2) + '\n', encoding='utf-8')
    # Old flat cube texture is superseded by casing/panel/core model layers.
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
data.pop('message.veilbound.transducer.status', None)
data.pop('message.veilbound.transducer.absorbed', None)
lang.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

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
