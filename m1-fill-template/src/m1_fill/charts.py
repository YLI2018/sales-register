"""Keep the template's charts exactly as designed.

openpyxl (the library that writes the workbook) reads charts only partly and writes them back with default
formatting. After saving, this module copies the original chart definitions (xl/charts/chartN.xml) from the
source workbook into the saved file. Cell data is untouched. See docs/adr/0004-restore-charts-from-template.md.
"""
import shutil
import tempfile
import zipfile
from pathlib import Path


def chart_parts(xlsx: Path):
    """Names of the chart parts inside an .xlsx file, sorted."""
    with zipfile.ZipFile(xlsx) as z:
        return sorted(n for n in z.namelist() if n.startswith("xl/charts/chart") and n.endswith(".xml"))


def restore_charts(source: Path, saved: Path) -> int:
    """Replace the chart parts of `saved` with those of `source`. Returns the number of charts restored.

    Raises ValueError if the two files do not hold the same chart parts (the layout would not match).
    """
    src_parts, out_parts = chart_parts(source), chart_parts(saved)
    if src_parts != out_parts:
        raise ValueError(f"chart parts differ: template {src_parts}, saved {out_parts}")
    with zipfile.ZipFile(source) as zs:
        originals = {n: zs.read(n) for n in src_parts}
    mode = saved.stat().st_mode
    tmp = Path(tempfile.mkstemp(suffix=".xlsx")[1])
    with zipfile.ZipFile(saved) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = originals.get(info.filename, zin.read(info.filename))
            zout.writestr(info, data)
    shutil.move(str(tmp), saved)
    saved.chmod(mode & 0o777)   # keep the saved file's normal permissions (the temporary file is owner-only)
    return len(src_parts)
