# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/assets', 'assets')],
    hiddenimports=['pywhatkit', 'pyautogui', 'pandas', 'pyexcel', 'pyexcel.plugins.xls', 'pyexcel.plugins.xlsx', 'PIL.Image', 'PIL.ImageTk', 'openpyxl', 'xlrd', 'tkinter', 'threading', 'webbrowser'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhatsAppSender',
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
    icon=['src\\assets\\icon.ico'],
)
