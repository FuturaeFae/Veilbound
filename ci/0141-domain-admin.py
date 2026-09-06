#!/usr/bin/env python3
from pathlib import Path
import runpy

# Apply the original, known-good 0.1.41 Domain-admin patch first.
runpy.run_path('ci/0141-domain-admin-base.py', run_name='__main__')

root = Path(__import__('sys').argv[1]).resolve()
p = root / 'src/main/java/dev/futurae/veilbound/platform/neoforge/NeoForgeDomainAdminCommandCoordinator.java'
s = p.read_text()

# Minecraft 26.2 moved cached identity lookup to Services.nameToIdCache() and uses
# record-style NameAndId accessors.
s = s.replace('import com.mojang.authlib.GameProfile;\n', '')
s = s.replace(
    'import net.minecraft.server.level.ServerPlayer;\n',
    'import net.minecraft.server.level.ServerPlayer;\nimport net.minecraft.server.players.NameAndId;\n')
s = s.replace(
    'public final class NeoForgeDomainAdminCommandCoordinator {',
    '// Minecraft 26.2 replacement for legacy getProfileCache().get(token)\npublic final class NeoForgeDomainAdminCommandCoordinator {',
    1)
s = s.replace(
    '.map(player -> player.getGameProfile().getName());',
    '.map(player -> player.nameAndId().name());')
s = s.replace(
    '            ServerPlayer online = server.getPlayerList().getPlayer(uuid);\n'
    '            return new ResolvedTarget(uuid, online == null ? uuid.toString() : online.getGameProfile().getName());\n',
    '            ServerPlayer online = server.getPlayerList().getPlayer(uuid);\n'
    '            String cachedName = server.services().nameToIdCache().get(uuid).map(NameAndId::name).orElse(null);\n'
    '            String label = online != null ? online.nameAndId().name() : cachedName != null ? cachedName : uuid.toString();\n'
    '            return new ResolvedTarget(uuid, label);\n')
s = s.replace(
    '            return new ResolvedTarget(online.getUUID(), online.getGameProfile().getName());\n',
    '            return new ResolvedTarget(online.getUUID(), online.nameAndId().name());\n')
s = s.replace(
    '        if (server.getProfileCache() != null) {\n'
    '            GameProfile profile = server.getProfileCache().get(token).orElse(null);\n'
    '            if (profile != null && profile.getId() != null) {\n'
    '                String label = profile.getName() == null || profile.getName().isBlank()\n'
    '                        ? profile.getId().toString()\n'
    '                        : profile.getName();\n'
    '                return new ResolvedTarget(profile.getId(), label);\n'
    '            }\n'
    '        }\n',
    '        NameAndId cached = server.services().nameToIdCache().get(token).orElse(null);\n'
    '        if (cached != null) {\n'
    '            String label = cached.name() == null || cached.name().isBlank() ? cached.id().toString() : cached.name();\n'
    '            return new ResolvedTarget(cached.id(), label);\n'
    '        }\n')

if 'getProfileCache() != null' in s or 'GameProfile profile =' in s:
    raise SystemExit('Legacy profile-cache code remained after 26.2 compatibility patch')
if 'server.services().nameToIdCache().get(token)' not in s:
    raise SystemExit('26.2 offline-name resolver was not installed')

p.write_text(s)
print('Applied Minecraft 26.2 NameAndId/offline target compatibility')