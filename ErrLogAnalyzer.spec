# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # [수정] 폰트 폴더를 실행 파일 내부 리소스에 포함
        ('app/assets/fonts', 'app/assets/fonts'),
        ('settings', 'settings'), # 설정 파일도 필요하다면 포함
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'reportlab.pdfbase.ttfonts',
        'reportlab.pdfbase.pdfmetrics',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.dates',
        'watchdog.observers',
        'watchdog.events',
        'PIL._tkinter_finder',
    ],
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

# [중요] EXE는 이제 가벼운 실행 파일 정보만 담습니다 (exclude_binaries=True)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ErrLogAnalyzer',
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
    icon=None,
)

# [중요] COLLECT 블록 추가: 모든 라이브러리를 폴더로 모읍니다
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ErrLogAnalyzer',
)