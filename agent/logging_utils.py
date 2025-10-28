# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Structured logging utilities for inspecta agent.

Provides consistent logging with file output and structured formats.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


class InspectaLogger:
    """Structured logger for inspecta operations."""

    def __init__(self, name: str = "inspecta"):
        self.logger = logging.getLogger(name)
        self.log_file: Optional[Path] = None

    def setup(
        self,
        log_file: Optional[Path] = None,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ) -> None:
        """Set up logging with console and optionally file output.

        Args:
            log_file: Path to log file (if None, only console logging)
            console_level: Logging level for console output
            file_level: Logging level for file output
        """
        self.logger.setLevel(logging.DEBUG)
        self.log_file = log_file

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler with simple format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_format = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler with detailed format
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
            file_handler.setLevel(file_level)
            file_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

            self.logger.debug("Logging initialized: %s", log_file)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)

    def log_command_execution(
        self, command: str, returncode: int, duration_ms: int
    ) -> None:
        """Log command execution details.

        Args:
            command: Command that was executed
            returncode: Exit code from the command
            duration_ms: Execution time in milliseconds
        """
        if returncode == 0:
            self.debug(
                "Command succeeded: %s (exit=%d, duration=%dms)",
                command,
                returncode,
                duration_ms,
            )
        else:
            self.warning(
                "Command failed: %s (exit=%d, duration=%dms)",
                command,
                returncode,
                duration_ms,
            )

    def log_test_result(
        self, test_name: str, status: str, details: Optional[str] = None
    ) -> None:
        """Log test execution result.

        Args:
            test_name: Name of the test
            status: Test status (ok, warn, error, fail)
            details: Additional details
        """
        level_map = {
            "ok": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR,
            "fail": logging.ERROR,
        }

        level = level_map.get(status, logging.INFO)
        msg = f"Test {test_name}: {status.upper()}"
        if details:
            msg += f" - {details}"

        self.logger.log(level, msg)


# Global logger instance
_logger = InspectaLogger()


def setup_logging(
    log_file: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> InspectaLogger:
    """Set up global logging configuration.

    Args:
        log_file: Path to log file
        console_level: Console logging level
        file_level: File logging level

    Returns:
        Configured logger instance
    """
    _logger.setup(log_file, console_level, file_level)
    return _logger


def get_logger() -> InspectaLogger:
    """Get the global logger instance."""
    return _logger
