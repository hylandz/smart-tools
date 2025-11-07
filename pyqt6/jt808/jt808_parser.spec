# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['jt808_ui.py'],
    pathex=['jt808'], # 添加src路径
    binaries=[],
    datas=[('assets/icons/*.ico', 'assets/icons/')],
    hiddenimports=['jt808','pathlib'],  # 显式声明隐藏导入
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
    name='JT808BSJParser_v2.1.1.exe',
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
    icon='assets/icons/app.ico',  # 主程序图标
)
