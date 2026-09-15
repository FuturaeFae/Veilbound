from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java'
text = path.read_text(encoding='utf-8')

# Use vanilla item sprites for the two-state selector rather than text labels/custom art.
if 'import net.minecraft.world.item.Items;' not in text:
    text = text.replace('import net.minecraft.world.item.ItemStack;\n', 'import net.minecraft.world.item.ItemStack;\nimport net.minecraft.world.item.Items;\n')

text = text.replace(
'''    private static final int SEARCH_DEBOUNCE_TICKS = 6;\n    private static final NumberFormat NUMBERS = NumberFormat.getIntegerInstance(Locale.US);\n''',
'''    private static final int SEARCH_DEBOUNCE_TICKS = 6;\n    private static final int MODE_SWITCH_X = 52;\n    private static final int MODE_SWITCH_Y = 30;\n    private static final int MODE_SEGMENT = 20;\n    private static final int MODE_SWITCH_WIDTH = MODE_SEGMENT * 2;\n    private static final int MODE_SWITCH_HEIGHT = 18;\n    private static final NumberFormat NUMBERS = NumberFormat.getIntegerInstance(Locale.US);\n''')

old_widget = '''        addRenderableWidget(Button.builder(\n                        Component.literal(mode == Mode.INVENTORY ? "Craft" : "Inv"),\n                        button -> toggleMode())\n                .bounds(left + 52, top + 30, 40, 18).build());\n\n'''
if old_widget not in text:
    raise SystemExit('mode switch finalize: old text toggle widget not found')
text = text.replace(old_widget, '')

needle = '''        int mouseX = (int) event.x();\n        int mouseY = (int) event.y();\n\n        // ME-terminal convention: shift-clicking a real vanilla player slot sends that stack into\n'''
replacement = '''        int mouseX = (int) event.x();\n        int mouseY = (int) event.y();\n\n        // True two-state mode switch: the left chest segment selects Inventory and the right\n        // crafting-table segment selects Crafting. This is intentionally not a Button toggle.\n        if (event.button() == 0 && handleModeSwitchClick(mouseX, mouseY)) return true;\n\n        // ME-terminal convention: shift-clicking a real vanilla player slot sends that stack into\n'''
if needle not in text:
    raise SystemExit('mode switch finalize: mouse click insertion point not found')
text = text.replace(needle, replacement, 1)

old_toggle = '''    private void toggleMode() {\n        mode = mode == Mode.INVENTORY ? Mode.CRAFTING : Mode.INVENTORY;\n        VeilInventoryPreferences.setCraftingMode(mode == Mode.CRAFTING);\n        searchDebounce = 0;\n        if (mode == Mode.CRAFTING) {\n            clearSelectedRecipe(false);\n            requestCraftables(0);\n        } else {\n            clearSelectedRecipe(false);\n            requestInventory(0);\n        }\n        rebuildWidgets();\n    }\n\n'''
new_toggle = '''    private boolean handleModeSwitchClick(int mouseX, int mouseY) {\n        int x = panelLeft() + MODE_SWITCH_X;\n        int y = panelTop() + MODE_SWITCH_Y;\n        if (!inside(mouseX, mouseY, x, y, MODE_SWITCH_WIDTH, MODE_SWITCH_HEIGHT)) return false;\n        setMode(mouseX < x + MODE_SEGMENT ? Mode.INVENTORY : Mode.CRAFTING);\n        return true;\n    }\n\n    private void setMode(Mode nextMode) {\n        if (nextMode == null || nextMode == mode) return;\n        mode = nextMode;\n        VeilInventoryPreferences.setCraftingMode(mode == Mode.CRAFTING);\n        searchDebounce = 0;\n        clearSelectedRecipe(false);\n        if (mode == Mode.CRAFTING) requestCraftables(0);\n        else requestInventory(0);\n        rebuildWidgets();\n    }\n\n'''
if old_toggle not in text:
    raise SystemExit('mode switch finalize: old toggle method not found')
text = text.replace(old_toggle, new_toggle, 1)

render_needle = '''        VanillaGuiStyle.playerInventorySlots(graphics, left, top,\n                VeilInventoryMenu.PLAYER_X, VeilInventoryMenu.PLAYER_Y, VeilInventoryMenu.HOTBAR_Y);\n\n        if (!snapshot.allowed()) {\n'''
render_replacement = '''        VanillaGuiStyle.playerInventorySlots(graphics, left, top,\n                VeilInventoryMenu.PLAYER_X, VeilInventoryMenu.PLAYER_Y, VeilInventoryMenu.HOTBAR_Y);\n        renderModeSwitch(graphics, mouseX, mouseY);\n\n        if (!snapshot.allowed()) {\n'''
if render_needle not in text:
    raise SystemExit('mode switch finalize: render insertion point not found')
text = text.replace(render_needle, render_replacement, 1)

method_insert = '''    private void renderModeSwitch(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {\n        int x = panelLeft() + MODE_SWITCH_X;\n        int y = panelTop() + MODE_SWITCH_Y;\n        boolean inventorySelected = mode == Mode.INVENTORY;\n\n        // One segmented control with two explicit states, modelled after vanilla recessed/raised\n        // controls. The selected half reads as the active switch position rather than a push button.\n        graphics.fill(x, y, x + MODE_SWITCH_WIDTH, y + MODE_SWITCH_HEIGHT, 0xFF373737);\n        drawModeSegment(graphics, x + 1, y + 1, inventorySelected, new ItemStack(Items.CHEST));\n        drawModeSegment(graphics, x + MODE_SEGMENT, y + 1, !inventorySelected, new ItemStack(Items.CRAFTING_TABLE));\n        graphics.fill(x + MODE_SEGMENT - 1, y + 1, x + MODE_SEGMENT, y + MODE_SWITCH_HEIGHT - 1, 0xFF555555);\n\n        if (inside(mouseX, mouseY, x, y, MODE_SEGMENT, MODE_SWITCH_HEIGHT)) {\n            graphics.setTooltipForNextFrame(font, Component.literal("Inventory"), mouseX, mouseY);\n        } else if (inside(mouseX, mouseY, x + MODE_SEGMENT, y, MODE_SEGMENT, MODE_SWITCH_HEIGHT)) {\n            graphics.setTooltipForNextFrame(font, Component.literal("Crafting"), mouseX, mouseY);\n        }\n    }\n\n    private void drawModeSegment(GuiGraphicsExtractor graphics, int x, int y, boolean selected, ItemStack icon) {\n        int width = MODE_SEGMENT - 1;\n        int height = MODE_SWITCH_HEIGHT - 2;\n        if (selected) {\n            // Selected switch position: bright top/left, dark bottom/right, matching vanilla buttons.\n            graphics.fill(x, y, x + width, y + height, 0xFFC6C6C6);\n            graphics.fill(x, y, x + width, y + 1, 0xFFFFFFFF);\n            graphics.fill(x, y, x + 1, y + height, 0xFFFFFFFF);\n            graphics.fill(x, y + height - 1, x + width, y + height, 0xFF555555);\n            graphics.fill(x + width - 1, y, x + width, y + height, 0xFF555555);\n        } else {\n            // Inactive side is recessed to make the control read as a two-position switch.\n            graphics.fill(x, y, x + width, y + height, 0xFF8B8B8B);\n            graphics.fill(x, y, x + width, y + 1, 0xFF555555);\n            graphics.fill(x, y, x + 1, y + height, 0xFF555555);\n        }\n        graphics.item(icon, x + 1, y);\n        if (!selected) graphics.fill(x + 1, y + 1, x + width - 1, y + height - 1, 0x33000000);\n    }\n\n'''
insert_before = '    private void renderInventoryGrid(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {'
if insert_before not in text:
    raise SystemExit('mode switch finalize: render method insertion point missing')
text = text.replace(insert_before, method_insert + insert_before, 1)

# Strict regression audit.
for marker in (
    'MODE_SWITCH_WIDTH = MODE_SEGMENT * 2',
    'handleModeSwitchClick',
    'setMode(mouseX < x + MODE_SEGMENT ? Mode.INVENTORY : Mode.CRAFTING)',
    'new ItemStack(Items.CHEST)',
    'new ItemStack(Items.CRAFTING_TABLE)',
    'renderModeSwitch(graphics, mouseX, mouseY)',
):
    if marker not in text:
        raise SystemExit(f'mode switch finalize missing marker: {marker}')
if 'Component.literal(mode == Mode.INVENTORY ? "Craft" : "Inv")' in text or 'private void toggleMode()' in text:
    raise SystemExit('mode switch finalize: text-button toggle survived')

path.write_text(text, encoding='utf-8')
print('VEILBOUND_0167_MODE_SWITCH=PASS control=segmented state=explicit inventory_icon=vanilla_chest crafting_icon=vanilla_crafting_table text_toggle=removed')
