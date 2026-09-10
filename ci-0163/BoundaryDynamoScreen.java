package dev.futurae.veilbound.client.screen;

import dev.futurae.veilbound.block.entity.BoundaryDynamoBlockEntity;
import dev.futurae.veilbound.menu.BoundaryDynamoMenu;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;

/** Dedicated Boundary Dynamo panel: two machine slots and live FE/burn/charging telemetry. */
public final class BoundaryDynamoScreen extends AbstractContainerScreen<BoundaryDynamoMenu> {
    private static final int PANEL = 0xF014111C;
    private static final int HEADER = 0xF029193A;
    private static final int BORDER = 0xFF9F7AC8;
    private static final int SLOT = 0xFF211B2B;
    private static final int SLOT_EDGE = 0xFF665774;
    private static final int FE_BG = 0xFF191A24;
    private static final int FE_FILL = 0xFF62C8F4;
    private static final int BURN_BG = 0xFF241A18;
    private static final int BURN_FILL = 0xFFF1A65A;

    public BoundaryDynamoScreen(BoundaryDynamoMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title, 236, 196);
        this.inventoryLabelX = 37;
        this.inventoryLabelY = 100;
        this.titleLabelX = 12;
        this.titleLabelY = 11;
    }

    @Override
    public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
        extractTransparentBackground(graphics);
        int x = leftPos;
        int y = topPos;
        graphics.fill(x, y, x + imageWidth, y + imageHeight, PANEL);
        graphics.fill(x, y, x + imageWidth, y + 34, HEADER);
        graphics.fill(x, y + 33, x + imageWidth, y + 34, BORDER);

        // True machine slots: no decorative dead inventory cells.
        drawSlot(graphics, x + 42, y + 67);
        drawSlot(graphics, x + 86, y + 67);

        // FE buffer bar.
        graphics.fill(x + 126, y + 49, x + 220, y + 61, FE_BG);
        int feWidth = 92 * menu.energyPercent() / 100;
        if (feWidth > 0) graphics.fill(x + 127, y + 50, x + 127 + feWidth, y + 60, FE_FILL);

        // Current fuel burn progress.
        graphics.fill(x + 126, y + 72, x + 220, y + 82, BURN_BG);
        int burnWidth = 92 * menu.burnPercent() / 100;
        if (burnWidth > 0) graphics.fill(x + 127, y + 73, x + 127 + burnWidth, y + 81, BURN_FILL);
    }

    private static void drawSlot(GuiGraphicsExtractor graphics, int x, int y) {
        graphics.fill(x, y, x + 20, y + 20, SLOT_EDGE);
        graphics.fill(x + 1, y + 1, x + 19, y + 19, SLOT);
    }

    @Override
    protected void extractLabels(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
        graphics.text(font, title, titleLabelX, titleLabelY, 0xFFF3ECFF, false);
        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.fuel"), 36, 48, 0xFFF1B675, false);
        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.charge"), 79, 48, 0xFF9EDCFF, false);

        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.energy",
                menu.storedForgeEnergy(), BoundaryDynamoBlockEntity.FE_CAPACITY), 126, 38, 0xFFBDEEFF, false);
        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.generation",
                BoundaryDynamoBlockEntity.FE_PER_BURN_TICK), 126, 62, 0xFFC8C0D2, false);
        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.burn",
                menu.burnTicks(), menu.totalBurnTicks()), 126, 74, 0xFFF0BE8E, false);
        graphics.text(font, Component.translatable("screen.veilbound.boundary_dynamo.output",
                BoundaryDynamoBlockEntity.MAX_FE_OUTPUT), 126, 85, 0xFFC8C0D2, false);

        Component chargeStatus;
        int statusColor;
        if (menu.chargeStack().isEmpty()) {
            chargeStatus = Component.translatable("screen.veilbound.boundary_dynamo.status.empty");
            statusColor = 0xFF9C94A8;
        } else if (menu.lastChargeTransfer() > 0) {
            chargeStatus = Component.translatable("screen.veilbound.boundary_dynamo.status.charging", menu.lastChargeTransfer());
            statusColor = 0xFF83E6B0;
        } else if (menu.storedForgeEnergy() <= 0) {
            chargeStatus = Component.translatable("screen.veilbound.boundary_dynamo.status.waiting");
            statusColor = 0xFFFFC47D;
        } else {
            chargeStatus = Component.translatable("screen.veilbound.boundary_dynamo.status.full");
            statusColor = 0xFFB9A9CE;
        }
        graphics.text(font, chargeStatus, 12, 91, statusColor, false);
        graphics.text(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, 0xFFCFC6D8, false);
    }
}
