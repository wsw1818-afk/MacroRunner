"""
모던 UI 테마 시스템
Catppuccin 기반 다크/라이트 모드 지원
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Literal
import json
from pathlib import Path

from ..utils.constants import COLORS, FONTS, font_config


class ThemeManager:
    """테마 관리자 - 다크/라이트 모드 전환 및 스타일 관리"""

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
        self._current_theme: Literal["dark", "light"] = "dark"
        self._callbacks = []
        self._style: ttk.Style = None

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def colors(self) -> Dict[str, str]:
        return COLORS[self._current_theme]

    def toggle_theme(self):
        """다크/라이트 모드 전환"""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._apply_theme()
        self._notify_callbacks()

    def set_theme(self, theme: Literal["dark", "light"]):
        """테마 설정"""
        if theme in ("dark", "light"):
            self._current_theme = theme
            self._apply_theme()
            self._notify_callbacks()

    def register_callback(self, callback):
        """테마 변경 시 호출될 콜백 등록"""
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        """등록된 콜백들에게 테마 변경 알림"""
        for callback in self._callbacks:
            try:
                callback(self._current_theme)
            except Exception:
                pass

    def init_style(self, root: tk.Tk):
        """ttk 스타일 초기화"""
        self._style = ttk.Style(root)
        self._root = root
        self._apply_theme()

    def refresh_fonts(self):
        """폰트 설정 재적용"""
        if self._style:
            self._apply_theme()
            self._notify_callbacks()

    def _apply_theme(self):
        """현재 테마 적용"""
        if self._style is None:
            return

        colors = self.colors

        # 동적 폰트 설정 가져오기
        fonts = font_config.get_fonts()

        # 기본 스타일 설정
        self._style.theme_use('clam')

        # TFrame
        self._style.configure(
            "TFrame",
            background=colors["bg_primary"]
        )

        self._style.configure(
            "Secondary.TFrame",
            background=colors["bg_secondary"]
        )

        self._style.configure(
            "Card.TFrame",
            background=colors["bg_secondary"],
            relief="flat"
        )

        # TLabel
        self._style.configure(
            "TLabel",
            background=colors["bg_primary"],
            foreground=colors["text_primary"],
            font=fonts["ui"]
        )

        self._style.configure(
            "Title.TLabel",
            background=colors["bg_primary"],
            foreground=colors["text_primary"],
            font=fonts["title"]
        )

        self._style.configure(
            "Subtitle.TLabel",
            background=colors["bg_primary"],
            foreground=colors["text_secondary"],
            font=fonts["subtitle"]
        )

        self._style.configure(
            "Muted.TLabel",
            background=colors["bg_primary"],
            foreground=colors["text_muted"],
            font=fonts["ui_small"]
        )

        self._style.configure(
            "Success.TLabel",
            background=colors["bg_primary"],
            foreground=colors["success"],
            font=fonts["ui"]
        )

        self._style.configure(
            "Error.TLabel",
            background=colors["bg_primary"],
            foreground=colors["error"],
            font=fonts["ui"]
        )

        # Warning Label 추가
        self._style.configure(
            "Warning.TLabel",
            background=colors["bg_primary"],
            foreground=colors["warning"],
            font=fonts["ui"]
        )

        self._style.configure(
            "Card.TLabel",
            background=colors["bg_secondary"],
            foreground=colors["text_primary"],
            font=fonts["ui"]
        )

        # TButton
        self._style.configure(
            "TButton",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            font=fonts["ui"],
            padding=(12, 8),
            relief="flat"
        )
        self._style.map(
            "TButton",
            background=[("active", colors["bg_hover"]), ("pressed", colors["accent"])],
            foreground=[("pressed", colors["bg_primary"])]
        )

        # Primary Button (강조)
        self._style.configure(
            "Primary.TButton",
            background=colors["accent"],
            foreground=colors["bg_primary"],
            font=fonts["ui_bold"],
            padding=(16, 10)
        )
        self._style.map(
            "Primary.TButton",
            background=[("active", colors["accent_hover"]), ("pressed", colors["accent"])]
        )

        # Success Button
        self._style.configure(
            "Success.TButton",
            background=colors["success"],
            foreground=colors["bg_primary"],
            font=fonts["ui_bold"],
            padding=(16, 10)
        )

        # Danger Button
        self._style.configure(
            "Danger.TButton",
            background=colors["error"],
            foreground=colors["bg_primary"],
            font=fonts["ui_bold"],
            padding=(12, 8)
        )

        # Icon Button (작은 버튼)
        self._style.configure(
            "Icon.TButton",
            background=colors["bg_secondary"],
            foreground=colors["text_secondary"],
            font=fonts["ui"],
            padding=(8, 6)
        )
        self._style.map(
            "Icon.TButton",
            background=[("active", colors["bg_tertiary"])]
        )

        # TEntry
        self._style.configure(
            "TEntry",
            fieldbackground=colors["bg_secondary"],
            foreground=colors["text_primary"],
            insertcolor=colors["text_primary"],
            padding=(8, 6)
        )

        self._style.configure(
            "Search.TEntry",
            fieldbackground=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            padding=(10, 8)
        )

        # TRadiobutton
        self._style.configure(
            "TRadiobutton",
            background=colors["bg_primary"],
            foreground=colors["text_primary"],
            font=fonts["ui"],
            padding=(8, 4)
        )
        self._style.map(
            "TRadiobutton",
            background=[("active", colors["bg_secondary"])]
        )

        self._style.configure(
            "Card.TRadiobutton",
            background=colors["bg_secondary"],
            foreground=colors["text_primary"]
        )

        # TCheckbutton
        self._style.configure(
            "TCheckbutton",
            background=colors["bg_primary"],
            foreground=colors["text_primary"],
            font=fonts["ui"],
            padding=(8, 4)
        )

        # TCombobox
        self._style.configure(
            "TCombobox",
            fieldbackground=colors["bg_secondary"],
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            arrowcolor=colors["text_secondary"],
            padding=(8, 6)
        )
        self._style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["bg_secondary"])],
            selectbackground=[("readonly", colors["accent"])],
            selectforeground=[("readonly", colors["bg_primary"])]
        )

        # TNotebook
        self._style.configure(
            "TNotebook",
            background=colors["bg_primary"],
            tabmargins=[2, 5, 2, 0]
        )
        self._style.configure(
            "TNotebook.Tab",
            background=colors["bg_secondary"],
            foreground=colors["text_secondary"],
            padding=[16, 8],
            font=fonts["ui"]
        )
        self._style.map(
            "TNotebook.Tab",
            background=[("selected", colors["bg_tertiary"])],
            foreground=[("selected", colors["text_primary"])]
        )

        # Treeview (리스트)
        self._style.configure(
            "Treeview",
            background=colors["bg_secondary"],
            foreground=colors["text_primary"],
            fieldbackground=colors["bg_secondary"],
            font=fonts["ui"],
            rowheight=36
        )
        self._style.configure(
            "Treeview.Heading",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            font=fonts["ui_bold"]
        )
        self._style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["bg_primary"])]
        )

        # Scrollbar
        self._style.configure(
            "Vertical.TScrollbar",
            background=colors["bg_secondary"],
            troughcolor=colors["bg_primary"],
            arrowcolor=colors["text_muted"],
            borderwidth=0
        )
        self._style.map(
            "Vertical.TScrollbar",
            background=[("active", colors["scrollbar"])]
        )

        # TSeparator
        self._style.configure(
            "TSeparator",
            background=colors["border"]
        )

        # TProgressbar
        self._style.configure(
            "TProgressbar",
            background=colors["accent"],
            troughcolor=colors["bg_secondary"]
        )

        # TPanedwindow
        self._style.configure(
            "TPanedwindow",
            background=colors["border"]
        )

        # TLabelframe
        self._style.configure(
            "TLabelframe",
            background=colors["bg_primary"],
            foreground=colors["text_primary"]
        )
        self._style.configure(
            "TLabelframe.Label",
            background=colors["bg_primary"],
            foreground=colors["text_primary"],
            font=fonts["ui_bold"]
        )


class ModernWidgets:
    """모던 스타일 위젯 팩토리"""

    @staticmethod
    def create_rounded_frame(parent, **kwargs) -> tk.Frame:
        """둥근 모서리 프레임 (Canvas 기반)"""
        theme = ThemeManager()
        colors = theme.colors

        frame = tk.Frame(
            parent,
            bg=colors["bg_secondary"],
            **kwargs
        )
        return frame

    @staticmethod
    def create_card(parent, title: str = None, **kwargs) -> ttk.Frame:
        """카드 스타일 프레임"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=16, **kwargs)

        if title:
            title_label = ttk.Label(card, text=title, style="Title.TLabel")
            title_label.pack(anchor="w", pady=(0, 12))

        return card

    @staticmethod
    def create_search_entry(parent, placeholder: str = "검색...", **kwargs) -> ttk.Entry:
        """검색 입력 필드"""
        theme = ThemeManager()
        colors = theme.colors

        container = ttk.Frame(parent, style="Secondary.TFrame")

        # 검색 아이콘 (텍스트로 대체)
        icon_label = ttk.Label(
            container,
            text="🔍",
            style="Card.TLabel",
            font=("Segoe UI", 12)
        )
        icon_label.pack(side="left", padx=(8, 0))

        entry = ttk.Entry(container, style="Search.TEntry", **kwargs)
        entry.pack(side="left", fill="x", expand=True, padx=8, pady=8)

        # 플레이스홀더 기능
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.configure(foreground=colors["text_primary"])

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.configure(foreground=colors["text_muted"])

        entry.insert(0, placeholder)
        entry.configure(foreground=colors["text_muted"])
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        container.entry = entry  # 참조 저장
        return container

    @staticmethod
    def create_icon_button(parent, text: str, command=None, **kwargs) -> ttk.Button:
        """아이콘 버튼"""
        return ttk.Button(
            parent,
            text=text,
            style="Icon.TButton",
            command=command,
            **kwargs
        )

    @staticmethod
    def create_status_indicator(parent, status: str = "disconnected") -> ttk.Frame:
        """상태 표시 인디케이터"""
        theme = ThemeManager()
        colors = theme.colors

        container = ttk.Frame(parent)

        # 상태에 따른 색상
        status_colors = {
            "connected": colors["success"],
            "disconnected": colors["error"],
            "connecting": colors["warning"]
        }

        indicator_color = status_colors.get(status, colors["text_muted"])

        # Canvas로 원형 인디케이터
        canvas = tk.Canvas(
            container,
            width=12,
            height=12,
            bg=colors["bg_primary"],
            highlightthickness=0
        )
        canvas.create_oval(2, 2, 10, 10, fill=indicator_color, outline="")
        canvas.pack(side="left", padx=(0, 6))

        container.canvas = canvas
        container.indicator_color = indicator_color

        return container


# 전역 테마 매니저 인스턴스
theme_manager = ThemeManager()
