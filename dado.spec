# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Dado - Your Budget Saver

import os
import sys

block_cipher = None

# Collect all hidden imports needed
hiddenimports = [
    'anthropic',
    'anthropic._client',
    'anthropic._types',
    'anthropic.types',
    'httpx',
    'httpcore',
    'h11',
    'anyio',
    'anyio._backends',
    'anyio._backends._asyncio',
    'sniffio',
    'certifi',
    'charset_normalizer',
    'idna',
    'socksio',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.pyplot',
    'bcrypt',
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'pydantic',
    'pydantic.main',
    'thefuzz',
    'thefuzz.fuzz',
    'thefuzz.process',
    'Levenshtein',
    'reportlab',
    'reportlab.lib.pagesizes',
    'reportlab.platypus',
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'sqlite3',
    'json',
    'csv',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test'],
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
    name='Dado',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No console window - pure GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Dado',
)
