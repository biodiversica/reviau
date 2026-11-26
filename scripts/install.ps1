# Install reviau and a shortcut for its browser interface, on Windows.
#
#   powershell -ExecutionPolicy ByPass -c "irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex"
#
# Installs uv if it is missing (uv brings its own Python, so none is needed
# beforehand), installs reviau as an isolated tool, with the reviau command on
# the PATH, and adds Desktop and Start menu shortcuts that open the interface.
# Run it again to upgrade.
#
# To uninstall, run it with REVIAU_UNINSTALL set (single quotes, so the
# PowerShell it is typed into leaves $env alone):
#
#   powershell -ExecutionPolicy ByPass -c '$env:REVIAU_UNINSTALL=1; irm https://github.com/biodiversica/reviau/releases/latest/download/install.ps1 | Out-String | iex'
#
# Either way, it says what it is about to do and asks before doing any of it.
#
# "| Out-String" matters: a release serves this file as
# application/octet-stream, and Windows PowerShell 5.1's irm then hands it to
# iex line by line, which breaks every function below.
#
# Environment overrides:
#   REVIAU_PACKAGE    what to install   (default: reviau)
#   REVIAU_UNINSTALL  1 removes reviau and its shortcuts. Reviewed segments and
#                     their reviau\ folders are never removed, nor is uv.
#   REVIAU_YES=1      go ahead without asking, e.g. from a script or CI
#
# Keep this file ASCII: Windows PowerShell 5.1 reads a BOM-less script as ANSI.

$ErrorActionPreference = "Stop"

$Package = if ($env:REVIAU_PACKAGE) { $env:REVIAU_PACKAGE } else { "reviau" }
$Uninstall = $env:REVIAU_UNINSTALL
# The version CI tests the installer on.
$Python = "3.12"
# Where the shortcuts go, and so where uninstalling looks for them.
$Places = @([Environment]::GetFolderPath("Desktop"), [Environment]::GetFolderPath("Programs"))
# Where the shortcuts' icon is kept: out of the tool's environment, which uv may
# rebuild on an upgrade.
$LocalData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\Local" }
$IconDir = Join-Path $LocalData "reviau"
$Icon = Join-Path $IconDir "reviau.ico"

function Say($Message) { Write-Host "==> $Message" }

function Find-Uv {
    $Found = Get-Command uv -ErrorAction SilentlyContinue
    if ($Found) { $Found.Source } else { Join-Path $HOME ".local\bin\uv.exe" }
}

# Whether to go ahead: yes under REVIAU_YES=1, otherwise whatever is answered.
function Confirm-Plan($Doing) {
    if ($env:REVIAU_YES -eq "1") { return $true }
    if ([Console]::IsInputRedirected) {
        throw "there is no console to ask in; set REVIAU_YES=1 to $Doing without asking."
    }
    $Answer = Read-Host "Continue? [y/N]"
    return ($Answer -match '^\s*(y|yes)\s*$')
}

function Remove-IfPresent($Path, $What) {
    if (Test-Path $Path) {
        Remove-Item -Recurse -Force $Path
        Say "Removed $What ($Path)"
    }
}

function Uninstall-Reviau {
    if ($Uninstall -ne "1") {
        throw "REVIAU_UNINSTALL must be 1, not '$Uninstall'"
    }
    Write-Host @"
This uninstalls reviau. It will:

  - remove reviau, with uv (uv itself stays)
  - remove the reviau shortcuts from your Desktop and Start menu

Segments, and the reviau\ folders that hold their reviews, are not removed.

"@
    if (-not (Confirm-Plan "uninstall")) {
        Write-Host "Nothing was removed."
        return
    }
    # Windows will not delete a program that is running.
    if (Get-Process -Name reviau -ErrorAction SilentlyContinue) {
        throw "reviau is running. Close its window (or press Ctrl+C in it), then run this again."
    }

    $Uv = Find-Uv
    if ((Test-Path $Uv) -and ((& $Uv tool list | Out-String) -match "(?m)^reviau ")) {
        Say "Uninstalling reviau"
        & $Uv tool uninstall reviau
        if ($LASTEXITCODE -ne 0) { throw "uv tool uninstall failed with exit code $LASTEXITCODE" }
    }
    foreach ($Folder in $Places) {
        Remove-IfPresent (Join-Path $Folder "reviau.lnk") "shortcut"
    }
    Remove-IfPresent $Icon "shortcut icon"
    # The folder held only the icon; anything else put there is left alone.
    if ((Test-Path $IconDir) -and -not (Get-ChildItem -Force $IconDir)) {
        Remove-Item -Force $IconDir
    }

    Say "Done. reviau is uninstalled."
    Write-Host ""
    Write-Host "  Segments and their reviews were left where they are."
}

function Install-Reviau {
    $Uv = Find-Uv
    $HaveUv = Test-Path $Uv

    # --- confirmation --------------------------------------------------------
    $UvText = if ($HaveUv) { "use uv, already installed at $Uv" } else { "install uv, the tool that installs reviau, into $(Join-Path $HOME '.local\bin')" }
    Write-Host @"
This installs reviau, a tool for reviewing folders of audio segments in the
browser. It will:

  - $UvText
  - install $Package with uv, isolated, along with a Python $Python
    of its own; your other Pythons are not touched (if reviau is already
    installed, it is upgraded)
  - add uv's tools folder to your user PATH
  - add reviau shortcuts, with its icon, to your Desktop and Start menu

"@
    if (-not (Confirm-Plan "install")) {
        Write-Host "Nothing was installed."
        return
    }

    # --- uv ------------------------------------------------------------------
    if (-not $HaveUv) {
        Say "Installing uv"
        $env:UV_INSTALL_DIR = Join-Path $HOME ".local\bin"
        # A separate process, so an exit in uv's installer cannot end this one.
        powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Uv)) { throw "uv could not be installed" }
    }

    # --- reviau --------------------------------------------------------------
    Say "Installing $Package"
    # Native commands do not stop on failure under $ErrorActionPreference, and
    # their stderr must not be redirected: 5.1 would turn uv's progress lines
    # into errors.
    & $Uv tool install --python $Python --upgrade $Package
    if ($LASTEXITCODE -ne 0) { throw "uv tool install failed with exit code $LASTEXITCODE" }
    & $Uv tool update-shell
    $Bin = (& $Uv tool dir --bin | Out-String).Trim()
    $Exe = Join-Path $Bin "reviau.exe"
    if (-not (Test-Path $Exe)) { throw "reviau was not installed where uv said it would be ($Exe)" }

    # --- icon ----------------------------------------------------------------
    # Copied out of the tool's environment to a place that stays put for as
    # long as the shortcuts point at it (scripts/make_icons.py draws it). A
    # package from before the logo has none, and the shortcuts then keep the
    # default icon.
    $ToolDir = (& $Uv tool dir | Out-String).Trim()
    $PackagedIcon = Join-Path $ToolDir "reviau\Lib\site-packages\reviau\web\icons\reviau.ico"
    $HaveIcon = Test-Path $PackagedIcon
    if ($HaveIcon) {
        New-Item -ItemType Directory -Force -Path $IconDir | Out-Null
        Copy-Item -Force $PackagedIcon $Icon
    }

    # --- shortcuts -----------------------------------------------------------
    # They open a console window: it shows the address and is where Ctrl+C
    # stops the interface. They start in the home folder, where Browse...
    # begins, with no folder open: the reviewer chooses one in the browser.
    $Shell = New-Object -ComObject WScript.Shell
    foreach ($Folder in $Places) {
        $Link = $Shell.CreateShortcut((Join-Path $Folder "reviau.lnk"))
        $Link.TargetPath = $Exe
        $Link.WorkingDirectory = $HOME
        $Link.Description = "Review folders of audio segments in the browser"
        if ($HaveIcon) { $Link.IconLocation = "$Icon,0" }
        $Link.Save()
    }

    $Version = (& $Exe --version | Out-String).Trim()
    Say "Done. $Version is installed."
    Write-Host ""
    Write-Host "  To start: double-click reviau on your Desktop or in the Start menu, and"
    Write-Host "  choose the folder of segments in the browser. Or, in a new terminal:"
    Write-Host ""
    Write-Host "    reviau C:\path\to\segments"
    Write-Host ""
    Write-Host "  'reviau --help' lists every option."
    Write-Host "  To upgrade later, run this installer again."
}

# Functions rather than an early return: under iex, a return at the top level
# does not reliably end the script.
if ($Uninstall) { Uninstall-Reviau } else { Install-Reviau }
