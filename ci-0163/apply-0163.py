from pathlib import Path
import json
import shutil
import sys

root = Path(sys.argv[1]).resolve()
here = Path(__file__).resolve().parent

# Version and registry bootstrap.
p = root / "gradle.properties"
s = p.read_text(encoding="utf-8")
if "mod_version=0.1.62-dev" not in s:
    raise SystemExit("expected 0.1.62 baseline version")
p.write_text(s.replace("mod_version=0.1.62-dev", "mod_version=0.1.63-dev", 1), encoding="utf-8")

p = root / "src/main/java/dev/futurae/veilbound/Veilbound.java"
s = p.read_text(encoding="utf-8")
needle = "        VeilboundBlockEntities.register(modBus);\n"
if needle not in s:
    raise SystemExit("Veilbound menu registry insertion point missing")
p.write_text(s.replace(needle, needle + "        dev.futurae.veilbound.registry.VeilboundMenus.register(modBus);\n", 1), encoding="utf-8")

# Replace the temporary 9-slot Dynamo container with a real two-slot menu and synchronized telemetry.
p = root / "src/main/java/dev/futurae/veilbound/block/entity/BoundaryDynamoBlockEntity.java"
s = p.read_text(encoding="utf-8")
s = s.replace("import net.minecraft.world.inventory.ChestMenu;\nimport net.minecraft.world.inventory.MenuType;\n",
              "import dev.futurae.veilbound.menu.BoundaryDynamoMenu;\nimport net.minecraft.world.inventory.ContainerData;\n")
s = s.replace(" * any item exposing NeoForge's item energy capability, including the Spatial Generator. The other\n * seven slots exist only because the vanilla 9x1 container screen is intentionally reused; they are\n * hard-disabled for insertion.</p>",
              " * any item exposing NeoForge's item energy capability, including the Spatial Generator.</p>")
s = s.replace("public static final int INVENTORY_SIZE = 9;", "public static final int INVENTORY_SIZE = 2;")
marker = "    private int totalBurnTicks;\n"
telemetry = """    private int totalBurnTicks;\n    private int lastChargeTransfer;\n    private final ContainerData menuData = new ContainerData() {\n        @Override\n        public int get(int index) {\n            return switch (index) {\n                case 0 -> energy.getAmountAsInt();\n                case 1 -> burnTicks;\n                case 2 -> totalBurnTicks;\n                case 3 -> lastChargeTransfer;\n                default -> 0;\n            };\n        }\n\n        @Override\n        public void set(int index, int value) {\n            switch (index) {\n                case 0 -> energy.setStored(value);\n                case 1 -> burnTicks = Math.max(0, value);\n                case 2 -> totalBurnTicks = Math.max(0, value);\n                case 3 -> lastChargeTransfer = Math.max(0, value);\n                default -> { }\n            }\n        }\n\n        @Override\n        public int getCount() {\n            return BoundaryDynamoMenu.DATA_COUNT;\n        }\n    };\n"""
if marker not in s:
    raise SystemExit("Dynamo telemetry insertion point missing")
s = s.replace(marker, telemetry, 1)
s = s.replace("    public int totalBurnTicks() { return totalBurnTicks; }\n",
              "    public int totalBurnTicks() { return totalBurnTicks; }\n    public ContainerData menuData() { return menuData; }\n", 1)
s = s.replace("        boolean changed = false;\n", "        boolean changed = false;\n        dynamo.lastChargeTransfer = 0;\n", 1)
s = s.replace("        if (dynamo.tryChargeInstalledItem()) changed = true;\n",
              "        int transferred = dynamo.tryChargeInstalledItem();\n        if (transferred > 0) {\n            dynamo.lastChargeTransfer = transferred;\n            changed = true;\n        }\n", 1)
s = s.replace("    private boolean tryChargeInstalledItem() {\n        if (energy.getAmountAsInt() <= 0) return false;\n",
              "    private int tryChargeInstalledItem() {\n        if (energy.getAmountAsInt() <= 0) return 0;\n", 1)
s = s.replace("        if (chargeStack.isEmpty()) return false;\n", "        if (chargeStack.isEmpty()) return 0;\n", 1)
s = s.replace("        if (target == null) return false;\n", "        if (target == null) return 0;\n", 1)
s = s.replace("        if (request <= 0) return false;\n", "        if (request <= 0) return 0;\n", 1)
s = s.replace("            if (inserted <= 0) return false;\n", "            if (inserted <= 0) return 0;\n", 1)
s = s.replace("            if (extracted != inserted) return false;\n", "            if (extracted != inserted) return 0;\n", 1)
s = s.replace("            return true;\n        }\n    }\n", "            return inserted;\n        }\n    }\n", 1)
s = s.replace("        // Minecraft 26.2 replacement for ChestMenu.oneRow: bind the one-row screen to this container.\n        return new ChestMenu(MenuType.GENERIC_9x1, containerId, inventory, this, 1);",
              "        return new BoundaryDynamoMenu(containerId, inventory, this);", 1)
p.write_text(s, encoding="utf-8")

# Client registration for the new custom screen.
p = root / "src/main/java/dev/futurae/veilbound/client/VeilboundClient.java"
s = p.read_text(encoding="utf-8")
s = s.replace("import dev.futurae.veilbound.client.screen.VeilInventoryScreen;\n",
              "import dev.futurae.veilbound.client.screen.VeilInventoryScreen;\nimport dev.futurae.veilbound.client.screen.BoundaryDynamoScreen;\n", 1)
s = s.replace("import dev.futurae.veilbound.registry.VeilboundBlockEntities;\n",
              "import dev.futurae.veilbound.registry.VeilboundBlockEntities;\nimport dev.futurae.veilbound.registry.VeilboundMenus;\n", 1)
s = s.replace("import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;\n",
              "import net.neoforged.neoforge.client.event.RegisterKeyMappingsEvent;\nimport net.neoforged.neoforge.client.event.RegisterMenuScreensEvent;\n", 1)
s = s.replace("        modBus.addListener(VeilboundClient::registerKeyMappings);\n",
              "        modBus.addListener(VeilboundClient::registerKeyMappings);\n        modBus.addListener(VeilboundClient::registerMenuScreens);\n", 1)
needle = "    private static void registerEnvironmentRenderers(RegisterCustomEnvironmentEffectRendererEvent event) {"
if needle not in s:
    raise SystemExit("client menu screen insertion point missing")
s = s.replace(needle,
              "    private static void registerMenuScreens(RegisterMenuScreensEvent event) {\n        event.register(VeilboundMenus.BOUNDARY_DYNAMO.get(), BoundaryDynamoScreen::new);\n    }\n\n" + needle,
              1)
p.write_text(s, encoding="utf-8")

# Copy the new dedicated menu, screen, and menu registry into the reconstructed source tree.
for staged, relative in {
    "BoundaryDynamoMenu.java": "src/main/java/dev/futurae/veilbound/menu/BoundaryDynamoMenu.java",
    "BoundaryDynamoScreen.java": "src/main/java/dev/futurae/veilbound/client/screen/BoundaryDynamoScreen.java",
    "VeilboundMenus.java": "src/main/java/dev/futurae/veilbound/registry/VeilboundMenus.java",
}.items():
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(here / staged, target)

# GUI language.
lang_path = root / "src/main/resources/assets/veilbound/lang/en_us.json"
lang = json.loads(lang_path.read_text(encoding="utf-8"))
lang["container.veilbound.boundary_dynamo"] = "Boundary Dynamo"
lang["tooltip.veilbound.boundary_dynamo"] = "Pre-Core FE generator • Fuel + item charging"
lang.update({
    "screen.veilbound.boundary_dynamo.fuel": "Fuel",
    "screen.veilbound.boundary_dynamo.charge": "Charge",
    "screen.veilbound.boundary_dynamo.energy": "FE: %s / %s",
    "screen.veilbound.boundary_dynamo.generation": "Generation: %s FE/t",
    "screen.veilbound.boundary_dynamo.burn": "Burn: %s / %s t",
    "screen.veilbound.boundary_dynamo.output": "Cable output: up to %s FE/t",
    "screen.veilbound.boundary_dynamo.status.empty": "Charge slot: insert an FE-capable item",
    "screen.veilbound.boundary_dynamo.status.charging": "Charging: +%s FE/t",
    "screen.veilbound.boundary_dynamo.status.waiting": "Charge slot: waiting for FE",
    "screen.veilbound.boundary_dynamo.status.full": "Charge slot: item full / no transfer",
})
lang_path.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

(root / "docs/0.1.63-validation.md").write_text(
    "# Veilbound 0.1.63 validation\n\n"
    "0.1.63 replaces the Boundary Dynamo's temporary generic 9-slot chest UI with a dedicated Veilbound machine menu and screen.\n\n"
    "Validated targets: exactly two machine slots (Fuel and Charge), live synchronized FE/burn/charging telemetry, custom bars/status text, shift-click routing, and retention of the 0.1.62 feature set.\n",
    encoding="utf-8",
)
