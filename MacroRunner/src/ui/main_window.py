"""
메인 윈도우
모든 컴포넌트 통합 및 이벤트 처리
"""
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from dataclasses import replace
import re

from ..core.macro_manager import MacroManager, Macro
from ..core.office_connector import OfficeConnector, MockOfficeConnector, ConnectionStatus
from ..utils.constants import SHORTCUTS, CONFIG_FILE, APP_NAME, APP_VERSION, FONTS, font_config
from .theme import ThemeManager, theme_manager
from .sidebar import Sidebar
from .code_editor import CodeEditor
from .statusbar import StatusBar, LogLevel
from .dialogs import (
    ask_confirm, ask_input, ask_category, show_history,
    show_backups, show_settings, ask_file_open, ask_file_save
)


class MainWindow(tk.Tk):
    """메인 애플리케이션 윈도우"""

    def __init__(self, use_mock: bool = False):
        super().__init__()

        self.theme = ThemeManager()
        self.macro_manager = MacroManager()

        if use_mock:
            self.office_connector = MockOfficeConnector()
        else:
            self.office_connector = OfficeConnector()

        self._current_macro: Optional[Macro] = None
        self._unsaved_changes = False
        self._settings = self._load_settings()

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()
        self._setup_callbacks()

        self.office_connector.start_monitoring()
        self._restore_last_state()

    def _setup_window(self):
        """윈도우 설정"""
        colors = self.theme.colors

        self.title(f"{APP_NAME}")
        self.geometry("950x650")
        self.minsize(750, 500)
        self.configure(bg=colors["bg_primary"])

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.theme.init_style(self)

    def _setup_ui(self):
        """UI 구성"""
        colors = self.theme.colors

        # 메인 컨테이너
        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill="both", expand=True)

        # PanedWindow
        self.paned = ttk.PanedWindow(self.main_container, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # 사이드바 (좌측) - 240px
        self.sidebar = Sidebar(
            self.paned,
            self.macro_manager,
            self.office_connector
        )
        self.sidebar.configure(width=240)
        self.paned.add(self.sidebar, weight=0)

        # 메인 에디터 영역
        self.editor_container = ttk.Frame(self.paned, style="TFrame")
        self.paned.add(self.editor_container, weight=1)

        self.after(100, lambda: self.paned.sashpos(0, 240))

        self._create_editor_area()

        # 상태바
        self.statusbar = StatusBar(self)
        self.statusbar.pack(fill="x", side="bottom")

        self.statusbar.log_info("MacroRunner 준비됨")

    def _create_editor_area(self):
        """에디터 영역"""
        colors = self.theme.colors

        # ===== 상단 툴바 =====
        toolbar = ttk.Frame(self.editor_container, style="TFrame")
        toolbar.pack(fill="x", padx=12, pady=(12, 6))

        # 매크로 이름
        self.macro_name_label = ttk.Label(
            toolbar,
            text="매크로를 선택하세요",
            style="Title.TLabel",
            font=("Segoe UI", 14, "bold")
        )
        self.macro_name_label.pack(side="left")

        # 수정됨 표시
        self.modified_label = ttk.Label(toolbar, text="", style="Warning.TLabel")
        self.modified_label.pack(side="left", padx=(8, 0))

        # 우측 아이콘 버튼들
        icon_frame = ttk.Frame(toolbar, style="TFrame")
        icon_frame.pack(side="right")

        ttk.Button(
            icon_frame, text="⚙️", style="Icon.TButton",
            command=self._show_settings, width=3
        ).pack(side="right", padx=2)

        ttk.Button(
            icon_frame, text="📋", style="Icon.TButton",
            command=self._show_history, width=3
        ).pack(side="right", padx=2)

        ttk.Button(
            icon_frame, text="📄", style="Icon.TButton",
            command=self._duplicate_macro, width=3
        ).pack(side="right", padx=2)

        # ===== 메타 정보 =====
        meta_frame = ttk.Frame(self.editor_container, style="TFrame")
        meta_frame.pack(fill="x", padx=12, pady=(0, 6))

        ttk.Label(meta_frame, text="카테고리:", style="Muted.TLabel").pack(side="left")
        self.category_btn = ttk.Button(
            meta_frame, text="일반", style="TButton",
            command=self._change_category, width=8
        )
        self.category_btn.pack(side="left", padx=(4, 12))

        ttk.Label(meta_frame, text="설명:", style="Muted.TLabel").pack(side="left")
        self.description_entry = ttk.Entry(meta_frame, font=("Segoe UI", 10))
        self.description_entry.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ===== 코드 에디터 =====
        self.code_editor = CodeEditor(self.editor_container)
        self.code_editor.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # ===== 하단 액션 바 =====
        action_bar = ttk.Frame(self.editor_container, style="TFrame")
        action_bar.pack(fill="x", padx=12, pady=(0, 12))

        # 실행 함수 선택
        func_frame = ttk.Frame(action_bar, style="TFrame")
        func_frame.pack(side="left")

        ttk.Label(func_frame, text="실행:", style="TLabel").pack(side="left")
        self.function_combo = ttk.Combobox(
            func_frame, state="readonly", width=20, font=("Segoe UI", 10)
        )
        self.function_combo.pack(side="left", padx=(4, 0))

        # 버튼들
        btn_frame = ttk.Frame(action_bar, style="TFrame")
        btn_frame.pack(side="right")

        ttk.Button(
            btn_frame, text="삭제", style="Danger.TButton",
            command=self._delete_macro, width=6
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame, text="저장", style="TButton",
            command=self._save_macro, width=6
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame, text="주입만", style="TButton",
            command=self._inject_only, width=8
        ).pack(side="right", padx=(8, 0))

        ttk.Button(
            btn_frame, text="▶ 실행", style="Primary.TButton",
            command=self._inject_and_run, width=10
        ).pack(side="right")

    def _setup_shortcuts(self):
        """단축키"""
        self.bind(SHORTCUTS["save"], lambda e: self._save_macro())
        self.bind(SHORTCUTS["run"], lambda e: self._inject_and_run())
        self.bind(SHORTCUTS["inject"], lambda e: self._inject_only())
        self.bind(SHORTCUTS["new"], lambda e: self._new_macro())
        self.bind(SHORTCUTS["delete"], lambda e: self._delete_macro())
        self.bind(SHORTCUTS["search"], lambda e: self.sidebar.search_entry.focus_set())
        self.bind(SHORTCUTS["duplicate"], lambda e: self._duplicate_macro())
        self.bind(SHORTCUTS["export"], lambda e: self._export_macros())
        self.bind(SHORTCUTS["import"], lambda e: self._import_macros())
        self.bind(SHORTCUTS["toggle_favorite"], lambda e: self._toggle_favorite())
        self.bind(SHORTCUTS["undo"], lambda e: self.code_editor.undo())
        self.bind(SHORTCUTS["redo"], lambda e: self.code_editor.redo())

    def _setup_callbacks(self):
        """콜백"""
        self.sidebar.on_select(self._on_macro_select)
        self.sidebar.on_new(self._new_macro)
        self.code_editor.on_change(self._on_code_change)
        self.macro_manager.on_change(self._on_manager_change)
        self.theme.register_callback(self._on_theme_change)

    def _load_settings(self) -> dict:
        """설정 로드"""
        default = {
            "theme": "dark",
            "auto_backup": True,
            "max_backups": 10,
            "syntax_highlight": True,
            "line_numbers": True,
            "last_program": "excel",
            "last_macro": None,
            "window_geometry": None,
            "ui_font": font_config.ui_font,
            "code_font": font_config.code_font,
            "ui_size": font_config.ui_size,
            "code_size": font_config.code_size
        }

        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    default.update(loaded)
        except Exception:
            pass

        font_config.set_from_settings(default)
        return default

    def _save_settings(self):
        """설정 저장"""
        self._settings["window_geometry"] = self.geometry()
        self._settings["last_program"] = self.sidebar.get_current_program()

        if self._current_macro:
            self._settings["last_macro"] = self._current_macro.name

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    def _restore_last_state(self):
        """상태 복원"""
        if self._settings.get("window_geometry"):
            try:
                self.geometry(self._settings["window_geometry"])
            except:
                pass

        if self._settings.get("theme"):
            self.theme.set_theme(self._settings["theme"])

    # === 이벤트 핸들러 ===

    def _on_macro_select(self, macro: Macro):
        """매크로 선택"""
        if self._unsaved_changes:
            if ask_confirm(self, "변경사항 저장", "저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?"):
                self._save_current_macro()

        self._current_macro = macro
        self._load_macro_to_editor(macro)
        self._unsaved_changes = False
        self._update_modified_label()

    def _load_macro_to_editor(self, macro: Macro):
        """매크로 로드"""
        self.macro_name_label.configure(text=macro.name)
        self.category_btn.configure(text=macro.category)
        self.description_entry.delete(0, "end")
        self.description_entry.insert(0, macro.description)
        self.code_editor.set_code(macro.code)
        self._update_function_list()

    def _update_function_list(self):
        """함수 목록 업데이트"""
        functions = self.code_editor.extract_functions()

        if functions:
            values = [f"{t} {n}()" for t, n in functions]
            self.function_combo.configure(values=values)
            self.function_combo.set(values[0])
        else:
            self.function_combo.configure(values=["(함수 없음)"])
            self.function_combo.set("(함수 없음)")

    def _on_code_change(self):
        """코드 변경"""
        self._unsaved_changes = True
        self._update_modified_label()
        self._update_function_list()

    def _update_modified_label(self):
        """수정됨 표시"""
        self.modified_label.configure(text="● 수정됨" if self._unsaved_changes else "")

    def _on_manager_change(self, action: str, data):
        """매니저 변경"""
        self.sidebar.refresh()

    def _on_theme_change(self, theme: str):
        """테마 변경"""
        colors = self.theme.colors
        self.configure(bg=colors["bg_primary"])
        self._settings["theme"] = theme

    def _on_close(self):
        """종료"""
        if self._unsaved_changes:
            if ask_confirm(self, "종료", "저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?"):
                self._save_current_macro()

        self._save_settings()
        self.macro_manager.save()
        self.office_connector.cleanup()
        self.destroy()

    # === 매크로 작업 ===

    def _new_macro(self):
        """새 매크로"""
        name = ask_input(self, "새 매크로", "매크로 이름:")
        if not name:
            return

        program = self.sidebar.get_current_program()

        if self.macro_manager.get(program, name):
            self.statusbar.log_error(f"'{name}' 이미 존재")
            return

        macro = Macro(
            name=name,
            code="Sub 새매크로()\n    \nEnd Sub",
            program=program
        )

        if self.macro_manager.add(macro):
            self.macro_manager.save()
            self.sidebar.refresh()
            self.sidebar.select_macro(name)
            self.statusbar.log_success(f"'{name}' 생성됨")

    def _save_macro(self):
        """저장"""
        self._save_current_macro()

    def _save_current_macro(self):
        """현재 매크로 저장"""
        if not self._current_macro:
            return

        errors = self.code_editor.validate_syntax()
        if errors:
            error_msg = "\n".join([f"Line {line}: {msg}" for line, msg in errors[:3]])
            self.statusbar.log_warning("문법 오류", error_msg)

        updated_macro = replace(
            self._current_macro,
            code=self.code_editor.get_code(),
            description=self.description_entry.get()
        )

        if self.macro_manager.update(updated_macro):
            self._current_macro = updated_macro
            self.macro_manager.save()
            self._unsaved_changes = False
            self._update_modified_label()
            self.statusbar.log_success(f"'{self._current_macro.name}' 저장됨")

    def _delete_macro(self):
        """삭제"""
        if not self._current_macro:
            return

        if not ask_confirm(
            self, "매크로 삭제",
            f"'{self._current_macro.name}'을(를) 삭제하시겠습니까?",
            danger=True
        ):
            return

        program = self.sidebar.get_current_program()
        name = self._current_macro.name

        if self.macro_manager.delete(program, name):
            self.macro_manager.save()
            self._current_macro = None
            self._unsaved_changes = False
            self.code_editor.clear()
            self.macro_name_label.configure(text="매크로를 선택하세요")
            self.sidebar.refresh()
            self.statusbar.log_info(f"'{name}' 삭제됨")

    def _duplicate_macro(self):
        """복제"""
        if not self._current_macro:
            return

        program = self.sidebar.get_current_program()
        new_macro = self.macro_manager.duplicate(program, self._current_macro.name)

        if new_macro:
            self.macro_manager.save()
            self.sidebar.refresh()
            self.sidebar.select_macro(new_macro.name)
            self.statusbar.log_success(f"'{new_macro.name}' 복제됨")

    def _change_category(self):
        """카테고리 변경"""
        if not self._current_macro:
            return

        categories = self.macro_manager.get_categories()
        result = ask_category(self, categories, self._current_macro.category)

        if result:
            self._current_macro.category = result
            self.category_btn.configure(text=result)
            self._unsaved_changes = True
            self._update_modified_label()

            if result not in categories:
                self.macro_manager.add_category(result)

    def _toggle_favorite(self):
        """즐겨찾기"""
        if not self._current_macro:
            return

        program = self.sidebar.get_current_program()
        is_fav = self.macro_manager.toggle_favorite(program, self._current_macro.name)
        self.macro_manager.save()
        self.sidebar.refresh()

        self.statusbar.log_info(f"즐겨찾기 {'추가' if is_fav else '해제'}")

    def _show_history(self):
        """히스토리"""
        if not self._current_macro:
            return

        history = self._current_macro.history
        if not history:
            self.statusbar.log_info("버전 히스토리 없음")
            return

        result = show_history(self, self._current_macro.name, history)
        if result:
            program = self.sidebar.get_current_program()
            if self.macro_manager.restore_version(program, self._current_macro.name, result):
                self.macro_manager.save()
                self._load_macro_to_editor(self._current_macro)
                self.statusbar.log_success(f"버전 {result}로 복원됨")

    def _show_settings(self):
        """설정"""
        result = show_settings(self, self._settings)
        if result:
            self._settings.update(result)
            self._save_settings()

            self.theme.set_theme(result["theme"])
            font_config.set_from_settings(result)
            self.theme.refresh_fonts()
            self.code_editor.update_fonts()

            self.statusbar.log_info("설정 저장됨")

    # === 주입 및 실행 ===

    def _inject_only(self):
        """주입만"""
        if not self._current_macro:
            self.statusbar.log_error("매크로를 선택하세요")
            return

        program = self.sidebar.get_current_program()
        code = self.code_editor.get_code()

        success, message = self.office_connector.inject_macro(program, code)

        if success:
            self.macro_manager.record_usage(program, self._current_macro.name)
            self.statusbar.log_success("주입 완료", "Alt+F8로 실행")
        else:
            self.statusbar.log_error("주입 실패", message)

    def _inject_and_run(self):
        """주입 및 실행"""
        if not self._current_macro:
            self.statusbar.log_error("매크로를 선택하세요")
            return

        selected = self.function_combo.get()
        if not selected or selected == "(함수 없음)":
            self.statusbar.log_error("실행할 함수를 선택하세요")
            return

        match = re.match(r'(Sub|Function)\s+(\w+)\(\)', selected)
        if not match:
            self.statusbar.log_error("함수 형식 오류")
            return

        function_name = match.group(2)
        program = self.sidebar.get_current_program()
        code = self.code_editor.get_code()

        success, message = self.office_connector.inject_and_run(program, code, function_name)

        if success:
            self.macro_manager.record_usage(program, self._current_macro.name)
            self.statusbar.log_success(f"'{function_name}' 실행 완료")
        else:
            self.statusbar.log_error("실행 실패", message)

    # === 내보내기/가져오기 ===

    def _export_macros(self):
        """내보내기"""
        filepath = ask_file_save(
            [("JSON 파일", "*.json")],
            ".json",
            "매크로 내보내기"
        )

        if not filepath:
            return

        if self.macro_manager.export_macros(filepath):
            self.statusbar.log_success("내보내기 완료", filepath)
        else:
            self.statusbar.log_error("내보내기 실패")

    def _import_macros(self):
        """가져오기"""
        filepath = ask_file_open(
            [("JSON 파일", "*.json"), ("VBA 파일", "*.vba *.bas")],
            "매크로 가져오기"
        )

        if not filepath:
            return

        if filepath.endswith(".json"):
            success, skipped = self.macro_manager.import_macros(filepath)
            if success > 0:
                self.macro_manager.save()
                self.sidebar.refresh()
                self.statusbar.log_success(
                    f"{success}개 가져오기 완료",
                    f"{skipped}개 스킵" if skipped else ""
                )
            else:
                self.statusbar.log_error("가져오기 실패")
        else:
            program = self.sidebar.get_current_program()
            macro = self.macro_manager.import_from_vba_file(filepath, program)
            if macro:
                self.macro_manager.save()
                self.sidebar.refresh()
                self.sidebar.select_macro(macro.name)
                self.statusbar.log_success(f"'{macro.name}' 가져오기 완료")
            else:
                self.statusbar.log_error("VBA 파일 가져오기 실패")


def run_app(use_mock: bool = False):
    """애플리케이션 실행"""
    app = MainWindow(use_mock=use_mock)
    app.mainloop()
