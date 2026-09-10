package dev.futurae.veilbound.client.screen;

import dev.futurae.veilbound.energy.TransducerTier;
import dev.futurae.veilbound.menu.DimensionalTransducerMenu;
import java.text.NumberFormat;
import java.util.Locale;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/** Dynamo-inspired transducer UI: Matter left, DE center, FE right. */
public final class DimensionalTransducerScreen extends AbstractContainerScreen<DimensionalTransducerMenu> {
    private static final NumberFormat NUMBERS = NumberFormat.getIntegerInstance(Locale.US);
    private static final int BAR_BG = 0xFF373737;
    private static final int MATTER_FILL = 0xFF653F88;
    private static final int DE_FILL = 0xFF5577CC;
    private static final int FE_FILL = 0xFFB4533A;

    public DimensionalTransducerScreen(DimensionalTransducerMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title, 236, 196);
        inventoryLabelX = 37;
        inventoryLabelY = 100;
        titleLabelX = 12;
        titleLabelY = 10;
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
        extractTransparentBackground(graphics);
        int x = leftPos;
        int y = topPos;
        VanillaGuiStyle.panel(graphics, x, y, imageWidth, imageHeight);
        VanillaGuiStyle.inset(graphics, x + 8, y + 32, imageWidth - 16, 66);

        drawVerticalMeter(graphics, x + 22, y + 42, 14, 46, menu.matterPercent(), MATTER_FILL);
        VanillaGuiStyle.slot(graphics, x + 57, y + 59);
        drawVerticalMeter(graphics, x + 111, y + 38, 18, 54, menu.dePercent(), DE_FILL);
        drawVerticalMeter(graphics, x + 199, y + 42, 14, 46, menu.energyPercent(), FE_FILL);
    }

    private static void drawVerticalMeter(GuiGraphicsExtractor g, int x, int y, int w, int h, int percent, int fill) {
        g.fill(x, y, x + w, y + h, VanillaGuiStyle.SHADOW);
        g.fill(x + 1, y + 1, x + w - 1, y + h - 1, VanillaGuiStyle.LIGHT);
        g.fill(x + 2, y + 2, x + w - 2, y + h - 2, BAR_BG);
        int inner = h - 4;
        int filled = inner * Math.max(0, Math.min(100, percent)) / 100;
        if (filled > 0) g.fill(x + 2, y + h - 2 - filled, x + w - 2, y + h - 2, fill);
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
        graphics.centeredText(font, title, imageWidth / 2, 10, VanillaGuiStyle.TEXT);
        graphics.centeredText(font, Component.translatable("screen.veilbound.transducer.matter"), 29, 34, VanillaGuiStyle.TEXT);
        graphics.centeredText(font, Component.translatable("screen.veilbound.transducer.de"), 120, 30, VanillaGuiStyle.TEXT);
        graphics.centeredText(font, Component.translatable("screen.veilbound.transducer.fe"), 206, 34, VanillaGuiStyle.TEXT);
        graphics.text(font, Component.translatable("screen.veilbound.transducer.input"), 48, 45, VanillaGuiStyle.MUTED_TEXT, false);

        graphics.text(font, Component.literal(NUMBERS.format(menu.storedMatter()) + " / " + NUMBERS.format(menu.matterCapacity())), 12, 91, VanillaGuiStyle.MUTED_TEXT, false);
        graphics.centeredText(font, Component.literal(NUMBERS.format(menu.dimensionalEnergy()) + " / " + NUMBERS.format(menu.dimensionalEnergyCapacity())), 120, 91, VanillaGuiStyle.MUTED_TEXT);
        Component feText = Component.literal(NUMBERS.format(menu.storedForgeEnergy()) + " / " + NUMBERS.format(menu.forgeEnergyCapacity()));
        graphics.text(font, feText, Math.max(136, 224 - font.width(feText)), 91, VanillaGuiStyle.MUTED_TEXT, false);

        TransducerTier tier = TransducerTier.values()[menu.tierLevel() - 1];
        graphics.text(font, Component.translatable("screen.veilbound.transducer.rate", NUMBERS.format(tier.maxDimensionalEnergyPerCycle())), 82, 76, VanillaGuiStyle.MUTED_TEXT, false);
        graphics.text(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, VanillaGuiStyle.TEXT, false);
    }
}
