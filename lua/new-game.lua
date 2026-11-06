-- Create a single-player game from the main menu (run in the MainMenu state, where GameSetupLogic is loaded).
-- Mirrors the Play Now path (after SalukiSwift/civ6-deity newgame.py): every setting has to be written
-- before BuildHeadlessGameSetup, which resets missing or invalid values to defaults.
-- Override any of these globals before running this file.
local C = {
  ruleset    = RULESET    or "RULESET_STANDARD",   -- base game; RULESET_EXPANSION_2 for Gathering Storm
  difficulty = DIFFICULTY or "DIFFICULTY_PRINCE",
  speed      = SPEED      or "GAMESPEED_QUICK",
  map_script = MAP_SCRIPT or "Pangaea.lua",
  map_size   = MAP_SIZE   or "MAPSIZE_STANDARD",
  leader     = LEADER     or "LEADER_GILGAMESH",
  game_seed  = GAME_SEED  or 20261106,
  map_seed   = MAP_SEED   or 20261106,
}
local ok, err = pcall(function()
  GameConfiguration.SetToDefaults()
  GameConfiguration.SetRuleSet(C.ruleset)
  GameConfiguration.SetValue("GAME_HANDICAP", DB.MakeHash(C.difficulty))
  GameConfiguration.SetValue("GAME_SPEED_TYPE", DB.MakeHash(C.speed))
  GameConfiguration.SetValue("GAME_SYNC_RANDOM_SEED", C.game_seed)
  MapConfiguration.SetScript(C.map_script)
  MapConfiguration.SetValue("MAP_SIZE", DB.MakeHash(C.map_size))
  MapConfiguration.SetValue("RANDOM_SEED", C.map_seed)
  PlayerConfigurations[0]:SetLeaderTypeName(C.leader)
  BuildHeadlessGameSetup()
  RebuildPlayerParameters(true)
  GameSetup_RefreshParameters()
  ReleasePlayerParameters()
  HideGameSetup()
  print("NEWGAME|seeds|" .. tostring(GameConfiguration.GetValue("GAME_SYNC_RANDOM_SEED")) .. "|" .. tostring(MapConfiguration.GetValue("RANDOM_SEED")))
  Network.HostGame(ServerType.SERVER_TYPE_NONE)
end)
print("NEWGAME|" .. tostring(ok) .. "|" .. tostring(err))
