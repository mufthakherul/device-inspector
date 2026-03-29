# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Tests for Linux distro capability and tool resolver helpers."""

from __future__ import annotations

from unittest.mock import mock_open, patch

from agent.plugins import linux_env


def test_parse_os_release_basic():
    text = (
        'ID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu 24.04 LTS"\n'
        'VERSION_ID="24.04"\n'
    )
    parsed = linux_env.parse_os_release(text)

    assert parsed["ID"] == "ubuntu"
    assert parsed["ID_LIKE"] == "debian"
    assert parsed["PRETTY_NAME"] == "Ubuntu 24.04 LTS"


@patch("agent.plugins.linux_env.platform.system", return_value="Linux")
def test_detect_linux_capabilities_apt(_mock_platform):
    text = 'ID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu 24.04 LTS"\n'
    caps = linux_env.detect_linux_capabilities(text)

    assert caps["id"] == "ubuntu"
    assert caps["package_manager"] == "apt"


@patch("agent.plugins.linux_env.platform.system", return_value="Linux")
def test_detect_linux_capabilities_dnf(_mock_platform):
    text = 'ID=fedora\nID_LIKE="rhel fedora"\nPRETTY_NAME="Fedora Linux 40"\n'
    caps = linux_env.detect_linux_capabilities(text)

    assert caps["id"] == "fedora"
    assert caps["package_manager"] == "dnf"


@patch("agent.plugins.linux_env.platform.system", return_value="Linux")
def test_tool_install_hint_uses_distro_package_manager(_mock_platform):
    text = "ID=ubuntu\nID_LIKE=debian\n"
    hint = linux_env.tool_install_hint("smartctl", os_release_text=text)
    assert "sudo apt install smartmontools" in hint


@patch("agent.plugins.linux_env.platform.system", return_value="Linux")
def test_tool_install_hint_unknown_distro(_mock_platform):
    text = "ID=unknownos\nID_LIKE=\n"
    hint = linux_env.tool_install_hint("fio", os_release_text=text)
    assert "package manager" in hint


@patch("agent.plugins.linux_env.platform.system", return_value="Linux")
@patch("builtins.open", new_callable=mock_open, read_data="ID=debian\nID_LIKE=debian\n")
def test_detect_linux_capabilities_reads_os_release(_mock_file, _mock_platform):
    caps = linux_env.detect_linux_capabilities()
    assert caps["package_manager"] == "apt"


@patch("agent.plugins.linux_env.os.geteuid", return_value=0, create=True)
def test_is_root_user_true(_mock_geteuid):
    assert linux_env.is_root_user() is True


@patch("agent.plugins.linux_env.os.geteuid", return_value=1000, create=True)
def test_is_root_user_false(_mock_geteuid):
    assert linux_env.is_root_user() is False


def test_root_permission_hint_format():
    msg = linux_env.root_permission_hint("dmidecode")
    assert "root/sudo" in msg
    assert "dmidecode" in msg
