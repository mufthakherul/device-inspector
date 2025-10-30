# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for inspecta CLI tool.
Creates standalone executables for Windows and macOS.

Build commands:
  Windows: pyinstaller --clean inspecta.spec
  macOS:   pyinstaller --clean inspecta.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Define the analysis configuration
a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('samples/', 'samples/'),  # Include sample data for testing
        ('LICENSE.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'agent',
        'agent.cli',
        'agent.report',
        'agent.scoring',
        'agent.exceptions',
        'agent.logging_utils',
        'agent.plugins',
        'agent.plugins.inventory',
        'agent.plugins.smart',
        'click',
        'jsonschema',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_mock',
        'pytest_cov',
        'black',
        'ruff',
        'bandit',
        'safety',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='inspecta',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path if available
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='inspecta.app',
        icon=None,
        bundle_identifier='com.mufthakherul.inspecta',
        info_plist={
            'CFBundleName': 'Inspecta',
            'CFBundleDisplayName': 'Device Inspector',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
        },
    )
