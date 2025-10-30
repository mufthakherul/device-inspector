#!/usr/bin/env python3
# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""
PyInstaller entry point wrapper for inspecta CLI.

This wrapper ensures the agent package is properly imported when
running as a standalone executable built with PyInstaller. It avoids
the "ImportError: attempted relative import with no known parent package"
error that occurs when agent/cli.py is used directly as the entry point.
"""

if __name__ == "__main__":
    from agent.cli import cli
    cli()
