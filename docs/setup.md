# Rig setup

The game runs on a Windows laptop: an Asus Zenbook Duo with a Core Ultra 9 185H, 32 GB of RAM, Intel Arc graphics and Windows 11 Home. The agents run elsewhere and reach the laptop over Tailscale and SSH. A Linux server without a GPU can't run Civ 6 usefully: Proton builds don't expose FireTuner, and software rendering is too slow.

## One-time setup on the game PC

1. Install Civ 6 from Steam. civ6-mcp expects the **Gathering Storm** ruleset, and the CivBench scenario saves also need the New Frontier Pass civs. Check ownership with `lua/list-mods.lua`: files on disk don't mean the account owns the DLC.
2. Run `windows/apply-fast-settings.ps1`. It backs up the three options files, then sets:
   - windowed 1280x800, no audio, no intro video
   - every graphics option at minimum, with shadows, bloom, lighting, clouds and AO off
   - quick movement and quick combat, no combat camera, no vignettes or historic-moment animations
   - start in strategic view, tutorial and expansion intro screens marked as seen
   - `EnableTuner 1`, `AutoEndTurn 0`
3. Run `windows/setup-civ6-mcp.ps1` (clones civ6-mcp and runs `uv sync`).
4. Run `windows/register-tasks.ps1`. It registers `Civ6Launch`, `Civ6Shot` and `Civ6Click` as interactive scheduled tasks.

## Things that were not obvious

- **SSH sessions can't open windows.** OpenSSH on Windows runs in session 0, so a GUI started from SSH never shows on the desktop. Launching, screenshots and clicks go through scheduled tasks with `LogonType Interactive`, which run in the signed-in user's desktop session. Register them with the identity from `WindowsIdentity.GetCurrent().Name`, not `$env:USERDOMAIN` (that is `WORKGROUP` over SSH).
- **FireTuner works from SSH.** The game listens on `127.0.0.1:4318`, and loopback TCP crosses sessions, so the MCP server can run in the SSH session. It takes about 2 minutes after launch to open.
- **The Lua state list alternates ID and name** (`['0', 'Main State', '1', 'DebugHotloadCache', '2', 'IntroScreen', ...]`). Send commands to the number before the name, not to the list index.
- **Output lines start with `O<NUL><state>: `.** Strip the prefix, NUL byte included.
- **The copyright screen ignores synthetic clicks.** Run `OnAccept()` in the `IntroScreen` state instead (`lua/accept-eula.lua`).
- **Front-end save names include the extension** (`0A_GROUND_CONTROL.Civ6Save`).
- **OneDrive moves Documents.** Civ 6 writes saves to `OneDrive\Documents\My Games`, while civ6-mcp looks in `%USERPROFILE%\Documents\My Games`. A directory junction from the second path to the first fixes it.
- **"One or more Mods has not been purchased"** means the save needs DLC the Steam account doesn't own, even when the files are installed. `Modding.GetInstalledMods()` reports `Allowance=false` for those.
- **FireTuner is disabled in every multiplayer mode, hotseat included.** Multi-agent games need the file-based MCP Bridge UI mod from Johnor12/civ6-mcp, or single-player puppeteering (civ6-mcp `docs/agent-vs-agent.md`).
