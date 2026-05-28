"""
Build unsigned MacroRunner variants for restrictive security PCs.
"""
import shutil
from pathlib import Path

import PyInstaller.__main__

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist_security"
BUILD_DIR = PROJECT_ROOT / "build_security"
RESULT_APP_DIR = Path("D:/OneDrive") / "코드작업" / "결과물" / "MacroRunner"
ONEFILE_NAME = "MacroRunner_security_unsigned"
FOLDER_NAME = "MacroRunner_security_folder"
ONEFILE_EXE = DIST_DIR / f"{ONEFILE_NAME}.exe"
FOLDER_DIST = DIST_DIR / FOLDER_NAME
RESULT_ONEFILE_EXE = RESULT_APP_DIR / f"{ONEFILE_NAME}.exe"
RESULT_FOLDER = RESULT_APP_DIR / FOLDER_NAME


def clean():
    """Remove previous security build artifacts."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    for spec in PROJECT_ROOT.glob(f"{ONEFILE_NAME}*.spec"):
        spec.unlink()
    for spec in PROJECT_ROOT.glob(f"{FOLDER_NAME}*.spec"):
        spec.unlink()


def common_args(name: str):
    return [
        str(PROJECT_ROOT / "src" / "main.py"),
        "--name", name,
        "--windowed",
        "--noconfirm",
        "--clean",
        "--noupx",
        "--hidden-import", "win32com.client",
        "--hidden-import", "pythoncom",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--add-data", f"{PROJECT_ROOT / 'macros'};macros",
        "--optimize", "2",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
    ]


def build_onefile():
    """Build an unsigned one-file EXE."""
    PyInstaller.__main__.run([
        *common_args(ONEFILE_NAME),
        "--onefile",
    ])


def build_folder():
    """Build an unsigned folder distribution without self extraction."""
    PyInstaller.__main__.run([
        *common_args(FOLDER_NAME),
        "--onedir",
    ])


def copy_results():
    """Copy security-PC build outputs without replacing the normal EXE."""
    if not ONEFILE_EXE.exists():
        raise FileNotFoundError(f"One-file build output was not created: {ONEFILE_EXE}")
    if not FOLDER_DIST.exists():
        raise FileNotFoundError(f"Folder build output was not created: {FOLDER_DIST}")

    RESULT_APP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ONEFILE_EXE, RESULT_ONEFILE_EXE)

    if RESULT_FOLDER.exists():
        shutil.rmtree(RESULT_FOLDER)
    shutil.copytree(FOLDER_DIST, RESULT_FOLDER)

    print("\n" + "=" * 50)
    print("Security PC build complete.")
    print(f"Unsigned one-file EXE: {RESULT_ONEFILE_EXE}")
    print(f"Unsigned folder build: {RESULT_FOLDER}")
    print("=" * 50)


if __name__ == "__main__":
    clean()
    build_onefile()
    build_folder()
    copy_results()
