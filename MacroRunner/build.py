"""
PyInstaller build script for MacroRunner.
"""
import shutil
import subprocess
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import PyInstaller.__main__

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
EXE_NAME = "MacroRunner.exe"
DIST_EXE = DIST_DIR / EXE_NAME
RESULT_DIR = Path("D:/OneDrive") / "\ucf54\ub4dc\uc791\uc5c5" / "\uacb0\uacfc\ubb3c"
RESULT_APP_DIR = RESULT_DIR / "MacroRunner"
RESULT_EXE = RESULT_APP_DIR / EXE_NAME
RESULT_BACKUP_DIR = RESULT_APP_DIR / "backups"


def clean():
    """Remove previous build artifacts."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    for spec in PROJECT_ROOT.glob("*.spec"):
        spec.unlink()


def build():
    """Run PyInstaller as a single portable EXE."""
    clean()

    PyInstaller.__main__.run([
        str(PROJECT_ROOT / "src" / "main.py"),
        "--name", "MacroRunner",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--hidden-import", "win32com.client",
        "--hidden-import", "pythoncom",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--add-data", f"{PROJECT_ROOT / 'macros'};macros",
        "--optimize", "2",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
    ])


def post_build():
    """Validate build output."""
    if not DIST_EXE.exists():
        raise FileNotFoundError(f"Build output was not created: {DIST_EXE}")

    print("\n" + "=" * 50)
    print("Build complete.")
    print(f"Output file: {DIST_EXE}")
    print("=" * 50)


def sign_exe():
    """Apply Authenticode signing to the built EXE."""
    if not DIST_EXE.exists():
        print("Signing target EXE was not found.")
        return False

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$exePath = @'
{DIST_EXE}
'@
$cert = Get-ChildItem Cert:\\CurrentUser\\My |
    Where-Object {{ $_.Subject -like '*MacroRunner*' }} |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1
if ($null -eq $cert) {{
    Write-Error 'MacroRunner signing certificate was not found. Run create_cert.ps1 first.'
    exit 1
}}
$result = Set-AuthenticodeSignature -FilePath $exePath -Certificate $cert -TimestampServer 'http://timestamp.digicert.com' -HashAlgorithm SHA256
if ($result.Status -eq 'Valid') {{
    Write-Host 'Signed MacroRunner.exe'
}} else {{
    Write-Error "Signing failed: $($result.Status)"
    exit 1
}}
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("Code signing complete.")
        return True

    print(f"Code signing failed: {result.stderr.strip()}")
    return False


def backup_existing_result():
    """Back up the currently published EXE before replacing it."""
    if not RESULT_EXE.exists():
        return None

    RESULT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    digest = sha256(RESULT_EXE.read_bytes()).hexdigest().upper()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"MacroRunner_{timestamp}_{digest[:12]}.exe"
    backup_path = RESULT_BACKUP_DIR / backup_name
    shutil.copy2(RESULT_EXE, backup_path)
    return backup_path


def copy_results():
    """Copy the portable EXE to the shared result folder."""
    if not DIST_EXE.exists():
        print("Build output to copy was not found.")
        return False

    RESULT_APP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = backup_existing_result()

    for stale_dir in [RESULT_APP_DIR / "_internal", RESULT_APP_DIR / "macros"]:
        if stale_dir.exists():
            shutil.rmtree(stale_dir)

    for stale_file in [RESULT_DIR / "MacroRunner_Setup.exe", RESULT_APP_DIR / "MacroRunner_Setup.exe"]:
        if stale_file.exists():
            stale_file.unlink()

    shutil.copy2(DIST_EXE, RESULT_EXE)

    print("\n" + "=" * 50)
    print("Result copy complete.")
    if backup_path:
        print(f"Previous EXE backup: {backup_path}")
    print(f"Portable EXE: {RESULT_EXE}")
    print("=" * 50)
    return True


if __name__ == "__main__":
    build()
    post_build()
    if not sign_exe():
        sys.exit(1)
    if not copy_results():
        sys.exit(1)
