# Install reviau on Windows.
#
#   powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | iex"
#
# Installs uv if it is missing (uv brings its own Python, so none is needed
# beforehand) and installs reviau as an isolated tool, with the reviau command
# on the PATH. Run it again to upgrade.
#
# Environment overrides:
#   REVIAU_PACKAGE   what to install   (default: reviau)
#
# Keep this file ASCII: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

$ErrorActionPreference = "Stop"

$Package = if ($env:REVIAU_PACKAGE) { $env:REVIAU_PACKAGE } else { "reviau" }
# The version CI tests the installer on.
$Python = "3.12"

function Say($Message) { Write-Host "==> $Message" }

# --- uv ----------------------------------------------------------------------
$Found = Get-Command uv -ErrorAction SilentlyContinue
$Uv = if ($Found) { $Found.Source } else { Join-Path $HOME ".local\bin\uv.exe" }
if (-not (Test-Path $Uv)) {
    Say "Installing uv"
    $env:UV_INSTALL_DIR = Join-Path $HOME ".local\bin"
    # A separate process, so an exit in uv's installer cannot end this one.
    powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Uv)) { throw "uv could not be installed" }
}

# --- reviau ------------------------------------------------------------------
Say "Installing $Package"
# Native commands do not stop on failure under $ErrorActionPreference, and their
# stderr must not be redirected: 5.1 would turn uv's progress lines into errors.
& $Uv tool install --python $Python --upgrade $Package
if ($LASTEXITCODE -ne 0) { throw "uv tool install failed with exit code $LASTEXITCODE" }
& $Uv tool update-shell
$Bin = (& $Uv tool dir --bin | Out-String).Trim()
$Exe = Join-Path $Bin "reviau.exe"
if (-not (Test-Path $Exe)) { throw "reviau was not installed where uv said it would be ($Exe)" }

$Version = (& $Exe --version | Out-String).Trim()
Say "Done. $Version is installed."
Write-Host ""
Write-Host "  Open a new terminal and run, for example:"
Write-Host ""
Write-Host "    reviau C:\path\to\segments"
Write-Host ""
Write-Host "  The review interface opens in a web browser. Run 'reviau' alone to"
Write-Host "  choose the folder from the interface instead."
Write-Host "  'reviau --help' lists every option."
Write-Host "  To upgrade later, run this installer again."
