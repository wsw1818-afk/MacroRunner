"""
Office COM 연동 모듈
Excel, PowerPoint, Word에 매크로 주입 및 실행
"""
import threading
import time
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import re

try:
    import win32com.client
    import pythoncom
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False


class ConnectionStatus(Enum):
    """연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """연결 정보"""
    status: ConnectionStatus
    app_name: str = ""
    document_name: str = ""
    error_message: str = ""


class OfficeConnector:
    """Office 애플리케이션 연결 및 매크로 주입"""

    def __init__(self):
        self._excel_app = None
        self._ppt_app = None
        self._word_app = None

        self._connection_status = {
            "excel": ConnectionInfo(ConnectionStatus.DISCONNECTED),
            "ppt": ConnectionInfo(ConnectionStatus.DISCONNECTED),
            "word": ConnectionInfo(ConnectionStatus.DISCONNECTED)
        }

        # 선택된 문서 인덱스 (1부터 시작, None이면 활성 문서 사용)
        self._selected_document_index = {
            "excel": None,
            "ppt": None,
            "word": None
        }

        self._status_callbacks: List[Callable] = []
        self._check_interval = 3  # 연결 상태 확인 주기 (초)
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False

    def start_monitoring(self):
        """연결 상태 모니터링 시작"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """모니터링 중지"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def _monitor_loop(self):
        """연결 상태 주기적 확인"""
        pythoncom.CoInitialize()
        try:
            while self._running:
                self._check_connections()
                time.sleep(self._check_interval)
        finally:
            pythoncom.CoUninitialize()

    def _check_connections(self):
        """모든 Office 앱 연결 상태 확인"""
        for program in ["excel", "ppt", "word"]:
            old_status = self._connection_status[program].status
            self._update_connection_status(program)
            new_status = self._connection_status[program].status

            if old_status != new_status:
                self._notify_status_change(program)

    def _update_connection_status(self, program: str):
        """특정 프로그램 연결 상태 업데이트"""
        if not HAS_WIN32COM:
            self._connection_status[program] = ConnectionInfo(
                ConnectionStatus.ERROR,
                error_message="pywin32 모듈이 설치되지 않았습니다."
            )
            return

        try:
            if program == "excel":
                app = win32com.client.GetActiveObject("Excel.Application")
                # 여러 인스턴스 정보 수집
                doc_count = app.Workbooks.Count
                doc_name = app.ActiveWorkbook.Name if app.ActiveWorkbook else "문서 없음"
                if doc_count > 1:
                    doc_name = f"{doc_name} (외 {doc_count - 1}개)"
                self._excel_app = app
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft Excel",
                    document_name=doc_name
                )

            elif program == "ppt":
                app = win32com.client.GetActiveObject("PowerPoint.Application")
                doc_count = app.Presentations.Count
                doc_name = app.ActivePresentation.Name if doc_count > 0 else "문서 없음"
                if doc_count > 1:
                    doc_name = f"{doc_name} (외 {doc_count - 1}개)"
                self._ppt_app = app
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft PowerPoint",
                    document_name=doc_name
                )

            elif program == "word":
                app = win32com.client.GetActiveObject("Word.Application")
                doc_count = app.Documents.Count
                doc_name = app.ActiveDocument.Name if doc_count > 0 else "문서 없음"
                if doc_count > 1:
                    doc_name = f"{doc_name} (외 {doc_count - 1}개)"
                self._word_app = app
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft Word",
                    document_name=doc_name
                )

        except Exception:
            self._connection_status[program] = ConnectionInfo(
                ConnectionStatus.DISCONNECTED,
                error_message=f"{program.upper()} 실행 중이 아닙니다."
            )

            # 캐시된 앱 객체 초기화
            if program == "excel":
                self._excel_app = None
            elif program == "ppt":
                self._ppt_app = None
            elif program == "word":
                self._word_app = None

    def get_connection_status(self, program: str) -> ConnectionInfo:
        """연결 상태 반환"""
        return self._connection_status.get(program, ConnectionInfo(ConnectionStatus.DISCONNECTED))

    def on_status_change(self, callback: Callable):
        """상태 변경 콜백 등록"""
        self._status_callbacks.append(callback)

    def _notify_status_change(self, program: str):
        """상태 변경 알림"""
        info = self._connection_status[program]
        for callback in self._status_callbacks:
            try:
                callback(program, info)
            except Exception:
                pass

    def connect(self, program: str) -> Tuple[bool, str]:
        """Office 앱에 연결 시도"""
        if not HAS_WIN32COM:
            return False, "pywin32 모듈이 설치되지 않았습니다."

        self._connection_status[program] = ConnectionInfo(ConnectionStatus.CONNECTING)
        self._notify_status_change(program)

        try:
            pythoncom.CoInitialize()

            if program == "excel":
                self._excel_app = win32com.client.GetActiveObject("Excel.Application")
                doc_name = self._excel_app.ActiveWorkbook.Name if self._excel_app.ActiveWorkbook else ""
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft Excel",
                    document_name=doc_name
                )

            elif program == "ppt":
                self._ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")
                doc_name = self._ppt_app.ActivePresentation.Name if self._ppt_app.Presentations.Count > 0 else ""
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft PowerPoint",
                    document_name=doc_name
                )

            elif program == "word":
                self._word_app = win32com.client.GetActiveObject("Word.Application")
                doc_name = self._word_app.ActiveDocument.Name if self._word_app.Documents.Count > 0 else ""
                self._connection_status[program] = ConnectionInfo(
                    ConnectionStatus.CONNECTED,
                    app_name="Microsoft Word",
                    document_name=doc_name
                )

            self._notify_status_change(program)
            return True, f"{program.upper()} 연결됨"

        except Exception as e:
            self._connection_status[program] = ConnectionInfo(
                ConnectionStatus.ERROR,
                error_message=str(e)
            )
            self._notify_status_change(program)
            return False, f"연결 실패: {e}"

    def inject_macro(self, program: str, code: str, module_name: str = "MacroRunner") -> Tuple[bool, str]:
        """매크로 코드 주입"""
        if not HAS_WIN32COM:
            return False, "pywin32 모듈이 설치되지 않았습니다."

        try:
            pythoncom.CoInitialize()

            if program == "excel":
                return self._inject_excel_macro(code, module_name)
            elif program == "ppt":
                return self._inject_ppt_macro(code, module_name)
            elif program == "word":
                return self._inject_word_macro(code, module_name)
            else:
                return False, f"지원하지 않는 프로그램: {program}"

        except Exception as e:
            return False, f"주입 실패: {e}"

    def _inject_excel_macro(self, code: str, module_name: str) -> Tuple[bool, str]:
        """Excel에 매크로 주입 (선택된 문서에 주입)"""
        try:
            # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
            excel_app = win32com.client.GetActiveObject("Excel.Application")

            # 선택된 문서 인덱스가 있으면 해당 문서 사용, 없으면 활성 문서
            doc_index = self._selected_document_index.get("excel")
            if doc_index and doc_index <= excel_app.Workbooks.Count:
                wb = excel_app.Workbooks(doc_index)
            else:
                wb = excel_app.ActiveWorkbook

            if not wb:
                return False, "활성 워크북이 없습니다."

            vb_project = wb.VBProject

            # 기존 모듈 제거
            for component in vb_project.VBComponents:
                if component.Name == module_name:
                    vb_project.VBComponents.Remove(component)
                    break

            # 새 모듈 추가
            new_module = vb_project.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
            new_module.Name = module_name
            new_module.CodeModule.AddFromString(code)

            return True, f"'{wb.Name}'에 '{module_name}' 모듈 주입 완료"

        except Exception as e:
            error_msg = str(e)
            if "programmatic access" in error_msg.lower() or "액세스" in error_msg:
                return False, ("VBA 프로젝트 접근이 차단되었습니다.\n"
                              "파일 → 옵션 → 보안 센터 → 보안 센터 설정 → 매크로 설정 →\n"
                              "'VBA 프로젝트 개체 모델에 대한 액세스 신뢰' 체크 필요")
            return False, f"Excel 주입 실패: {e}"

    def _inject_ppt_macro(self, code: str, module_name: str) -> Tuple[bool, str]:
        """PowerPoint에 매크로 주입 (선택된 문서에 주입)"""
        try:
            # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
            ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")

            if ppt_app.Presentations.Count == 0:
                return False, "활성 프레젠테이션이 없습니다."

            # 선택된 문서 인덱스가 있으면 해당 문서 사용, 없으면 활성 문서
            doc_index = self._selected_document_index.get("ppt")
            if doc_index and doc_index <= ppt_app.Presentations.Count:
                presentation = ppt_app.Presentations(doc_index)
            else:
                presentation = ppt_app.ActivePresentation

            vb_project = presentation.VBProject

            # 기존 모듈 제거
            for component in vb_project.VBComponents:
                if component.Name == module_name:
                    vb_project.VBComponents.Remove(component)
                    break

            # 새 모듈 추가
            new_module = vb_project.VBComponents.Add(1)
            new_module.Name = module_name
            new_module.CodeModule.AddFromString(code)

            return True, f"'{presentation.Name}'에 '{module_name}' 모듈 주입 완료"

        except Exception as e:
            error_msg = str(e)
            if "programmatic access" in error_msg.lower() or "액세스" in error_msg:
                return False, ("VBA 프로젝트 접근이 차단되었습니다.\n"
                              "파일 → 옵션 → 보안 센터 → 보안 센터 설정 → 매크로 설정 →\n"
                              "'VBA 프로젝트 개체 모델에 대한 액세스 신뢰' 체크 필요")
            return False, f"PowerPoint 주입 실패: {e}"

    def _inject_word_macro(self, code: str, module_name: str) -> Tuple[bool, str]:
        """Word에 매크로 주입 (선택된 문서에 주입)"""
        try:
            # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
            word_app = win32com.client.GetActiveObject("Word.Application")

            if word_app.Documents.Count == 0:
                return False, "활성 문서가 없습니다."

            # 선택된 문서 인덱스가 있으면 해당 문서 사용, 없으면 활성 문서
            doc_index = self._selected_document_index.get("word")
            if doc_index and doc_index <= word_app.Documents.Count:
                doc = word_app.Documents(doc_index)
            else:
                doc = word_app.ActiveDocument

            vb_project = doc.VBProject

            # 기존 모듈 제거
            for component in vb_project.VBComponents:
                if component.Name == module_name:
                    vb_project.VBComponents.Remove(component)
                    break

            # 새 모듈 추가
            new_module = vb_project.VBComponents.Add(1)
            new_module.Name = module_name
            new_module.CodeModule.AddFromString(code)

            return True, f"'{doc.Name}'에 '{module_name}' 모듈 주입 완료"

        except Exception as e:
            error_msg = str(e)
            if "programmatic access" in error_msg.lower() or "액세스" in error_msg:
                return False, ("VBA 프로젝트 접근이 차단되었습니다.\n"
                              "파일 → 옵션 → 보안 센터 → 보안 센터 설정 → 매크로 설정 →\n"
                              "'VBA 프로젝트 개체 모델에 대한 액세스 신뢰' 체크 필요")
            return False, f"Word 주입 실패: {e}"

    def run_macro(self, program: str, macro_name: str, module_name: str = "MacroRunner") -> Tuple[bool, str]:
        """매크로 실행 (선택된 문서에서 실행)"""
        if not HAS_WIN32COM:
            return False, "pywin32 모듈이 설치되지 않았습니다."

        try:
            pythoncom.CoInitialize()

            if program == "excel":
                # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
                excel_app = win32com.client.GetActiveObject("Excel.Application")

                # 선택된 문서 인덱스가 있으면 해당 문서 활성화
                doc_index = self._selected_document_index.get("excel")
                if doc_index and doc_index <= excel_app.Workbooks.Count:
                    wb = excel_app.Workbooks(doc_index)
                    wb.Activate()

                excel_app.Run(macro_name)
                return True, f"Excel 매크로 '{macro_name}' 실행 완료"

            elif program == "ppt":
                # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
                ppt_app = win32com.client.GetActiveObject("PowerPoint.Application")

                if ppt_app.Presentations.Count == 0:
                    return False, "활성 프레젠테이션이 없습니다."

                # 선택된 문서 인덱스가 있으면 해당 문서 활성화
                doc_index = self._selected_document_index.get("ppt")
                if doc_index and doc_index <= ppt_app.Presentations.Count:
                    pres = ppt_app.Presentations(doc_index)
                    if pres.Windows.Count > 0:
                        pres.Windows(1).Activate()
                else:
                    pres = ppt_app.ActivePresentation

                pres_name = pres.Name

                # 확장자 제거한 이름
                pres_name_no_ext = pres_name.rsplit('.', 1)[0] if '.' in pres_name else pres_name

                # 시도할 매크로 경로들
                macro_paths = [
                    f"{pres_name}!{module_name}.{macro_name}",      # 전체 이름
                    f"{pres_name_no_ext}!{module_name}.{macro_name}",  # 확장자 제거
                    f"{module_name}.{macro_name}",                  # 모듈.매크로만
                    macro_name                                       # 매크로 이름만
                ]

                last_error = None
                for path in macro_paths:
                    try:
                        ppt_app.Run(path)
                        return True, f"PowerPoint 매크로 '{macro_name}' 실행 완료"
                    except Exception as e:
                        last_error = e
                        continue

                return False, f"매크로 실행 실패 (모든 경로 시도): {last_error}"

            elif program == "word":
                # 매번 새로운 COM 객체 생성 (스레딩 오류 방지)
                word_app = win32com.client.GetActiveObject("Word.Application")

                # 선택된 문서 인덱스가 있으면 해당 문서 활성화
                doc_index = self._selected_document_index.get("word")
                if doc_index and doc_index <= word_app.Documents.Count:
                    doc = word_app.Documents(doc_index)
                    doc.Activate()

                word_app.Run(macro_name)
                return True, f"Word 매크로 '{macro_name}' 실행 완료"

            else:
                return False, f"지원하지 않는 프로그램: {program}"

        except Exception as e:
            return False, f"매크로 실행 실패: {e}"

    def inject_and_run(self, program: str, code: str, function_name: str,
                       module_name: str = "MacroRunner") -> Tuple[bool, str]:
        """매크로 주입 후 실행"""
        import time

        # PPT의 경우 Python으로 직접 실행 (VBA 주입 없이)
        if program == "ppt":
            return self._run_ppt_macro_direct(function_name)

        # 주입
        success, message = self.inject_macro(program, code, module_name)
        if not success:
            return False, message

        # 주입 후 VBA 컴파일 대기
        time.sleep(0.5)

        # 실행 (모듈 이름 전달)
        return self.run_macro(program, function_name, module_name)

    def _run_ppt_macro_direct(self, function_name: str) -> Tuple[bool, str]:
        """PPT 매크로를 Python으로 직접 실행"""
        try:
            from .ppt_macro_executor import ppt_executor
            import tkinter.simpledialog as sd
            import tkinter.messagebox as mb

            func_lower = function_name.lower()
            doc_index = self._selected_document_index.get("ppt")

            # 압축 전용 함수 처리 (이미지 배치 없이 안내만 표시)
            is_compress_only = (
                "압축만" in func_lower or
                func_lower in ("전체이미지압축", "현재슬라이드압축") or
                ("압축" in func_lower and "비율" not in func_lower and "여백" not in func_lower)
            )
            if is_compress_only:
                mb.showinfo(
                    "이미지 압축 안내",
                    "추가 용량 절감을 위해:\n"
                    "1. 파일 > 다른 이름으로 저장\n"
                    "2. 도구 > 그림 압축 선택\n"
                    "3. 원하는 해상도 선택 (권장: 웹 150ppi)"
                )
                return True, "이미지 압축 안내 표시됨"

            # 배치 모드 결정
            if "비율무시" in func_lower:
                mode = 1
            elif "비율유지" in func_lower:
                mode = 2
            elif "여백" in func_lower:
                mode = 3
            else:
                mode = 2

            # 여백맞춤(mode=3)일 때 margin 입력받기
            margin = 0.0
            if mode == 3:
                val = sd.askfloat(
                    "여백 입력",
                    "테두리 안 여백(포인트)을 입력하세요.\n가로/세로 동일 수치로 적용됩니다.\n예: 10",
                    initialvalue=10.0,
                    minvalue=0.0
                )
                if val is None:
                    return False, "취소됨"
                margin = val

            result = ppt_executor.execute_image_placement(mode=mode, margin=margin, doc_index=doc_index)

            # 배치+압축 함수인 경우 압축 안내 추가
            if result[0] and "압축" in func_lower:
                mb.showinfo(
                    "이미지 압축 안내",
                    "배치 완료!\n\n추가 용량 절감을 위해:\n"
                    "1. 파일 > 다른 이름으로 저장\n"
                    "2. 도구 > 그림 압축 선택\n"
                    "3. 원하는 해상도 선택 (권장: 웹 150ppi)"
                )
            return result

        except Exception as e:
            return False, f"PPT 직접 실행 실패: {e}"

    def extract_functions(self, code: str) -> List[Tuple[str, str]]:
        """코드에서 Public Sub/Function 추출 (Private 제외)"""
        functions = []

        # Sub 찾기 (Private 제외)
        for match in re.finditer(r'^[ \t]*((Private|Public|Friend)\s+)?Sub\s+(\w+)\s*\(', code, re.IGNORECASE | re.MULTILINE):
            if match.group(2) and match.group(2).lower() == 'private':
                continue
            functions.append(("Sub", match.group(3)))

        # Function 찾기 (Private 제외)
        for match in re.finditer(r'^[ \t]*((Private|Public|Friend)\s+)?Function\s+(\w+)\s*\(', code, re.IGNORECASE | re.MULTILINE):
            if match.group(2) and match.group(2).lower() == 'private':
                continue
            functions.append(("Function", match.group(3)))

        return functions

    def get_open_documents(self, program: str) -> List[Tuple[int, str]]:
        """열려 있는 모든 문서 목록 반환 (인덱스, 이름)"""
        if not HAS_WIN32COM:
            return []

        try:
            pythoncom.CoInitialize()
            documents = []

            if program == "excel":
                app = win32com.client.GetActiveObject("Excel.Application")
                for i in range(1, app.Workbooks.Count + 1):
                    wb = app.Workbooks(i)
                    documents.append((i, wb.Name))

            elif program == "ppt":
                app = win32com.client.GetActiveObject("PowerPoint.Application")
                for i in range(1, app.Presentations.Count + 1):
                    pres = app.Presentations(i)
                    documents.append((i, pres.Name))

            elif program == "word":
                app = win32com.client.GetActiveObject("Word.Application")
                for i in range(1, app.Documents.Count + 1):
                    doc = app.Documents(i)
                    documents.append((i, doc.Name))

            return documents

        except Exception:
            return []

    def activate_document(self, program: str, index: int) -> Tuple[bool, str]:
        """특정 문서를 활성화하고 선택 상태 저장"""
        if not HAS_WIN32COM:
            return False, "pywin32 모듈이 설치되지 않았습니다."

        try:
            pythoncom.CoInitialize()

            # 선택한 문서 인덱스 저장
            self._selected_document_index[program] = index

            if program == "excel":
                app = win32com.client.GetActiveObject("Excel.Application")
                wb = app.Workbooks(index)
                wb.Activate()
                return True, f"'{wb.Name}' 활성화됨"

            elif program == "ppt":
                app = win32com.client.GetActiveObject("PowerPoint.Application")
                pres = app.Presentations(index)
                # PPT는 윈도우를 활성화해야 함
                if pres.Windows.Count > 0:
                    pres.Windows(1).Activate()
                return True, f"'{pres.Name}' 활성화됨"

            elif program == "word":
                app = win32com.client.GetActiveObject("Word.Application")
                doc = app.Documents(index)
                doc.Activate()
                return True, f"'{doc.Name}' 활성화됨"

            return False, "지원하지 않는 프로그램"

        except Exception as e:
            return False, f"문서 활성화 실패: {e}"

    def cleanup(self):
        """리소스 정리"""
        self.stop_monitoring()
        self._excel_app = None
        self._ppt_app = None
        self._word_app = None


# Mock 클래스 (테스트용)
class MockOfficeConnector:
    """테스트용 Mock Office Connector"""

    def __init__(self):
        self._connection_status = {
            "excel": ConnectionInfo(ConnectionStatus.CONNECTED, "Excel", "TestBook.xlsx"),
            "ppt": ConnectionInfo(ConnectionStatus.CONNECTED, "PowerPoint", "TestPPT.pptx"),
            "word": ConnectionInfo(ConnectionStatus.DISCONNECTED)
        }
        self._injected_code = {}
        self._run_history = []

    def start_monitoring(self):
        pass

    def stop_monitoring(self):
        pass

    def get_connection_status(self, program: str) -> ConnectionInfo:
        return self._connection_status.get(program, ConnectionInfo(ConnectionStatus.DISCONNECTED))

    def on_status_change(self, callback: Callable):
        pass

    def connect(self, program: str) -> Tuple[bool, str]:
        self._connection_status[program] = ConnectionInfo(
            ConnectionStatus.CONNECTED,
            app_name=f"Mock {program.upper()}",
            document_name="MockDocument"
        )
        return True, f"{program} 연결됨 (Mock)"

    def inject_macro(self, program: str, code: str, module_name: str = "MacroRunner") -> Tuple[bool, str]:
        self._injected_code[program] = {"code": code, "module": module_name}
        return True, f"Mock: {module_name} 주입됨"

    def run_macro(self, program: str, macro_name: str) -> Tuple[bool, str]:
        self._run_history.append({"program": program, "macro": macro_name})
        if program == "ppt":
            return False, "PowerPoint는 자동 실행이 제한됩니다."
        return True, f"Mock: {macro_name} 실행됨"

    def inject_and_run(self, program: str, code: str, function_name: str,
                       module_name: str = "MacroRunner") -> Tuple[bool, str]:
        self.inject_macro(program, code, module_name)
        return self.run_macro(program, function_name)

    def extract_functions(self, code: str) -> List[Tuple[str, str]]:
        functions = []
        for match in re.finditer(r'\bSub\s+(\w+)\s*\(', code, re.IGNORECASE):
            functions.append(("Sub", match.group(1)))
        for match in re.finditer(r'\bFunction\s+(\w+)\s*\(', code, re.IGNORECASE):
            functions.append(("Function", match.group(1)))
        return functions

    def cleanup(self):
        pass

    # 테스트용 메서드
    def get_injected_code(self, program: str) -> Optional[dict]:
        return self._injected_code.get(program)

    def get_run_history(self) -> List[dict]:
        return self._run_history

    def set_connection_status(self, program: str, status: ConnectionStatus):
        self._connection_status[program] = ConnectionInfo(status)
