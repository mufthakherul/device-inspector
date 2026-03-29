# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Linux distribution capability and tooling helpers.

Sprint 5 utilities:
- detect distro/package-manager from /etc/os-release
- generate distro-aware install hints for probe tools
- provide consistent permission diagnostics for root-required probes
"""

from __future__ import annotations

import os
import platform
from typing import Dict, Optional

_PKG_MANAGER_INSTALL_CMD = {
    "apt": "sudo apt install",
    "dnf": "sudo dnf install",
    "yum": "sudo yum install",
    "pacman": "sudo pacman -S",
    "zypper": "sudo zypper install",
    "apk": "sudo apk add",
}


_TOOL_PACKAGE_MAP = {
    "dmidecode": {
        "apt": "dmidecode",
        "dnf": "dmidecode",
        "yum": "dmidecode",
        "pacman": "dmidecode",
        "zypper": "dmidecode",
        "apk": "dmidecode",
    },
    "upower": {
        "apt": "upower",
        "dnf": "upower",
        "yum": "upower",
        "pacman": "upower",
        "zypper": "upower",
        "apk": "upower",
    },
    "sysbench": {
        "apt": "sysbench",
        "dnf": "sysbench",
        "yum": "sysbench",
        "pacman": "sysbench",
        "zypper": "sysbench",
        "apk": "sysbench",
    },
    "fio": {
        "apt": "fio",
        "dnf": "fio",
        "yum": "fio",
        "pacman": "fio",
        "zypper": "fio",
        "apk": "fio",
    },
    "memtester": {
        "apt": "memtester",
        "dnf": "memtester",
        "yum": "memtester",
        "pacman": "memtester",
        "zypper": "memtester",
        "apk": "memtester",
    },
    "smartctl": {
        "apt": "smartmontools",
        "dnf": "smartmontools",
        "yum": "smartmontools",
        "pacman": "smartmontools",
        "zypper": "smartmontools",
        "apk": "smartmontools",
    },
    "sensors": {
        "apt": "lm-sensors",
        "dnf": "lm_sensors",
        "yum": "lm_sensors",
        "pacman": "lm_sensors",
        "zypper": "sensors",
        "apk": "lm-sensors",
    },
}


def parse_os_release(text: str) -> Dict[str, str]:
    """Parse /etc/os-release style key=value lines."""
    parsed: Dict[str, str] = {}
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip().strip('"').strip("'")
        parsed[key] = value
    return parsed


def _detect_package_manager(distro_id: str, distro_like: str) -> str:
    joined = f"{(distro_id or '').lower()} {(distro_like or '').lower()}"

    if any(token in joined for token in ("debian", "ubuntu", "mint", "pop")):
        return "apt"
    if any(
        token in joined
        for token in (
            "rhel",
            "fedora",
            "centos",
            "rocky",
            "almalinux",
            "ol",
            "amzn",
        )
    ):
        return "dnf"
    if any(token in joined for token in ("arch", "manjaro", "endeavouros")):
        return "pacman"
    if any(token in joined for token in ("suse", "opensuse", "sles")):
        return "zypper"
    if "alpine" in joined:
        return "apk"
    return "unknown"


def detect_linux_capabilities(os_release_text: Optional[str] = None) -> Dict[str, str]:
    """Detect Linux distro metadata and package manager capabilities."""
    if platform.system().lower() != "linux":
        return {
            "platform": platform.system().lower(),
            "id": "",
            "id_like": "",
            "name": "",
            "version_id": "",
            "package_manager": "unknown",
        }

    if os_release_text is None:
        try:
            with open("/etc/os-release", "r", encoding="utf-8") as fh:
                os_release_text = fh.read()
        except OSError:
            os_release_text = ""

    parsed = parse_os_release(os_release_text)
    distro_id = parsed.get("ID", "").lower()
    distro_like = parsed.get("ID_LIKE", "").lower()
    package_manager = _detect_package_manager(distro_id, distro_like)

    return {
        "platform": "linux",
        "id": distro_id,
        "id_like": distro_like,
        "name": parsed.get("PRETTY_NAME") or parsed.get("NAME", ""),
        "version_id": parsed.get("VERSION_ID", ""),
        "package_manager": package_manager,
    }


def tool_install_hint(tool_name: str, os_release_text: Optional[str] = None) -> str:
    """Build distro-aware installation hint for a tool."""
    capabilities = detect_linux_capabilities(os_release_text=os_release_text)
    manager = capabilities.get("package_manager", "unknown")
    pkg = _TOOL_PACKAGE_MAP.get(tool_name, {}).get(manager, tool_name)

    install_cmd = _PKG_MANAGER_INSTALL_CMD.get(manager)
    if install_cmd:
        return f"Install with: {install_cmd} {pkg}"

    return f"Install '{pkg}' using your Linux distribution package manager"


def is_root_user() -> bool:
    """Return True when current process has root privileges."""
    geteuid = getattr(os, "geteuid", None)
    if callable(geteuid):
        return geteuid() == 0
    return False


def root_permission_hint(tool_name: str) -> str:
    """Return a standardized root/sudo diagnostic message."""
    return (
        f"{tool_name} requires root/sudo privileges. "
        "Re-run with sudo or grant required capabilities."
    )
