# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['2929_ui.py'],
    pathex=['bsj2929'],
    binaries=[],
    datas=[('assets/icons/*.ico', 'assets/icons/')],
    hiddenimports=['bsj2929', 'tkinter', 'pathlib'],
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
    name='BSJ2929Parser_v1.1.4.exe',
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
    icon=['assets/icons/app.ico'],
)
