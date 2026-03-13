# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['H:\\Claude_work\\macro\\MacroRunner\\src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('H:\\Claude_work\\macro\\MacroRunner\\macros', 'macros')],
    hiddenimports=['win32com.client', 'pythoncom', 'tkinter', 'tkinter.ttk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    exclude_binaries=True,
    name='MacroRunner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MacroRunner',
)
