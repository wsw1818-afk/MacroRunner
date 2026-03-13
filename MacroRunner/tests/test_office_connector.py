"""
OfficeConnector 테스트
"""
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.office_connector import (
    OfficeConnector, MockOfficeConnector, ConnectionStatus, ConnectionInfo
)


class TestMockOfficeConnector:
    """Mock Office Connector 테스트"""

    @pytest.fixture
    def connector(self):
        return MockOfficeConnector()

    def test_initial_status(self, connector):
        """초기 연결 상태"""
        excel_status = connector.get_connection_status("excel")
        assert excel_status.status == ConnectionStatus.CONNECTED

        word_status = connector.get_connection_status("word")
        assert word_status.status == ConnectionStatus.DISCONNECTED

    def test_connect(self, connector):
        """연결 테스트"""
        success, message = connector.connect("word")
        assert success == True
        assert "연결됨" in message

        status = connector.get_connection_status("word")
        assert status.status == ConnectionStatus.CONNECTED

    def test_inject_macro(self, connector):
        """매크로 주입 테스트"""
        code = "Sub Test()\nEnd Sub"
        success, message = connector.inject_macro("excel", code, "TestModule")

        assert success == True
        assert "주입됨" in message

        # 주입된 코드 확인
        injected = connector.get_injected_code("excel")
        assert injected is not None
        assert injected["code"] == code
        assert injected["module"] == "TestModule"

    def test_run_macro_excel(self, connector):
        """Excel 매크로 실행 테스트"""
        success, message = connector.run_macro("excel", "TestMacro")
        assert success == True
        assert "실행됨" in message

        # 실행 기록 확인
        history = connector.get_run_history()
        assert len(history) == 1
        assert history[0]["program"] == "excel"
        assert history[0]["macro"] == "TestMacro"

    def test_run_macro_ppt(self, connector):
        """PowerPoint 매크로 실행 테스트 (제한됨)"""
        success, message = connector.run_macro("ppt", "TestMacro")
        assert success == False
        assert "제한" in message

    def test_inject_and_run(self, connector):
        """주입 및 실행 테스트"""
        code = "Sub RunTest()\nEnd Sub"
        success, message = connector.inject_and_run("excel", code, "RunTest")

        assert success == True

        # 주입 확인
        injected = connector.get_injected_code("excel")
        assert injected is not None

        # 실행 기록 확인
        history = connector.get_run_history()
        assert any(h["macro"] == "RunTest" for h in history)

    def test_extract_functions(self, connector):
        """함수 추출 테스트"""
        code = '''
        Sub TestSub()
        End Sub

        Function TestFunc() As String
        End Function

        Private Sub PrivateSub()
        End Sub
        '''

        functions = connector.extract_functions(code)

        assert len(functions) == 3
        assert ("Sub", "TestSub") in functions
        assert ("Function", "TestFunc") in functions
        assert ("Sub", "PrivateSub") in functions

    def test_set_connection_status(self, connector):
        """연결 상태 설정 테스트"""
        connector.set_connection_status("excel", ConnectionStatus.DISCONNECTED)
        status = connector.get_connection_status("excel")
        assert status.status == ConnectionStatus.DISCONNECTED


class TestConnectionInfo:
    """ConnectionInfo 테스트"""

    def test_connected_info(self):
        """연결됨 상태 정보"""
        info = ConnectionInfo(
            status=ConnectionStatus.CONNECTED,
            app_name="Microsoft Excel",
            document_name="Test.xlsx"
        )

        assert info.status == ConnectionStatus.CONNECTED
        assert info.app_name == "Microsoft Excel"
        assert info.document_name == "Test.xlsx"

    def test_disconnected_info(self):
        """연결 안됨 상태 정보"""
        info = ConnectionInfo(
            status=ConnectionStatus.DISCONNECTED,
            error_message="Excel이 실행되지 않음"
        )

        assert info.status == ConnectionStatus.DISCONNECTED
        assert info.error_message == "Excel이 실행되지 않음"


class TestFunctionExtraction:
    """함수 추출 테스트"""

    @pytest.fixture
    def connector(self):
        return MockOfficeConnector()

    def test_simple_sub(self, connector):
        """단순 Sub 추출"""
        code = "Sub MySub()\nEnd Sub"
        functions = connector.extract_functions(code)

        assert len(functions) == 1
        assert functions[0] == ("Sub", "MySub")

    def test_sub_with_params(self, connector):
        """파라미터가 있는 Sub"""
        code = "Sub MySubWithParams(x As Integer, y As String)\nEnd Sub"
        functions = connector.extract_functions(code)

        assert len(functions) == 1
        assert functions[0] == ("Sub", "MySubWithParams")

    def test_function_with_return_type(self, connector):
        """반환 타입이 있는 Function"""
        code = "Function MyFunc(x As Integer) As String\nEnd Function"
        functions = connector.extract_functions(code)

        assert len(functions) == 1
        assert functions[0] == ("Function", "MyFunc")

    def test_multiple_functions(self, connector):
        """여러 함수"""
        code = '''
        Sub First()
        End Sub

        Sub Second()
        End Sub

        Function Third() As Boolean
        End Function
        '''
        functions = connector.extract_functions(code)

        assert len(functions) == 3

    def test_case_insensitive(self, connector):
        """대소문자 구분 없음"""
        code = "SUB UpperCase()\nEND SUB\nsub lowerCase()\nend sub"
        functions = connector.extract_functions(code)

        assert len(functions) == 2

    def test_no_functions(self, connector):
        """함수 없음"""
        code = "' Just a comment\nDim x As Integer"
        functions = connector.extract_functions(code)

        assert len(functions) == 0

    def test_inline_sub(self, connector):
        """인라인 Sub (한 줄)"""
        code = "Sub Quick(): MsgBox 1: End Sub"
        functions = connector.extract_functions(code)

        assert len(functions) == 1

    def test_real_world_code(self, connector):
        """실제 코드 예시"""
        code = '''
Option Explicit

' 실행용 매크로
Sub 실행_비율유지O()
    Call FitAllShapesToBestCell(True)
End Sub

Sub 실행_비율유지X()
    Call FitAllShapesToBestCell(False)
End Sub

Private Function GetEffectiveRange(cell As Range) As Range
    If cell.MergeCells Then
        Set GetEffectiveRange = cell.MergeArea
    Else
        Set GetEffectiveRange = cell
    End If
End Function
        '''
        functions = connector.extract_functions(code)

        assert len(functions) == 3
        names = [f[1] for f in functions]
        assert "실행_비율유지O" in names
        assert "실행_비율유지X" in names
        assert "GetEffectiveRange" in names


class TestOfficeConnectorIntegration:
    """Office Connector 통합 테스트 (Mock 사용)"""

    @pytest.fixture
    def connector(self):
        return MockOfficeConnector()

    def test_workflow_excel(self, connector):
        """Excel 워크플로우 테스트"""
        # 1. 연결 확인
        status = connector.get_connection_status("excel")
        assert status.status == ConnectionStatus.CONNECTED

        # 2. 매크로 주입
        code = '''
Sub 테스트매크로()
    MsgBox "Hello"
End Sub
        '''
        success, _ = connector.inject_macro("excel", code)
        assert success == True

        # 3. 실행
        success, _ = connector.run_macro("excel", "테스트매크로")
        assert success == True

        # 4. 기록 확인
        history = connector.get_run_history()
        assert len(history) >= 1

    def test_workflow_ppt(self, connector):
        """PowerPoint 워크플로우 테스트"""
        # 1. 연결
        connector.connect("ppt")
        status = connector.get_connection_status("ppt")
        assert status.status == ConnectionStatus.CONNECTED

        # 2. 매크로 주입
        code = "Sub PPT매크로()\nEnd Sub"
        success, _ = connector.inject_macro("ppt", code)
        assert success == True

        # 3. 실행 (제한됨)
        success, message = connector.run_macro("ppt", "PPT매크로")
        assert success == False

    def test_error_handling(self, connector):
        """에러 처리 테스트"""
        # 연결 안된 상태
        connector.set_connection_status("word", ConnectionStatus.DISCONNECTED)
        status = connector.get_connection_status("word")
        assert status.status == ConnectionStatus.DISCONNECTED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
