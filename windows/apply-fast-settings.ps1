# Civ 6 fastest settings for agent play (backs up originals first).
# Window: borderless on the primary screen at its native size (pass that screen's physical pixels), so clicking
# another screen doesn't minimize the game. UIUpscale 1.0 is 200%, to match Windows' 200% scaling on a 3K panel.
param([int]$Width = 2880, [int]$Height = 1800, [int]$WindowMode = 2, [double]$UIUpscale = 1.0)
$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'
$d = "$env:LOCALAPPDATA\Firaxis Games\Sid Meier's Civilization VI"
$stamp = '20261106'
function Set-Opts($file, $map) {
  $p = Join-Path $d $file
  $bak = "$p.bak-$stamp"
  if (-not (Test-Path $bak)) { Copy-Item $p $bak }
  $lines = Get-Content $p
  foreach ($k in $map.Keys) {
    $hit = $false
    $lines = $lines | ForEach-Object { if ($_ -match "^$k(\s|$)") { $hit = $true; "$k $($map[$k])" } else { $_ } }
    if (-not $hit) { "  MISSING KEY $file : $k" }
  }
  Set-Content -Path $p -Value $lines -Encoding ascii
  "updated $file"
}
Set-Opts 'AppOptions.txt' ([ordered]@{
  RenderWidth = $Width; RenderHeight = $Height; FullScreen = $WindowMode; UIUpscale = ('{0:F6}' -f $UIUpscale); PlayIntroVideo = 0; EnableTuner = 1; EnableAudio = 0
})
Set-Opts 'GraphicsOptions.txt' ([ordered]@{
  PerformanceImpact = 0; MemoryImpact = 0; MSAA = 0; ShadowMapResolution = 1024; ReducedAssetTextures = 1
  TerrainSynthesisDetailLevel = 0; TerrainQuality = 0; ReducedTerrainMaterials = 1; LowQualityTerrainShader = 1
  SSReflectPasses = 0; UseLowResWater = 1; UseLowQualityWaterShader = 1; MinimapQuality = 0
  VFXDetailLevel = 0; ClutterDetailLevel = 0; EnableAO = 0; EnableBloom = 0; EnableShadows = 0
  EnableDynamicLighting = 0; EnableCloudShadows = 0; Quality = 0
})
Set-Opts 'UserOptions.txt' ([ordered]@{
  QuickMovement = 1; QuickCombat = 1; AutoEndTurn = 0; AI_MasterLogging = 0; NetMessageLogs = 0
  PlayVignettes = 0; PlayHistoricMomentAnimation = 0; LookAtPlayerTurnCombat = 0; LookAtPlayerOffTurnCombat = 0
  HasChosenTutorialLevel = 1; HasSeenXP1FeaturesScreen = 1; HasSeenXP2FeaturesScreen = 1
  HideXP1FeaturesScreen = 1; HideXP2FeaturesScreen = 1; StartInStrategicView = 1
})
"== verify"
foreach ($f in 'AppOptions.txt','GraphicsOptions.txt','UserOptions.txt') {
  Select-String -Path (Join-Path $d $f) -Pattern '^(RenderWidth|RenderHeight|FullScreen|UIUpscale|PlayIntroVideo|EnableTuner|EnableAudio|PerformanceImpact|TerrainQuality|EnableShadows|EnableBloom|QuickMovement|QuickCombat|AutoEndTurn|StartInStrategicView|HasChosenTutorialLevel) ' | ForEach-Object { "  $f  $($_.Line)" }
}
Get-ChildItem $d -Filter '*.bak-*' -Name | ForEach-Object { "  backup: $_" }
