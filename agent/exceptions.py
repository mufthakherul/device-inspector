# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Custom exceptions for the inspecta agent.

Provides clear, actionable exception classes for common error scenarios.
"""
from __future__ import annotations


class InspectaError(Exception):
    """Base exception for all inspecta errors."""


class ToolNotFoundError(InspectaError):
    """Raised when a required system tool is not found.

    Attributes:
        tool_name: Name of the missing tool
        install_command: Suggested installation command
    """

    def __init__(self, tool_name: str, install_command: str = ""):
        self.tool_name = tool_name
        self.install_command = install_command

        message = f"{tool_name} not found."
        if install_command:
            message += f" Install with: {install_command}"

        super().__init__(message)


class PermissionError(InspectaError):
    """Raised when operation requires elevated privileges.

    Attributes:
        operation: Description of the operation that failed
        suggestion: Suggested command to run with proper privileges
    """

    def __init__(self, operation: str, suggestion: str = ""):
        self.operation = operation
        self.suggestion = suggestion

        message = f"Permission denied for: {operation}"
        if suggestion:
            message += f"\nTry running with: {suggestion}"

        super().__init__(message)


class DeviceError(InspectaError):
    """Raised when device detection or access fails.

    Attributes:
        device: Device identifier that caused the error
        reason: Human-readable reason for the failure
    """

    def __init__(self, device: str, reason: str):
        self.device = device
        self.reason = reason
        super().__init__(f"Device error for {device}: {reason}")


class ParseError(InspectaError):
    """Raised when parsing tool output fails.

    Attributes:
        tool_name: Name of the tool whose output failed to parse
        details: Additional error details
    """

    def __init__(self, tool_name: str, details: str = ""):
        self.tool_name = tool_name
        self.details = details

        message = f"Failed to parse {tool_name} output"
        if details:
            message += f": {details}"

        super().__init__(message)


class TimeoutError(InspectaError):
    """Raised when an operation times out.

    Attributes:
        operation: Description of the operation that timed out
        timeout_seconds: Number of seconds before timeout
    """

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{operation} timed out after {timeout_seconds} seconds")
