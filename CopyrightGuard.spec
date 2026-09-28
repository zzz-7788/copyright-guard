# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Conda stores these dependencies outside DLLs; include them for standalone Windows builds.
conda_bin = Path(sys.prefix) / 'Library' / 'bin'
# Avoid collecting unrelated DLLs from other tools on PATH (e.g. another ICU build).
if sys.platform == 'win32':
    windows_root = Path(os.environ.get('SystemRoot', 'C:/Windows'))
    os.environ['PATH'] = os.pathsep.join(map(str, (
        Path(sys.executable).parent, conda_bin, windows_root / 'System32', windows_root,
    )))
extra_binaries = [
    (str(conda_bin / name), '.')
    for name in ('sqlite3.dll', 'ffi.dll')
    if (conda_bin / name).is_file()
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=[('app/resources/styles/theme.qss', 'app/resources/styles')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CopyrightGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
