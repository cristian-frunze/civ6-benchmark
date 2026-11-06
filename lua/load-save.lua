-- Load a single-player save from the main menu (run in the MainMenu state). Set SAVE_NAME first.
SAVE_NAME = SAVE_NAME or "0A_GROUND_CONTROL"
if not ExposedMembers then ExposedMembers = {} end
ExposedMembers.BenchLoad = "pending"
local function OnResults(fileList, qid)
  UI.CloseFileListQuery(qid)
  LuaEvents.FileListQueryResults.Remove(OnResults)
  local names = {}
  for i, s in ipairs(fileList) do
    names[#names+1] = tostring(s.Name)
    if s.Name == SAVE_NAME or s.Name == SAVE_NAME .. ".Civ6Save" then
      ExposedMembers.BenchLoad = "found"
      Network.LoadGame(s, ServerType.SERVER_TYPE_NONE)
      return
    end
  end
  ExposedMembers.BenchLoad = "not found: " .. table.concat(names, ",")
end
LuaEvents.FileListQueryResults.Add(OnResults)
local opts = SaveLocationOptions.NORMAL + SaveLocationOptions.AUTOSAVE + SaveLocationOptions.QUICKSAVE + SaveLocationOptions.LOAD_METADATA
UI.QuerySaveGameList(SaveLocations.LOCAL_STORAGE, SaveTypes.SINGLE_PLAYER, opts)
print("query sent")
