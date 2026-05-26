"""
Temporary desktop debug logging for EXE troubleshooting.
"""
import logging
import os
import platform
import sys
from pathlib import Path

LOG_FILENAME = "MacroRunner_debug.log"


class _LogStream:
    """File-like stream that forwards writes to a logger."""

    def __init__(self, logger: logging.Logger, level: int):
        self._logger = logger
        self._level = level
        self._buffer = ""

    def write(self, message: str):
        if not message:
            return

        self._buffer += message
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self._logger.log(self._level, line.rstrip())

    def flush(self):
        if self._buffer.strip():
            self._logger.log(self._level, self._buffer.rstrip())
        self._buffer = ""


def get_desktop_log_path() -> Path:
    """Return the debug log path on the current user's desktop."""
    known_desktop = _get_windows_known_desktop()
    if known_desktop and known_desktop.exists():
        return known_desktop / LOG_FILENAME

    candidates = [
        Path(os.environ.get("USERPROFILE", "")) / "Desktop",
        Path.home() / "Desktop",
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate / LOG_FILENAME

    return Path.home() / LOG_FILENAME


def _get_windows_known_desktop():
    if os.name != "nt":
        return None

    try:
        import ctypes
        import uuid
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]

            @classmethod
            def from_uuid(cls, value):
                data4 = (wintypes.BYTE * 8).from_buffer_copy(value.bytes[8:])
                return cls(value.time_low, value.time_mid, value.time_hi_version, data4)

        desktop_id = GUID.from_uuid(uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641"))
        path_ptr = wintypes.LPWSTR()
        result = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(desktop_id),
            0,
            None,
            ctypes.byref(path_ptr)
        )
        if result != 0:
            return None

        try:
            return Path(path_ptr.value)
        finally:
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
    except Exception:
        return None


def setup_desktop_debug_logging() -> logging.Logger:
    """Configure append-only debug logging on the desktop."""
    log_path = get_desktop_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("MacroRunner")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(handler)

    sys.stdout = _LogStream(logger, logging.INFO)
    sys.stderr = _LogStream(logger, logging.ERROR)

    logger.info("=" * 72)
    logger.info("MacroRunner debug logging started")
    logger.info("Log file: %s", log_path)
    logger.info("Executable: %s", sys.executable)
    logger.info("Frozen: %s", getattr(sys, "frozen", False))
    logger.info("Python: %s", sys.version.replace("\n", " "))
    logger.info("Platform: %s", platform.platform())
    logger.info("CWD: %s", os.getcwd())
    logger.info("Args: %s", sys.argv)
    _log_app_context(logger)

    return logger


def _log_app_context(logger: logging.Logger):
    try:
        from src.utils.constants import (
            APP_VERSION,
            APP_BUILD,
            APP_DIR,
            PACKAGE_DIR,
            PACKAGE_MACROS_DIR,
            USER_DATA_DIR,
            MACRO_INDEX_FILE,
        )

        logger.info("App version: %s", APP_VERSION)
        logger.info("App build: %s", APP_BUILD)
        logger.info("App dir: %s", APP_DIR)
        logger.info("Package dir: %s", PACKAGE_DIR)
        logger.info("Package macros dir: %s exists=%s", PACKAGE_MACROS_DIR, PACKAGE_MACROS_DIR.exists())
        logger.info("User data dir: %s", USER_DATA_DIR)
        logger.info("User macro index: %s exists=%s", MACRO_INDEX_FILE, MACRO_INDEX_FILE.exists())
    except Exception:
        logger.exception("Failed to log app context")
