"""
PyInstaller 빌드 스크립트
MacroRunner v2.0
"""
import PyInstaller.__main__
import shutil
import subprocess
import sys
from pathlib import Path

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
RESULT_DIR = Path(r"D:\OneDrive\코드작업\결과물")

def clean():
    """이전 빌드 정리"""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    # spec 파일 삭제
    for spec in PROJECT_ROOT.glob("*.spec"):
        spec.unlink()

def build():
    """PyInstaller 빌드 실행"""
    clean()

    PyInstaller.__main__.run([
        str(PROJECT_ROOT / "src" / "main.py"),
        "--name", "MacroRunner",
        "--onedir",
        "--windowed",
        "--noconfirm",

        # 아이콘 (있는 경우)
        # "--icon", str(PROJECT_ROOT / "assets" / "icon.ico"),

        # 숨겨진 임포트
        "--hidden-import", "win32com.client",
        "--hidden-import", "pythoncom",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",

        # 데이터 파일
        "--add-data", f"{PROJECT_ROOT / 'macros'};macros",

        # 최적화
        "--optimize", "2",

        # 출력 디렉토리
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
    ])

def post_build():
    """빌드 후 처리"""
    # macros 폴더 확인
    macros_dir = DIST_DIR / "MacroRunner" / "macros"
    macros_dir.mkdir(exist_ok=True)

    # 기본 macro_index.json 복사
    src_index = PROJECT_ROOT / "macros" / "macro_index.json"
    dst_index = macros_dir / "macro_index.json"

    if src_index.exists() and not dst_index.exists():
        shutil.copy(src_index, dst_index)

    # backups 폴더 생성
    backups_dir = DIST_DIR / "MacroRunner" / "backups"
    backups_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 50)
    print("빌드 완료!")
    print(f"출력 경로: {DIST_DIR / 'MacroRunner'}")
    print("=" * 50)

def sign_exe():
    """빌드된 EXE에 코드 서명 적용"""
    exe_path = DIST_DIR / "MacroRunner" / "MacroRunner.exe"
    if not exe_path.exists():
        print("서명 대상 EXE가 없습니다.")
        return False

    ps_script = f"""
$ErrorActionPreference = 'Stop'
$exePath = @'
{exe_path}
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
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Code signing complete.")
        return True
    else:
        print(f"Code signing failed: {result.stderr.strip()}")
        return False

def copy_results():
    """빌드 결과물을 결과물 폴더로 복사"""
    app_source = DIST_DIR / "MacroRunner"
    app_target = RESULT_DIR / "MacroRunner"

    if not app_source.exists():
        print("복사할 빌드 결과물이 없습니다.")
        return False

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    stale_installer = RESULT_DIR / "MacroRunner_Setup.exe"
    if stale_installer.exists():
        stale_installer.unlink()

    shutil.copytree(app_source, app_target, dirs_exist_ok=True)

    print("\n" + "=" * 50)
    print("결과물 복사 완료!")
    print(f"결과물 경로: {app_target}")
    print("=" * 50)
    return True

if __name__ == "__main__":
    build()
    post_build()
    if not sign_exe():
        sys.exit(1)
    if not copy_results():
        sys.exit(1)
