"""
상태바 컴포넌트
실행 로그, 상태 메시지, 단축키 안내
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum

from .theme import ThemeManager


class LogLevel(Enum):
    """로그 레벨"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LogEntry:
    """로그 항목"""
    timestamp: datetime
    level: LogLevel
    message: str
    details: str = ""


class StatusBar(ttk.Frame):
    """상태바 - 로그 표시 및 상태 정보"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Secondary.TFrame", **kwargs)

        self.theme = ThemeManager()
        self._logs: List[LogEntry] = []
        self._max_logs = 100
        self._expanded = False

        self._setup_ui()

        # 테마 변경 콜백
        self.theme.register_callback(self._on_theme_change)

    def _setup_ui(self):
        """UI 구성"""
        colors = self.theme.colors

        # 메인 컨테이너
        self.configure(padding=(16, 8))

        # 상단 바 (항상 표시)
        self.top_bar = ttk.Frame(self, style="Secondary.TFrame")
        self.top_bar.pack(fill="x")

        # 상태 아이콘
        self.status_icon = ttk.Label(
            self.top_bar,
            text="✓",
            style="Success.TLabel",
            font=("Segoe UI", 11)
        )
        self.status_icon.pack(side="left", padx=(0, 8))

        # 상태 메시지
        self.status_label = ttk.Label(
            self.top_bar,
            text="준비",
            style="TLabel"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # 단축키 안내
        self.shortcut_label = ttk.Label(
            self.top_bar,
            text="Ctrl+Enter: 실행 | Ctrl+S: 저장",
            style="Muted.TLabel"
        )
        self.shortcut_label.pack(side="right", padx=(16, 0))

        # 확장 버튼
        self.expand_btn = ttk.Button(
            self.top_bar,
            text="▲",
            style="Icon.TButton",
            command=self._toggle_expand,
            width=3
        )
        self.expand_btn.pack(side="right", padx=(8, 0))

        # 확장 영역 (로그 목록)
        self.log_frame = ttk.Frame(self, style="Secondary.TFrame")
        # 기본적으로 숨김

        # 로그 텍스트
        self.log_text = tk.Text(
            self.log_frame,
            height=6,
            font=("Consolas", 9),
            bg=colors["bg_tertiary"],
            fg=colors["text_secondary"],
            relief="flat",
            padx=8,
            pady=8,
            state="disabled",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, pady=(8, 0))

        # 로그 레벨별 태그 설정
        self._setup_log_tags()

    def _setup_log_tags(self):
        """로그 레벨별 태그 설정"""
        colors = self.theme.colors

        self.log_text.tag_configure(
            "info",
            foreground=colors["text_secondary"]
        )
        self.log_text.tag_configure(
            "success",
            foreground=colors["success"]
        )
        self.log_text.tag_configure(
            "warning",
            foreground=colors["warning"]
        )
        self.log_text.tag_configure(
            "error",
            foreground=colors["error"]
        )
        self.log_text.tag_configure(
            "timestamp",
            foreground=colors["text_muted"]
        )

    def _toggle_expand(self):
        """로그 영역 확장/축소"""
        if self._expanded:
            self.log_frame.pack_forget()
            self.expand_btn.configure(text="▲")
        else:
            self.log_frame.pack(fill="both", expand=True)
            self.expand_btn.configure(text="▼")

        self._expanded = not self._expanded

    def _on_theme_change(self, theme: str):
        """테마 변경 시"""
        colors = self.theme.colors
        self.log_text.configure(
            bg=colors["bg_tertiary"],
            fg=colors["text_secondary"]
        )
        self._setup_log_tags()

    def _add_log_to_text(self, entry: LogEntry):
        """로그 텍스트에 항목 추가"""
        self.log_text.configure(state="normal")

        # 타임스탬프
        time_str = entry.timestamp.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{time_str}] ", "timestamp")

        # 메시지
        self.log_text.insert("end", f"{entry.message}\n", entry.level.value)

        # 상세 정보 (있는 경우)
        if entry.details:
            self.log_text.insert("end", f"  └ {entry.details}\n", "info")

        # 스크롤
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # Public API

    def log(self, message: str, level: LogLevel = LogLevel.INFO, details: str = ""):
        """로그 추가"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            details=details
        )

        self._logs.append(entry)

        # 최대 개수 유지
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

        # 텍스트에 추가
        self._add_log_to_text(entry)

        # 상태바 업데이트
        self._update_status(entry)

    def log_info(self, message: str, details: str = ""):
        """정보 로그"""
        self.log(message, LogLevel.INFO, details)

    def log_success(self, message: str, details: str = ""):
        """성공 로그"""
        self.log(message, LogLevel.SUCCESS, details)

    def log_warning(self, message: str, details: str = ""):
        """경고 로그"""
        self.log(message, LogLevel.WARNING, details)

    def log_error(self, message: str, details: str = ""):
        """에러 로그"""
        self.log(message, LogLevel.ERROR, details)

    def _update_status(self, entry: LogEntry):
        """상태바 메시지 업데이트"""
        icons = {
            LogLevel.INFO: "ℹ️",
            LogLevel.SUCCESS: "✓",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "✗"
        }

        styles = {
            LogLevel.INFO: "TLabel",
            LogLevel.SUCCESS: "Success.TLabel",
            LogLevel.WARNING: "TLabel",
            LogLevel.ERROR: "Error.TLabel"
        }

        self.status_icon.configure(text=icons[entry.level])
        self.status_label.configure(text=entry.message, style=styles[entry.level])

    def set_status(self, message: str, level: LogLevel = LogLevel.INFO):
        """상태 메시지만 설정 (로그 없이)"""
        entry = LogEntry(datetime.now(), level, message)
        self._update_status(entry)

    def clear_logs(self):
        """로그 지우기"""
        self._logs.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.set_status("로그가 지워졌습니다.", LogLevel.INFO)

    def get_logs(self) -> List[LogEntry]:
        """로그 목록 반환"""
        return list(self._logs)

    def export_logs(self, filepath: str) -> bool:
        """로그 내보내기"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for entry in self._logs:
                    time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{time_str}] [{entry.level.value.upper()}] {entry.message}\n")
                    if entry.details:
                        f.write(f"  Details: {entry.details}\n")
            return True
        except Exception:
            return False

    def update_shortcuts(self, shortcuts: List[Tuple[str, str]]):
        """단축키 안내 업데이트"""
        text = " | ".join([f"{key}: {desc}" for key, desc in shortcuts])
        self.shortcut_label.configure(text=text)
