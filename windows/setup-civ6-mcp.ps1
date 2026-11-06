$ErrorActionPreference = 'Continue'; $ProgressPreference = 'SilentlyContinue'
$root = "$env:USERPROFILE\civ6-bench"
New-Item -ItemType Directory -Force -Path $root | Out-Null
Set-Location $root
if (-not (Test-Path "$root\civ6-mcp")) { git clone -q https://github.com/lmwilki/civ6-mcp.git 2>&1 | Out-String }
Set-Location "$root\civ6-mcp"
"HEAD: " + (git log -1 --format='%h %cs')
$env:UV_PYTHON_PREFERENCE = 'only-managed'
uv sync 2>&1 | Select-Object -Last 8 | Out-String
"py: " + (uv run python --version 2>&1)
"entry points:"; Select-String -Path pyproject.toml -Pattern '^\[project.scripts\]' -Context 0,5 | Out-String
