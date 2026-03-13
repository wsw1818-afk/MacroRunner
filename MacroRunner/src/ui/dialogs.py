"""
다이얼로그 컴포넌트
확인 다이얼로그, 입력 다이얼로그, 설정 다이얼로그
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
from typing import Optional, List, Callable
from datetime import datetime

from .theme import ThemeManager
from ..utils.constants import (
    RECOMMENDED_UI_FONTS, RECOMMENDED_CODE_FONTS,
    FONT_SIZE_MIN, FONT_SIZE_MAX, font_config
)


class BaseDialog(tk.Toplevel):
    """기본 다이얼로그 클래스"""

    def __init__(self, parent, title: str, width: int = 400, height: int = 300):
        super().__init__(parent)

        self.theme = ThemeManager()
        colors = self.theme.colors

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(bg=colors["bg_primary"])

        # 모달 설정
        self.transient(parent)
        self.grab_set()

        # 중앙 배치
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")

        self.result = None

        # ESC로 닫기
        self.bind("<Escape>", lambda e: self.cancel())

    def cancel(self):
        """취소"""
        self.result = None
        self.destroy()

    def ok(self):
        """확인"""
        self.destroy()


class ConfirmDialog(BaseDialog):
    """확인 다이얼로그"""

    def __init__(self, parent, title: str, message: str,
                 confirm_text: str = "확인", cancel_text: str = "취소",
                 danger: bool = False):
        super().__init__(parent, title, 400, 180)

        colors = self.theme.colors

        # 메시지
        msg_frame = ttk.Frame(self, style="TFrame", padding=24)
        msg_frame.pack(fill="both", expand=True)

        ttk.Label(
            msg_frame,
            text=message,
            style="TLabel",
            wraplength=350
        ).pack(pady=(0, 24))

        # 버튼
        btn_frame = ttk.Frame(msg_frame, style="TFrame")
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text=cancel_text,
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        style = "Danger.TButton" if danger else "Primary.TButton"
        ttk.Button(
            btn_frame,
            text=confirm_text,
            style=style,
            command=self.confirm
        ).pack(side="right")

        self.result = False

    def confirm(self):
        self.result = True
        self.destroy()


class InputDialog(BaseDialog):
    """입력 다이얼로그"""

    def __init__(self, parent, title: str, prompt: str,
                 default: str = "", placeholder: str = ""):
        super().__init__(parent, title, 400, 180)

        colors = self.theme.colors

        # 컨텐츠
        content = ttk.Frame(self, style="TFrame", padding=24)
        content.pack(fill="both", expand=True)

        # 프롬프트
        ttk.Label(
            content,
            text=prompt,
            style="TLabel"
        ).pack(anchor="w", pady=(0, 8))

        # 입력 필드
        self.entry = ttk.Entry(content, style="TEntry", font=("Segoe UI", 11))
        self.entry.pack(fill="x", pady=(0, 16))

        if default:
            self.entry.insert(0, default)
            self.entry.select_range(0, "end")

        # 버튼
        btn_frame = ttk.Frame(content, style="TFrame")
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text="취소",
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame,
            text="확인",
            style="Primary.TButton",
            command=self.ok
        ).pack(side="right")

        # 포커스
        self.entry.focus_set()

        # Enter로 확인
        self.entry.bind("<Return>", lambda e: self.ok())

    def ok(self):
        self.result = self.entry.get()
        self.destroy()


class CategoryDialog(BaseDialog):
    """카테고리 선택/추가 다이얼로그"""

    def __init__(self, parent, categories: List[str], current: str = ""):
        super().__init__(parent, "카테고리 선택", 350, 300)

        colors = self.theme.colors

        content = ttk.Frame(self, style="TFrame", padding=24)
        content.pack(fill="both", expand=True)

        # 기존 카테고리 목록
        ttk.Label(
            content,
            text="카테고리 선택",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        # 리스트박스
        self.listbox = tk.Listbox(
            content,
            font=("Segoe UI", 10),
            bg=colors["bg_secondary"],
            fg=colors["text_primary"],
            selectbackground=colors["accent"],
            selectforeground=colors["bg_primary"],
            relief="flat",
            highlightthickness=0
        )
        self.listbox.pack(fill="both", expand=True, pady=(0, 16))

        for cat in categories:
            self.listbox.insert("end", cat)
            if cat == current:
                self.listbox.select_set("end")

        # 새 카테고리 입력
        ttk.Label(
            content,
            text="또는 새 카테고리 입력",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(0, 4))

        self.new_entry = ttk.Entry(content, style="TEntry")
        self.new_entry.pack(fill="x", pady=(0, 16))

        # 버튼
        btn_frame = ttk.Frame(content, style="TFrame")
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame,
            text="취소",
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame,
            text="선택",
            style="Primary.TButton",
            command=self.ok
        ).pack(side="right")

        # 더블클릭으로 선택
        self.listbox.bind("<Double-1>", lambda e: self.ok())

    def ok(self):
        # 새 카테고리가 입력되었으면 우선
        new_cat = self.new_entry.get().strip()
        if new_cat:
            self.result = new_cat
        else:
            # 리스트에서 선택
            selection = self.listbox.curselection()
            if selection:
                self.result = self.listbox.get(selection[0])
            else:
                self.result = None

        self.destroy()


class HistoryDialog(BaseDialog):
    """버전 히스토리 다이얼로그"""

    def __init__(self, parent, macro_name: str, history: List[dict]):
        super().__init__(parent, f"'{macro_name}' 버전 히스토리", 500, 400)

        colors = self.theme.colors

        content = ttk.Frame(self, style="TFrame", padding=24)
        content.pack(fill="both", expand=True)

        # 버전 목록
        list_frame = ttk.Frame(content, style="TFrame")
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("version", "date"),
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("version", text="버전")
        self.tree.heading("date", text="수정일")
        self.tree.column("version", width=80)
        self.tree.column("date", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 히스토리 데이터 추가
        self.history = history
        for i, h in enumerate(reversed(history)):
            try:
                date = datetime.fromisoformat(h["modified"]).strftime("%Y-%m-%d %H:%M")
            except:
                date = h.get("modified", "")

            self.tree.insert("", "end", iid=str(i), values=(f"v{h['version']}", date))

        # 버튼
        btn_frame = ttk.Frame(content, style="TFrame")
        btn_frame.pack(fill="x", pady=(16, 0))

        ttk.Button(
            btn_frame,
            text="닫기",
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame,
            text="이 버전으로 복원",
            style="Primary.TButton",
            command=self.restore
        ).pack(side="right")

    def restore(self):
        selection = self.tree.selection()
        if selection:
            idx = int(selection[0])
            # 역순으로 저장했으므로 다시 역순
            actual_idx = len(self.history) - 1 - idx
            self.result = self.history[actual_idx]["version"]
        self.destroy()


class BackupDialog(BaseDialog):
    """백업 관리 다이얼로그"""

    def __init__(self, parent, backups: List[tuple]):
        super().__init__(parent, "백업 관리", 500, 400)

        colors = self.theme.colors

        content = ttk.Frame(self, style="TFrame", padding=24)
        content.pack(fill="both", expand=True)

        ttk.Label(
            content,
            text="저장된 백업 목록",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        # 백업 목록
        list_frame = ttk.Frame(content, style="TFrame")
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("date", "path"),
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("date", text="백업 시간")
        self.tree.heading("path", text="파일 경로")
        self.tree.column("date", width=150)
        self.tree.column("path", width=300)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 백업 데이터 추가
        self.backups = backups
        for path, dt in backups:
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            self.tree.insert("", "end", iid=path, values=(date_str, path))

        # 버튼
        btn_frame = ttk.Frame(content, style="TFrame")
        btn_frame.pack(fill="x", pady=(16, 0))

        ttk.Button(
            btn_frame,
            text="닫기",
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame,
            text="이 백업으로 복원",
            style="Primary.TButton",
            command=self.restore
        ).pack(side="right")

    def restore(self):
        selection = self.tree.selection()
        if selection:
            self.result = selection[0]
        self.destroy()


class SettingsDialog(BaseDialog):
    """설정 다이얼로그"""

    def __init__(self, parent, settings: dict):
        super().__init__(parent, "설정", 500, 580)

        self.settings = dict(settings)
        colors = self.theme.colors

        # 스크롤 가능한 영역
        canvas = tk.Canvas(self, bg=colors["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 마우스 휠 스크롤
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = ttk.Frame(scrollable_frame, style="TFrame", padding=24)
        content.pack(fill="both", expand=True)

        # 테마 설정
        theme_frame = ttk.LabelFrame(content, text="테마", padding=12)
        theme_frame.pack(fill="x", pady=(0, 16))

        self.theme_var = tk.StringVar(value=settings.get("theme", "dark"))
        ttk.Radiobutton(
            theme_frame,
            text="다크 모드",
            value="dark",
            variable=self.theme_var
        ).pack(anchor="w")
        ttk.Radiobutton(
            theme_frame,
            text="라이트 모드",
            value="light",
            variable=self.theme_var
        ).pack(anchor="w")

        # 글꼴 설정
        font_frame = ttk.LabelFrame(content, text="글꼴", padding=12)
        font_frame.pack(fill="x", pady=(0, 16))

        # 시스템에서 사용 가능한 폰트 가져오기
        try:
            available_fonts = sorted(set(tkfont.families()))
        except:
            available_fonts = []

        # UI 폰트
        ui_font_row = ttk.Frame(font_frame)
        ui_font_row.pack(fill="x", pady=(0, 8))

        ttk.Label(ui_font_row, text="UI 글꼴:").pack(side="left")
        self.ui_font_var = tk.StringVar(value=settings.get("ui_font", font_config.ui_font))

        # 권장 폰트 우선 + 나머지 폰트
        ui_font_list = RECOMMENDED_UI_FONTS.copy()
        for f in available_fonts:
            if f not in ui_font_list:
                ui_font_list.append(f)

        self.ui_font_combo = ttk.Combobox(
            ui_font_row,
            textvariable=self.ui_font_var,
            values=ui_font_list,
            width=20,
            state="readonly"
        )
        self.ui_font_combo.pack(side="left", padx=(8, 16))

        ttk.Label(ui_font_row, text="크기:").pack(side="left")
        self.ui_size_var = tk.StringVar(value=str(settings.get("ui_size", font_config.ui_size)))
        ui_size_spin = ttk.Spinbox(
            ui_font_row,
            from_=FONT_SIZE_MIN,
            to=FONT_SIZE_MAX,
            width=5,
            textvariable=self.ui_size_var
        )
        ui_size_spin.pack(side="left", padx=(8, 0))

        # 코드 폰트
        code_font_row = ttk.Frame(font_frame)
        code_font_row.pack(fill="x", pady=(8, 8))

        ttk.Label(code_font_row, text="코드 글꼴:").pack(side="left")
        self.code_font_var = tk.StringVar(value=settings.get("code_font", font_config.code_font))

        # 권장 코드 폰트 우선 + 나머지 폰트
        code_font_list = RECOMMENDED_CODE_FONTS.copy()
        for f in available_fonts:
            if f not in code_font_list:
                code_font_list.append(f)

        self.code_font_combo = ttk.Combobox(
            code_font_row,
            textvariable=self.code_font_var,
            values=code_font_list,
            width=20,
            state="readonly"
        )
        self.code_font_combo.pack(side="left", padx=(8, 16))

        ttk.Label(code_font_row, text="크기:").pack(side="left")
        self.code_size_var = tk.StringVar(value=str(settings.get("code_size", font_config.code_size)))
        code_size_spin = ttk.Spinbox(
            code_font_row,
            from_=FONT_SIZE_MIN,
            to=FONT_SIZE_MAX,
            width=5,
            textvariable=self.code_size_var
        )
        code_size_spin.pack(side="left", padx=(8, 0))

        # 폰트 미리보기
        preview_frame = ttk.Frame(font_frame)
        preview_frame.pack(fill="x", pady=(12, 0))

        ttk.Label(preview_frame, text="미리보기:", style="Muted.TLabel").pack(anchor="w")

        self.preview_text = tk.Text(
            preview_frame,
            height=3,
            wrap="word",
            bg=colors["bg_secondary"],
            fg=colors["text_primary"],
            relief="flat",
            padx=8,
            pady=8
        )
        self.preview_text.pack(fill="x", pady=(4, 0))
        self.preview_text.insert("1.0", "UI 글꼴 미리보기\n코드 글꼴: Sub Test()\n    MsgBox \"Hello\"")
        self.preview_text.configure(state="disabled")

        # 폰트 변경 시 미리보기 업데이트
        self.ui_font_combo.bind("<<ComboboxSelected>>", self._update_preview)
        self.code_font_combo.bind("<<ComboboxSelected>>", self._update_preview)
        ui_size_spin.bind("<KeyRelease>", self._update_preview)
        code_size_spin.bind("<KeyRelease>", self._update_preview)

        self._update_preview()

        # 자동 백업 설정
        backup_frame = ttk.LabelFrame(content, text="자동 백업", padding=12)
        backup_frame.pack(fill="x", pady=(0, 16))

        self.auto_backup_var = tk.BooleanVar(value=settings.get("auto_backup", True))
        ttk.Checkbutton(
            backup_frame,
            text="저장 시 자동 백업",
            variable=self.auto_backup_var
        ).pack(anchor="w")

        # 백업 보관 개수
        backup_count_frame = ttk.Frame(backup_frame)
        backup_count_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(backup_count_frame, text="최대 백업 개수:").pack(side="left")

        self.max_backups_var = tk.StringVar(value=str(settings.get("max_backups", 10)))
        backup_spin = ttk.Spinbox(
            backup_count_frame,
            from_=1,
            to=50,
            width=5,
            textvariable=self.max_backups_var
        )
        backup_spin.pack(side="left", padx=(8, 0))

        # 에디터 설정
        editor_frame = ttk.LabelFrame(content, text="에디터", padding=12)
        editor_frame.pack(fill="x", pady=(0, 16))

        self.syntax_highlight_var = tk.BooleanVar(value=settings.get("syntax_highlight", True))
        ttk.Checkbutton(
            editor_frame,
            text="구문 강조",
            variable=self.syntax_highlight_var
        ).pack(anchor="w")

        self.line_numbers_var = tk.BooleanVar(value=settings.get("line_numbers", True))
        ttk.Checkbutton(
            editor_frame,
            text="줄 번호 표시",
            variable=self.line_numbers_var
        ).pack(anchor="w")

        # 버튼
        btn_frame = ttk.Frame(content, style="TFrame")
        btn_frame.pack(fill="x", pady=(16, 0))

        ttk.Button(
            btn_frame,
            text="취소",
            style="TButton",
            command=self.cancel
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame,
            text="저장",
            style="Primary.TButton",
            command=self.save
        ).pack(side="right")

    def _update_preview(self, event=None):
        """폰트 미리보기 업데이트"""
        try:
            ui_font = self.ui_font_var.get()
            code_font = self.code_font_var.get()
            ui_size = int(self.ui_size_var.get())
            code_size = int(self.code_size_var.get())

            self.preview_text.configure(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", f"UI 글꼴 미리보기 ({ui_font}, {ui_size}pt)\n")
            self.preview_text.insert("end", f"코드: Sub Test() ({code_font}, {code_size}pt)")

            # 첫 번째 줄에 UI 폰트 적용
            self.preview_text.tag_configure("ui_preview", font=(ui_font, ui_size))
            self.preview_text.tag_add("ui_preview", "1.0", "1.end")

            # 두 번째 줄에 코드 폰트 적용
            self.preview_text.tag_configure("code_preview", font=(code_font, code_size))
            self.preview_text.tag_add("code_preview", "2.0", "2.end")

            self.preview_text.configure(state="disabled")
        except (ValueError, tk.TclError):
            pass

    def save(self):
        self.result = {
            "theme": self.theme_var.get(),
            "ui_font": self.ui_font_var.get(),
            "code_font": self.code_font_var.get(),
            "ui_size": int(self.ui_size_var.get()),
            "code_size": int(self.code_size_var.get()),
            "auto_backup": self.auto_backup_var.get(),
            "max_backups": int(self.max_backups_var.get()),
            "syntax_highlight": self.syntax_highlight_var.get(),
            "line_numbers": self.line_numbers_var.get()
        }
        self.destroy()


# 유틸리티 함수

def ask_confirm(parent, title: str, message: str, danger: bool = False) -> bool:
    """확인 다이얼로그 표시"""
    dialog = ConfirmDialog(parent, title, message, danger=danger)
    parent.wait_window(dialog)
    return dialog.result


def ask_input(parent, title: str, prompt: str, default: str = "") -> Optional[str]:
    """입력 다이얼로그 표시"""
    dialog = InputDialog(parent, title, prompt, default)
    parent.wait_window(dialog)
    return dialog.result


def ask_category(parent, categories: List[str], current: str = "") -> Optional[str]:
    """카테고리 선택 다이얼로그 표시"""
    dialog = CategoryDialog(parent, categories, current)
    parent.wait_window(dialog)
    return dialog.result


def show_history(parent, macro_name: str, history: List[dict]) -> Optional[int]:
    """히스토리 다이얼로그 표시"""
    dialog = HistoryDialog(parent, macro_name, history)
    parent.wait_window(dialog)
    return dialog.result


def show_backups(parent, backups: List[tuple]) -> Optional[str]:
    """백업 다이얼로그 표시"""
    dialog = BackupDialog(parent, backups)
    parent.wait_window(dialog)
    return dialog.result


def show_settings(parent, settings: dict) -> Optional[dict]:
    """설정 다이얼로그 표시"""
    dialog = SettingsDialog(parent, settings)
    parent.wait_window(dialog)
    return dialog.result


def ask_file_open(filetypes: List[tuple] = None, title: str = "파일 열기") -> Optional[str]:
    """파일 열기 다이얼로그"""
    if filetypes is None:
        filetypes = [
            ("VBA 파일", "*.vba *.bas"),
            ("텍스트 파일", "*.txt"),
            ("모든 파일", "*.*")
        ]
    return filedialog.askopenfilename(title=title, filetypes=filetypes)


def ask_file_save(filetypes: List[tuple] = None, default_ext: str = ".json",
                  title: str = "파일 저장") -> Optional[str]:
    """파일 저장 다이얼로그"""
    if filetypes is None:
        filetypes = [
            ("JSON 파일", "*.json"),
            ("모든 파일", "*.*")
        ]
    return filedialog.asksaveasfilename(
        title=title,
        filetypes=filetypes,
        defaultextension=default_ext
    )
