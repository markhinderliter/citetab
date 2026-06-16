# PyInstaller spec — citetab onedir desktop app (v0.5 item 3b).
#
# onedir (COLLECT) build launching into citetab.app.main via citetab_app.py.
# The data-collection entries below are the freeze's load-bearing part: eyecite's
# reporter/court tables and pdfminer's CMaps are read at runtime and are NOT
# auto-detected, and citetab's own _bundled tree must ship so importlib.resources
# can resolve rules/profiles/schemas inside the frozen layout.
import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

entry = os.path.join(SPECPATH, "citetab_app.py")  # noqa: F821 - SPECPATH is PyInstaller-injected

datas = []
datas += collect_data_files("citetab")  # citetab/_bundled/{rules,profiles,schemas}
datas += collect_data_files("reporters_db")  # eyecite reporter tables (JSON)
datas += collect_data_files("courts_db")  # eyecite courts.json + data/places/*.txt
datas += collect_data_files("pdfminer")  # CMap *.json.gz (used via pdfplumber)
datas += collect_data_files("docx")  # python-docx default-docx-template tree

hiddenimports = []
hiddenimports += collect_submodules("eyecite")
hiddenimports += collect_submodules("citetab")

a = Analysis(
    [entry],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_cov", "mypy", "ruff"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="citetab",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # windowed: no console window for the double-click GUI path
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="citetab",
)
