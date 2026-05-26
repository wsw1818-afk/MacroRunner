"""
MacroRunner main entry point.
"""
import os
import sys

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.debug_logging import setup_desktop_debug_logging


def main():
    """Run MacroRunner."""
    logger = setup_desktop_debug_logging()
    try:
        from src.ui.main_window import run_app

        test_mode = "--test" in sys.argv
        use_mock = "--mock" in sys.argv or test_mode
        logger.info("Starting app. use_mock=%s", use_mock)

        run_app(use_mock=use_mock, auto_close_ms=1200 if test_mode else None)
        logger.info("App exited normally")
    except Exception:
        logger.exception("Unhandled app error")
        raise


if __name__ == "__main__":
    main()
