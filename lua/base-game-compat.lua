-- Base-game compatibility for civ6-mcp, which is written for Gathering Storm.
-- windows/civ_mcp_http.py rewrites each Lua chunk civ6-mcp sends, and prepends this file (as one line, so
-- error line numbers still match) whenever the rewritten chunk uses a CB_ name:
--   obj:GetFavor(...)        -> obj:CB_GetFavor(...)      (every method in CB_FALLBACK)
--   Game.GetEras()           -> CB_ERAS()
--   Game.GetWorldCongress()  -> CB_WC()
--   GameInfo.Governors       -> (GameInfo.Governors or CB_EMPTY)   (and the other expansion tables)
-- Each CB_ name calls the real function when the game has it and returns a neutral value when it doesn't:
-- favor 0, loyalty 100, no governors, no ages, no World Congress. Base-game science victory points are the
-- 5 space projects. The game's own scripts never see a change: base UI code checks names such as
-- Game.GetEras to detect expansions, so this only adds new CB_ names.
-- Never call engine getters blindly here: an unknown getter can crash the game, and pcall doesn't catch that.
if not CB_READY then
  local function zero() return 0 end
  local function none() return nil end
  local function no() return false end
  local function empty() return {} end
  CB_EMPTY = setmetatable({}, { __call = function() return function() return nil end end,
    __index = function() return nil end })
  local governors = { GetGovernorPoints = zero, GetGovernorPointsSpent = zero, GetGovernor = none,
    CanAppoint = no, CanPromoteGovernor = no, HasGovernor = no }
  local identity = { GetLoyalty = function() return 100 end, GetLoyaltyPerTurn = zero,
    GetMaxLoyalty = function() return 100 end, GetTurnsToConversion = function() return -1 end }
  local function eraNow() local q = Players[Game.GetLocalPlayer()]; return q and q:GetEra() or 0 end
  local eras = { GetCurrentEra = eraNow, GetPlayerCurrentScore = zero, GetPlayerGoldenAgeThreshold = zero,
    GetPlayerDarkAgeThreshold = zero, HasGoldenAge = no, HasDarkAge = no, HasHeroicGoldenAge = no,
    HasHeroicAge = no, GetPlayerNumAllowedCommemorations = zero, GetPlayerCommemorateChoices = empty,
    GetPlayerActiveCommemorations = empty }
  local congress = { IsInSession = no, GetMeetingStatus = function() return { TurnsLeft = -1 } end,
    GetResolutions = empty, GetProposals = empty, GetVotesandFavorCost = function() return 0, 0 end }
  local space = { "PROJECT_LAUNCH_EARTH_SATELLITE", "PROJECT_LAUNCH_MOON_LANDING", "PROJECT_LAUNCH_MARS_REACTOR",
    "PROJECT_LAUNCH_MARS_HABITATION", "PROJECT_LAUNCH_MARS_HYDROPONICS" }
  local function spaceDone(stats)
    local n = 0
    for _, t in ipairs(space) do
      local row = GameInfo.Projects[t]
      if row and stats.GetNumProjectsAdvanced and stats:GetNumProjectsAdvanced(row.Index) > 0 then n = n + 1 end
    end
    return n
  end
  function CB_ERAS() if Game.GetEras then return Game.GetEras() end return eras end
  function CB_WC() if Game.GetWorldCongress then return Game.GetWorldCongress() end return congress end
  -- method name -> what it returns when the game lacks it (called with the object as self)
  CB_FALLBACK = {
    GetFavor = zero, GetGovernors = function() return governors end,
    GetAllianceType = function() return -1 end, GetAllianceLevel = zero, GetGrievancesAgainst = zero,
    GetResourceStockpileCap = zero, GetResourceAccumulationPerTurn = zero, GetResourceImportPerTurn = zero,
    GetUnitResourceDemandPerTurn = zero, GetCulturalIdentity = function() return identity end,
    GetDiplomaticVictoryPoints = zero, GetScienceVictoryPoints = spaceDone,
    GetScienceVictoryPointsTotalNeeded = function() return #space end, GetNextRebelledCity = none,
  }
  CB_PATCHED = {}
  function CB_ADD(obj)
    local mt = obj and getmetatable(obj)
    local idx = (type(mt) == "table") and mt.__index or nil
    if type(idx) ~= "table" or CB_PATCHED[idx] then return end
    for name, fallback in pairs(CB_FALLBACK) do
      local real = idx[name]
      idx["CB_" .. name] = function(self, ...)
        if real then return real(self, ...) end
        return fallback(self, ...)
      end
    end
    CB_PATCHED[idx] = true
  end
  CB_READY = true
end
-- Add the CB_ methods to each class civ6-mcp calls them on. Cities appear only once someone has one, so
-- that part retries on each chunk until it succeeds.
if not CB_CLASSES_DONE then
  local me = Game.GetLocalPlayer()
  local p = (me ~= nil and me >= 0) and Players[me] or nil
  if p then
    CB_ADD(p); CB_ADD(p:GetDiplomacy()); CB_ADD(p:GetResources()); CB_ADD(p:GetStats()); CB_ADD(p:GetCities())
    CB_CLASSES_DONE = true
  end
end
if not CB_CITY_DONE then
  for i = 0, 63 do
    local q = Players[i]
    if q and q:IsAlive() then
      for _, c in q:GetCities():Members() do CB_ADD(c); CB_CITY_DONE = true; break end
    end
    if CB_CITY_DONE then break end
  end
end
