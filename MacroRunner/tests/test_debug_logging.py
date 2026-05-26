"""
Debug logging tests.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import debug_logging


def test_desktop_log_path_uses_userprofile_desktop(tmp_path, monkeypatch):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    monkeypatch.setattr(debug_logging, "_get_windows_known_desktop", lambda: None)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    assert debug_logging.get_desktop_log_path() == desktop / "MacroRunner_debug.log"


def test_setup_desktop_debug_logging_writes_file(tmp_path, monkeypatch):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    monkeypatch.setattr(debug_logging, "_get_windows_known_desktop", lambda: None)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    logger = logging.getLogger("MacroRunner")

    try:
        logger = debug_logging.setup_desktop_debug_logging()
        logger.info("direct log")
        sys.stdout.write("stdout log\n")
        sys.stderr.write("stderr log\n")

        for handler in logger.handlers:
            handler.flush()

        log_text = (desktop / "MacroRunner_debug.log").read_text(encoding="utf-8")
        assert "MacroRunner debug logging started" in log_text
        assert "App build:" in log_text
        assert "direct log" in log_text
        assert "stdout log" in log_text
        assert "stderr log" in log_text
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
