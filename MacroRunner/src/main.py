"""
MacroRunner 메인 엔트리포인트
"""
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.main_window import run_app


def main():
    """메인 함수"""
    # 테스트 모드 플래그
    use_mock = "--mock" in sys.argv or "--test" in sys.argv

    run_app(use_mock=use_mock)


if __name__ == "__main__":
    main()
