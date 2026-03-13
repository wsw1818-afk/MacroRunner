"""
테스트 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """모든 테스트 실행"""
    project_root = Path(__file__).parent.parent

    # pytest 실행
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(project_root / "tests"),
            "-v",
            "--tb=short",
            "-x",  # 첫 실패 시 중단
            "--color=yes"
        ],
        cwd=project_root
    )

    return result.returncode


def run_coverage():
    """커버리지 측정과 함께 테스트 실행"""
    project_root = Path(__file__).parent.parent

    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(project_root / "tests"),
            "-v",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_report"
        ],
        cwd=project_root
    )

    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        sys.exit(run_coverage())
    else:
        sys.exit(run_tests())
