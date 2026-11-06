# Rig setup

The game runs on a Windows laptop: an Asus Zenbook Duo with a Core Ultra 9 185H, 32 GB of RAM, Intel Arc graphics and Windows 11 Home. The agents run elsewhere and reach the laptop over Tailscale and SSH. A Linux server without a GPU can't run Civ 6 usefully: Proton builds don't expose FireTuner, and software rendering is too slow.

## One-time setup on the game PC

1. Install Civ 6 from Steam. civ6-mcp expects the **Gathering Storm** ruleset, and the CivBench scenario saves also need the New Frontier Pass civs. Check ownership with `lua/list-mods.lua`: files on disk don't mean the account owns the DLC.
2. Run `windows/apply-fast-settings.ps1`. It backs up the three options files, then sets:
   - borderless window at the primary screen's size (default 2880x1800) with the UI at 200%, no audio, no intro video
   - every graphics option at minimum, with shadows, bloom, lighting, clouds and AO off
   - quick movement and quick combat, no combat camera, no vignettes or historic-moment animations
   - start in strategic view, tutorial and expansion intro screens marked as seen
   - `EnableTuner 1`, `AutoEndTurn 0`
3. Run `windows/setup-civ6-mcp.ps1` (clones civ6-mcp and runs `uv sync`).
4. Run `windows/register-tasks.ps1`. It registers these interactive scheduled tasks:
   - `Civ6Launch`: starts the DX11 build
   - `Civ6Shot` and `Civ6Click`: screenshot and click
   - `Civ6Exec`: runs any PowerShell file in the desktop session, via `remote/zexec.sh`
   - `Civ6Mcp`: the long-lived civ6-mcp HTTP server
5. On the agent machine, run `remote/tunnel.sh` (an SSH tunnel to the server). Agents then use `http://127.0.0.1:18771/mcp`.
6. Optional, for watching: `windows/open-warroom.ps1` opens the war room page full screen on the second screen. It reads its URL from a local `warroom.json`.

## Things that were not obvious

- **SSH sessions can't open windows.** OpenSSH on Windows runs in session 0, so a GUI started from SSH never shows on the desktop. Launching, screenshots and clicks go through scheduled tasks with `LogonType Interactive`, which run in the signed-in user's desktop session. Register them with the identity from `WindowsIdentity.GetCurrent().Name`, not `$env:USERDOMAIN` (that is `WORKGROUP` over SSH).
- **FireTuner works from SSH.** The game listens on `127.0.0.1:4318`, and loopback TCP crosses sessions, so the MCP server can run in the SSH session. It takes about 2 minutes after launch to open.
- **The Lua state list alternates ID and name** (`['0', 'Main State', '1', 'DebugHotloadCache', '2', 'IntroScreen', ...]`). Send commands to the number before the name, not to the list index.
- **Output lines start with `O<NUL><state>: `.** Strip the prefix, NUL byte included.
- **The copyright screen ignores synthetic clicks.** Run `OnAccept()` in the `IntroScreen` state instead (`lua/accept-eula.lua`).
- **Front-end save names include the extension** (`0A_GROUND_CONTROL.Civ6Save`).
- **OneDrive moves Documents.** Civ 6 writes saves to `OneDrive\Documents\My Games`, while civ6-mcp looks in `%USERPROFILE%\Documents\My Games`. A directory junction from the second path to the first fixes it.
- **"One or more Mods has not been purchased"** means the save needs DLC the Steam account doesn't own, even when the files are installed. `Modding.GetInstalledMods()` reports `Allowance=false` for those.
- **FireTuner takes one client at a time.** While a client is connected, the game stops listening on 4318. So civ6-mcp runs as one long-lived HTTP server (`windows/civ_mcp_http.py`) that holds the only connection. Agents connect to that server, and nothing else talks to the tuner during a game. Over SSH stdio, every agent restart killed the server abruptly, and civ6-mcp warns that an abrupt tuner disconnect can crash the game.
- **The MCP SDK runs the server lifespan once per client session.** civ6-mcp opens its tuner connection in the lifespan, so the HTTP wrapper shares one lifespan across sessions. It also no-ops civ6-mcp's side web API on port 8000, whose shutdown took the main server down.
- **Use the DX11 build on the Zenbook Duo.** DX12 crashed with "Device Reset" (DXGI 0x887a0005) when the second screen turned on. Steam asks which build to launch the first time; tick "Always use this option".
- **Borderless, not fullscreen.** Exclusive fullscreen minimizes when you click the other screen. `FullScreen 2` is borderless at the desktop size, and `UIUpscale 1.0` is 200%.
- **Tailscale DNS may be off on the game PC.** If it is, the war room browser maps the share hostname to the server's tailnet IP with `--host-resolver-rules`, in its own profile, so the laptop's DNS settings stay as they are.
- **civ6-mcp is built for Gathering Storm.** On the base game, `get_game_overview` fails on `GetFavor()`, and about 60 Lua call sites use Rise and Fall or Gathering Storm functions. The HTTP wrapper rewrites them to `CB_` stand-ins (see the README). It adds only new names: the game's own UI checks names like `Game.GetEras` to detect expansions, so redefining those could change its behavior.
- **Never call engine getters blindly.** A probe that called every `Get*` method on game objects crashed the game; `pcall` doesn't catch a native crash. civ6-mcp's `restart_and_load` brought it back in about 2.5 minutes.
- **Base-game alliances unlock with Civil Service**, not Diplomatic Service (`GameInfo.DiplomaticActions`), and science victory takes 5 space projects (3 for Mars).
- **Pin civ6-mcp's run id per game.** It names its diary and logs `{kind}_{civ}_{seed}_{run id}` and draws a new run id at every server start, so a mid-game restart would hand the agent an empty diary. `run_game.py --prepare` sets `CIV_MCP_RUN_ID` to the game id.
- **Headless Claude Code drops thinking text** unless you pass `--thinking-display summarized`; the `showThinkingSummaries` setting only applies to interactive sessions.
- **Windows OpenSSH limits:** a command line holds about 32K characters, and stdin piped to PowerShell hangs past about 8 KB. `remote/zput.sh` sends files in 4 KB chunks, and the archive keeps its request small.
- **A save load can move a unit.** civ6-mcp closes the leader screen by clicking CONTINUE GAME near the bottom of the screen. When the screen closes between mouse down and mouse up, the click lands on the map and walks the selected unit toward it: game 1's first try lost turn 1 when its settler walked two tiles off the river. It depends on timing (the same load was clean an hour earlier), so `run_game.py --prepare` checks that every unit has full moves after loading a turn-start save, and loads it again if not. civ6-mcp's own mid-game recovery reloads have the same risk; the archive's per-turn saves and screenshots show it if it happens.
- **PowerShell doesn't expand `%USERPROFILE%`**, and single-quoted `$env:USERPROFILE` stays literal. Paths sent to the game PC go through `[Environment]::ExpandEnvironmentVariables`.
- **FireTuner is disabled in every multiplayer mode, hotseat included.** Multi-agent games need the file-based MCP Bridge UI mod from Johnor12/civ6-mcp, or single-player puppeteering (civ6-mcp `docs/agent-vs-agent.md`).
