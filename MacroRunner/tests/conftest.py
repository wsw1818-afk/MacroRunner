"""
Pytest 설정 및 공통 픽스처
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """프로젝트 루트 경로"""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_project_dir():
    """임시 프로젝트 디렉토리"""
    temp = tempfile.mkdtemp(prefix="macrorunner_test_")
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_vba_code():
    """샘플 VBA 코드"""
    return '''
Option Explicit

Sub 테스트매크로()
    MsgBox "Hello, World!"
End Sub

Function 더하기(a As Integer, b As Integer) As Integer
    더하기 = a + b
End Function
    '''


@pytest.fixture
def sample_macro_data():
    """샘플 매크로 데이터"""
    return {
        "name": "테스트매크로",
        "code": "Sub Test()\nEnd Sub",
        "program": "excel",
        "description": "테스트용 매크로",
        "category": "일반",
        "favorite": False,
        "use_count": 0
    }


@pytest.fixture
def mock_office_connector():
    """Mock Office Connector"""
    from src.core.office_connector import MockOfficeConnector
    return MockOfficeConnector()


# 헤드리스 환경 감지
def pytest_configure(config):
    """pytest 설정"""
    import os

    # CI 환경에서는 GUI 테스트 스킵
    if os.environ.get("CI") or os.environ.get("HEADLESS"):
        config.addinivalue_line(
            "markers", "gui: mark test as requiring GUI"
        )


def pytest_collection_modifyitems(config, items):
    """GUI 테스트 조건부 스킵"""
    import os

    if os.environ.get("CI") or os.environ.get("HEADLESS"):
        skip_gui = pytest.mark.skip(reason="GUI not available in headless mode")
        for item in items:
            if "gui" in item.keywords:
                item.add_marker(skip_gui)
