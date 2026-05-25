"""
상수 및 설정값 정의
"""
import os
import sys
from pathlib import Path

# 버전 정보
APP_VERSION = "2.0.0"
APP_NAME = "MacroRunner"
IS_FROZEN = getattr(sys, 'frozen', False)

# 경로 설정
# PyInstaller로 빌드된 경우 실행 파일 위치, 아니면 소스 위치
if IS_FROZEN:
    # PyInstaller로 빌드된 exe 실행 중
    # exe 파일이 있는 디렉토리 (예: C:\Program Files (x86)\MacroRunner)
    APP_DIR = Path(sys.executable).parent
    # 사용자 데이터는 AppData에 저장 (쓰기 권한 보장)
    USER_DATA_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home())) / APP_NAME
else:
    # 개발 환경 - 소스 디렉토리 사용
    APP_DIR = Path(__file__).parent.parent.parent
    USER_DATA_DIR = APP_DIR

# EXE 배포본에는 기본 매크로가 앱 디렉토리에 포함될 수 있지만,
# 실제 저장/수정은 항상 쓰기 권한이 보장되는 사용자 데이터 폴더에서 수행한다.
PACKAGE_MACROS_DIR = APP_DIR / "macros"
USER_MACROS_DIR = USER_DATA_DIR / "macros"

if IS_FROZEN:
    MACROS_DIR = USER_MACROS_DIR
else:
    MACROS_DIR = PACKAGE_MACROS_DIR if PACKAGE_MACROS_DIR.exists() else USER_MACROS_DIR

# backups와 config는 항상 사용자 데이터 폴더에 저장 (쓰기 권한 보장)
BACKUPS_DIR = USER_DATA_DIR / "backups"
CONFIG_FILE = USER_DATA_DIR / "config.json"
MACRO_INDEX_FILE = MACROS_DIR / "macro_index.json"

# 하위 호환성을 위한 BASE_DIR (사용자 데이터 폴더로 설정)
BASE_DIR = USER_DATA_DIR

# 지원 프로그램
SUPPORTED_PROGRAMS = {
    "excel": "Microsoft Excel",
    "ppt": "Microsoft PowerPoint",
    "word": "Microsoft Word"
}

# 색상 테마 (다크 모드)
COLORS = {
    "dark": {
        "bg_primary": "#1e1e2e",      # 메인 배경
        "bg_secondary": "#313244",     # 보조 배경
        "bg_tertiary": "#45475a",      # 세 번째 배경
        "bg_hover": "#585b70",         # 호버 상태
        "accent": "#89b4fa",           # 강조색 (파랑)
        "accent_hover": "#b4befe",     # 강조색 호버
        "success": "#a6e3a1",          # 성공 (초록)
        "warning": "#f9e2af",          # 경고 (노랑)
        "error": "#f38ba8",            # 에러 (빨강)
        "text_primary": "#cdd6f4",     # 주요 텍스트
        "text_secondary": "#a6adc8",   # 보조 텍스트
        "text_muted": "#6c7086",       # 흐린 텍스트
        "border": "#45475a",           # 테두리
        "scrollbar": "#585b70",        # 스크롤바
    },
    "light": {
        "bg_primary": "#eff1f5",
        "bg_secondary": "#e6e9ef",
        "bg_tertiary": "#dce0e8",
        "bg_hover": "#ccd0da",
        "accent": "#1e66f5",
        "accent_hover": "#7287fd",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "error": "#d20f39",
        "text_primary": "#4c4f69",
        "text_secondary": "#5c5f77",
        "text_muted": "#8c8fa1",
        "border": "#ccd0da",
        "scrollbar": "#bcc0cc",
    }
}

# VBA 키워드 (구문 강조용)
VBA_KEYWORDS = {
    "keywords": [
        "Sub", "End Sub", "Function", "End Function", "If", "Then", "Else",
        "ElseIf", "End If", "For", "To", "Step", "Next", "Do", "While", "Loop",
        "Until", "Wend", "Select", "Case", "End Select", "With", "End With",
        "Dim", "As", "Set", "Let", "Const", "Public", "Private", "Static",
        "ByVal", "ByRef", "Optional", "ParamArray", "New", "Nothing", "True",
        "False", "And", "Or", "Not", "Xor", "Mod", "Is", "Like", "Exit",
        "GoTo", "On", "Error", "Resume", "Call", "Return", "Property", "Get",
        "Let", "Set", "End Property", "Type", "End Type", "Enum", "End Enum",
        "Event", "RaiseEvent", "Implements", "Option", "Explicit", "Base",
        "Compare", "Preserve", "ReDim", "Erase", "Debug", "Print", "MsgBox",
        "InputBox", "DoEvents"
    ],
    "types": [
        "Integer", "Long", "Single", "Double", "Currency", "String", "Boolean",
        "Byte", "Date", "Object", "Variant", "Range", "Worksheet", "Workbook",
        "Application", "Shape", "Table", "Slide", "Presentation"
    ],
    "operators": [
        "+", "-", "*", "/", "\\", "^", "&", "=", "<>", "<", ">", "<=", ">="
    ]
}

# 폰트 설정 (가독성 향상을 위해 크기 증가)
# 기본 폰트 (사용자 설정으로 변경 가능)
DEFAULT_UI_FONT = "Segoe UI"
DEFAULT_CODE_FONT = "Consolas"
DEFAULT_UI_SIZE = 12
DEFAULT_CODE_SIZE = 14

# 권장 UI 폰트 목록
RECOMMENDED_UI_FONTS = [
    "Segoe UI",
    "맑은 고딕",
    "나눔고딕",
    "Arial",
    "Tahoma",
    "Verdana",
    "Microsoft YaHei",
    "Yu Gothic UI"
]

# 권장 코드 폰트 목록
RECOMMENDED_CODE_FONTS = [
    "Consolas",
    "D2Coding",
    "Cascadia Code",
    "Fira Code",
    "JetBrains Mono",
    "Source Code Pro",
    "Monaco",
    "Courier New"
]

# 폰트 크기 범위
FONT_SIZE_MIN = 8
FONT_SIZE_MAX = 24

# 동적 폰트 설정 (런타임에 변경 가능)
class FontConfig:
    """동적 폰트 설정 관리"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ui_font = DEFAULT_UI_FONT
        self._code_font = DEFAULT_CODE_FONT
        self._ui_size = DEFAULT_UI_SIZE
        self._code_size = DEFAULT_CODE_SIZE
        self._callbacks = []

    @property
    def ui_font(self) -> str:
        return self._ui_font

    @ui_font.setter
    def ui_font(self, value: str):
        self._ui_font = value
        self._notify_callbacks()

    @property
    def code_font(self) -> str:
        return self._code_font

    @code_font.setter
    def code_font(self, value: str):
        self._code_font = value
        self._notify_callbacks()

    @property
    def ui_size(self) -> int:
        return self._ui_size

    @ui_size.setter
    def ui_size(self, value: int):
        self._ui_size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, value))
        self._notify_callbacks()

    @property
    def code_size(self) -> int:
        return self._code_size

    @code_size.setter
    def code_size(self, value: int):
        self._code_size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, value))
        self._notify_callbacks()

    def get_fonts(self) -> dict:
        """현재 폰트 설정 반환"""
        return {
            "ui": (self._ui_font, self._ui_size),
            "ui_bold": (self._ui_font, self._ui_size, "bold"),
            "ui_small": (self._ui_font, self._ui_size - 1),
            "code": (self._code_font, self._code_size),
            "code_bold": (self._code_font, self._code_size, "bold"),
            "title": (self._ui_font, self._ui_size + 6, "bold"),
            "subtitle": (self._ui_font, self._ui_size + 2),
        }

    def set_from_settings(self, settings: dict):
        """설정에서 폰트 값 로드"""
        if "ui_font" in settings:
            self._ui_font = settings["ui_font"]
        if "code_font" in settings:
            self._code_font = settings["code_font"]
        if "ui_size" in settings:
            self._ui_size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, settings["ui_size"]))
        if "code_size" in settings:
            self._code_size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, settings["code_size"]))
        self._notify_callbacks()

    def to_settings(self) -> dict:
        """현재 폰트 설정을 딕셔너리로 반환"""
        return {
            "ui_font": self._ui_font,
            "code_font": self._code_font,
            "ui_size": self._ui_size,
            "code_size": self._code_size
        }

    def register_callback(self, callback):
        """폰트 변경 콜백 등록"""
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        """콜백 알림"""
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass

# 전역 폰트 설정 인스턴스
font_config = FontConfig()

# FONTS 딕셔너리 (하위 호환성을 위해 유지)
def get_fonts():
    """현재 폰트 설정 반환"""
    return font_config.get_fonts()

FONTS = {
    "ui": (DEFAULT_UI_FONT, DEFAULT_UI_SIZE),
    "ui_bold": (DEFAULT_UI_FONT, DEFAULT_UI_SIZE, "bold"),
    "ui_small": (DEFAULT_UI_FONT, DEFAULT_UI_SIZE - 1),
    "code": (DEFAULT_CODE_FONT, DEFAULT_CODE_SIZE),
    "code_bold": (DEFAULT_CODE_FONT, DEFAULT_CODE_SIZE, "bold"),
    "title": (DEFAULT_UI_FONT, DEFAULT_UI_SIZE + 6, "bold"),
    "subtitle": (DEFAULT_UI_FONT, DEFAULT_UI_SIZE + 2),
}

# 단축키 설정
SHORTCUTS = {
    "save": "<Control-s>",
    "run": "<Control-Return>",
    "inject": "<Control-Shift-Return>",
    "new": "<Control-n>",
    "delete": "<Delete>",
    "search": "<Control-f>",
    "duplicate": "<Control-d>",
    "export": "<Control-e>",
    "import": "<Control-i>",
    "toggle_favorite": "<Control-b>",
    "undo": "<Control-z>",
    "redo": "<Control-y>",
}

# 자동 백업 설정
BACKUP_SETTINGS = {
    "enabled": True,
    "interval_minutes": 30,
    "max_backups": 10,
    "on_save": True,
}

# 기본 카테고리
DEFAULT_CATEGORIES = [
    "일반",
    "보고서",
    "데이터 정리",
    "서식",
    "자동화",
    "기타"
]
