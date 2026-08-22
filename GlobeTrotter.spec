# -*- mode: python ; coding: utf-8 -*-
# GlobeTrotter PyInstaller spec
# Build: pyinstaller GlobeTrotter.spec

import sys
from pathlib import Path

block_cipher = None
root = Path(".").resolve()

a = Analysis(
    ["run.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        # App source package
        ("app", "app"),
        # tkcalendar locale data
        ("*.tcl", "."),
    ],
    hiddenimports=[
        # CustomTkinter
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        # SQLAlchemy dialects
        "sqlalchemy.dialects.sqlite",
        # Pydantic internals
        "pydantic.deprecated.class_validators",
        "pydantic_core",
        # tkcalendar
        "tkcalendar",
        "babel.numbers",
        # Matplotlib backends
        "matplotlib.backends.backend_agg",
        "matplotlib.backends.backend_tkagg",
        # bcrypt
        "bcrypt",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "wx", "gi", "IPython"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GlobeTrotter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,        # No console window — pure GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",   # Uncomment if you add an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GlobeTrotter",
)
