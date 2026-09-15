from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / 'src/main/java/dev/futurae/veilbound/client/screen/VeilInventoryScreen.java'
text = path.read_text(encoding='utf-8')

# Replace the two generic text X buttons with compact pixel-drawn vanilla-style clear controls.
for block in (
'''        addRenderableWidget(Button.builder(Component.literal("×"), button -> clearSearch())
                .bounds(left + 174, top + 30, 16, 18).build());

''',
'''        addRenderableWidget(Button.builder(Component.literal("×"), button -> clearSelectedRecipe(true))
                .bounds(side + 50, top + 4, 14, 14).build());

''',
):
    if block not in text:
        raise SystemExit('close control finalize: expected old X button not found')
    text = text.replace(block, '', 1)

click_needle = '''        int mouseX = (int) event.x();
        int mouseY = (int) event.y();

'''
click_insert = '''        int mouseX = (int) event.x();
        int mouseY = (int) event.y();

        if (event.button() == 0 && handleClearControlClick(mouseX, mouseY)) return true;

'''
if click_needle not in text:
    raise SystemExit('close control finalize: mouse click insertion point missing')
text = text.replace(click_needle, click_insert, 1)

if '        renderModeSwitch(graphics, mouseX, mouseY);\n' in text:
    text = text.replace(
        '        renderModeSwitch(graphics, mouseX, mouseY);\n',
        '        renderModeSwitch(graphics, mouseX, mouseY);\n        renderClearControls(graphics, mouseX, mouseY);\n',
        1,
    )
else:
    needle = '''        VanillaGuiStyle.playerInventorySlots(graphics, left, top,
                VeilInventoryMenu.PLAYER_X, VeilInventoryMenu.PLAYER_Y, VeilInventoryMenu.HOTBAR_Y);
'''
    if needle not in text:
        raise SystemExit('close control finalize: render insertion point missing')
    text = text.replace(needle, needle + '        renderClearControls(graphics, mouseX, mouseY);\n', 1)

methods = r'''    private boolean handleClearControlClick(int mouseX, int mouseY) {
        int searchX = panelLeft() + 174;
        int searchY = panelTop() + 30;
        if (inside(mouseX, mouseY, searchX, searchY, 16, 18)) {
            clearSearch();
            return true;
        }
        if (mode == Mode.CRAFTING) {
            int recipeX = sideLeft() + 50;
            int recipeY = sideTop() + 4;
            if (inside(mouseX, mouseY, recipeX, recipeY, 14, 14)) {
                clearSelectedRecipe(true);
                return true;
            }
        }
        return false;
    }

    private void renderClearControls(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
        int searchX = panelLeft() + 174;
        int searchY = panelTop() + 30;
        boolean searchHover = inside(mouseX, mouseY, searchX, searchY, 16, 18);
        drawVanillaClearControl(graphics, searchX, searchY, 16, 18, searchHover);
        if (searchHover) {
            graphics.setTooltipForNextFrame(font, Component.literal("Clear search"), mouseX, mouseY);
        }

        if (mode == Mode.CRAFTING) {
            int recipeX = sideLeft() + 50;
            int recipeY = sideTop() + 4;
            boolean recipeHover = inside(mouseX, mouseY, recipeX, recipeY, 14, 14);
            drawVanillaClearControl(graphics, recipeX, recipeY, 14, 14, recipeHover);
            if (recipeHover) {
                graphics.setTooltipForNextFrame(font, Component.literal("Clear recipe"), mouseX, mouseY);
            }
        }
    }

    private void drawVanillaClearControl(
            GuiGraphicsExtractor graphics, int x, int y, int width, int height, boolean hovered) {
        graphics.fill(x, y, x + width, y + height, 0xFF373737);
        graphics.fill(x + 1, y + 1, x + width - 1, y + height - 1, 0xFFFFFFFF);
        int face = hovered ? 0xFFDCDCDC : 0xFFC6C6C6;
        graphics.fill(x + 2, y + 2, x + width - 1, y + height - 1, face);
        graphics.fill(x + width - 2, y + 2, x + width - 1, y + height - 1, 0xFF555555);
        graphics.fill(x + 2, y + height - 2, x + width - 1, y + height - 1, 0xFF555555);

        // Pixel-drawn X stays crisp at every GUI scale and does not inherit font baseline quirks.
        int cx = x + width / 2;
        int cy = y + height / 2;
        int ink = hovered ? 0xFF5A2020 : 0xFF3F3F3F;
        for (int i = -3; i <= 3; i++) {
            graphics.fill(cx + i, cy + i, cx + i + 1, cy + i + 1, ink);
            graphics.fill(cx + i, cy - i, cx + i + 1, cy - i + 1, ink);
        }
    }

'''
insert_before = '    private boolean handleScrollBarClick(int mouseX, int mouseY, int button) {'
if insert_before not in text:
    raise SystemExit('close control finalize: method insertion point missing')
text = text.replace(insert_before, methods + insert_before, 1)

# Minecraft 26.2 makes AbstractContainerScreen.tick() final; container screens use containerTick().
old_tick = '''    @Override
    public void tick() {
        super.tick();
'''
new_tick = '''    @Override
    protected void containerTick() {
'''
if old_tick in text:
    text = text.replace(old_tick, new_tick, 1)
elif '    protected void containerTick() {\n' not in text:
    raise SystemExit('close control finalize: terminal tick hook not recognized')

for marker in (
    'handleClearControlClick',
    'renderClearControls(graphics, mouseX, mouseY)',
    'drawVanillaClearControl',
    'Component.literal("Clear search")',
    'Component.literal("Clear recipe")',
    'protected void containerTick()',
):
    if marker not in text:
        raise SystemExit(f'close control finalize missing marker: {marker}')
if 'Button.builder(Component.literal("×")' in text:
    raise SystemExit('close control finalize: generic X button survived')
if 'public void tick()' in text:
    raise SystemExit('close control finalize: final tick override survived')

path.write_text(text, encoding='utf-8')
print('VEILBOUND_0167_CLEAR_CONTROLS=PASS x=pixel_drawn bevel=vanilla hover=polished tooltips=clear_search_clear_recipe generic_text_buttons=removed container_tick=26.2')
