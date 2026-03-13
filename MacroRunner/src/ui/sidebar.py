"""
사이드바 컴포넌트
매크로 목록, 검색, 프로그램 선택 (탭 기반)
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List

from ..core.macro_manager import Macro, MacroManager
from ..core.office_connector import OfficeConnector, ConnectionStatus
from .theme import ThemeManager, ModernWidgets


class Sidebar(ttk.Frame):
    """사이드바 - 탭 기반 프로그램 선택, 검색, 매크로 목록"""

    def __init__(self, parent, macro_manager: MacroManager,
                 office_connector: OfficeConnector, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        self.theme = ThemeManager()
        self.macro_manager = macro_manager
        self.office_connector = office_connector

        self._current_program = tk.StringVar(value="excel")
        self._search_var = tk.StringVar()
        self._filter_var = tk.StringVar(value="all")

        self._on_select_callback: Optional[Callable] = None
        self._on_new_callback: Optional[Callable] = None

        self._setup_ui()
        self._setup_bindings()
        self._refresh_list()

        # 테마 변경 콜백
        self.theme.register_callback(self._on_theme_change)

    def _setup_ui(self):
        """UI 구성"""
        colors = self.theme.colors

        # ===== 상단: 프로그램 탭 =====
        self._create_program_tabs()

        # ===== 연결 상태 바 =====
        self._create_connection_bar()

        # ===== 검색 =====
        self._create_search()

        # ===== 매크로 목록 (메인 영역) =====
        self._create_macro_list()

        # ===== 하단: 새 매크로 버튼 =====
        self._create_bottom_bar()

    def _create_program_tabs(self):
        """프로그램 선택 탭 (상단)"""
        colors = self.theme.colors

        tab_frame = ttk.Frame(self, style="TFrame")
        tab_frame.pack(fill="x")

        self.tab_buttons = {}
        programs = [
            ("Excel", "excel", "📊"),
            ("PPT", "ppt", "📽️"),
            ("Word", "word", "📝")
        ]

        for text, value, icon in programs:
            btn = tk.Button(
                tab_frame,
                text=f"{icon} {text}",
                font=("Segoe UI", 10),
                bd=0,
                padx=12,
                pady=8,
                cursor="hand2",
                command=lambda v=value: self._select_program(v)
            )
            btn.pack(side="left", fill="x", expand=True)
            self.tab_buttons[value] = btn

        self._update_tab_styles()

    def _update_tab_styles(self):
        """탭 스타일 업데이트"""
        colors = self.theme.colors
        current = self._current_program.get()

        for value, btn in self.tab_buttons.items():
            if value == current:
                btn.configure(
                    bg=colors["accent"],
                    fg="#ffffff",
                    activebackground=colors["accent"],
                    activeforeground="#ffffff"
                )
            else:
                btn.configure(
                    bg=colors["bg_tertiary"],
                    fg=colors["text_secondary"],
                    activebackground=colors["bg_secondary"],
                    activeforeground=colors["text_primary"]
                )

    def _select_program(self, program: str):
        """프로그램 선택"""
        self._current_program.set(program)
        self._update_tab_styles()
        self._on_program_change()

    def _create_connection_bar(self):
        """연결 상태 바"""
        colors = self.theme.colors

        self.conn_frame = ttk.Frame(self, style="TFrame")
        self.conn_frame.pack(fill="x", padx=8, pady=4)

        # 상태 인디케이터
        self.status_indicator = tk.Canvas(
            self.conn_frame,
            width=8,
            height=8,
            bg=colors["bg_primary"],
            highlightthickness=0
        )
        self.status_indicator.pack(side="left", padx=(0, 6))
        self._draw_status_indicator(ConnectionStatus.DISCONNECTED)

        # 상태 텍스트
        self.status_label = ttk.Label(
            self.conn_frame,
            text="연결 안됨",
            style="Muted.TLabel",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # 연결 버튼
        self.connect_btn = ttk.Button(
            self.conn_frame,
            text="연결",
            style="TButton",
            command=self._try_connect,
            width=5
        )
        self.connect_btn.pack(side="right")

        # 문서 선택 (숨김 상태로 시작)
        self.doc_select_frame = ttk.Frame(self, style="TFrame")

        self.doc_combo = ttk.Combobox(
            self.doc_select_frame,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.doc_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.doc_combo.bind("<<ComboboxSelected>>", self._on_document_select)

        ttk.Button(
            self.doc_select_frame,
            text="↻",
            style="Icon.TButton",
            command=self._refresh_document_list,
            width=2
        ).pack(side="right")

    def _draw_status_indicator(self, status: ConnectionStatus):
        """상태 인디케이터 그리기"""
        colors = self.theme.colors
        self.status_indicator.delete("all")

        status_colors = {
            ConnectionStatus.CONNECTED: colors["success"],
            ConnectionStatus.DISCONNECTED: colors["text_muted"],
            ConnectionStatus.CONNECTING: colors["warning"],
            ConnectionStatus.ERROR: colors["error"]
        }

        color = status_colors.get(status, colors["text_muted"])
        self.status_indicator.create_oval(0, 0, 8, 8, fill=color, outline="")

    def _create_search(self):
        """검색 및 필터"""
        colors = self.theme.colors

        search_frame = ttk.Frame(self, style="TFrame")
        search_frame.pack(fill="x", padx=8, pady=(4, 2))

        # 검색 입력
        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=("Segoe UI", 10)
        )
        self.search_entry.pack(fill="x")
        self._set_placeholder(self.search_entry, "🔍 검색...")

        # 필터 버튼들
        filter_frame = ttk.Frame(self, style="TFrame")
        filter_frame.pack(fill="x", padx=8, pady=(0, 4))

        filters = [("전체", "all"), ("⭐ 즐겨찾기", "favorite"), ("🕐 최근", "recent")]

        for text, value in filters:
            btn = ttk.Radiobutton(
                filter_frame,
                text=text,
                value=value,
                variable=self._filter_var,
                style="TRadiobutton",
                command=self._refresh_list
            )
            btn.pack(side="left", padx=(0, 6))

    def _set_placeholder(self, entry: ttk.Entry, placeholder: str):
        """플레이스홀더 설정"""
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")

        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, placeholder)

        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def _create_macro_list(self):
        """매크로 목록"""
        colors = self.theme.colors

        # 리스트 프레임 (expand로 남은 공간 모두 사용)
        list_frame = ttk.Frame(self, style="TFrame")
        list_frame.pack(fill="both", expand=True, padx=8, pady=2)

        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=("name",),
            show="tree",
            selectmode="browse",
            style="Treeview"
        )

        # 스크롤바
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 컬럼 설정
        self.tree.column("#0", width=24, stretch=False)
        self.tree.column("name", width=200)

        # 이벤트
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

    def _create_bottom_bar(self):
        """하단 바"""
        colors = self.theme.colors

        bottom = ttk.Frame(self, style="TFrame")
        bottom.pack(fill="x", padx=8, pady=8)

        # 테마 토글
        self.theme_btn = ttk.Button(
            bottom,
            text="🌙",
            style="Icon.TButton",
            command=self._toggle_theme,
            width=3
        )
        self.theme_btn.pack(side="left")

        # 새 매크로 버튼
        new_btn = ttk.Button(
            bottom,
            text="+ 새 매크로",
            style="Primary.TButton",
            command=self._on_new_macro
        )
        new_btn.pack(side="right", fill="x", expand=True, padx=(8, 0))

    def _setup_bindings(self):
        """이벤트 바인딩"""
        self._search_var.trace_add("write", lambda *args: self._refresh_list())
        self.office_connector.on_status_change(self._on_connection_status_change)

    def _on_theme_change(self, theme: str):
        """테마 변경"""
        colors = self.theme.colors
        self.status_indicator.configure(bg=colors["bg_primary"])
        self._update_tab_styles()

        program = self._current_program.get()
        status = self.office_connector.get_connection_status(program)
        self._draw_status_indicator(status.status)

        self.theme_btn.configure(text="☀️" if theme == "dark" else "🌙")

    def _toggle_theme(self):
        """테마 전환"""
        self.theme.toggle_theme()

    def _on_program_change(self):
        """프로그램 변경"""
        self._refresh_list()
        self._update_connection_status()

    def _update_connection_status(self):
        """연결 상태 업데이트"""
        program = self._current_program.get()
        info = self.office_connector.get_connection_status(program)

        self._draw_status_indicator(info.status)

        if info.status == ConnectionStatus.CONNECTED:
            # 파일명만 표시 (경로 제외)
            doc_name = info.document_name.split("\\")[-1].split("/")[-1]
            if len(doc_name) > 20:
                doc_name = doc_name[:17] + "..."
            self.status_label.configure(text=doc_name, style="Success.TLabel")
            self.connect_btn.configure(text="✓", state="disabled")
            self._refresh_document_list()
        elif info.status == ConnectionStatus.CONNECTING:
            self.status_label.configure(text="연결 중...", style="Muted.TLabel")
            self.connect_btn.configure(state="disabled")
            self.doc_select_frame.pack_forget()
        else:
            self.status_label.configure(text="연결 안됨", style="Muted.TLabel")
            self.connect_btn.configure(text="연결", state="normal")
            self.doc_select_frame.pack_forget()

    def _refresh_document_list(self):
        """문서 목록 새로고침"""
        program = self._current_program.get()
        documents = self.office_connector.get_open_documents(program)

        if len(documents) > 1:
            self._document_list = documents
            doc_names = [name for i, name in documents]
            self.doc_combo['values'] = doc_names

            selected_idx = self.office_connector._selected_document_index.get(program)
            if selected_idx:
                for idx, (i, name) in enumerate(documents):
                    if i == selected_idx:
                        self.doc_combo.current(idx)
                        break
            else:
                self.doc_combo.current(0)
                if documents:
                    self.office_connector._selected_document_index[program] = documents[0][0]

            self.doc_select_frame.pack(fill="x", padx=8, pady=(0, 4))
        else:
            self.doc_select_frame.pack_forget()

    def _on_document_select(self, event=None):
        """문서 선택"""
        if not hasattr(self, '_document_list'):
            return

        selection_idx = self.doc_combo.current()
        if 0 <= selection_idx < len(self._document_list):
            doc_index, doc_name = self._document_list[selection_idx]
            program = self._current_program.get()
            success, message = self.office_connector.activate_document(program, doc_index)
            if success:
                self.after(100, self._update_connection_status)

    def _on_connection_status_change(self, program: str, info):
        """연결 상태 변경 콜백"""
        if program == self._current_program.get():
            self.after(0, self._update_connection_status)

    def _try_connect(self):
        """연결 시도"""
        program = self._current_program.get()
        success, message = self.office_connector.connect(program)
        self._update_connection_status()

    def _refresh_list(self):
        """매크로 목록 새로고침"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        program = self._current_program.get()
        filter_type = self._filter_var.get()
        search_query = self._search_var.get()

        if search_query.startswith("🔍"):
            search_query = ""

        # 매크로 가져오기
        if filter_type == "favorite":
            macros = self.macro_manager.get_favorites(program)
        elif filter_type == "recent":
            macros = self.macro_manager.get_recent(program)
        else:
            macros = self.macro_manager.get_all(program)

        # 검색 필터
        if search_query:
            macros = [m for m in macros if search_query.lower() in m.name.lower()]

        # 즐겨찾기 우선 정렬
        macros.sort(key=lambda m: (not m.favorite, m.name.lower()))

        # 트리에 추가
        for macro in macros:
            icon = "⭐" if macro.favorite else "  "
            self.tree.insert(
                "",
                "end",
                iid=macro.name,
                text=icon,
                values=(macro.name,),
                tags=("favorite",) if macro.favorite else ()
            )

    def _on_tree_select(self, event=None):
        """항목 선택"""
        selection = self.tree.selection()
        if selection and self._on_select_callback:
            name = selection[0]
            program = self._current_program.get()
            macro = self.macro_manager.get(program, name)
            if macro:
                self._on_select_callback(macro)

    def _on_tree_double_click(self, event=None):
        """더블 클릭 - 즐겨찾기 토글"""
        selection = self.tree.selection()
        if selection:
            name = selection[0]
            program = self._current_program.get()
            self.macro_manager.toggle_favorite(program, name)
            self._refresh_list()
            if self.tree.exists(name):
                self.tree.selection_set(name)

    def _on_new_macro(self):
        """새 매크로"""
        if self._on_new_callback:
            self._on_new_callback()

    # === Public API ===

    def on_select(self, callback: Callable[[Macro], None]):
        self._on_select_callback = callback

    def on_new(self, callback: Callable):
        self._on_new_callback = callback

    def get_current_program(self) -> str:
        return self._current_program.get()

    def get_selected_macro(self) -> Optional[Macro]:
        selection = self.tree.selection()
        if selection:
            name = selection[0]
            program = self._current_program.get()
            return self.macro_manager.get(program, name)
        return None

    def select_macro(self, name: str):
        if self.tree.exists(name):
            self.tree.selection_set(name)
            self.tree.see(name)

    def refresh(self):
        self._refresh_list()
        self._update_connection_status()
