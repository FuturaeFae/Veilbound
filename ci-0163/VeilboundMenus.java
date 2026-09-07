package dev.futurae.veilbound.registry;

import dev.futurae.veilbound.Veilbound;
import dev.futurae.veilbound.menu.BoundaryDynamoMenu;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.inventory.MenuType;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.extensions.IMenuTypeExtension;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Custom menu registrations for physical Veilbound machines. */
public final class VeilboundMenus {
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(Registries.MENU, Veilbound.MOD_ID);

    public static final DeferredHolder<MenuType<?>, MenuType<BoundaryDynamoMenu>> BOUNDARY_DYNAMO =
            MENUS.register("boundary_dynamo", () -> IMenuTypeExtension.create(BoundaryDynamoMenu::new));

    private VeilboundMenus() {}

    public static void register(IEventBus modBus) {
        MENUS.register(modBus);
    }
}
