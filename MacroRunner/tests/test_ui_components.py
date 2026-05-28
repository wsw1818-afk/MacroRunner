"""
UI 컴포넌트 테스트
"""
import pytest
import tkinter as tk
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def tk_root():
    """Shared Tk root for UI widget tests."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"GUI not available: {exc}")

    root.withdraw()
    yield root
    root.destroy()


class TestFunctionDisplay:
    """Execution function display labels."""

    def test_known_macro_function_label_is_korean(self):
        from src.ui.main_window import _format_function_label

        assert (
            _format_function_label("Sub", "MR_FitPictures_KeepAspect")
            == "비율 유지로 맞추기"
        )
        assert (
            _format_function_label("Sub", "MR_FitPictures_Fill_WithMargin")
            == "꽉 채우기 + 여백"
        )

    def test_unknown_macro_function_label_keeps_vba_name(self):
        from src.ui.main_window import _format_function_label

        assert _format_function_label("Sub", "CustomRun") == "Sub CustomRun()"

    def test_resolve_korean_function_label(self):
        from src.ui.main_window import _resolve_function_selection

        function_map = {"영역 꽉 채우기": "MR_FitPictures_Fill"}

        assert (
            _resolve_function_selection("영역 꽉 채우기", function_map)
            == "MR_FitPictures_Fill"
        )

    def test_resolve_legacy_function_label(self):
        from src.ui.main_window import _resolve_function_selection

        assert _resolve_function_selection("Sub CustomRun()", {}) == "CustomRun"


class TestMainWindowSizing:
    """Default window sizing."""

    def test_default_window_uses_larger_layout_on_normal_screen(self):
        from src.ui.main_window import _window_size_for_screen

        width, height, min_width, min_height = _window_size_for_screen(1366, 768)

        assert width == 1180
        assert height == 698
        assert min_width == 960
        assert min_height == 680

    def test_default_window_is_clamped_to_small_screen(self):
        from src.ui.main_window import _window_size_for_screen

        width, height, min_width, min_height = _window_size_for_screen(1024, 768)

        assert width == 984
        assert height == 698
        assert min_width == 960
        assert min_height == 680

    def test_saved_geometry_size_parsing(self):
        from src.ui.main_window import _parse_geometry_size

        assert _parse_geometry_size("950x650+10+20") == (950, 650)
        assert _parse_geometry_size("bad") is None

    def test_saved_geometry_must_fit_current_screen_bounds(self):
        from src.ui.main_window import _is_saved_geometry_usable

        assert _is_saved_geometry_usable("984x698+20+20", 960, 680, 984, 698, 1200, 900)
        assert not _is_saved_geometry_usable("950x650+20+20", 960, 680, 984, 698, 1200, 900)
        assert not _is_saved_geometry_usable("1200x800+20+20", 960, 680, 984, 698, 1200, 900)
        assert not _is_saved_geometry_usable("984x698+20+220", 960, 680, 984, 698, 1200, 900)


class TestCodeEditor:
    """CodeEditor 테스트"""

    @pytest.fixture
    def root(self, tk_root):
        """Shared Tk root for CodeEditor tests."""
        return tk_root

    @pytest.fixture
    def editor(self, root):
        """테스트용 에디터"""
        from src.ui.code_editor import CodeEditor
        return CodeEditor(root)

    def test_set_get_code(self, editor):
        """코드 설정 및 가져오기"""
        code = "Sub Test()\nEnd Sub"
        editor.set_code(code)

        result = editor.get_code()
        assert result == code

    def test_clear(self, editor):
        """에디터 내용 지우기"""
        editor.set_code("Some code")
        editor.clear()

        assert editor.get_code() == ""

    def test_extract_functions(self, editor):
        """함수 추출"""
        code = '''
Sub MySub()
End Sub

Function MyFunc() As String
End Function
        '''
        editor.set_code(code)

        functions = editor.extract_functions()
        assert len(functions) == 2

    def test_validate_syntax_valid(self, editor):
        """유효한 구문 검증"""
        code = '''
Sub Valid()
    If True Then
        MsgBox 1
    End If
End Sub
        '''
        editor.set_code(code)

        errors = editor.validate_syntax()
        assert len(errors) == 0

    def test_validate_syntax_invalid(self, editor):
        """유효하지 않은 구문 검증"""
        code = '''
Sub Invalid()
    If True Then
        MsgBox 1
End Sub
        '''
        editor.set_code(code)

        errors = editor.validate_syntax()
        assert len(errors) > 0

    def test_validate_unclosed_sub(self, editor):
        """닫히지 않은 Sub"""
        code = "Sub Unclosed()"
        editor.set_code(code)

        errors = editor.validate_syntax()
        assert len(errors) > 0
        assert any("Sub" in str(e) for e in errors)

    def test_validate_unclosed_for(self, editor):
        """닫히지 않은 For"""
        code = '''
Sub Test()
    For i = 1 To 10
End Sub
        '''
        editor.set_code(code)

        errors = editor.validate_syntax()
        assert len(errors) > 0

    def test_is_modified(self, editor):
        """수정 여부 확인"""
        editor.set_code("Initial")

        # 초기에는 수정 안됨
        assert editor.is_modified() == False

    def test_undo_redo(self, editor):
        """실행 취소/다시 실행"""
        editor.set_code("Line 1")

        # undo/redo 메서드 호출 (에러 없이 실행되는지)
        editor.undo()
        editor.redo()


class TestThemeManager:
    """ThemeManager 테스트"""

    @pytest.fixture
    def theme(self):
        from src.ui.theme import ThemeManager
        return ThemeManager()

    def test_initial_theme(self, theme):
        """초기 테마"""
        assert theme.current_theme == "dark"

    def test_toggle_theme(self, theme):
        """테마 전환"""
        initial = theme.current_theme

        theme.toggle_theme()
        assert theme.current_theme != initial

        theme.toggle_theme()
        assert theme.current_theme == initial

    def test_set_theme(self, theme):
        """테마 설정"""
        theme.set_theme("light")
        assert theme.current_theme == "light"

        theme.set_theme("dark")
        assert theme.current_theme == "dark"

    def test_colors(self, theme):
        """색상 반환"""
        colors = theme.colors

        assert "bg_primary" in colors
        assert "accent" in colors
        assert "text_primary" in colors

    def test_callback(self, theme):
        """테마 변경 콜백"""
        callback_called = []

        def on_change(new_theme):
            callback_called.append(new_theme)

        theme.register_callback(on_change)
        theme.toggle_theme()

        assert len(callback_called) == 1


class TestStatusBar:
    """StatusBar 테스트"""

    @pytest.fixture
    def root(self, tk_root):
        """Shared Tk root for StatusBar tests."""
        return tk_root

    @pytest.fixture
    def statusbar(self, root):
        from src.ui.statusbar import StatusBar
        return StatusBar(root)

    def test_log_info(self, statusbar):
        """정보 로그"""
        statusbar.log_info("테스트 메시지")

        logs = statusbar.get_logs()
        assert len(logs) == 1
        assert logs[0].message == "테스트 메시지"

    def test_log_success(self, statusbar):
        """성공 로그"""
        statusbar.log_success("성공!")

        logs = statusbar.get_logs()
        assert logs[-1].level.value == "success"

    def test_log_error(self, statusbar):
        """에러 로그"""
        statusbar.log_error("에러 발생", "상세 정보")

        logs = statusbar.get_logs()
        assert logs[-1].level.value == "error"
        assert logs[-1].details == "상세 정보"

    def test_clear_logs(self, statusbar):
        """로그 지우기"""
        statusbar.log_info("1")
        statusbar.log_info("2")
        statusbar.clear_logs()

        logs = statusbar.get_logs()
        assert len(logs) == 0

    def test_export_logs(self, statusbar):
        """로그 내보내기"""
        statusbar.log_info("Export test")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            filepath = f.name

        try:
            result = statusbar.export_logs(filepath)
            assert result == True

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Export test" in content
        finally:
            Path(filepath).unlink(missing_ok=True)


class TestDialogs:
    """다이얼로그 테스트"""

    def test_file_type_filters(self):
        """파일 유형 필터 형식 확인"""
        from src.ui.dialogs import ask_file_open, ask_file_save

        # 함수가 존재하는지만 확인 (실제 실행은 GUI 필요)
        assert callable(ask_file_open)
        assert callable(ask_file_save)


class TestIntegration:
    """통합 테스트"""

    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_main_window_creation(self, temp_dir, monkeypatch):
        """메인 윈도우 생성 테스트 (Mock 모드)"""
        # 경로 패치
        monkeypatch.setattr("src.core.macro_manager.MACROS_DIR", temp_dir / "macros")
        monkeypatch.setattr("src.core.macro_manager.BACKUPS_DIR", temp_dir / "backups")
        monkeypatch.setattr("src.core.macro_manager.MACRO_INDEX_FILE", temp_dir / "macros" / "macro_index.json")
        monkeypatch.setattr("src.utils.constants.CONFIG_FILE", temp_dir / "config.json")

        from src.ui.main_window import MainWindow

        # Mock 모드로 생성 후 바로 종료
        try:
            window = MainWindow(use_mock=True)
            window.update()  # 이벤트 처리

            # 기본 상태 확인
            assert window.macro_manager is not None
            assert window.office_connector is not None

            window.destroy()
        except tk.TclError:
            # 헤드리스 환경에서는 스킵
            pytest.skip("GUI not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
