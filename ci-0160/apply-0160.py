from pathlib import Path
import json
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

def replace(path, old, new):
    p = root / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'expected source fragment missing: {path}')
    p.write_text(text.replace(old, new), encoding='utf-8')

replace('gradle.properties', 'mod_version=0.1.59-dev', 'mod_version=0.1.60-dev')

policy_src = Path(__file__).with_name('BreachCombatPolicy.java')
policy_dst = root / 'src/main/java/dev/futurae/veilbound/breach/BreachCombatPolicy.java'
policy_dst.write_text(policy_src.read_text(encoding='utf-8'), encoding='utf-8')

replace('src/main/java/dev/futurae/veilbound/breach/BreachRuntimePolicy.java',
'''    private final BreachSpawnPolicy spawnPolicy;\n    private final BreachHazardPolicy hazardPolicy;\n''',
'''    private final BreachSpawnPolicy spawnPolicy;\n    private final BreachHazardPolicy hazardPolicy;\n    private final BreachCombatPolicy combatPolicy;\n''')
replace('src/main/java/dev/futurae/veilbound/breach/BreachRuntimePolicy.java',
'''        this(fractureDeltaPerEvaluation, fractureThreshold, maximumFractureMeter, maxOpenBreaches,\n                stitcherRange, stitcherDimensionalEnergyCosts, spawnPolicy, BreachHazardPolicy.developmentDefault());\n''',
'''        this(fractureDeltaPerEvaluation, fractureThreshold, maximumFractureMeter, maxOpenBreaches,\n                stitcherRange, stitcherDimensionalEnergyCosts, spawnPolicy, BreachHazardPolicy.developmentDefault(),\n                BreachCombatPolicy.developmentDefault());\n''')
replace('src/main/java/dev/futurae/veilbound/breach/BreachRuntimePolicy.java',
'''            BreachSpawnPolicy spawnPolicy,\n            BreachHazardPolicy hazardPolicy) {\n        Objects.requireNonNull(fractureDeltaPerEvaluation, "fractureDeltaPerEvaluation");\n        Objects.requireNonNull(stitcherDimensionalEnergyCosts, "stitcherDimensionalEnergyCosts");\n        this.spawnPolicy = Objects.requireNonNull(spawnPolicy, "spawnPolicy");\n        this.hazardPolicy = Objects.requireNonNull(hazardPolicy, "hazardPolicy");\n''',
'''            BreachSpawnPolicy spawnPolicy,\n            BreachHazardPolicy hazardPolicy) {\n        this(fractureDeltaPerEvaluation, fractureThreshold, maximumFractureMeter, maxOpenBreaches,\n                stitcherRange, stitcherDimensionalEnergyCosts, spawnPolicy, hazardPolicy,\n                BreachCombatPolicy.developmentDefault());\n    }\n\n    public BreachRuntimePolicy(\n            Map<StabilityBand, Double> fractureDeltaPerEvaluation,\n            double fractureThreshold,\n            double maximumFractureMeter,\n            int maxOpenBreaches,\n            double stitcherRange,\n            Map<BreachSeverity, Long> stitcherDimensionalEnergyCosts,\n            BreachSpawnPolicy spawnPolicy,\n            BreachHazardPolicy hazardPolicy,\n            BreachCombatPolicy combatPolicy) {\n        Objects.requireNonNull(fractureDeltaPerEvaluation, "fractureDeltaPerEvaluation");\n        Objects.requireNonNull(stitcherDimensionalEnergyCosts, "stitcherDimensionalEnergyCosts");\n        this.spawnPolicy = Objects.requireNonNull(spawnPolicy, "spawnPolicy");\n        this.hazardPolicy = Objects.requireNonNull(hazardPolicy, "hazardPolicy");\n        this.combatPolicy = Objects.requireNonNull(combatPolicy, "combatPolicy");\n''')
replace('src/main/java/dev/futurae/veilbound/breach/BreachRuntimePolicy.java',
'    public BreachHazardPolicy hazardPolicy() { return hazardPolicy; }\n',
'    public BreachHazardPolicy hazardPolicy() { return hazardPolicy; }\n    public BreachCombatPolicy combatPolicy() { return combatPolicy; }\n')

replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeStabilityPolicyReloadListener.java',
'import dev.futurae.veilbound.breach.BreachRuntimePolicy;\n',
'import dev.futurae.veilbound.breach.BreachRuntimePolicy;\nimport dev.futurae.veilbound.breach.BreachCombatPolicy;\n')
replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeStabilityPolicyReloadListener.java',
'''                BreachHazardPolicy hazardPolicy = new BreachHazardPolicy(hazardBands, particleInterval);\n\n                BreachRuntimePolicy breachPolicy = new BreachRuntimePolicy(\n''',
'''                BreachHazardPolicy hazardPolicy = new BreachHazardPolicy(hazardBands, particleInterval);\n\n                BreachCombatPolicy fallbackCombat = fallbackBreach.combatPolicy();\n                JsonObject combat = object(breach, "intruder_combat");\n                BreachCombatPolicy combatPolicy = new BreachCombatPolicy(\n                        integer(combat, "crawler_snare_ticks", fallbackCombat.crawlerSnareTicks()),\n                        integer(combat, "crawler_mining_fatigue_ticks", fallbackCombat.crawlerMiningFatigueTicks()),\n                        integer(combat, "stalker_darkness_ticks", fallbackCombat.stalkerDarknessTicks()),\n                        integer(combat, "stalker_weakness_ticks", fallbackCombat.stalkerWeaknessTicks()),\n                        longValue(combat, "wraith_de_drain", fallbackCombat.wraithDimensionalEnergyDrain()),\n                        decimal(combat, "wraith_fracture_shock", fallbackCombat.wraithFractureShock()),\n                        integer(combat, "wraith_weakness_ticks", fallbackCombat.wraithWeaknessTicks()));\n\n                BreachRuntimePolicy breachPolicy = new BreachRuntimePolicy(\n''')
replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeStabilityPolicyReloadListener.java',
'''                        stitcherCosts,\n                        spawnPolicy,\n                        hazardPolicy);\n''',
'''                        stitcherCosts,\n                        spawnPolicy,\n                        hazardPolicy,\n                        combatPolicy);\n''')

replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeBreachCoordinator.java',
'import dev.futurae.veilbound.entity.BreachLinkedCreature;\n',
'''import dev.futurae.veilbound.entity.BreachLinkedCreature;\nimport dev.futurae.veilbound.entity.NullWraithEntity;\nimport dev.futurae.veilbound.entity.RiftStalkerEntity;\nimport dev.futurae.veilbound.entity.VoidCrawlerEntity;\n''')
replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeBreachCoordinator.java',
'import net.minecraft.network.chat.Component;\n',
'''import net.minecraft.network.chat.Component;\nimport net.minecraft.world.effect.MobEffectInstance;\nimport net.minecraft.world.effect.MobEffects;\n''')
replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeBreachCoordinator.java',
'import net.neoforged.neoforge.event.entity.EntityMobGriefingEvent;\n',
'''import net.neoforged.neoforge.event.entity.EntityMobGriefingEvent;\nimport net.neoforged.neoforge.event.entity.living.LivingDamageEvent;\n''')
replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeBreachCoordinator.java',
'''    public void onMobGrief(EntityMobGriefingEvent event) {\n        if (event.getEntity() instanceof BreachLinkedCreature) event.setCanGrief(false);\n    }\n\n''',
'''    public void onMobGrief(EntityMobGriefingEvent event) {\n        if (event.getEntity() instanceof BreachLinkedCreature) event.setCanGrief(false);\n    }\n\n    /** Distinct post-hit pressure for creatures still linked to a currently-open Breach. */\n    public void onLivingDamagePost(LivingDamageEvent.Post event) {\n        if (!(event.getEntity() instanceof ServerPlayer target) || event.getHealthDamage() <= 0.0F) return;\n        Entity attacker = event.getSource().getEntity();\n        if (!(attacker instanceof BreachLinkedCreature linked)) return;\n        UUID ownerId = linked.veilboundDomainOwnerId().orElse(null);\n        UUID breachId = linked.veilboundSourceBreachId().orElse(null);\n        if (ownerId == null || breachId == null) return;\n        DomainRecord record = runtime.domains().getRecord(ownerId).orElse(null);\n        if (record == null || !record.state().coreActive()) return;\n        if (!record.identity().dimensionId().equals(target.level().dimension().identifier().toString())) return;\n        if (record.state().breaches().stream().noneMatch(b -> b.open() && b.id().equals(breachId))) return;\n\n        var combat = runtime.stabilityPolicy().policy().breachPolicy().combatPolicy();\n        ServerLevel level = (ServerLevel) target.level();\n        if (attacker instanceof VoidCrawlerEntity) {\n            addEffect(target, MobEffects.SLOWNESS, combat.crawlerSnareTicks());\n            addEffect(target, MobEffects.MINING_FATIGUE, combat.crawlerMiningFatigueTicks());\n            level.sendParticles(ParticleTypes.SCULK_SOUL, target.getX(), target.getY() + 0.35D, target.getZ(), 8, 0.25D, 0.15D, 0.25D, 0.02D);\n            return;\n        }\n        if (attacker instanceof RiftStalkerEntity) {\n            addEffect(target, MobEffects.DARKNESS, combat.stalkerDarknessTicks());\n            addEffect(target, MobEffects.WEAKNESS, combat.stalkerWeaknessTicks());\n            level.sendParticles(ParticleTypes.REVERSE_PORTAL, target.getX(), target.getY() + 1.0D, target.getZ(), 12, 0.3D, 0.6D, 0.3D, 0.05D);\n            return;\n        }\n        if (attacker instanceof NullWraithEntity) {\n            long drain = Math.min(record.state().dimensionalEnergy(), combat.wraithDimensionalEnergyDrain());\n            if (drain > 0) record.state().consumeDimensionalEnergy(drain);\n            double maxFracture = runtime.stabilityPolicy().policy().breachPolicy().maximumFractureMeter();\n            record.state().setFractureMeter(Math.min(maxFracture, record.state().fractureMeter() + combat.wraithFractureShock()));\n            addEffect(target, MobEffects.WEAKNESS, combat.wraithWeaknessTicks());\n            level.sendParticles(ParticleTypes.SOUL, target.getX(), target.getY() + 1.0D, target.getZ(), 14, 0.35D, 0.65D, 0.35D, 0.03D);\n            ServerPlayer owner = level.getServer().getPlayerList().getPlayer(ownerId);\n            if (owner != null && drain > 0) owner.sendSystemMessage(Component.translatable("message.veilbound.breach.wraith_core_drain", drain), true);\n        }\n    }\n\n    private static void addEffect(ServerPlayer player, net.minecraft.core.Holder<net.minecraft.world.effect.MobEffect> effect, int ticks) {\n        if (ticks > 0) player.addEffect(new MobEffectInstance(effect, ticks, 0));\n    }\n\n''')

replace('src/main/java/dev/futurae/veilbound/Veilbound.java',
'        NeoForge.EVENT_BUS.addListener(BREACHES::onMobGrief);\n',
'        NeoForge.EVENT_BUS.addListener(BREACHES::onMobGrief);\n        NeoForge.EVENT_BUS.addListener(BREACHES::onLivingDamagePost);\n')
p = root / 'src/main/java/dev/futurae/veilbound/Veilbound.java'
t = p.read_text(encoding='utf-8')
dup = '        NeoForge.EVENT_BUS.addListener(EventPriority.HIGHEST, VEIL_BOUNDARY::onBreakBlock);\n' * 2
if dup in t:
    p.write_text(t.replace(dup, '        NeoForge.EVENT_BUS.addListener(EventPriority.HIGHEST, VEIL_BOUNDARY::onBreakBlock);\n'), encoding='utf-8')

replace('src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeVeilforgedEquipmentCoordinator.java',
'''        if(band==ArmorBand.CAUSAL && event.getNewDamage()>=defender.getHealth()\n                && !event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {\n''',
'''        float healthDamageAfterAbsorption=Math.max(0F,event.getNewDamage()-defender.getAbsorptionAmount());\n        if(band==ArmorBand.CAUSAL && healthDamageAfterAbsorption>=defender.getHealth()\n                && !event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {\n''')

p = root / 'src/main/resources/data/veilbound/veilbound/balance/domain_stability.json'
data = json.loads(p.read_text(encoding='utf-8'))
data['breach']['intruder_combat'] = {
    'crawler_snare_ticks': 80,
    'crawler_mining_fatigue_ticks': 60,
    'stalker_darkness_ticks': 80,
    'stalker_weakness_ticks': 80,
    'wraith_de_drain': 5000,
    'wraith_fracture_shock': 4.0,
    'wraith_weakness_ticks': 100,
}
p.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

p = root / 'src/main/resources/assets/veilbound/lang/en_us.json'
lang = json.loads(p.read_text(encoding='utf-8'))
lang['codex.veilbound.breaches.3'] = 'Void Crawlers snare movement/mining; Rift Stalkers cloud sight and weaken; Null Wraith strikes drain Core DE and add fracture pressure. Their physical drops remain progression resources.'
lang['message.veilbound.breach.wraith_core_drain'] = 'A Null Wraith tore %s DE from your Dimensional Core.'
p.write_text(json.dumps(lang, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

replace('docs/player-guide.md',
'Instability can naturally form Breaches. Breaches produce hazards, Veil creatures, and materials that are deliberately excluded from normal Matter transmutation.\n',
'Instability can naturally form Breaches. Breaches produce hazards, Veil creatures, and materials that are deliberately excluded from normal Matter transmutation. Breach fauna now apply distinct dimensional pressure: Crawlers snare movement/mining, Stalkers inflict darkness/weakness, and Null Wraith strikes drain source-Domain Core DE while adding fracture. Combat values are reloadable in the Domain stability balance datapack.\n')

(root / 'docs/0.1.60-validation.md').write_text('''# Veilbound 0.1.60 validation\n\n- Void Crawler hits snare movement and mining.\n- Rift Stalker hits apply darkness and weakness.\n- Null Wraith hits drain configured Core DE, add bounded fracture shock, and weaken.\n- Effects require real health damage and a still-open linked Breach.\n- `intruder_combat` is reloadable in `domain_stability.json`.\n- Causal rollback now accounts for absorption hearts before deciding lethality.\n- Duplicate Veil boundary break-listener registration is removed.\n''', encoding='utf-8')
