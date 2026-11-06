-- Create a hotseat game from the main menu (run in the MainMenu state over FireTuner, like new-game.lua): HUMANS
-- human seats, then AI seats up to PLAYERS, base ruleset. Hosting the session ends in the staging room; start it
-- from there through the MCP Bridge front-end context (Network.LaunchGame()), since FireTuner stops answering
-- inside a multiplayer session. Override any of these globals before running this file.
local C = {
  ruleset    = RULESET    or "RULESET_STANDARD",
  difficulty = DIFFICULTY or "DIFFICULTY_PRINCE",
  speed      = SPEED      or "GAMESPEED_ONLINE",
  map_script = MAP_SCRIPT or "Pangaea.lua",
  map_size   = MAP_SIZE   or "MAPSIZE_STANDARD",
  game_seed  = GAME_SEED  or 20261106,
  map_seed   = MAP_SEED   or 20261106,
  -- seat order: humans first; names show on the turn-change screen
  leaders    = LEADERS    or { "LEADER_GILGAMESH", "LEADER_PERICLES", "LEADER_CLEOPATRA", "LEADER_TRAJAN",
                               "LEADER_BARBAROSSA", "LEADER_PHILIP_II", "LEADER_T_ROOSEVELT", "LEADER_PEDRO" },
  names      = NAMES      or { "Opus A", "Opus B", "Opus C", "Opus D" },
  humans     = HUMANS     or 4,
}
local ok, err = pcall(function()
  GameConfiguration.SetToDefaults(GameModeTypes.HOTSEAT)
  GameConfiguration.SetRuleSet(C.ruleset)
  GameConfiguration.SetValue("GAME_HANDICAP", DB.MakeHash(C.difficulty))
  GameConfiguration.SetValue("GAME_SPEED_TYPE", DB.MakeHash(C.speed))
  GameConfiguration.SetValue("GAME_SYNC_RANDOM_SEED", C.game_seed)
  MapConfiguration.SetScript(C.map_script)
  MapConfiguration.SetValue("MAP_SIZE", DB.MakeHash(C.map_size))
  MapConfiguration.SetValue("RANDOM_SEED", C.map_seed)
  GameConfiguration.SetParticipatingPlayerCount(#C.leaders)
  for i, leader in ipairs(C.leaders) do
    local pc = PlayerConfigurations[i - 1]
    if i <= C.humans then
      pc:SetSlotStatus(SlotStatus.SS_TAKEN)
      pc:SetHotseatName(C.names[i] or ("Agent " .. i))
    else
      pc:SetSlotStatus(SlotStatus.SS_COMPUTER)
    end
    pc:SetLeaderTypeName(leader)
  end
  for i = #C.leaders, 11 do
    local pc = PlayerConfigurations[i]
    if pc and pc:GetSlotStatus() ~= SlotStatus.SS_CLOSED then pc:SetSlotStatus(SlotStatus.SS_CLOSED) end
  end
  BuildHeadlessGameSetup()
  RebuildPlayerParameters(true)
  GameSetup_RefreshParameters()
  ReleasePlayerParameters()
  HideGameSetup()
  for i = 0, #C.leaders - 1 do
    local pc = PlayerConfigurations[i]
    print("NEWHOTSEAT|slot|" .. i .. "|" .. tostring(pc:GetSlotStatus()) .. "|" .. tostring(pc:GetLeaderTypeName()) .. "|" .. tostring(pc:GetPlayerName()))
  end
  print("NEWHOTSEAT|hotseat|" .. tostring(GameConfiguration.IsHotseat()) .. "|players|" .. tostring(GameConfiguration.GetParticipatingPlayerCount()))
  Network.HostGame(ServerType.SERVER_TYPE_HOTSEAT)
end)
print("NEWHOTSEAT|" .. tostring(ok) .. "|" .. tostring(err))
