"""
PyInstaller 빌드 스크립트
MacroRunner v2.0
"""
import PyInstaller.__main__
import shutil
from pathlib import Path

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

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

if __name__ == "__main__":
    build()
    post_build()
