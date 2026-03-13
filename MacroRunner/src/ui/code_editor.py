"""
VBA 코드 에디터 컴포넌트
구문 강조, 줄 번호, 자동 들여쓰기 지원
"""
import tkinter as tk
from tkinter import ttk
import re
from typing import Callable, Optional, List, Tuple

from ..utils.constants import VBA_KEYWORDS, FONTS, font_config
from .theme import ThemeManager


class LineNumbers(tk.Canvas):
    """줄 번호 표시 캔버스"""

    def __init__(self, parent, text_widget: tk.Text, **kwargs):
        self.theme = ThemeManager()
        colors = self.theme.colors

        super().__init__(
            parent,
            width=50,
            bg=colors["bg_tertiary"],
            highlightthickness=0,
            **kwargs
        )
        self.text_widget = text_widget
        self._line_count = 0

    def redraw(self):
        """줄 번호 다시 그리기"""
        self.delete("all")
        colors = self.theme.colors
        fonts = font_config.get_fonts()

        self.configure(bg=colors["bg_tertiary"])

        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break

            y = dline[1]
            linenum = str(i).split(".")[0]

            self.create_text(
                45,
                y,
                anchor="ne",
                text=linenum,
                fill=colors["text_muted"],
                font=fonts["code"]
            )

            i = self.text_widget.index(f"{i}+1line")


class CodeEditor(ttk.Frame):
    """VBA 코드 에디터 - 구문 강조 및 편의 기능"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.theme = ThemeManager()
        self._on_change_callback: Optional[Callable] = None
        self._syntax_tags_configured = False

        self._setup_ui()
        self._setup_syntax_highlighting()
        self._setup_bindings()

        # 테마 변경 콜백 등록
        self.theme.register_callback(self._on_theme_change)

    def _setup_ui(self):
        """UI 구성"""
        colors = self.theme.colors
        fonts = font_config.get_fonts()

        # 메인 컨테이너
        self.container = ttk.Frame(self, style="Card.TFrame")
        self.container.pack(fill="both", expand=True)

        # 줄 번호 + 에디터 영역
        self.edit_frame = tk.Frame(self.container, bg=colors["bg_secondary"])
        self.edit_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # 텍스트 위젯
        self.text = tk.Text(
            self.edit_frame,
            wrap="none",
            font=fonts["code"],
            bg=colors["bg_secondary"],
            fg=colors["text_primary"],
            insertbackground=colors["accent"],
            selectbackground=colors["accent"],
            selectforeground=colors["bg_primary"],
            relief="flat",
            padx=12,
            pady=12,
            undo=True,
            maxundo=50,
            autoseparators=True
        )

        # 줄 번호
        self.line_numbers = LineNumbers(self.edit_frame, self.text)
        self.line_numbers.pack(side="left", fill="y")

        # 스크롤바
        self.v_scrollbar = ttk.Scrollbar(
            self.edit_frame,
            orient="vertical",
            command=self._on_scroll
        )
        self.v_scrollbar.pack(side="right", fill="y")

        self.h_scrollbar = ttk.Scrollbar(
            self.container,
            orient="horizontal",
            command=self.text.xview
        )
        self.h_scrollbar.pack(side="bottom", fill="x")

        # 텍스트 위젯 스크롤 연결
        self.text.configure(
            yscrollcommand=self._on_text_scroll,
            xscrollcommand=self.h_scrollbar.set
        )
        self.text.pack(side="left", fill="both", expand=True)

    def _on_scroll(self, *args):
        """스크롤 이벤트 처리"""
        self.text.yview(*args)
        self.line_numbers.redraw()

    def _on_text_scroll(self, first, last):
        """텍스트 스크롤 시 줄 번호도 업데이트"""
        self.v_scrollbar.set(first, last)
        self.line_numbers.redraw()

    def _setup_syntax_highlighting(self):
        """구문 강조 태그 설정"""
        colors = self.theme.colors
        fonts = font_config.get_fonts()

        # 키워드
        self.text.tag_configure(
            "keyword",
            foreground="#cba6f7",  # Mauve
            font=fonts["code_bold"]
        )

        # 타입
        self.text.tag_configure(
            "type",
            foreground="#f9e2af",  # Yellow
            font=fonts["code"]
        )

        # 문자열
        self.text.tag_configure(
            "string",
            foreground="#a6e3a1",  # Green
            font=fonts["code"]
        )

        # 주석
        self.text.tag_configure(
            "comment",
            foreground=colors["text_muted"],
            font=fonts["code"]
        )

        # 숫자
        self.text.tag_configure(
            "number",
            foreground="#fab387",  # Peach
            font=fonts["code"]
        )

        # 함수/서브루틴 이름
        self.text.tag_configure(
            "function",
            foreground="#89b4fa",  # Blue
            font=fonts["code_bold"]
        )

        # 오류 (빨간 밑줄)
        self.text.tag_configure(
            "error",
            underline=True,
            underlinefg=colors["error"]
        )

        self._syntax_tags_configured = True

    def _setup_bindings(self):
        """이벤트 바인딩"""
        # 내용 변경 시
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._on_key_release)

        # 줄 번호 업데이트
        self.text.bind("<Configure>", lambda e: self.line_numbers.redraw())
        self.text.bind("<MouseWheel>", lambda e: self.after(10, self.line_numbers.redraw))

        # 자동 들여쓰기
        self.text.bind("<Return>", self._auto_indent)

        # 탭 크기 조정
        self.text.bind("<Tab>", self._handle_tab)

    def _on_modified(self, event=None):
        """텍스트 수정 이벤트"""
        if self.text.edit_modified():
            self._apply_syntax_highlighting()
            if self._on_change_callback:
                self._on_change_callback()
            self.text.edit_modified(False)

    def _on_key_release(self, event=None):
        """키 입력 후 줄 번호 업데이트"""
        self.line_numbers.redraw()

    def _apply_syntax_highlighting(self):
        """구문 강조 적용"""
        if not self._syntax_tags_configured:
            return

        # 기존 태그 제거
        for tag in ["keyword", "type", "string", "comment", "number", "function"]:
            self.text.tag_remove(tag, "1.0", "end")

        content = self.text.get("1.0", "end-1c")

        # 주석 처리 (가장 먼저)
        for match in re.finditer(r"'[^\n]*", content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("comment", start, end)

        # 문자열
        for match in re.finditer(r'"[^"]*"', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("string", start, end)

        # 키워드
        for keyword in VBA_KEYWORDS["keywords"]:
            pattern = rf'\b{re.escape(keyword)}\b'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add("keyword", start, end)

        # 타입
        for type_name in VBA_KEYWORDS["types"]:
            pattern = rf'\b{re.escape(type_name)}\b'
            for match in re.finditer(pattern, content, re.IGNORECASE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text.tag_add("type", start, end)

        # 함수/서브 이름
        for match in re.finditer(r'\b(Sub|Function)\s+(\w+)', content, re.IGNORECASE):
            start = f"1.0+{match.start(2)}c"
            end = f"1.0+{match.end(2)}c"
            self.text.tag_add("function", start, end)

        # 숫자
        for match in re.finditer(r'\b\d+\.?\d*\b', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("number", start, end)

    def _auto_indent(self, event=None):
        """자동 들여쓰기"""
        # 현재 줄의 들여쓰기 가져오기
        line = self.text.get("insert linestart", "insert")
        indent = ""
        for char in line:
            if char in " \t":
                indent += char
            else:
                break

        # 현재 줄이 블록 시작인 경우 추가 들여쓰기
        stripped = line.strip().lower()
        if any(stripped.startswith(kw) for kw in ["sub ", "function ", "if ", "for ", "do ", "while ", "with ", "select "]):
            indent += "    "

        # 새 줄에 들여쓰기 삽입
        self.text.insert("insert", f"\n{indent}")
        self.line_numbers.redraw()
        return "break"

    def _handle_tab(self, event=None):
        """탭을 4개 스페이스로 변환"""
        self.text.insert("insert", "    ")
        return "break"

    def _on_theme_change(self, theme: str):
        """테마 변경 시 색상 업데이트"""
        colors = self.theme.colors
        fonts = font_config.get_fonts()

        self.text.configure(
            bg=colors["bg_secondary"],
            fg=colors["text_primary"],
            insertbackground=colors["accent"],
            selectbackground=colors["accent"],
            selectforeground=colors["bg_primary"],
            font=fonts["code"]
        )

        self.edit_frame.configure(bg=colors["bg_secondary"])
        self.line_numbers.configure(bg=colors["bg_tertiary"])
        self.line_numbers.redraw()

        self._setup_syntax_highlighting()
        self._apply_syntax_highlighting()

    def update_fonts(self):
        """폰트 설정 업데이트"""
        fonts = font_config.get_fonts()

        self.text.configure(font=fonts["code"])
        self._setup_syntax_highlighting()
        self._apply_syntax_highlighting()
        self.line_numbers.redraw()

    # Public API

    def get_code(self) -> str:
        """코드 내용 반환"""
        return self.text.get("1.0", "end-1c")

    def set_code(self, code: str):
        """코드 내용 설정"""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", code)
        self._apply_syntax_highlighting()
        self.line_numbers.redraw()
        self.text.edit_modified(False)
        self.text.edit_reset()

    def clear(self):
        """에디터 내용 지우기"""
        self.text.delete("1.0", "end")
        self.line_numbers.redraw()

    def on_change(self, callback: Callable):
        """내용 변경 콜백 등록"""
        self._on_change_callback = callback

    def extract_functions(self) -> List[Tuple[str, str]]:
        """코드에서 Sub/Function 추출"""
        code = self.get_code()
        functions = []

        # Sub 찾기
        for match in re.finditer(r'\bSub\s+(\w+)\s*\(', code, re.IGNORECASE):
            functions.append(("Sub", match.group(1)))

        # Function 찾기
        for match in re.finditer(r'\bFunction\s+(\w+)\s*\(', code, re.IGNORECASE):
            functions.append(("Function", match.group(1)))

        return functions

    def is_modified(self) -> bool:
        """수정 여부 확인"""
        return self.text.edit_modified()

    def set_readonly(self, readonly: bool = True):
        """읽기 전용 모드 설정"""
        state = "disabled" if readonly else "normal"
        self.text.configure(state=state)

    def undo(self):
        """실행 취소"""
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        """다시 실행"""
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def validate_syntax(self) -> List[Tuple[int, str]]:
        """기본 VBA 문법 검사"""
        errors = []
        code = self.get_code()
        lines = code.split("\n")

        sub_count = 0
        function_count = 0
        if_count = 0
        for_count = 0
        with_count = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip().lower()

            # Sub/Function 카운트
            if stripped.startswith("sub "):
                sub_count += 1
            elif stripped == "end sub":
                sub_count -= 1
                if sub_count < 0:
                    errors.append((i, "End Sub without matching Sub"))
                    sub_count = 0

            if stripped.startswith("function "):
                function_count += 1
            elif stripped == "end function":
                function_count -= 1
                if function_count < 0:
                    errors.append((i, "End Function without matching Function"))
                    function_count = 0

            # If 카운트
            if stripped.startswith("if ") and stripped.endswith("then"):
                if_count += 1
            elif stripped == "end if":
                if_count -= 1
                if if_count < 0:
                    errors.append((i, "End If without matching If"))
                    if_count = 0

            # For 카운트
            if stripped.startswith("for "):
                for_count += 1
            elif stripped.startswith("next"):
                for_count -= 1
                if for_count < 0:
                    errors.append((i, "Next without matching For"))
                    for_count = 0

            # With 카운트
            if stripped.startswith("with "):
                with_count += 1
            elif stripped == "end with":
                with_count -= 1
                if with_count < 0:
                    errors.append((i, "End With without matching With"))
                    with_count = 0

        # 닫히지 않은 블록
        if sub_count > 0:
            errors.append((len(lines), f"{sub_count} unclosed Sub block(s)"))
        if function_count > 0:
            errors.append((len(lines), f"{function_count} unclosed Function block(s)"))
        if if_count > 0:
            errors.append((len(lines), f"{if_count} unclosed If block(s)"))
        if for_count > 0:
            errors.append((len(lines), f"{for_count} unclosed For block(s)"))
        if with_count > 0:
            errors.append((len(lines), f"{with_count} unclosed With block(s)"))

        return errors
