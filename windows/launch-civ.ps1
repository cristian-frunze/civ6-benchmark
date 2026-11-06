# Start Civ 6 inside the user's session (run via the Civ6Launch scheduled task). Uses the DX11 build: the DX12
# build crashed with "Device Reset" (DXGI 0x887a0005) when the Zenbook Duo's second screen came on.
$exe = "C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization VI\Base\Binaries\Win64Steam\CivilizationVI.exe"
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)
