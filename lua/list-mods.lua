local mods = Modding.GetInstalledMods()
for i, m in ipairs(mods) do
  local info = Modding.GetModInfo(m.Handle) or {}
  local own = info.Allowance
  if own == nil then own = m.Allowance end
  print(string.format("MOD|%s|%s|enabled=%s|official=%s|allowance=%s|source=%s",
    tostring(m.Id), tostring(m.Name), tostring(m.Enabled), tostring(m.Official), tostring(own), tostring(m.Source)))
end
print("count=" .. #mods)
