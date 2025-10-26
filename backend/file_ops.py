"""
File operations module for PRISM
Provides read, write, append, create, and open operations on Windows.
"""

import os
import io
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class FileOps:
    """Safe-ish file operations for local system."""

    def __init__(self):
        self.home = Path.home()

    def handle(self, operation: str, path: str, content: str | None = None) -> Tuple[bool, str]:
        op = (operation or "").lower().strip()
        if not path and op != "open":
            return False, "No file path provided."
        try:
            if op == "read":
                return self._read(path)
            if op == "write":
                return self._write(path, content or "")
            if op == "append":
                return self._append(path, content or "")
            if op == "create":
                return self._create(path, content or "")
            if op == "open":
                return self._open(path)
            return False, f"Unsupported operation: {operation}"
        except Exception as e:
            logger.error(f"File op error ({operation} {path}): {e}")
            return False, f"File operation failed: {e}"

    def _read(self, path: str) -> Tuple[bool, str]:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return False, "File not found."
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                data = f.read()
            preview = data[:1000]
            suffix = "" if len(data) <= 1000 else "\n... (truncated)"
            return True, f"Read {len(data)} chars from {p}:\n{preview}{suffix}"
        except Exception as e:
            return False, f"Failed to read file: {e}"

    def _write(self, path: str, content: str) -> Tuple[bool, str]:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Wrote {len(content)} chars to {p}"

    def _append(self, path: str, content: str) -> Tuple[bool, str]:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return True, f"Appended {len(content)} chars to {p}"

    def _create(self, path: str, content: str) -> Tuple[bool, str]:
        p = Path(path)
        if p.exists():
            return False, f"File already exists: {p}"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Created file {p} ({len(content)} chars)"

    def _open(self, path: str) -> Tuple[bool, str]:
        try:
            if not path:
                # Open home folder by default
                os.startfile(str(self.home))
                return True, f"Opened {self.home}"
            p = Path(path)
            os.startfile(str(p))
            return True, f"Opened {p}"
        except Exception as e:
            return False, f"Failed to open: {e}"
